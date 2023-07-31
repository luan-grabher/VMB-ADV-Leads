from __future__ import print_function
import json

import os.path
import time
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import getConfig

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentialsJson = 'google_sheets_credentials.json'
tokenJson = 'token_google.json'


def get_credentials():
    creds = None
    if os.path.exists(tokenJson):
        creds = Credentials.from_authorized_user_file(tokenJson, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentialsJson, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenJson, 'w') as token:
            token.write(creds.to_json())
        
    return creds

def insert_processos_on_sheet(config, processos):
    sheetId  = config['googleSheets']['sheetId']
    sheetName = config['googleSheets']['sheetName']
    credentials = get_credentials()
    
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    
    
    result = sheet.values().get(spreadsheetId=sheetId, range=sheetName).execute()
    values = result.get('values', [])

    colunaDataCadastro = 0    
    colunaDataDistribuicao = 1
    colunaCliente = 3
    colunaSocio = 4
    colunaBanco = 5
    colunaProcesso = 6
    colunaTribunal = 7
    colunaDocumento = 8
    colunaValor = 9
    colunaTelefone1 = 12
    colunaTelefone2 = 13
    colunaTelefone3 = 14

    lastEmptyRow = len(values) - 1
    for row in reversed(values):
        if len(row) > colunaProcesso + 1 and row[colunaProcesso] != '' and row[colunaProcesso] != None:
            break            

        lastEmptyRow -= 1

    dataCadastro = time.strftime("%d/%m/%Y")
    insertedValues = list()
    for index, processo in processos.iterrows():
        row = [None] * 15
        row[colunaDataCadastro] = dataCadastro
        row[colunaDataDistribuicao] = processo['Data Distribuicao']
        row[colunaCliente] = processo['Cliente']
        row[colunaSocio] = processo['Socio']
        row[colunaBanco] = processo['Banco']
        row[colunaProcesso] = processo['Processo']
        row[colunaTribunal] = processo['Tribunal']
        row[colunaDocumento] = processo['Documento']
        row[colunaValor] = processo['Valor']

        telefones = json.loads(processo['Telefone']) if processo['Telefone'] != None else []
        row[colunaTelefone1] = telefones[0] if len(telefones) > 0 else None
        row[colunaTelefone2] = telefones[1] if len(telefones) > 1 else None
        row[colunaTelefone3] = telefones[2] if len(telefones) > 2 else None

        insertedValues.append(row)
        lastEmptyRow += 1

    body = {
        'values': insertedValues
    }

    result = sheet.values().update(spreadsheetId=sheetId, range=sheetName + '!A' + str(lastEmptyRow - 1), valueInputOption='USER_ENTERED', body=body).execute()

if __name__ == '__main__':
    config =  getConfig()

    processos_fakes = pd.DataFrame()
    processos_fakes['Data Distribuicao'] = ['01/01/2021', '02/02/2021', '03/03/2021']
    processos_fakes['Processo'] = ['9999999-99.2023.8.26.0100', '1111111-99.2023.8.26.0100', '2222222-99.2023.8.26.0100']
    processos_fakes['Valor'] = [100000.00, 200000.00, 300000.00]
    processos_fakes['Cliente'] = ['EMPRESA X', '', None]
    processos_fakes['Socio'] = ['FULANO DE TAL', 'CICLANO DE TAL', 'BELTRANO DE TAL']
    processos_fakes['Documento'] = ['99.999.999/0001-01', '123.456.789-00', '987.654.321-00']
    processos_fakes['Banco'] = ['Bradesco S/A', 'Itau S/A', 'Santander S/A']
    processos_fakes['Telefone'] = [json.dumps(['(51) 99999-9999', '(51) 99999-9999']), json.dumps(['(51) 99999-9999']), None]
    processos_fakes['Tribunal'] = ['TJSP', 'TJRS', 'TJMT']

    insert_processos_on_sheet(config, processos_fakes)