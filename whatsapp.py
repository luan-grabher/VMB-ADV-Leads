import json
import re
import pywhatkit
import pandas as pd

from config import getConfig


def send_whatsapp_messages_to_processos(config, processos):
    messageTemplate = config['whatsapp']['messageTemplate']

    for index, processo in processos.iterrows():
        numero_processo = processo['Processo']
        socio = processo['Socio']
        banco = processo['Banco']
        message = messageTemplate.format(processo=numero_processo, socio=socio, banco=banco)

        if processo['Telefones'] is None:
            continue
        
        for telefone in json.loads(processo['Telefones']):
            telefone = re.sub(r'[^\d]', '', telefone)
            telefone = '+55' + telefone
            telefone = '+5551997668057'  #FOR TESTING PURPOSES ONLY, REMOVE THIS LINE AFTER TESTS
            pywhatkit.sendwhatmsg_instantly(telefone, message, wait_time=8, tab_close=True)

if __name__ == "__main__":
    config =  getConfig()

    processos_fakes = pd.DataFrame()
    processos_fakes['Processo'] = ['9999999-99.2023.8.26.0100', '1111111-99.2023.8.26.0100', '2222222-99.2023.8.26.0100']
    processos_fakes['Socio'] = ['FULANO DE TAL', 'CICLANO DE TAL', 'BELTRANO DE TAL']
    processos_fakes['Banco'] = ['Bradesco S/A', 'Itau S/A', 'Santander S/A']
    processos_fakes['Telefones'] = [json.dumps(['(51) 99766-8057', '(51) 99766-8057']), json.dumps(['(51) 99766-8057']), None]

    send_whatsapp_messages_to_processos(config, processos_fakes)

