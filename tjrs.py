
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


def get_dados_processos_tjrs(config, processos):
    install()

    user = config['tjrs']['user']
    password = config['tjrs']['password']
    urls = config['tjrs']['urls']
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
            if 'Advogad' not in cliente and 'Advogad' not in socio:
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
                        'Tribunal' : ['TJRS']
                    })
                ])

    driver.quit()

    return dados_processos


def login(driver, loginConfig, user, password):
    driver.get(loginConfig['url'])

    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['user']).send_keys(user)
    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(password)

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

    resolveuCaptcha = False
    while not resolveuCaptcha:
        hasHashOnUrl = re.search(r'hash=', driver.current_url)
        resolveuCaptcha = hasHashOnUrl != None


def acessar_detalhes_processo(driver, consultaConfig, processo):
    nro_processo = processo['Processo']
    
    inputPesquisa =  driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['inputPesquisa'])
    inputPesquisa.clear()
    inputPesquisa.send_keys(nro_processo)
    inputPesquisa.send_keys(u'\ue007')


def get_valor_acao_processo(driver, consultaConfig):
    valorAcaoProcesso = driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['valorAcaoProcesso'])
    time.sleep(0.25)
    valorAcaoProcesso = valorAcaoProcesso.text
    valorAcaoProcesso = valorAcaoProcesso.replace(
        'R$ ', '').replace('.', '').replace(',', '.')
    valorAcaoProcesso = float(valorAcaoProcesso)

    return valorAcaoProcesso


def get_partes(driver, consultaConfig):
    partes_css  = consultaConfig['css']['todasPartes']

    btnTodasPartes = None
    try:
        btnTodasPartes = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['btnMostrarTodasPartes'])
    except:
        pass

    if btnTodasPartes:
        btnTodasPartes.click()
    else:
        partes_css = consultaConfig['css']['partesPrincipais']

    partes = driver.find_elements(By.CSS_SELECTOR, partes_css)
    partes = [parte.find_elements(By.TAG_NAME, 'td')[1] for parte in partes]
    time.sleep(0.25)

    banco = partes[0].text.lower()
    banco = banco.split('advogad')[0].replace('\n', ' ').strip()
    banco = ' '.join([word[0].upper() + word[1:] for word in banco.split(' ')])
    banco = banco.replace('Banco ', '').strip()

    if banco.startswith('Do Brasil'):
        banco = 'Banco ' + banco

    quantidade_partes = len(partes)
    if quantidade_partes == 2:
        return banco, '', partes[1].text
    elif quantidade_partes > 2:
        return banco, partes[1].text, partes[2].text
    
    return banco, '', ''

def get_data_hora_distribuicao(driver, consultaConfig):
    data_hora_distribuicao = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['dataHoraDistribuicaoProcesso'])
    time.sleep(0.25)
    data_hora_distribuicao = data_hora_distribuicao.text
    data_hora_distribuicao = data_hora_distribuicao.split(' ')[0]
    
    return data_hora_distribuicao

def get_cnpj_ou_cpf(driver, consultaConfig):
    btnVisualizarAutos = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['btnVisualizarAutos'])
    driver.execute_script("arguments[0].removeAttribute('target')", btnVisualizarAutos)
    btnVisualizarAutos.click()

    btnPrimeiraPagina = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnPrimeiraPagina']))
    )
    btnPrimeiraPagina.click()
    time.sleep(1)
    btnPrimeiraPagina.click() #as vezes buga, entao clica duas vezes p
    time.sleep(1)

    iframePdf = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['iframePdf'])
    driver.switch_to.frame(iframePdf)

    textoPDF = ''
    cssPaginaPDF = consultaConfig['css']['paginaPDF']
        
    primeiraPagina = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, cssPaginaPDF.replace("{numero_pagina}", '1')))
    )
    time.sleep(0.5)
    textoPDF = primeiraPagina.text

    
    segundaPagina = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, cssPaginaPDF.replace("{numero_pagina}", '2')))
    )
    time.sleep(0.5)
    textoPDF += ' ' + segundaPagina.text
    

    textoPDF = textoPDF.replace('\n', ' ').strip()
    textoPDF = textoPDF.replace('  ', ' ').strip()
    textoPDF = textoPDF.replace('/ ', '/').strip()
    textoPDF = textoPDF.replace(' /', '/').strip()
    textoPDF = textoPDF.replace(' .', '.').strip()
    textoPDF = textoPDF.replace('. ', '.').strip()
    textoPDF = textoPDF.replace(' -', '-').strip()
    textoPDF = textoPDF.replace('- ', '-').strip()
    textoPDF = re.sub(r"(\d) \.", r"\1.", textoPDF)
    textoPDF = textoPDF.lower()

    regexCnpj = "\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
    regexCpf = "\d{3}\.\d{3}\.\d{3}-\d{2}"

    posicaoPrimeiroCNPJ = re.search(regexCnpj, textoPDF)
    textoAposCnpjBanco = textoPDF[posicaoPrimeiroCNPJ.end():]

    primeiroCnpjAposBanco = re.search(regexCnpj, textoAposCnpjBanco)
    if primeiroCnpjAposBanco:
        primeiroCnpjAposBanco = primeiroCnpjAposBanco.group(0)
        return primeiroCnpjAposBanco
    
    primeiroCpfAposBanco = re.search(regexCpf, textoAposCnpjBanco)
    if primeiroCpfAposBanco:
        primeiroCpfAposBanco = primeiroCpfAposBanco.group(0)
        return primeiroCpfAposBanco
    
    primeiroCPF = re.search(regexCpf, textoPDF)
    if primeiroCPF:
        primeiroCPF = primeiroCPF.group(0)
        return primeiroCPF

    return None

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjrs(config, TJRS)
    print(dados_processos)
