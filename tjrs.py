
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

regexCnpj = "\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
regexCpf = "\d{3}\.\d{3}\.\d{3}-\d{2}"

def get_dados_processos_tjrs(config, processos):
    install_chromedriver()

    user = config['tjrs']['user']
    password = config['tjrs']['password']
    urls = config['tjrs']['urls']
    valorMinimo = float(config['valorMinimo'])

    
    sheetId  = config['googleSheets']['sheetId']
    processos_planilha = getProcessosFromPlanilha(config, sheetId)

    driver = webdriver.Chrome()
    driver.set_window_size(1050, 1000)

    login(driver, urls['login'], user, password)

    consultaConfig = urls['consulta']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        try:
            isProcessoExistsOnPlanilha = processos_planilha['Processo'].str.contains(processo['Processo']).any() if not processos_planilha.empty else False
            if isProcessoExistsOnPlanilha:
                dados_processos = pd.concat([dados_processos, processos_planilha[processos_planilha['Processo'].str.contains(processo['Processo'])]])
                continue

            isProcessoExistsOnDadosProcessos = dados_processos['Processo'].str.contains(processo['Processo']).any() if not dados_processos.empty else False
            if isProcessoExistsOnDadosProcessos:
                continue

            acessar_detalhes_processo(driver, consultaConfig, processo)

            valorAcaoProcesso = get_valor_acao_processo(
                driver, consultaConfig)
            if valorAcaoProcesso >= valorMinimo:

                banco, nome = get_partes(driver, consultaConfig)
                if nome != None and nome != '':

                    data_hora_distribuicao = get_data_hora_distribuicao(driver, consultaConfig)
                    documento = get_cnpj_ou_cpf(driver, consultaConfig)
                    if documento == None or documento == '':
                        continue

                    isCPF = re.search(regexCpf, documento)
                    isCNPJ = re.search(regexCnpj, documento)

                    processo = pd.DataFrame({
                        'Data Distribuicao': [data_hora_distribuicao],
                        'Processo': [processo['Processo']],
                        'Valor': [valorAcaoProcesso],
                        'Cliente': [nome if isCNPJ else None],
                        'Socio': [nome if isCPF else None],
                        'Documento': [documento],
                        'Banco': [banco],
                        'Tribunal' : ['TJRS']
                    })

                    insert_processos_on_sheet(config, processo)

                    dados_processos = pd.concat([
                        dados_processos,
                        processo
                    ])
        except Exception as e:
            print('Erro ao consultar processo: ' + processo['Processo'])
            print(e)
            continue

    driver.quit()

    return dados_processos


def login(driver, loginConfig, user, password):
    driver.get(loginConfig['url'])

    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['user']).send_keys(user)
    driver.find_element(
        By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(password)

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

    time.sleep(5)

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
    btnHistoricoValorCausa = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, consultaConfig['css']['btnHistoricoValorCausa']))
    )
    valorAcaoProcesso = driver.execute_script('return arguments[0].parentElement.textContent', btnHistoricoValorCausa)
    valorAcaoProcesso = valorAcaoProcesso.replace('R$ ', '').replace('.', '').replace(',', '.').strip()
    valorAcaoProcesso = float(valorAcaoProcesso)

    return valorAcaoProcesso


def get_partes(driver, consultaConfig):
    reuBox = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['reuBox'])

    reuBoxHtml = reuBox.get_attribute('innerHTML')
    hasAdvogado = re.search(r'advogado', reuBoxHtml.lower())
    if hasAdvogado != None:
        return '', ''

    try:
        nomeBanco = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['nomeBanco']).text
        nome = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['nomeSocio']).text

        return nomeBanco, nome
    except:
        pass
    
    return '', ''

def get_data_hora_distribuicao(driver, consultaConfig):
    data_hora_distribuicao = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['dataHoraDistribuicaoProcesso'])
    time.sleep(0.25)
    data_hora_distribuicao = data_hora_distribuicao.text
    data_hora_distribuicao = data_hora_distribuicao.split(' ')[0]
    
    return data_hora_distribuicao

def get_cnpj_ou_cpf(driver, consultaConfig):
    try:
        documentoSocio = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['documentoSocio'])
        documentoSocio = documentoSocio.text

        return documentoSocio
    except:
        return ''

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosFromFile(config, arquivoTeste)

    dados_processos = get_dados_processos_tjrs(config, TJRS)
    print(dados_processos)
