#########################################################################
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

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException


logging.basicConfig(level=logging.INFO)

def build_path(subfolder):
    current_folder = os.getcwd()
    folderpath = os.path.join(current_folder, subfolder)
    folderpath = os.path.abspath(folderpath)
    if not os.path.exists(folderpath): os.makedirs(folderpath)
    return folderpath


def busca_documetos(
    url='https://sip.sgb.gov.br/sip/login.php?sigla_orgao_sistema=CPRM&sigla_sistema=SEI&infra_url=L3NlaS8=', 
    doc_type = "REMA - Empréstimo de Materiais ou Ex. Geológicos",
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
def main(*args, **kwargs):
    # docs = busca_documetos()
    teste = parse_csv_results("temp/raspaidinhas.csv")
    
        
if __name__ == '__main__':
    main()