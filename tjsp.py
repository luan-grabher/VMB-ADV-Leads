
import re
from arquivoExcel import getDadosFromFile
from chromedriver_install import install_chromedriver
from config import getConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time

from googleSheets import getProcessosFromPlanilha, insert_processos_on_sheet


def get_dados_processos_tjsp(config, processos):
    install_chromedriver()

    user = config['tjsp']['user']
    password = config['tjsp']['password']
    urls = config['tjsp']['urls']
    valorMinimo = float(config['valorMinimo'])

    sheetId  = config['googleSheets']['sheetId']
    processos_planilha = getProcessosFromPlanilha(config, sheetId)

    driver = webdriver.Chrome()

    login(driver, urls['login'], user, password)

    consultaConfig = urls['consulta']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        isProcessoExistsOnPlanilha = processos_planilha['Processo'].str.contains(processo['Processo']).any() if not processos_planilha.empty else False
        if isProcessoExistsOnPlanilha:
            dados_processos = pd.concat([dados_processos, processos_planilha[processos_planilha['Processo'].str.contains(processo['Processo'])]])
            continue

        isProcessoExistsOnDadosProcessos = dados_processos['Processo'].str.contains(processo['Processo']).any() if not dados_processos.empty else False
        if isProcessoExistsOnDadosProcessos:
            continue

        acessar_detalhes_processo(driver, consultaConfig, processo)

        valorAcaoProcesso = get_valor_acao_processo(
            driver, consultaConfig, valorMinimo)
        if valorAcaoProcesso >= valorMinimo:

            banco, cliente, socio = get_partes(driver, consultaConfig)
            if 'Advogad' not in cliente and 'Advogad' not in socio:
                data_hora_distribuicao = get_data_hora_distribuicao(driver, consultaConfig)
                documento = get_cnpj_ou_cpf(driver, consultaConfig)

                processo = pd.DataFrame({
                    'Data Distribuicao': [data_hora_distribuicao],
                    'Processo': [processo['Processo']],
                    'Valor': [valorAcaoProcesso],
                    'Cliente': [cliente],
                    'Socio': [socio],
                    'Documento': [documento],
                    'Banco': [banco],
                    'Tribunal' : ['TJSP']
                })

                insert_processos_on_sheet(config, processo)

                dados_processos = pd.concat([
                    dados_processos,
                    processo
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


def acessar_detalhes_processo(driver, consultaConfig, processo):
    tj_number = consultaConfig['tjNumber']

    nro_processo_completo = processo['Processo']
    nro_processo, nro_foro = nro_processo_completo.split(tj_number)

    driver.get(consultaConfig['url'])
    driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['numeroDigitoAnoUnificado']).send_keys(nro_processo)
    driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['foroNumeroUnificado']).send_keys(nro_foro)
    driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['botaoConsultarProcessos']).click()

    driver.find_element(
        By.CSS_SELECTOR, consultaConfig['css']['botaoExpandirDadosSecundarios']).click()


def get_valor_acao_processo(driver, consultaConfig, valorMinimo):
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
        driver.execute_script("arguments[0].click();", btnTodasPartes)
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
    driver.execute_script("arguments[0].click();", btnVisualizarAutos)

    btnPrimeiraPagina = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnPrimeiraPagina']))
    )
    driver.execute_script("arguments[0].click();", btnPrimeiraPagina)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", btnPrimeiraPagina) #as vezes buga, entao clica duas vezes p
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
    if not posicaoPrimeiroCNPJ:
        return None

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
    TJSP, TJRS, TJMT = getDadosFromFile(config, arquivoTeste)

    dados_processos = get_dados_processos_tjsp(config, TJSP)
