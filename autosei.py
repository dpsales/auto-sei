########################################################################
# busca todos os arquivos período explícito sem especificar a data
#########################################################################

import os
import csv
import re
import pandas as pd
import logging
import sys

from collections import OrderedDict
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


MODULE_DIR = Path(__file__).parent


logging.basicConfig(level=logging.INFO)

def build_path(subfolder):
    current_folder = os.getcwd()
    folderpath = os.path.join(current_folder, subfolder)
    folderpath = os.path.abspath(folderpath)
    if not os.path.exists(folderpath): os.makedirs(folderpath)
    return folderpath






def busca_documentos(
    # TO DO: entrar com o endereço SEI 
    url, 
    # TO DO: selecionar o tipo
    #separa a lista de documentos
    doc_type, #tipo de documento
    period = None,  # (start_date, end_date)
    output_dir="extraidos",
    charset="iso-8859-1",
    passwordfile='.password/password.txt'
):
    # nomes_arquivos = build_path('nomes_arquivos')
    _output_dir = build_path(output_dir)

    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)
    driver.get(url)

    # login page
    username_fld = driver.find_element("xpath", '//*[@id="txtUsuario"]')
    password_fld = driver.find_element("xpath", '//*[@id="pwdSenha"]')
    submit_button = driver.find_element("xpath", '//*[@id="sbmLogin"]')

    if not os.path.exists(passwordfile):
        message = "O arquivo de autenticação não existe. Colocar em .password/password.txt"
        logging.exception(message)
        raise Exception(message)

    with open(passwordfile) as f:
        _username, _password = f.read().strip().split(":", maxsplit=1)
        username_fld.send_keys(_username)
        password_fld.send_keys(_password)
        
    submit_button.click()
    del _password
    logging.info(f"Autenticando como {_username}")

    # home page (Chamar o item de menu de pesquisa)
    searching = driver.find_element("xpath", '//*[@id="main-menu"]/li[5]/a')
    searching.click()

    # search page - Selecionando os widgets a serem preenchidos
    logging.info(f"Preenchendo o formulário de pesquisa")
    
    # Combo tipo de documento
    # TODO: Transformar esta opçao em argumento
    
    def documento_type():
        l_documentos = (driver.find_element("xpath", '//*[@id="divSeriePesquisa"]').text())
        selecao = input('s_doc')
        for documento in l_documentos: 
            print(documento)
            if documento.text == selecao:
                return doc_type 

        return doc_type
        
    
    driver.find_element("xpath", '//*[@id="selSeriePesquisa"]').send_keys(doc_type)
    
    # Radio Data Documento - Período Explícito
    # TODO: Adicionar período de pesquisa como parâmetro
    driver.find_element("xpath", '//*[@id="optPeriodoExplicito"]').click()
    
    # Buscar
    driver.find_element("xpath", '//*[@id="sbmPesquisar"]').click()
    
    # Wait
    driver.implicitly_wait(0.5)
    
    # Manipulação de Período
    if period:
        start_date, end_date = period
    
        if start_date:
            if not end_date:
                logging.warn("Não foi passado end_date: end_date será considerado a data de hoje")
                end_date = date.today()        
            else:
                if start_date >= end_date:
                    message = "A data de início e fim da pesquisa não pode ser menor ou igual"
                    logging.error(message)
                    raise Exception(message)            
        else:
            logging.warn("Não foi passado start_date: ignorando end_date, caso informado")
            end_date = None
        
        date_mask = r"%d/%m/%Y"        
        
        driver.implicitly_wait(0.5)
        driver.find_element("xpath", '//*[@id="txtDataInicio"]').send_keys(start_date.strftime(date_mask))
        driver.find_element("xpath", '//*[@id="txtDataFim"]').send_keys(end_date.strftime(date_mask))

    # TODO: capturar na página de pesquisa a quantidade de documentos achados
    
    # getting files
    def get_files():       
        list_documents = []
        original_window = driver.current_window_handle 
        
        try:     
            page_docs_search = driver.find_element("xpath", '//*[@id="conteudo"]')
                        
            wait = WebDriverWait(driver, timeout=20)
            wait.until(lambda d : page_docs_search.is_displayed())
            
        except NoSuchElementException:
            logging.warn("Não tem resultados de pesquisa")
            sys.exit(-1)
           
        elements = page_docs_search.find_elements("xpath", 'table/tbody/tr[1]')
        
        for element in elements:
            pr_elemento = element.find_element("xpath", 'td[1]')
            
            # pega dados de cada documento na table de pesquisa
            processo = re.search('\d{5}\.\d{6}\/\d{4}\-\d{2}', pr_elemento.text).group()            
            documento = int(element.find_element("xpath", 'td[2]').text)
            url = pr_elemento.find_element("xpath", 'a[2]').get_attribute('href')
            
            # chama os links e salva os conteúdos em HTML
            driver.switch_to.new_window('tab')
            driver.get(url)
            
            out_html = build_path(os.path.join(_output_dir, "html"))
            html_extracted = os.path.join(out_html, f'documento_{documento}.html')
            
            # TODO: Procurar uma forma do selenium entregar o charset da página
            with open(html_extracted, 'w', encoding=charset) as file:
                file.write(driver.page_source)
            
            list_documents.append(
                {'processo': processo, 'documento': documento, 'url': url, "extraido": html_extracted, "charset": charset}
            )
            
            driver.close()
            driver.switch_to.window(original_window)
        
        return list_documents

    # pagination
    documentos = get_files()        
    
    while True:
        try:
            paginas_tag = driver.find_element(by=By.CLASS_NAME, value="paginas")
            
            proxima_pagina = paginas_tag.find_element("xpath", "span[last()]/a[@href]") 
            if not proxima_pagina.text.lower().strip().startswith("p"):
                logging.info(f"Paginação concluída.")
                break
            
            link = proxima_pagina.get_attribute('href')
            proxima_pagina.click()
            logging.info(f"Evento de click disparado: {link}") 
            
            documentos = documentos + get_files()
            
        except NoSuchElementException:
            logging.warn("A paginação acabou")
            break
        
        except StaleElementReferenceException:
            pass
            
        except Exception as e:
            logging.exception(f"Erro não esperado: {e}")
            sys.exit(-1)        

    driver.close()
    driver.quit()
    
    out_csv = os.path.join(_output_dir, "processos.csv")
    pd.DataFrame(documentos).to_csv(out_csv, index=False)
    
    return out_csv
    

