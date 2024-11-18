#Entrada de dados
# widget Entry 
# Sintaxe
# textbox = ttk.Entry(mestre, *opition)


import tkinter as tk
from tkinter import ttk   
from pathlib import Path
from tkcalendar import DateEntry
from ttkthemes import ThemedTk


current_dir = Path(__file__).parent

def import_parametro_sei(url, doc_type, data_inicial, data_final):
    dados = f"{url} {doc_type} {data_inicial} {data_final}" 
    print(dados)
    return dados


#criar Janela 1

def carregar_janela_principal():
    # def import_parametro_sei():
    #     url = entry_url.get()
    #     doc_type = entry_doc_type.get()
    #     # di = entry_di.get()
    #     # df = entry_df.get()
    #     # output_dir = entry_dir.get()
    #     # charset = entry_chaser.get()
    #     # passwordfile=entry_password.get()
    #     dados = f"{url} {doc_type}" # {passwordfile} {output_dir} {di} {df} {charset}"
    #     label_entrada.config(text=dados)
    #     print(dados)
    
        # Mostrar segunda janela com login
    def abrir_segunda_janela():
        janela2=tk.Toplevel()
        janela2.title("Janela de Login")
        janela2.config(bg="lightblue")
        janela2.resizable(False, False)
        janela2.iconbitmap(current_dir.joinpath("logo-sei.ico"))
        janela2.geometry("300x200")
        
        
        label_login = tk.Label(janela2, text = "Login", bg="lightblue", font = ("Arial", 14, "bold"))
        label_login.grid(row = 0, column = 0, padx=1, pady=3)
        entry_login = ttk.Entry(janela2, width=15)
        entry_login.grid(row=0, column= 1, padx=2, pady=3)
        
        label_password = tk.Label(janela2, text = "Password", bg="lightblue", font = ("Arial", 14, "bold"))
        label_password.grid(row = 1, column = 0, padx=1, pady=4)
        entry_password = ttk.Entry(janela2, width= 15, show = "*")
        entry_password.grid(row=1, column= 1, padx=2, pady=4)
        
        def save_arq():
            with open(".password/password.txt", "w") as arq:
                arq.write(f'{entry_login.get()}:{entry_password.get()}')
                #fechar a janela de login
            janela2.destroy()
                               
        botao_voltar = ttk.Button(janela2, text = 'Salvar o Login e a senha ', style="big.TButton", command = save_arq)
        botao_voltar.grid(row = 2, column = 0, columnspan=2)
    
    janela = ThemedTk(theme="arc")
    #canvas = tk.Canvas(janela, width=900, height=600, bg='lightblue', insertborderwidth="10", highlightthickness = 6)
    #canvas.pack()
    
    janela.title("Tirando dados do SEI")
    
    # canvas.create_window(200, 140, window = entry )
    
    
    # janela.geometry("900x600")
    janela.config(bg="lightblue")
    # janela.resizable(False, False)
    janela.iconbitmap(current_dir.joinpath("logo-sei.ico"))
    #janela.rowconfigure(0, weight=1)
    #janela.columnconfigure([5,5], weight=2)

    img = tk.PhotoImage(file=current_dir.joinpath("logo-sei.png"), width=300, height=200)
    logo = tk.Label(janela, image=img, background="lightblue")

    logo.grid(row=0, column= 0, padx=1, pady=3)
    
    FONT = "Arial"

    mensagem1 = tk.Label(janela,
                        text="Busca de dados dos documentos SEI",
                        fg="gray",
                        #  image= img,
                        bg ="lightblue",
                        font=(FONT,"20"),
                        width=30,
                        height=5)

    mensagem1.grid(row=0, column= 1, columnspan=20, padx=1, pady=3)

    #criar o Entry
    label_url = ttk.Label(janela,
                        text="URL do sistema SEI *",
                        background="lightblue",
                        font=(FONT))

    label_url.grid(row=2,
                column= 0,
                padx=10,
                pady=5,
                sticky="nsew")

    entry_url = ttk.Entry(janela,
                        width=15)

    entry_url.grid(row=2,
                column=1,
                columnspan=8,
                padx=10,
                pady=5,
                sticky="nsew")

    label_doc_type = ttk.Label(janela,
                            text="Qual é o tipo de documento que quer os dados?*",
                            background="lightblue",
                            font=(FONT))
    label_doc_type.grid(row=3,
                        column=0,
                        padx=10,
                        pady=5,
                        sticky="nsew")

    entry_doc_type = ttk.Entry(janela,
                            width=20)

    entry_doc_type.grid(row=3,
                        column=1,
                        # columnspan=8,
                        padx=10,
                        pady=5,
                        sticky="nsew")
    
    label_obrigacao = ttk.Label(janela,
                        text="* São obrigatórios",
                        background="lightblue",
                        font= (FONT, 14, "bold"),
                        foreground="red")
    
    label_obrigacao.grid(row=4,
                        # columnspan=2,
                        padx=10,
                        pady=5)
    label_datainicial = ttk.Label(janela,
                        text="Data de inicio da pesquisa:", 
                        background="lightblue",
                        font=(FONT))
    label_datainicial.grid(row=5,
                        column=0,
                        padx=10,
                        pady=5,
                        sticky="nsew")

            
    entry_datainicial = DateEntry(janela,
                                dateformat = "%d/%m/%Y", 
                                selectmode = 'day'                                          
                                )

    entry_datainicial.grid(row=5,
                        column=1,
                        # padx=8,
                        # pady=5
                        )
    
    # entry_datainicial.grid(row=5,
    #                     column=1,
    #                     columnspan=8,
    #                     padx=10,
    #                     pady=5,Janela 
    #                     sticky="nsew")
    

    label_datafinal = ttk.Label(janela,
                        text="Data de inicio da pesquisa:",
                        background="lightblue", 
                        font=(FONT))
    label_datafinal.grid(row=6,
                        column=0,
                        # padx=8,
                        # pady=5,
                        sticky="nsew")

    entry_datafinal = DateEntry(janela,
                                dateformat = "%d/%m/%Y", 
                                selectmode = 'day'
                                )
    # def select_datef():
    #     datef = entry_datafinal.get_date()
    #     date_label.config(text = datef)
    
    entry_datafinal.grid(row=6,
                        column=1,
                        # padx=8,
                        # pady=5,
                        )

    print(entry_datafinal, entry_datainicial)
    # Salvar as entradas
    # s = ttk.Style()
    # s = ("big.TButton",
    #     fg='black',
    #     bg="darkgray",
    #     font = (FONT, 16))
    
    botao_login = ttk.Button(janela,
                             text = "Login",
                            #  font=(FONT, "12", "bold"),
                             style="big.TButton",
                             command=abrir_segunda_janela
                             )
    botao_login.grid(row=7,
                     columnspan=2,
                     padx=15,
                     pady=5
                     )
    
    
    # manipulador de evento click
    def botao_entrada_click():
        _label = import_parametro_sei(entry_url.get(), entry_doc_type.get(), entry_datainicial.get_date(), entry_datafinal.get_date())
        label_entrada.config(text=_label)

    botao_entrada = ttk.Button(janela,
                            text="Salvar as entradas",
                            # font=(FONT, "16", "bold"),
                            style="big.TButton",
                            command=botao_entrada_click)
    
    botao_entrada.grid(row=20,
                    columnspan=2,
                    padx=15,
                    pady=3)

    # mostrar os dados para rodar o Scrit do SEI

    label_entrada = ttk.Label(janela,
                            text="",
                            background="lightblue",
                            font=(FONT, "16"))

    label_entrada.grid(row=30,
                    column=0,
                    padx=10,
                    pady=5)
    

    # Mostrar a Janela 
    janela.mainloop()


def main():
    return carregar_janela_principal()
        
if __name__ == '__main__':
    main()