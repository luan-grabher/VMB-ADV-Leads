from config import getConfig
from googleSheets import getProcessosFromPlanilha


def main():
    config = getConfig()

    sheetId  = config['googleSheets']['sheetId']
    processos_planilha = getProcessosFromPlanilha(config, sheetId)

    processo = {
        "Processo": "99999"
    }

    if processos_planilha.empty:
        print('Planilha vazia')
        return

    #verifica se algum processo da planilha tem o mesmo número do processo que está sendo consultado
    isProcessoExistsOnPlanilha = processos_planilha['Processo'].str.contains(processo['Processo']).any()

    print(processos_planilha, isProcessoExistsOnPlanilha)

if __name__ == "__main__":
    main()