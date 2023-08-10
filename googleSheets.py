from __future__ import print_function
import json

import os.path
import re
import time
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from urllib.parse import quote

from config import getConfig

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentialsJson = 'google_sheets_credentials.json'
tokenJson = 'token_google.json'

colunaDataCadastro = 0    
colunaDataDistribuicao = 1
colunaCliente = 3
colunaSocio = 4
colunaBanco = 5
colunaProcesso = 6
colunaTribunal = 7
colunaDocumento = 8
colunaValor = 9
colunaStatus = 10
colunaTelefone1 = 12
colunaTelefone2 = 13
colunaTelefone3 = 14


def get_credentials():
    creds = None
    if os.path.exists(tokenJson):
        creds = Credentials.from_authorized_user_file(tokenJson, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                os.remove(tokenJson)
                return get_credentials()
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

    lastEmptyRow = len(values) - 1
    for row in reversed(values):
        if len(row) > colunaProcesso + 1 and row[colunaProcesso] != '' and row[colunaProcesso] != None:
            break            

        lastEmptyRow -= 1
    
    firstEmptyRow = lastEmptyRow + 2 # 2 beacause the real first empty row is the next one to insert it

    dataCadastro = time.strftime("%d/%m/%Y")
    insertedValues = list()
    for index, processo in processos.iterrows():
        row = [None] * 15
        row[colunaDataCadastro] = dataCadastro
        row[colunaDataDistribuicao] = processo['Data Distribuicao'] if 'Data Distribuicao' in processo else None
        row[colunaCliente] = processo['Cliente'] if 'Cliente' in processo else None
        row[colunaSocio] = processo['Socio'] if 'Socio' in processo else None
        row[colunaBanco] = processo['Banco'] if 'Banco' in processo else None
        row[colunaProcesso] = processo['Processo'] if 'Processo' in processo else None
        row[colunaTribunal] = processo['Tribunal'] if 'Tribunal' in processo else None
        row[colunaDocumento] = processo['Documento'] if 'Documento' in processo else None
        row[colunaValor] = processo['Valor'] if 'Valor' in processo else None
        row[colunaStatus] = processo['Status'] if 'Status' in processo else 'Aguardando telefones'

        telefones_processo  = processo['Telefone'] if 'Telefone' in processo else None
        telefones = json.loads(telefones_processo) if telefones_processo != None else None
        lenTelefones = len(telefones) if telefones != None and type(telefones) is list else 0
        row[colunaTelefone1] = telefones[0] if lenTelefones > 0 else None
        row[colunaTelefone2] = telefones[1] if lenTelefones > 1 else None
        row[colunaTelefone3] = telefones[2] if lenTelefones > 2 else None

        insertedValues.append(row)
        lastEmptyRow += 1

    body = {
        'values': insertedValues
    }

    result = sheet.values().update(spreadsheetId=sheetId, range=sheetName + '!A' + str(firstEmptyRow), valueInputOption='USER_ENTERED', body=body).execute()

def getProcessosFromPlanilha(config, planilhaId):
    sheetName = config['googleSheets']['sheetName']

    processos = pd.DataFrame()

    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=planilhaId, range=sheetName).execute()
    values = result.get('values', [])
    values.pop(0)

    for row in values:
        processo = dict()
        processo['Data Distribuicao'] = row[colunaDataDistribuicao] if len(row) > colunaDataDistribuicao else None
        processo['Cliente'] = row[colunaCliente] if len(row) > colunaCliente else None
        processo['Socio'] = row[colunaSocio] if len(row) > colunaSocio else None
        processo['Banco'] = row[colunaBanco] if len(row) > colunaBanco else None
        processo['Processo'] = row[colunaProcesso] if len(row) > colunaProcesso else None
        processo['Tribunal'] = row[colunaTribunal] if len(row) > colunaTribunal else None
        processo['Documento'] = row[colunaDocumento] if len(row) > colunaDocumento else None
        processo['Valor'] = row[colunaValor] if len(row) > colunaValor else None
        processo['Status'] = row[colunaStatus] if len(row) > colunaStatus else None

        telefone1 = row[colunaTelefone1] if len(row) > colunaTelefone1 else None
        telefone2 = row[colunaTelefone2] if len(row) > colunaTelefone2 else None
        telefone3 = row[colunaTelefone3] if len(row) > colunaTelefone3 else None
        processo['Telefone'] = json.dumps([telefone1, telefone2, telefone3])

        isProcessoValido = processo['Processo'] != None and processo['Processo'] != ''
        if isProcessoValido:
            processos = pd.concat([processos, pd.DataFrame([processo])])

    return processos

