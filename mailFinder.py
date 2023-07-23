import imaplib
import email
import os
from config import getConfig

def connect_to_gmail(username, password):
    try:
        # Conectar ao servidor do Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com')

        # Fazer login na conta do Gmail
        mail.login(username, password)

        return mail
    except Exception as e:
        print(f"Erro ao conectar ao Gmail: {e}")
        return None

def find_unread_email_with_subject_and_attachment(mail, subject, attachment_extension='.zip'):
    # Selecionar a caixa de entrada
    mail.select('inbox')

    #Filtro: subject:(:subject) has::attachment
    status, messages = mail.search(None, f'(UNSEEN SUBJECT "{subject}")')

    # Obter o número do último e-mail encontrado
    message_ids = messages[0].split()
    if not message_ids:
        return None
    latest_email_id = message_ids[-1]

    # Obter o conteúdo do último e-mail
    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    # Verificar se o e-mail contém anexos
    for part in msg.walk():
        if str(part.get_content_type()).find("application/") != -1 and str(part.get_content_type()).find("zip") != -1:
            filename = part.get_filename()
            if filename:
                if not os.path.isdir('./tmp/'):
                    os.mkdir('./tmp/')

                attachment_filename = os.path.join('./tmp/', filename)
                with open(attachment_filename, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                return attachment_filename
                
    return None

def main():
    config = getConfig()

    # Configurações da conta do Gmail
    username = config['gmail']['user']
    password = config['gmail']['pass']

    # Conectar ao Gmail
    mail = connect_to_gmail(username, password)
    if not mail:
        return

    # Procurar por e-mails não lidos com o assunto '%Remessa do Dia%' e com anexo .zip
    subject = "Remessa do Dia"
    attachment_filename = find_unread_email_with_subject_and_attachment(mail, subject)

    if attachment_filename:
        print(f"Anexo '{attachment_filename}' encontrado no e-mail com o assunto '{subject}'.")
    else:
        print("Nenhum e-mail com o assunto '%Remessa do Dia%' e com anexo .zip encontrado.")

    # Fechar a conexão com o Gmail
    mail.logout()

if __name__ == "__main__":
    main()
