from easygui import choicebox
from arquivoExcel import getDadosFromFile
from assertiva import putTelefonesOnProcessos
from config import getConfig
from tjmt import get_dados_processos_tjmt
from tjrs import get_dados_processos_tjrs
from tjsp import get_dados_processos_tjsp
import pandas as pd
from tkinter import Tk, filedialog, messagebox

def main():
    try:
        config = getConfig()
        processos = pd.DataFrame()

        tribunalSelecionado = selecionaTribunal()

        if tribunalSelecionado != 'COMPLETAR TELEFONES ASSERTIVA':        
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

            if tribunalSelecionado == 'TJMT':
                processos = get_dados_processos_tjmt(config, TJMT) if len(TJMT) > 0 else pd.DataFrame()

            if tribunalSelecionado == 'TJRS':
                processos = get_dados_processos_tjrs(config, TJRS) if len(TJRS) > 0 else pd.DataFrame()
            
            if tribunalSelecionado == 'TJSP':
                processos = get_dados_processos_tjsp(config, TJSP) if len(TJSP) > 0 else pd.DataFrame()

        if len(processos) == 0 and tribunalSelecionado != 'COMPLETAR TELEFONES ASSERTIVA':
            messagebox.showerror('Nenhum processo encontrado', 'Nenhum processo encontrado')
            return

        if tribunalSelecionado == 'COMPLETAR TELEFONES ASSERTIVA':
            putTelefonesOnProcessos(config)

        messagebox.showinfo('Processos inseridos na planilha', 'Processos inseridos na planilha, execução finalizada')
    except Exception as e:
        print(e)
        messagebox.showerror('Erro', str(e))

def selecionaTribunal():
    options = list(['TJMT', 'TJRS', 'TJSP', 'COMPLETAR TELEFONES ASSERTIVA'])
    
    selected = choicebox("Selecione o tribunal", "Tribunais disponíveis", options)
    if not selected:
        raise Exception('Nenhum tribunal selecionado, programa encerrado')

    return selected

if __name__ == "__main__":
    main()

