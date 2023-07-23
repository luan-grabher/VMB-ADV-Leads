# A fazeres:
# [x] Conectar a arquivo de configuração json
# [x] Ler e-mails e achar ultimo e-mail nao lido com assunto '%Remessa do Dia%' e contém anexo .zip
# [x] Baixar arquivo zip do e-mail
# [x] Extrai arquivos do zip
# [ ] Conforme a lista de filtros de arquivos .xlsx no arquivo de configuração extrai os dados de cada arquivo com os filtros necessários
# [ ] Faz o filtro desses dados e pega o nro processo
# [ ] Login TJSP
# [ ] Entrar na pagina de detalhes do processo
# [ ] Parar se for menor que R$ 100.000,00
# [ ] Parar se no final ‘qto’ houver advogado
# [ ] Pega detalhes do processo nome da pessoa/empresa, valor, datas
# [ ] Pegar CNPJ/CPF em ‘Visualizar Autos’ → Petição Inicial
# [ ] Login Assertiva
# [ ] Consulta por CNPJ/CPF na Assertiva
# [ ] Clica em ‘buscar relacionados’ até desaparecer e pega 3 primeiros numeros com whatsapp habilitado
# [ ] Inserir Dados na planilha google
# [ ] Chamar No Whatsapp. Criar link com o numero e mensagem personalizada abre o whatsapp web e envia a mensagem.

from arquivoExcel import getDadosZip
from config import getConfig
from mailFinder import connect_to_gmail, find_unread_email_with_subject_and_attachment

def main():
    config = getConfig()
    username = config['gmail']['user']
    password = config['gmail']['pass']
    
    mail = connect_to_gmail(username, password)
    if not mail:
        return
    
    filter = config['gmail']['filter']
    attachment_filename = find_unread_email_with_subject_and_attachment(mail, filter)
    if not attachment_filename:
        return
    
    dadosExcel = getDadosZip(config, attachment_filename)

if __name__ == "__main__":
    main()

