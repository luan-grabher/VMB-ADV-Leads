
from arquivoExcel import getDadosZip
from config import getConfig
from chromedriver_autoinstaller import install
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time


def get_dados_processos_tjsp(config, processos):
    install()

    user = config['tjsp']['user']
    password = config['tjsp']['password']
    urls = config['tjsp']['urls']
    valorMinimo = float(config['valorMinimo'])

    driver = webdriver.Chrome()

    login(driver, urls['login'], user, password)

    consultaConfig = urls['consulta']
    base_url_consulta = consultaConfig['url']

    dados_processos = pd.DataFrame()
    for index, processo in processos.iterrows():
        acessar_detalhes_processo(driver, consultaConfig, processo)

        valorAcaoProcesso = get_valor_acao_processo(
            driver, consultaConfig, valorMinimo)
        if valorAcaoProcesso >= valorMinimo:

            banco, cliente, socio = get_partes(driver, consultaConfig)
            if 'Advogad' not in cliente and 'Advogad' not in socio:
                data_hora_distribuicao = get_data_hora_distribuicao(driver, consultaConfig)

                dados_processos = pd.concat([
                    dados_processos,
                    pd.DataFrame({
                        'Data Distribuicao': [data_hora_distribuicao],
                        'Processo': [processo['Processo']],
                        'Valor': [valorAcaoProcesso],
                        'Cliente': [cliente],
                        'Socio': [socio],
                        'Banco': [banco]
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

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/arquivo.zip'
    TJSP, TJRS, TJMT = getDadosZip(config, arquivoTeste)

    dados_processos = get_dados_processos_tjsp(config, TJSP)
    print(dados_processos)