def atualizaProcessosFromPlanilha(config, planilhaId, processos):
    whatsappConfig = config['whatsapp']
    messageTemplatePath = "whatsappMensagemTemplate.txt"
    messageTemplate = open(messageTemplatePath, 'r', encoding='utf-8').read()

    sheetName = config['googleSheets']['sheetName']

    credentials = get_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=planilhaId, range=sheetName).execute()
    values = result.get('values', [])

    #para cada processo, atualiza o status
    for row in values:
        isFindProcesso = False

        socio = row[colunaSocio] if len(row) > colunaSocio else None
        cliente = row[colunaCliente] if len(row) > colunaCliente else None
        nome = cliente if cliente else socio

        for index, processo in processos.iterrows():
            socio = processo['Socio'] if 'Socio' in processo else None
            cliente = processo['Cliente'] if 'Cliente' in processo else None
            nome = cliente if cliente else socio

            if len(row) > colunaProcesso and row[colunaProcesso] == processo['Processo']:
                #add columns if not exists
                while len(row) < colunaTelefone3 + 1:
                    row.append(None)

                row[colunaStatus] = processo['Status'] if 'Status' in processo else None

                if not 'Telefone' in processo or processo['Telefone'] == None or processo['Telefone'] == '':
                    continue

                telefones = json.loads(processo['Telefone'])
                lenTelefones = len(telefones) if telefones != None and type(telefones) is list else 0

                telefone1 = None
                if lenTelefones > 0:
                    telefone1 = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefones[0])

                telefone2 = None
                if lenTelefones > 1:
                    telefone2 = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefones[1])

                telefone3 = None
                if lenTelefones > 2:
                    telefone3 = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefones[2])
                                                            
                row[colunaTelefone1] = telefone1
                row[colunaTelefone2] = telefone2
                row[colunaTelefone3] = telefone3

                isFindProcesso = True
                break
            
        if not isFindProcesso:
            telefone1 = row[colunaTelefone1] if len(row) > colunaTelefone1 else None
            telefone2 = row[colunaTelefone2] if len(row) > colunaTelefone2 else None
            telefone3 = row[colunaTelefone3] if len(row) > colunaTelefone3 else None

            if telefone1:
                row[colunaTelefone1] = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefone1)

            if telefone2:
                row[colunaTelefone2] = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefone2)

            if telefone3:
                row[colunaTelefone3] = getTelefoneOrWhatsappLink(messageTemplate, whatsappConfig['assinatura'], nome, telefone3)

    body = {
        'values': values
    }

    result = sheet.values().update(spreadsheetId=planilhaId, range=sheetName + '!A1', valueInputOption='USER_ENTERED', body=body).execute()    

def getTelefoneOrWhatsappLink(messageTemplate, assinatura, nome, phone):
    if not nome:
        return phone

    

    phone = re.sub(r'[^\d]', '', phone)
    label = f'({phone[0:2]}) {phone[2:]}'

    phone = '+55' + phone    

    message = messageTemplate.format(nome=nome, assinatura = assinatura)
    whatsapp_link = f"https://web.whatsapp.com/send?phone={phone}&text={quote(message)}"
    return '=HYPERLINK("' + whatsapp_link + '";"' + label + '")'
    

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

    #insert_processos_on_sheet(config, processos_fakes)

    atualizaProcessosFromPlanilha(config, config['googleSheets']['sheetId'], processos_fakes)