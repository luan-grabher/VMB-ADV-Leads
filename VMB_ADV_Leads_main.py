from arquivoExcel import getDadosFromFile
from assertiva import getProcessosComTelefone
from config import getConfig
from googleSheets import insert_processos_on_sheet
from tjmt import get_dados_processos_tjmt
from tjrs import get_dados_processos_tjrs
from tjsp import get_dados_processos_tjsp
import pandas as pd
from tkinter import Tk, filedialog, messagebox

def main():
    try:
        config = getConfig()
        
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

        messagebox.showinfo('Processos inseridos na planilha', 'Processos inseridos na planilha, execução finalizada')
    except Exception as e:
        messagebox.showerror('Erro', str(e))

if __name__ == "__main__":
    main()

