#########################################################################
# busca todos os arquivos período explícito sem especificar a data
#########################################################################

import os
import re
import pandas as pd
import logging
import sys

from collections import OrderedDict

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


def busca_documetos(**kwargs):
    # nomes_arquivos = build_path('nomes_arquivos')
    dir_extracted_html = build_path('extraidos')

    driver = webdriver.Chrome()
    driver.implicitly_wait(0.5)
    url = 'https://sip.sgb.gov.br/sip/login.php?sigla_orgao_sistema=CPRM&sigla_sistema=SEI&infra_url=L3NlaS8='
    driver.get(url)

    # login page
    username_fld = driver.find_element("xpath", '//*[@id="txtUsuario"]')
    password_fld = driver.find_element("xpath", '//*[@id="pwdSenha"]')
    submit_button = driver.find_element("xpath", '//*[@id="sbmLogin"]')

    passwordfile = '.password/password.txt'

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
    doc_type = driver.find_element("xpath", '//*[@id="selSeriePesquisa"]')
    doc_type.send_keys('REMA - Empréstimo de Materiais ou Ex. Geológicos')
    
    # Radio Data Documento - Período Explícito
    # TODO: Adicionar período de pesquisa como parâmetro
    driver.find_element("xpath", '//*[@id="optPeriodoExplicito"]').click()
    
    # Buscar
    driver.find_element("xpath", '//*[@id="sbmPesquisar"]').click()

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
            
            html_extracted = os.path.join(dir_extracted_html, f'documento_{documento}.html')
            
            # TODO: Procurar uma forma do selenium entregar o charset da página
            with open(html_extracted, 'w', encoding='utf-8') as file:
                file.write(driver.page_source)
            
            list_documents.append(
                {'processo': processo, 'documento': documento, 'url': url, "extraido": html_extracted}
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
    
    return documentos
    

    ############################################################# 
    # para ler todos os arquivos em html e criar um DataFrame 
    ############################################################# 
    
    arquivo = os.listdir('arquivos') 
    fname = [f'arquivos/{arq}' for arq in arquivo if arq.endswith(".html")] 
    
    
    lista_df=[] 
    
    for i in fname: 
    
        with open(i, "r", encoding="iso-8859-1") as f: 
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


# Função de entrada
def main(*args, **kwargs):
    docs = busca_documetos()
        
if __name__ == '__main__':
    main()