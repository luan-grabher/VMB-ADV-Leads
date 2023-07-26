
import re
import pandas as pd
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import requests

regexCnpj = "\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
regexCpf = "\d{3}\.\d{3}\.\d{3}-\d{2}"

def getProcessosComTelefone(config, processos):
    install()

    configAssertiva = config['assertiva']

    driver = webdriver.Chrome()
    driver.set_window_size(1000, 1000)

    login(driver, configAssertiva)

    processosComTelefone = pd.DataFrame()

    for index, processo in processos.iterrows():
        telefone = getTelefone(driver, configAssertiva, processo)

        if telefone:
            processoComTelefone = processo.copy()
            processoComTelefone['Telefone'] = telefone

            processosComTelefone = pd.concat([
                processosComTelefone,
                pd.DataFrame(processoComTelefone)
            ])

    input('Pressione enter para continuar...')
    
    driver.quit()

def login(driver, configAssertiva):
    loginConfig = configAssertiva['urls']['login']
    driver.get(loginConfig['url'])

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, loginConfig['css']['user']))
    ).send_keys(configAssertiva['user'])

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(configAssertiva['password'])

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

    inicio_url = configAssertiva['urls']['inicio']['url']
    #wait for load on this page
    WebDriverWait(driver, 10).until(
        EC.url_matches(inicio_url)
    )


def getTelefone(driver, configAssertiva, processo):
    documento = processo['Documento']
    isCpf = re.search(regexCpf, documento) is not None
    tipoDocumento = 'cpf' if isCpf else 'cnpj'

    consultaConfig = configAssertiva['urls']['consulta']
    url = consultaConfig['url']
    urlConsultaNormalized = url.format(tipoDocumento = tipoDocumento)

    driver.get(urlConsultaNormalized)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnFinalidadeDeUso']))
    ).click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['finalidadeDeUsoConfirmacaoDeIdentidade']))
    ).click()

    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['inputDocumento']).send_keys(documento)
    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['btnConsultarDoc']).click()

    tituloTelefones = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['tituloTelefones']))
    )

    divTelefones = None
    parent = tituloTelefones.find_element(By.XPATH, '..')
    while divTelefones is None:        
        hasMuiBoxRootClass = 'MuiBox-root' in parent.get_attribute('class')
        if hasMuiBoxRootClass:
            divTelefones = parent
        else:
            parent = parent.find_element(By.XPATH, '..')


    input('Pressione enter para continuar...')
    
    

if __name__ == "__main__":
    config = getConfig()

    processos = pd.read_json('./tmp/dados_processos.json')

    print(getProcessosComTelefone(config, processos))