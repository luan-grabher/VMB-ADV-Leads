
import pandas as pd
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def getProcessosComTelefone(config, processos):
    install()

    configAssertiva = config['assertiva']

    driver = webdriver.Chrome()

    login(driver, configAssertiva)

    input('Pressione enter para continuar...')

    driver.quit()

def login(driver, configAssertiva):
    loginConfig = configAssertiva['urls']['login']
    driver.get(loginConfig['url'])

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, loginConfig['css']['user']))
    ).send_keys(configAssertiva['user'])

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['password']).send_keys(configAssertiva['password'])

    driver.find_element(By.CSS_SELECTOR, loginConfig['css']['submit']).click()

if __name__ == "__main__":
    config = getConfig()

    processos = pd.read_json('./tmp/dados_processos.json')

    print(getProcessosComTelefone(config, processos))