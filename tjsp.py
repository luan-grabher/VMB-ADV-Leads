
from arquivoExcel import getDadosZip
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By

def get_dados_processos_tjsp(config, processos):
    install()
    
    user = config['tjsp']['user']
    password = config['tjsp']['password']
    urls = config['tjsp']['urls']

    driver = webdriver.Chrome()
    driver.get(urls['login']['url'])

    #login
    driver.find_element(By.CSS_SELECTOR, urls['login']['css']['user']).send_keys(user)
    driver.find_element(By.CSS_SELECTOR, urls['login']['css']['password']).send_keys(password)
    driver.find_element(By.CSS_SELECTOR, urls['login']['css']['submit']).click()


    #pause the driver to test
    input("Press Enter to continue...")

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjsp(config, TJSP)
    print(dados_processos)