############################################################# 
# para ler todos os arquivos em html e criar um DataFrame 
############################################################# 
def parse_csv_results(csvfile):
    with open(csvfile) as _csvfile:
        lista_df=[] 
        
        reader = csv.DictReader(_csvfile)
        
        for row in reader:
            extraido = row["extraido"]
            charset = row["charset"]
            
            with open(extraido, encoding=charset) as f: 
                soup = BeautifulSoup(f.read(), "html.parser") 
        
            tags = [tag for tag in soup.find("div", id="conteudo").children if len(tag.text.strip()) > 0 and not re.match(r"^\d+\.", tag.text.strip())] 
            # Cada HTML, um dicionário ordenado 
            dict_series = OrderedDict() 
        
            for index in range(len(tags)): 
                tag = tags[index] 
                
                if tag.name == "b": 
                    key = tag.text.strip().rstrip(":") 
                    value = tags[index + 1].text.strip() 
                    
                    dict_series[key] = value         
        
            # Empilhar todos os dicionários para criar o df e interpretar os dtypes 
            df = ( 
                pd.DataFrame([dict_series]) 
                    .apply(lambda x: pd.to_numeric(x.str.replace(",", "."), errors="ignore")) 
                    .apply(lambda x: x.replace("Sim", True).replace("Não", False))         
            ) 
            lista_df.append(df)
            
    return pd.concat(lista_df)


# Função de entrada
# def main(*args, **kwargs):
#     docs = busca_documentos()
#     results = parse_csv_results(docs)
    
#     print(results)

 # TO DO: entrar com o endereço SEI 
    # url='https://sip.sgb.gov.br/sip/login.php?sigla_orgao_sistema=CPRM&sigla_sistema=SEI&infra_url=L3NlaS8=', 
    # # TO DO: selecionar o tipo
    # #separa a lista de documentos
    # doc_type = "REMA - Empréstimo de Materiais ou Ex. Geológicos", #tipo de documento
    # period = None,  # (start_date, end_date)
    # output_dir="extraidos",
    # charset="iso-8859-1",
    # passwordfile='.password/password.txt'

