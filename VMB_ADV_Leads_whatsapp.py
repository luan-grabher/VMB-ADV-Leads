from config import getConfig
from easygui import choicebox
import pyautogui as pg

from googleSheets import atualizaProcessosFromPlanilha, getProcessosFromPlanilha
from whatsapp import send_whatsapp_messages_to_processos

def enviarWhatsPlanilhaGoogle(config):
    whatsapp_config = config['whatsapp']
    planilhasGoogleDisponiveis = whatsapp_config['planilhasGoogleDisponiveis']

    planilhaId = selecionaPlanilha(planilhasGoogleDisponiveis)
    processosPlanilha  = getProcessosFromPlanilha(config, planilhaId)

    processos_aguardando_whats = processosPlanilha[processosPlanilha['Status'] == 'Aguardando whats']

    if len(processos_aguardando_whats) == 0:
        pg.alert('Não há processos aguardando envio de whats')
        return
    
    processos_com_whats_enviados = send_whatsapp_messages_to_processos(config, processos_aguardando_whats)
    numeros_processos_whats_enviados = [processo['Processo'] for processo in processos_com_whats_enviados]
    
    #atualiza status apenas dos processos que foram enviados
    processosPlanilha.loc[
        processosPlanilha['Processo'].isin(numeros_processos_whats_enviados),
        'Status'
    ] = 'Enviado whats'


    #atualiza planilha
    atualizaProcessosFromPlanilha(config, planilhaId, processosPlanilha)

    pg.alert('Whats enviados com sucesso')

def selecionaPlanilha(planilhasGoogleDisponiveis):
    options = list(planilhasGoogleDisponiveis.keys())
    
    selected = choicebox("Selecione a planilha", "Planilhas disponíveis", options)
    planilhaId = planilhasGoogleDisponiveis[selected]

    return planilhaId

if __name__ == "__main__":
    config = getConfig()

    enviarWhatsPlanilhaGoogle(config)