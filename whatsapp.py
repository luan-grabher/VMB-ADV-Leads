import json
import os
import re
from easygui import choicebox
import pandas as pd
import time
import pyautogui as pg
from urllib.parse import quote
from chromedriver_install import install_chromedriver
from config import getConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from googleSheets import atualizaProcessosFromPlanilha, getProcessosFromPlanilha

cookies_whatsapp = 'cookies_whatsapp.json'

def send_whatsapp_messages_to_processos(config, planilha_id):
    whatsappConfig =   config['whatsapp']

    processosPlanilha  = getProcessosFromPlanilha(config, planilha_id)
    processos_aguardando_whats = processosPlanilha[processosPlanilha['Status'] == 'Aguardando whats']

    if len(processos_aguardando_whats) == 0:
        raise Exception('Não há processos aguardando envio de whats')

    messageTemplatePath = "whatsappMensagemTemplate.txt"
    messageTemplate = open(messageTemplatePath, 'r', encoding='utf-8').read()

    options = getBrowserOptions()
    driver  = webdriver.Chrome(options=options)
    print('path do chromedriver utilizado: ', str(driver.service.path))

    loginWhatsapp(driver)    

    for index, processo in processos_aguardando_whats.iterrows():
        socio = processo['Socio'] if 'Socio' in processo else ''
        cliente = processo['Cliente'] if 'Cliente' in processo else ''
        
        if not cliente and not socio:
            continue

        message = messageTemplate.format(nome=cliente if cliente else socio, assinatura = whatsappConfig['assinatura']) 

        if processo['Telefone'] is None:
            continue
        
        telefones = json.loads(processo['Telefone'])
        for telefone in telefones:
            if not telefone:
                continue

            telefone = re.sub(r'[^\d]', '', telefone)
            telefone = '+55' + telefone
            telefone = '+5551997668057'  #FOR TESTING PURPOSES ONLY, REMOVE THIS LINE AFTER TESTS

            sendMessage(driver, telefone, message)

            processo['Status'] = 'Enviado whats'
            atualizaProcessosFromPlanilha(config, planilha_id, pd.DataFrame([processo]))


    driver.quit()

def loginWhatsapp(driver):
    try:
        driver.get("https://web.whatsapp.com/")
        time.sleep(10)

        selectorQrCode = "div[data-testid='qrcode']"
        selectorSide = "#side"
        
        hasQrCode = True
        while hasQrCode:

            try:
                driver.find_element(By.CSS_SELECTOR, selectorQrCode)            
                time.sleep(1)
            except:            
                hasQrCode = False

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selectorSide))
        )
    except Exception as e:
        print(e)
        pg.alert(text='Erro ao logar no whatsapp, tente novamente', title='Erro', button='OK')
        driver.quit()

def getBrowserOptions():
    options = webdriver.ChromeOptions() 

    existsSeleniumProfileFolder = os.path.exists('seleniumProfile')
    if not existsSeleniumProfileFolder:
        os.mkdir('seleniumProfile')
        re
    else:
        folderFullPath = os.path.join(os.getcwd(), 'seleniumProfile')
        options.add_argument(f"user-data-dir={folderFullPath}")

    return options

def sendMessage(driver, telefone, message):
    driver.get(f"https://web.whatsapp.com/send?phone={telefone}&text={quote(message)}")
    time.sleep(10)

    #todo: validar se é esse codigo mesmo
    selectorSendButton = "span[data-testid='send']"
    selectorSendButtonBlocked = "button[data-testid='ptt-ready-btn']"
    selectorMessages = "div[data-testid='msg-container']"
    selectorMessagesSuccessIcons = "div[data-testid='msg-container'] span[data-testid='msg-dblcheck']"
    #msg-check  - mensagem enviada mas nao recebida, tambem serve para mensagem recebida mas nao lida

    '''
        BOTAO NAO TEM WHATS:
        <button data-testid="popup-controls-ok" class="emrlamx0 aiput80m h1a80dm5 sta02ykp g0rxnol2 l7jjieqr hnx8ox4h f8jlpxt4 l1l4so3b le5p0ye3 m2gb0jvt rfxpxord gwd8mfxi mnh9o63b qmy7ya1v dcuuyf4k swfxs4et bgr8sfoe a6r886iw fx1ldmn8 orxa12fk bkifpc9x hjo1mxmu oixtjehm rpz5dbxo bn27j4ou snayiamo szmswy5k"><div class="tvf2evcx m0h2a7mj lb5m6g5c j7l1k36l ktfrpxia nu7pwgvd p357zi0d dnb887gk gjuq5ydh i2cterl7 ac2vgrno sap93d0t gndfcl4n"><div class="tvf2evcx m0h2a7mj lb5m6g5c j7l1k36l ktfrpxia nu7pwgvd p357zi0d dnb887gk gjuq5ydh i2cterl7 i6vnu1w3 qjslfuze ac2vgrno sap93d0t gndfcl4n" data-testid="content">OK</div></div></button>
    '''

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selectorSendButton))
    )

    sendButton = driver.find_element(By.CSS_SELECTOR, selectorSendButton)
    sendButton.click()

    isMessageInputEmpty = False
    while not isMessageInputEmpty:
        try:
            driver.find_element(By.CSS_SELECTOR, selectorSendButtonBlocked)
            isMessageInputEmpty = True
        except:
            time.sleep(1)
    time.sleep(2)
    
    isMessageCorrectlySent = False
    while not isMessageCorrectlySent:
        time.sleep(1)

        totalMessages = len(driver.find_elements(By.CSS_SELECTOR, selectorMessages))
        totalMessagesSuccess = len(driver.find_elements(By.CSS_SELECTOR, selectorMessagesSuccessIcons))

        if totalMessages == totalMessagesSuccess:
            isMessageCorrectlySent = True

if __name__ == "__main__":
    install_chromedriver()
    config =  getConfig()

    nro_processo = '9999999-99.2023.8.26.0100'
    telefone = json.dumps(['(51) 99766-8057'])

    quantidades_processos_testes = 10

    processos_fakes = pd.DataFrame()
    processos_fakes['Processo'] = [nro_processo] * quantidades_processos_testes
    processos_fakes['Cliente'] = ['Cliente X'] * quantidades_processos_testes
    processos_fakes['Socio'] = ['Socio X'] * quantidades_processos_testes
    processos_fakes['Banco'] = ['Banco Y'] * quantidades_processos_testes
    processos_fakes['Telefone'] = [telefone] * quantidades_processos_testes


    send_whatsapp_messages_to_processos(config, processos_fakes)

