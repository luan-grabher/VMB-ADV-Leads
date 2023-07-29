
import re
from arquivoExcel import getDadosZip
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time


def get_dados_processos_tjmt(config, processos):
    install()

    user = config['tjmt']['user']
    password = config['tjmt']['password']
    urls = config['tjmt']['urls']
    valorMinimo = float(config['valorMinimo'])

    driver = webdriver.Chrome()
    driver.set_window_size(1050, 1000)

    login(driver, urls['login'], user, password)

    consultaConfig = urls['consulta']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        acessar_detalhes_processo(driver, consultaConfig, processo)

        valorAcaoProcesso = get_valor_acao_processo(
            driver, consultaConfig)
        if valorAcaoProcesso >= valorMinimo:

            banco, cliente, socio = get_partes(driver, consultaConfig)
            if socio != None and socio != '':

                data_hora_distribuicao = get_data_hora_distribuicao(driver, consultaConfig)
                documento = get_cnpj_ou_cpf(driver, consultaConfig)

                dados_processos = pd.concat([
                    dados_processos,
                    pd.DataFrame({
                        'Data Distribuicao': [data_hora_distribuicao],
                        'Processo': [processo['Processo']],
                        'Valor': [valorAcaoProcesso],
                        'Cliente': [cliente],
                        'Socio': [socio],
                        'Documento': [documento],
                        'Banco': [banco],
                        'Tribunal' : ['TJMT']
                    })
                ])

    driver.quit()

    return dados_processos


def login(driver, loginConfig, user, password):
    driver.get(loginConfig['url'])

    try:
        iframeLogin = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, loginConfig['css']['iframeLogin']))
        )
        driver.switch_to.frame(iframeLogin)
    except:
        pass

    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['user']).send_keys(user)
    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(password)

    try:
        driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()
    except:
        driver.find_element(By.CSS_SELECTOR, loginConfig['css']['btnEntrar']).click()


def acessar_detalhes_processo(driver, consultaConfig, processo):
    driver.get(consultaConfig['url'])

    nro_processo = processo['Processo']
    nro_processo = nro_processo.replace('.8.11.', '')
    nro_processo = re.sub(r'[^0-9]', '', nro_processo)
    
    inputPesquisa =  driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['inputPesquisa'])
    inputPesquisa.send_keys(nro_processo)
    inputPesquisa.send_keys(u'\ue007')

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnVisualizarProcesso']))
    ).click()

    try:
        WebDriverWait(driver, 3).until(
            EC.alert_is_present()
        ).accept()
    except:
        pass

    driver.switch_to.window(driver.window_handles[0])
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnAbrirDetalhes']))
    ).click()


def get_valor_acao_processo(driver, consultaConfig):
    maisDetalhes = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['maisDetalhes']))
    )
    time.sleep(0.25)
    maisDetalhes = maisDetalhes.text.lower()
    maisDetalhes = maisDetalhes.replace('\n', ' ')
    maisDetalhes = maisDetalhes.split('valor da causa')[1]
    maisDetalhes = maisDetalhes.split('segredo de justi')[0]

    regexReplace = "[^0-9\,]"
    valorAcao = re.sub(regexReplace, '', maisDetalhes)
    valorAcao = valorAcao.replace(',', '.')
    valorAcao = float(valorAcao)

    return valorAcao


def get_partes(driver, consultaConfig):
    reuBox = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['reuBox'])

    reuBoxHtml = reuBox.get_attribute('innerHTML')
    hasAdvogado = re.search(r'advogado', reuBoxHtml.lower())
    if hasAdvogado != None:
        return '', '', ''

    try:
        nomeBanco = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['nomeBanco']).text
        nomeSocio = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['nomeSocio']).text

        return nomeBanco, None, nomeSocio
    except:
        pass
    
    return '', '', ''

def get_data_hora_distribuicao(driver, consultaConfig):
    data_hora_distribuicao = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['dataHoraDistribuicaoProcesso'])
    time.sleep(0.25)
    data_hora_distribuicao = data_hora_distribuicao.text
    data_hora_distribuicao = data_hora_distribuicao.split(' ')[0]
    
    return data_hora_distribuicao

def get_cnpj_ou_cpf(driver, consultaConfig):
    documentoSocio = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['documentoSocio'])
    documentoSocio = documentoSocio.text

    return documentoSocio

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjmt(config, TJMT)
    print(dados_processos)
