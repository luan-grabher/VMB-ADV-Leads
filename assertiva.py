
import json
import re
import time
import pandas as pd
from chromedriver_install import install_chromedriver
from config import getConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from googleSheets import atualizaProcessosFromPlanilha, getProcessosFromPlanilha, insert_processos_on_sheet

regexCnpj = "\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
regexCpf = "\d{3}\.\d{3}\.\d{3}-\d{2}"

def putTelefonesOnProcessos(config):
    planilhaId = config['googleSheets']['sheetId']
    processos = getProcessosFromPlanilha(config, planilhaId)
    processosAguardandoTelefones = processos[processos['Status'] == 'Aguardando telefones']

    install_chromedriver()

    configAssertiva = config['assertiva']

    driver = webdriver.Chrome()
    driver.set_window_size(1000, 1000)

    login(driver, configAssertiva)

    processos['Telefone'] = None

    for index, processo in processosAguardandoTelefones.iterrows():
        telefone = getTelefone(driver, configAssertiva, processo)

        if telefone != None:            
            processo['Telefone'] = telefone
            processo['Status'] = 'Aguardando whats' 
            atualizaProcessosFromPlanilha(config, planilhaId, pd.DataFrame([processo]))

        time.sleep(2)     

    driver.quit()

    return processos

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

def aceitarCookies(driver, configCookies):
    isBotaoCookiesExists = True
    while isBotaoCookiesExists:
        try:
            driver.find_element(By.CSS_SELECTOR, configCookies['botaoCookies']).click()
            time.sleep(1)
        except:
            isBotaoCookiesExists = False
    
    isBotaoConfidencialAlertExists = True
    while isBotaoConfidencialAlertExists:
        try:
            driver.find_element(By.CSS_SELECTOR, configCookies['btnConfidencialAlert']).click()
            time.sleep(1)
        except:
            isBotaoConfidencialAlertExists = False


def getTelefone(driver, configAssertiva, processo):
    try:
        documento = processo['Documento']
        if not documento or documento == '':
            return None

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

        aceitarCookies(driver, configAssertiva['cookies'])

        divTelefones = None
        parent = tituloTelefones.find_element(By.XPATH, '..')
        while divTelefones is None:        
            hasMuiBoxRootClass = 'MuiBox-root' in parent.get_attribute('class')
            if hasMuiBoxRootClass:
                divTelefones = parent
            else:
                parent = parent.find_element(By.XPATH, '..')
            
        cardsTelefone = divTelefones.find_elements(By.CSS_SELECTOR, consultaConfig['css']['cardTelefone'])
        cardsComWhatsapp = getCardTelefonesWithWhatsapp(driver, consultaConfig, cardsTelefone)

        if len(cardsComWhatsapp) == 0:
            isbtnMaisTelefonesExists = True
            while isbtnMaisTelefonesExists:
                try:
                    driver.find_element(By.CSS_SELECTOR, consultaConfig['css']['btnMaisTelefones']).click()
                    time.sleep(1)
                except:
                    isbtnMaisTelefonesExists = False

            cardsTelefone = divTelefones.find_elements(By.CSS_SELECTOR, consultaConfig['css']['cardTelefone'])
            cardsComWhatsapp = getCardTelefonesWithWhatsapp(driver, consultaConfig, cardsTelefone)

        if len(cardsComWhatsapp) == 0:
            return None
        
        telefones = []
        for card in cardsComWhatsapp:
            telefone = card.find_element(By.CSS_SELECTOR, consultaConfig['css']['telefone']).text
            telefones.append(telefone)
        
        return json.dumps(telefones)
    
    except Exception as e:
        print('Erro ao buscar telefone do processo: ' + str(processo) + ' - ' + str(e))

def getCardTelefonesWithWhatsapp(driver, consultaConfig, cards):
    cardsComWhatsapp = []
    for card in cards:
        botaoWhatsapp = card.find_element(By.CSS_SELECTOR, consultaConfig['css']['telefoneBotaoWhatsapp'])
        hasDisableAttribute = botaoWhatsapp.get_attribute('disabled') is not None
        if not hasDisableAttribute:
            cardsComWhatsapp.append(card)
        

    return cardsComWhatsapp
    

if __name__ == "__main__":
    config = getConfig()

    print(putTelefonesOnProcessos(config))