def carregar_janela_principal():    
    import tkinter as tk    
    
    from tkinter import ttk
    from threading import Thread
    
    class CustomThread(Thread):    
        def __init__(self, group=None, target=None, name=None,
                    args=(), kwargs={}, Verbose=None):
            Thread.__init__(self, group, target, name, args, kwargs)
            self._return = None

        def run(self):
            if self._target is not None:
                self._return = self._target(*self._args, **self._kwargs)
                
        def join(self, *args):
            Thread.join(self, *args)
            return self._return
    
    FONT = "ArialBlack"

    janela = tk.Tk()
    janela.title("Tirando dados do SEI")
    janela.geometry("900x600")
    janela.config(bg="lightblue")
    janela.resizable(False, False)
    janela.iconbitmap(MODULE_DIR.joinpath("resources", "logo-sei.ico"))
    janela.rowconfigure(0, weight=1)
    janela.columnconfigure([5,5], weight=2)

    img = tk.PhotoImage(
        file=MODULE_DIR.joinpath("resources", "logo-sei.png"), 
        width=300, 
        height=200
    )
    
    logo = tk.Label(janela, image=img, background="lightblue")

    logo.grid(row=0, column= 0, padx=1, pady=3)

    mensagem1 = tk.Label(
        janela,
        text="Busca de dados dos documentos SEI",
        fg="gray",
        bg ="lightblue",
        font=(FONT, "20"),
        width=80,
        height=6
    )

    mensagem1.grid(
        row=0, 
        column= 1, 
        columnspan=20, 
        padx=1, 
        pady=3
    )

    # criar o Entry
    label_url = ttk.Label(
        janela,
        text="Url do sistema SEI",
        font=FONT
    )

    label_url.grid(
        row=2,
        column= 0,
        padx=10,
        pady=5,
        sticky="nsew"
    )

    entry_url = ttk.Entry(
        janela,
        width=35
    )

    entry_url.grid(
        row=2,
        column=1,
        columnspan=8,
        padx=10,
        pady=5,
        sticky="nsew"
    )

    label_doc_type = ttk.Label(
        janela,
        text="Qual é o tipo de documento que quer os dados?", 
        font=FONT
    )
    
    label_doc_type.grid(
        row=3,
        column=0,
        padx=10,
        pady=5,
        sticky="nsew"
    )

    entry_doc_type = ttk.Entry(
        janela, 
        width=35
    )

    entry_doc_type.grid(
        row=3,
        column=1,
        columnspan=8,
        padx=10,
        pady=5,
        sticky="nsew"
    )

    # Estilo do botão
    s = ttk.Style()
    s.configure("big.TButton", fg='black', bg="darkgray", font = (FONT, 16))
    
    # manipulador de evento click
    def schedule_check(t):
        """
        Schedule the execution of the `check_if_done()` function after
        one second.
        """
        janela.after(1000, check_if_done, t)

    def check_if_done(t):
        # If the thread has finished, re-enable the button and show a message.
        if not t.is_alive():
            print(t.join())      
            label_entrada.config(text="File successfully downloaded!")
            botao_entrada.config(state="normal")
        else:
            # Otherwise check again after one second.
            schedule_check(t)
        
    
    def botao_entrada_click():
        # Add label for waiting
        label_entrada.config(text="Buscando dados no SEI...")
        # Disable the button while downloading the file.
        botao_entrada.config(state="disabled")        
        
        # Start the crawler in a new thread.
        url = entry_url.get()
        doc_type = entry_doc_type.get()
        t = CustomThread(target=busca_documentos, args=(url, doc_type))
        t.start()
        # Start checking periodically if the thread has finished.
        schedule_check(t)
        

    botao_entrada = ttk.Button(
        janela,
        text="Salvar as entradas",
        style="big.TButton",
        command=botao_entrada_click
    )
    
    botao_entrada.grid(
        row=4,
        columnspan=7,
        padx=10,
        pady=5
    )

    # mostrar os dados para rodar o Script do SEI
    label_entrada = ttk.Label(
        janela,
        text="",
        font=(FONT, "10")
    )

    label_entrada.grid(
        row=10,
        column=0,
        padx=10,
        pady=5
    )

    # Mostrar a Janela 
    janela.mainloop()
    
    
def main():
    import argparse
    
    run_in_commandline = '--gui' not in sys.argv
    
    parser = argparse.ArgumentParser(
        description="Programa para capturar dados do SEI"
    )
    
    # argumentos obrigatórios para caso executar em linha de comando (gui = False)
    parser.add_argument("--url", required=run_in_commandline, help="URL do SEI a ser pesquisado")
    parser.add_argument("--doc", required=run_in_commandline, help="Tipo do documento SEI")
    parser.add_argument("--salvar", required=run_in_commandline, help="Diretório para salvar os resultados", type=Path)
    parser.add_argument("--passwordfile", required=run_in_commandline, help="Arquivo com a senha do SEI, em ASCII", default='.password/password.txt')
    
    # argumentos opcionais para linha de comando
    parser.add_argument("-di", "--data-inicio", type=date, help="Data de início da pesquisa", dest="di")
    parser.add_argument("-df", "--data-fim", help="Data de fim da pesquisa", dest="df")
    parser.add_argument("--charset", help="codificação de caracteres", default="iso-8859-1")
    
    # inicializar em MainWindow 
    parser.add_argument(
        "--gui", 
        help="Carregar em modo janela. Caso esta opção for fornecida, todas as demais serão ignoradas", 
        action="store_true", 
        dest="gui",
        required=False
    )
    
    # Início do tratamento dos argumentos
    args = parser.parse_args()
    
    if args.gui:
        carregar_janela_principal()
        return 0
    
    else:    
        docs = busca_documentos(
            url=args.url,
            doc_type=args.doc,
            period=(args.di or None, args.df or None),
            output_dir=args.salvar,
            charset=args.charset,
            passwordfile=args.passwordfile
        )
        
        results = parse_csv_results(docs)
        
        print(results)
        
if __name__ == '__main__':
    main()


