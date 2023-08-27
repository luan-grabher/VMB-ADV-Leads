import os
import re
import zipfile
from config import getConfig
import pandas as pd

def extract_zip(zip_filename, extract_to):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def getDadosFromFile(config, filefullpath):
    '''
    excel_name_filter = config['excel']['name']
    contains = excel_name_filter['contains'].split('%') if 'contains' in excel_name_filter else None
    notContains = excel_name_filter['notContains'].split('%') if 'notContains' in excel_name_filter else None

    filename = os.path.basename(filefullpath)
    if contains:
        for contain in contains:
            if contain not in filename:
                return None
    if notContains:
        for notContain in notContains:
            if notContain in filename:
                return None
    '''
        
    excel_file = filefullpath
    
    columns = config['excel']['columns']
    dados = pd.read_excel(excel_file, engine='openpyxl', usecols=columns, na_filter=True)

    filtros = {}
    for column in columns:
        if column in config['excel']['filtros']:
            filtros[column] = config['excel']['filtros'][column]

    #filtra as linhas que estao nos filtros das colunas
    dadosFiltrados = pd.DataFrame()
    for index, dado in dados.iterrows():
        isValid = True
        
        for filtro in filtros:
            if filtro in dado:
                isContainsAny = False
                isContains = True
                isNotContains = True

                if 'containsAny' in filtros[filtro]:
                    containsAny = filtros[filtro]['containsAny']
                    for contain in containsAny:
                        if re.search(contain.lower(), dado[filtro].lower()):
                            isContainsAny = True
                            break
                else:
                    isContainsAny = True

                if 'contains' in filtros[filtro]:
                    contains = filtros[filtro]['contains']
                    for contain in contains:
                        if not re.search(contain.lower(), dado[filtro].lower()):
                            isContains = False
                            break
                
                if 'notContains' in filtros[filtro]:
                    notContains = filtros[filtro]['notContains']

                    for notContain in notContains:
                        if re.search(notContain.lower(), dado[filtro].lower()):
                            isNotContains = False
                            break

                if not isContainsAny or not isContains or not isNotContains:
                    isValid = False
                    break
            
        if isValid:
            dadosFiltrados = pd.concat([dadosFiltrados, dado.to_frame().transpose()], ignore_index=True)

    if dadosFiltrados.empty:
        raise Exception('Nenhum processo com os filtros encontrado no arquivo excel')
    
    TJSP = dadosFiltrados.loc[dadosFiltrados['Tribunal'] == 'TJSP']
    TJRS = dadosFiltrados.loc[dadosFiltrados['Tribunal'] == 'TJRS']
    TJMT = dadosFiltrados.loc[dadosFiltrados['Tribunal'] == 'TJMT']

    return [TJSP, TJRS, TJMT]

if __name__ == "__main__":
    config = getConfig()

    arquivoTeste = './tmp/teste.xlsx'
    print(
        getDadosFromFile(config, arquivoTeste)
    )