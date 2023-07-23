
from arquivoExcel import getDadosZip
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd

def get_dados_processos_tjsp(config, processos):
    install()
    
    user = config['tjsp']['user']
    password = config['tjsp']['password']
    urls = config['tjsp']['urls']

    driver = webdriver.Chrome()

    login(driver, urls['login'], user, password)

    base_url_consulta = urls['consulta']['url']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        driver.get(base_url_consulta.replace('{processo}', processo['Processo']))
        
        input("Press Enter to continue...")


    #pause the driver to test
    input("Press Enter to continue...")

def login(driver, loginConfig, user, password):
    driver.get(loginConfig['url'])
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['user']).send_keys(user)
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjsp(config, TJSP)
    print(dados_processos)