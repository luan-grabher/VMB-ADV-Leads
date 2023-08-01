# A fazeres:
# [x] Conectar a arquivo de configuração json
# [x] Ler e-mails e achar ultimo e-mail nao lido com assunto '%Remessa do Dia%' e contém anexo .zip
# [x] Baixar arquivo zip do e-mail
# [x] Extrai arquivos do zip
# [x] Conforme a lista de filtros de arquivos .xlsx no arquivo de configuração extrai os dados de cada arquivo com os filtros necessários
# [x] Faz o filtro desses dados e pega o nro processo
# [x] Login TJSP
# [x] Entrar na pagina de detalhes do processo
# [x] Parar se for menor que R$ 100.000,00
# [x] Parar se no final ‘qto’ houver advogado
# [x] Pega detalhes do processo nome da pessoa/empresa, valor, datas
# [x] Pegar CNPJ/CPF em ‘Visualizar Autos’ → Petição Inicial
# [x] Login Assertiva
# [x] Consulta por CNPJ/CPF na Assertiva
# [x] Clica em ‘buscar relacionados’ até desaparecer e pega 3 primeiros numeros com whatsapp habilitado
# [x] Inserir Dados na planilha google
# [x] Chamar No Whatsapp. Criar link com o numero e mensagem personalizada abre o whatsapp web e envia a mensagem.

from arquivoExcel import getDadosFromFile
from assertiva import getProcessosComTelefone
from config import getConfig
from googleSheets import insert_processos_on_sheet
from mailFinder import connect_to_gmail, find_unread_email_with_subject_and_attachment
from tjmt import get_dados_processos_tjmt
from tjrs import get_dados_processos_tjrs
from tjsp import get_dados_processos_tjsp
import pandas as pd
from tkinter import Tk, filedialog, messagebox

from whatsapp import send_whatsapp_messages_to_processos

def main():
    config = getConfig()
    username = config['gmail']['user']
    password = config['gmail']['pass']
    
    '''
    mail = connect_to_gmail(username, password)
    if not mail:
        return
    
    filter = config['gmail']['filter']
    attachment_filename = find_unread_email_with_subject_and_attachment(mail, filter)
    if not attachment_filename:
        return
    ''' #NÃO APAGA O CODIGO, POIS PODE SERR RESTAURADO SE FOR UTILIZAR O ROBÔ FULL AUTOMATICO

    #TODO: Salvar informações na planilha do google separada da viviane e luana com status 'aguardando envio whats'
    #TODO: Separar envio de whats em outra execução que seleciona ou a planilha viviane ou a luana com status 'aguardando envio whats' e grava status 'enviado whats' ou 'erro' na planilha
    #TODO: Fazer testes com dados atualizados
    #TODO: Correções de bugs
    #TODO: 

    Tk().withdraw()
    messagebox.showinfo('Selecione o arquivo xlsx da remessa do dia', 'Selecione o arquivo xlsx da remessa do dia')
    attachment_filename = filedialog.askopenfilename(defaultextension='.xlsx', filetypes=[('Arquivo Excel', '*.xlsx')])

    if not attachment_filename:
        messagebox.showerror('Arquivo excel não selecionado', 'Arquivo excel não selecionado')
        return

    isXlsx = attachment_filename.endswith('.xlsx')
    if not isXlsx:
        messagebox.showerror('Arquivo excel não selecionado', 'Arquivo excel não selecionado')
        return
    
    
    TJSP, TJRS, TJMT = getDadosFromFile(config, attachment_filename)

    processosTJMT = get_dados_processos_tjmt(config, TJMT) if len(TJMT) > 0 else pd.DataFrame()
    processosTJRS = get_dados_processos_tjrs(config, TJRS) if len(TJRS) > 0 else pd.DataFrame()
    processosTJSP = get_dados_processos_tjsp(config, TJSP) if len(TJSP) > 0 else pd.DataFrame()

    processos = pd.concat([processosTJSP, processosTJRS, processosTJMT], ignore_index=True)

    processos_com_telefone = getProcessosComTelefone(config, processos)
    
    insert_processos_on_sheet(config, processos_com_telefone)

    send_whatsapp_messages_to_processos(config, processos_com_telefone)

if __name__ == "__main__":
    main()

