
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

#TODO: Alguns processos o nome do socio/cliente esta ficando com o cpf ou cnpj.
#TODO: Alguns processos estao ficando sem cpf ou cnpj.


def get_dados_processos_tjmt(config, processos):
    install_chromedriver()

    user = config['tjmt']['user']
    password = config['tjmt']['password']
    urls = config['tjmt']['urls']
    valorMinimo = float(config['valorMinimo'])

    sheetId  = config['googleSheets']['sheetId']
    processos_planilha = getProcessosFromPlanilha(config, sheetId)

    driver = webdriver.Chrome()
    driver.set_window_size(1050, 1000)

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
            driver, consultaConfig)
        if valorAcaoProcesso >= valorMinimo:
            
            if not hasAdvogado(driver, consultaConfig):

                banco, cliente, socio, cnpj, cpf = get_partes(driver, consultaConfig)
                if socio != None and socio != '':

                    data_hora_distribuicao = get_data_hora_distribuicao(driver, consultaConfig)
                    documento = cnpj if cnpj != None and cnpj != '' else cpf

                    processo = {
                            'Data Distribuicao': [data_hora_distribuicao],
                            'Processo': [processo['Processo']],
                            'Valor': [valorAcaoProcesso],
                            'Cliente': [cliente],
                            'Socio': [socio],
                            'Documento': [documento],
                            'Banco': [banco],
                            'Tribunal' : ['TJMT'],
                            'Status': ['Aguardando telefones']
                    }

                    insert_processos_on_sheet(config, pd.DataFrame(processo))

                    dados_processos = pd.concat([
                        dados_processos,
                        pd.DataFrame(processo)
                    ])

    driver.quit()

    return dados_processos


def login(driver, loginConfig, user, password, retry=True):
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

    try:
        selector_wait_login = ".nome-sobrenome"
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector_wait_login))
        )
    except:
        if retry:
            login(driver, loginConfig, user, password, False)
        else:
            raise Exception('Não foi possível fazer login')

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

def hasAdvogado(driver, consultaConfig):
    poloPassivo = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['poloPassivo'])
    htmlLower = poloPassivo.get_attribute('innerHTML').lower()
    hasAdvogado = re.search(r'advogad', htmlLower)
    if hasAdvogado != None:
        return True
    
    return False

def get_partes(driver, consultaConfig):
    poloPassivo = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['poloPassivo'])

    reuBoxHtml = poloPassivo.get_attribute('innerHTML')
    hasAdvogado = re.search(r'advogado', reuBoxHtml.lower())
    if hasAdvogado != None:
        return '', '', ''

    poloAtivo = driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['poloAtivo']).text
    poloAtivo = poloAtivo.replace('\n', ' ')
    poloAtivo = poloAtivo.split('Polo ativo')[1].strip()
    nomeBanco = poloAtivo.split('- CNPJ')[0].strip()

    regexCnpj = "\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
    regexCpf = "\d{3}\.\d{3}\.\d{3}-\d{2}"

    poloPassivoText = poloPassivo.text
    poloPassivoText = poloPassivoText.replace('\n', ' ')
    poloPassivoText = poloPassivoText.split('Polo passivo')[1].strip()
    poloPassivoSplit = poloPassivoText.split(')')
    poloPassivoSplit = list(filter(None, poloPassivoSplit))

    cliente = ''
    socio = ''
    cnpj = ''
    cpf = ''

    if len(poloPassivoSplit) > 1:
        for parte in poloPassivoSplit:
            isCnpj = re.search(regexCnpj, parte)
            if isCnpj != None and cnpj == '':
                cnpj = isCnpj.group(0)
                cliente = parte.split('- CNPJ')[0].strip()
            
            isCpf = re.search(regexCpf, parte)
            if isCpf != None and cpf == '':
                cpf = isCpf.group(0)
                socio = parte.split('- CPF')[0].strip()

            if cnpj != '' and cpf != '':
                break
    else:
        cliente = ''
        socio = poloPassivoSplit[0].strip()
        cpf = re.search(regexCpf, poloPassivoSplit[0])
        cpf = cpf.group(0) if cpf != None else ''
    
    return nomeBanco, cliente, socio, cnpj, cpf

mesesAbreviados = {
    'jan': '01',
    'fev': '02',
    'mar': '03',
    'abr': '04',
    'mai': '05',
    'jun': '06',
    'jul': '07',
    'ago': '08',
    'set': '09',
    'out': '10',
    'nov': '11',
    'dez': '12'
}
def get_data_hora_distribuicao(driver, consultaConfig):
    data_hora_distribuicao = driver.find_elements(By.CSS_SELECTOR, consultaConfig['css']['dataHoraDistribuicaoProcesso'])
    data_hora_distribuicao = data_hora_distribuicao[-1]
    time.sleep(0.25)
    data_hora_distribuicao = data_hora_distribuicao.text

    data_split = data_hora_distribuicao.split(' ')
    dia = data_split[0]
    mes = mesesAbreviados[data_split[1].lower()]
    ano = data_split[2]
    
    return f'{dia}/{mes}/{ano}'

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosFromFile(config, arquivoTeste)

    dados_processos = get_dados_processos_tjmt(config, TJMT)
    print(dados_processos)
