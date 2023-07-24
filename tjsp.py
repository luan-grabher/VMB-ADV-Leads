
from arquivoExcel import getDadosZip
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time

def get_dados_processos_tjsp(config, processos):
    install()
    
    user = config['tjsp']['user']
    password = config['tjsp']['password']
    urls = config['tjsp']['urls']
    valorMinimo = float(config['valorMinimo'])

    driver = webdriver.Chrome()

    login(driver, urls['login'], user, password)

    consultaConfig = urls['consulta']
    base_url_consulta = consultaConfig['url']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        acessar_detalhes_processo(driver, consultaConfig, processo)

        valorAcaoProcesso = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['valorAcaoProcesso'])
        time.sleep(0.25)
        valorAcaoProcesso = valorAcaoProcesso.text
        valorAcaoProcesso = valorAcaoProcesso.replace('R$ ', '').replace('.', '').replace(',', '.')
        valorAcaoProcesso = float(valorAcaoProcesso)

        if valorAcaoProcesso >= valorMinimo:
            dados_processos = pd.concat([dados_processos, {
                'Processo': processo['Processo'],
                'Valor': valorAcaoProcesso,
            }])
        
        time.sleep(1)


    driver.quit()

    print(dados_processos)

def login(driver, loginConfig, user, password):
    driver.get(loginConfig['url'])
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['user']).send_keys(user)
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

def acessar_detalhes_processo(driver, consultaConfig, processo):
    '''
        "numeroDigitoAnoUnificado" : "#numeroDigitoAnoUnificado",
        "foroNumeroUnificado" : "#foroNumeroUnificado",
    '''
    tj_number = consultaConfig['tjNumber']

    nro_processo_completo = processo['Processo']
    nro_processo, nro_foro = nro_processo_completo.split(tj_number)


    driver.get(consultaConfig['url'])
    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['numeroDigitoAnoUnificado']).send_keys(nro_processo)
    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['foroNumeroUnificado']).send_keys(nro_foro)
    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['botaoConsultarProcessos']).click()

    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['botaoExpandirDadosSecundarios']).click()

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjsp(config, TJSP)
    print(dados_processos)