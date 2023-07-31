import json
import os
import re
import pywhatkit
import pandas as pd
import webbrowser as web
import time
import pyautogui as pg
from pyautogui import hotkey, press
from urllib.parse import quote
from config import getConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

cookies_whatsapp = 'cookies_whatsapp.json'

def send_whatsapp_messages_to_processos(config, processos):
    messageTemplate = config['whatsapp']['messageTemplate']

    options = getBrowserOptions()
    driver  = webdriver.Chrome(options=options)
    loginWhatsapp(driver)    

    for index, processo in processos.iterrows():
        numero_processo = processo['Processo']
        socio = processo['Socio']
        banco = processo['Banco']
        message = messageTemplate.format(processo=numero_processo, socio=socio, banco=banco)

        if processo['Telefone'] is None:
            continue
        
        for telefone in json.loads(processo['Telefone']):
            telefone = re.sub(r'[^\d]', '', telefone)
            telefone = '+55' + telefone
            telefone = '+5551997668057'  #FOR TESTING PURPOSES ONLY, REMOVE THIS LINE AFTER TESTS

            sendMessage(driver, telefone, message)

def loginWhatsapp(driver):
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
    selectorMessageLoading = "div[data-testid='message-datetime']"

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
    
    isMessageCorrectlySent = False
    while not isMessageCorrectlySent:
        time.sleep(1)
        try:            
            driver.find_element(By.CSS_SELECTOR, selectorMessageLoading)            
        except:
            isMessageCorrectlySent = True
        

if __name__ == "__main__":
    config =  getConfig()

    nro_processo = '9999999-99.2023.8.26.0100'
    telefone = json.dumps(['+55 51 99766-8057'])

    quantidades_processos_testes = 10

    processos_fakes = pd.DataFrame()
    #put quantidades_processos_testes in range 'Processo', 'Socio', 'Banco', 'Telefone'
    processos_fakes['Processo'] = [nro_processo] * quantidades_processos_testes
    processos_fakes['Socio'] = ['Socio X'] * quantidades_processos_testes
    processos_fakes['Banco'] = ['Banco Y'] * quantidades_processos_testes
    processos_fakes['Telefone'] = [telefone] * quantidades_processos_testes


    send_whatsapp_messages_to_processos(config, processos_fakes)

