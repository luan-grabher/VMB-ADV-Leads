import json
import os
import re
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

cookies_whatsapp = 'cookies_whatsapp.json'

def send_whatsapp_messages_to_processos(config, processos):
    whatsappConfig =   config['whatsapp']

    messageTemplatePath = "whatsappMensagemTemplate.txt"
    messageTemplate = open(messageTemplatePath, 'r', encoding='utf-8').read()

    options = getBrowserOptions()
    driver  = webdriver.Chrome(options=options)
    print('path do chromedriver utilizado: ', str(driver.service.path))

    loginWhatsapp(driver)    

    processos_com_whats_enviados = []
    for index, processo in processos.iterrows():
        socio = processo['Socio']
        cliente = processo['Cliente']
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

            processos_com_whats_enviados.append(processo)
        
        processos_com_whats_enviados = pd.DataFrame(processos_com_whats_enviados)
        processos_com_whats_enviados.drop_duplicates(subset=['Processo'], inplace=True)
        processos_com_whats_enviados = processos_com_whats_enviados.to_dict('records')


    driver.quit()
    return processos_com_whats_enviados

def loginWhatsapp(driver):
    try:
        driver.get("https://web.whatsapp.com/")
        time.sleep(5)

        selectorQrCode = "div[data-testid='qrcode']"
        selectorSide = "#side"
        
        hasQrCode = True
        while hasQrCode:

            try:
                driver.find_element(By.CSS_SELECTOR, selectorQrCode)            
                time.sleep(1)
            except:            
                hasQrCode = False

        WebDriverWait(driver, 20).until(
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

