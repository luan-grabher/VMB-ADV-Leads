from config import getConfig
from easygui import choicebox
import pyautogui as pg

from googleSheets import atualizaProcessosFromPlanilha, getProcessosFromPlanilha
from whatsapp import send_whatsapp_messages_to_processos

def enviarWhatsPlanilhaGoogle(config):
    try:
        whatsapp_config = config['whatsapp']
        planilhasGoogleDisponiveis = whatsapp_config['planilhasGoogleDisponiveis']

        planilhaId = selecionaPlanilha(planilhasGoogleDisponiveis)
        send_whatsapp_messages_to_processos(config, planilhaId)

        pg.alert('Mensagens via Whatsapp enviadas com sucesso')
    except Exception as e:
        pg.alert(str(e))

def selecionaPlanilha(planilhasGoogleDisponiveis):
    options = list(planilhasGoogleDisponiveis.keys())
    
    selected = choicebox("Selecione a planilha", "Planilhas disponíveis", options)
    if not selected:
        raise Exception('Nenhuma planilha selecionada, programa encerrado')

    planilhaId = planilhasGoogleDisponiveis[selected]

    return planilhaId

if __name__ == "__main__":
    config = getConfig()

    enviarWhatsPlanilhaGoogle(config)