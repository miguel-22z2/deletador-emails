import imaplib
import threading
import customtkinter as ctk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MESES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

PASTAS_LIXEIRA_GMAIL = ["[Gmail]/Trash", "[Gmail]/Lixeira"]

# nomes possíveis de cada pasta (o programa tenta um por um)
PASTAS_POSSIVEIS = {
    "INBOX": ["INBOX"],
    "Spam": ["[Gmail]/Spam", "Junk", "Spam"],
    "Lixeira": ["[Gmail]/Trash", "[Gmail]/Lixeira", "Trash"],
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Deletor de Emails")
        self.geometry("560x640")
        self.resizable(False, False)

        titulo = ctk.CTkLabel(self, text="Deletor de Emails",
                              font=ctk.CTkFont(size=24, weight="bold"))
        titulo.pack(pady=(20, 10))

        quadro = ctk.CTkFrame(self, corner_radius=12)
        quadro.pack(padx=20, pady=10, fill="x")

        self.entrada_servidor = ctk.CTkEntry(quadro, placeholder_text="Servidor IMAP")
        self.entrada_servidor.insert(0, "imap.gmail.com")
        self.entrada_servidor.pack(padx=15, pady=(15, 8), fill="x")

        self.entrada_email = ctk.CTkEntry(quadro, placeholder_text="Seu e-mail")
        self.entrada_email.pack(padx=15, pady=8, fill="x")

        self.entrada_senha = ctk.CTkEntry(quadro, placeholder_text="Senha de app", show="*")
        self.entrada_senha.pack(padx=15, pady=8, fill="x")

        self.menu_pasta = ctk.CTkOptionMenu(quadro, values=["INBOX", "Spam", "Lixeira"])
        self.menu_pasta.pack(padx=15, pady=8, fill="x")

        self.menu_filtro = ctk.CTkOptionMenu(
            quadro,
            values=["Remetente", "Assunto", "Antes da data (DD/MM/AAAA)",
                    "Promoções (Gmail)"],
            command=self.mudar_filtro)
        self.menu_filtro.pack(padx=15, pady=8, fill="x")

        self.entrada_valor = ctk.CTkEntry(quadro, placeholder_text="Valor do filtro")
        self.entrada_valor.pack(padx=15, pady=(8, 15), fill="x")

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(padx=20, pady=5, fill="x")

        self.botao_contar = ctk.CTkButton(botoes, text="Contar (sem deletar)",
                                          command=self.clicar_contar)
        self.botao_contar.pack(side="left", expand=True, padx=(0, 5), fill="x")

        self.botao_deletar = ctk.CTkButton(botoes, text="Deletar", fg_color="#c0392b",
                                           hover_color="#922b21",
                                           command=self.clicar_deletar)
        self.botao_deletar.pack(side="left", expand=True, padx=(5, 0), fill="x")

        self.barra = ctk.CTkProgressBar(self)
        self.barra.set(0)
        self.barra.pack(padx=20, pady=(15, 5), fill="x")

        self.log = ctk.CTkTextbox(self, height=190, corner_radius=12)
        self.log.pack(padx=20, pady=10, fill="both", expand=True)
        self.log.configure(state="disabled")

    # ---------- utilidades de interface ----------

    def escrever_log(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def log_seguro(self, texto):
        # permite escrever no log a partir da thread
        self.after(0, lambda: self.escrever_log(texto))

    def progresso_seguro(self, valor):
        self.after(0, lambda: self.barra.set(valor))

    def travar_botoes(self, travar):
        if travar:
            estado = "disabled"
        else:
            estado = "normal"
        self.botao_contar.configure(state=estado)
        self.botao_deletar.configure(state=estado)

    def travar_botoes_seguro(self, travar):
        self.after(0, lambda: self.travar_botoes(travar))

    # ---------- lógica de e-mail ----------

    def mudar_filtro(self, escolha):
        # ajusta o texto do campo conforme o filtro escolhido
        if escolha == "Promoções (Gmail)":
            self.entrada_valor.configure(placeholder_text="Mais antigos que X dias (vazio = todos)")
        elif escolha == "Remetente":
            self.entrada_valor.configure(placeholder_text="Ex.: newsletter@exemplo.com")
        elif escolha == "Assunto":
            self.entrada_valor.configure(placeholder_text="Texto do assunto")
        else:
            self.entrada_valor.configure(placeholder_text="Ex.: 01/01/2025")

    def abrir_pasta(self, conexao, nome_pasta):
        nomes = PASTAS_POSSIVEIS[nome_pasta]
        for i in range(len(nomes)):
            status, _ = conexao.select('"' + nomes[i] + '"')
            if status == "OK":
                return True
        return False

    def montar_busca(self, conexao, tipo, valor):
        if tipo == "Remetente":
            status, dados = conexao.search("UTF-8", "FROM", valor.encode("utf-8"))
        elif tipo == "Assunto":
            status, dados = conexao.search("UTF-8", "SUBJECT", valor.encode("utf-8"))
        elif tipo == "Data":
            partes = valor.split("/")
            if len(partes) != 3:
                raise ValueError("Use a data no formato DD/MM/AAAA")
            dia = int(partes[0])
            mes = int(partes[1])
            ano = int(partes[2])
            data_imap = str(dia) + "-" + MESES[mes - 1] + "-" + str(ano)
            status, dados = conexao.search(None, "BEFORE", data_imap)
        else:
            # Promoções: só funciona no Gmail (busca X-GM-RAW)
            busca = "category:promotions"
            if valor != "":
                busca = busca + " older_than:" + valor + "d"
            status, dados = conexao.search(None, "X-GM-RAW", '"' + busca + '"')
        return status, dados

    def mover_para_lixeira_gmail(self, conexao, id_email):
        for i in range(len(PASTAS_LIXEIRA_GMAIL)):
            status, _ = conexao.copy(id_email, PASTAS_LIXEIRA_GMAIL[i])
            if status == "OK":
                return True
        return False

    def executar(self, deletar):
        servidor = self.dados["servidor"]
        email = self.dados["email"]
        senha = self.dados["senha"]
        tipo = self.dados["tipo"]
        valor = self.dados["valor"]

        self.travar_botoes_seguro(True)
        self.progresso_seguro(0)
        conexao = None

        try:
            self.log_seguro("Conectando em " + servidor + "...")
            conexao = imaplib.IMAP4_SSL(servidor)
            conexao.login(email, senha)
            pasta = self.dados["pasta"]
            if not self.abrir_pasta(conexao, pasta):
                self.log_seguro("Não consegui abrir a pasta " + pasta + ".")
                return
            self.log_seguro("Pasta aberta: " + pasta)

            status, dados = self.montar_busca(conexao, tipo, valor)
            if status != "OK":
                self.log_seguro("Erro na busca.")
                return

            ids = dados[0].split()
            total = len(ids)
            self.log_seguro("Emails encontrados: " + str(total))

            if deletar and total > 0:
                # só manda pra lixeira se for Gmail e a pasta for a INBOX
                mover_antes = "gmail" in servidor and pasta == "INBOX"
                for i in range(total):
                    if mover_antes:
                        self.mover_para_lixeira_gmail(conexao, ids[i])
                    conexao.store(ids[i], "+FLAGS", "\\Deleted")
                    self.progresso_seguro((i + 1) / total)
                conexao.expunge()
                self.log_seguro("Deletados: " + str(total))
            elif deletar:
                self.log_seguro("Nada para deletar.")
            else:
                self.progresso_seguro(1)
                self.log_seguro("Modo contagem: nada foi deletado.")

        except Exception as erro:
            self.log_seguro("Erro: " + str(erro))
        finally:
            if conexao is not None:
                try:
                    conexao.close()
                    conexao.logout()
                except Exception:
                    pass
            self.travar_botoes_seguro(False)

    # ---------- eventos ----------

    def ler_campos(self):
        self.dados = {
            "servidor": self.entrada_servidor.get().strip(),
            "email": self.entrada_email.get().strip(),
            "senha": self.entrada_senha.get(),
            "tipo": self.menu_filtro.get(),
            "valor": self.entrada_valor.get().strip(),
            "pasta": self.menu_pasta.get(),
        }

        if self.dados["tipo"].startswith("Antes"):
            self.dados["tipo"] = "Data"
        elif self.dados["tipo"].startswith("Promo"):
            self.dados["tipo"] = "Promocoes"

        if self.dados["email"] == "" or self.dados["senha"] == "":
            messagebox.showwarning("Atenção", "Preencha e-mail e senha.")
            return False

        if self.dados["tipo"] == "Promocoes":
            # o valor é opcional, mas se vier precisa ser número de dias
            if self.dados["valor"] != "" and not self.dados["valor"].isdigit():
                messagebox.showwarning("Atenção", "Em Promoções, informe só o número de dias.")
                return False
            if "gmail" not in self.dados["servidor"]:
                messagebox.showwarning("Atenção", "O filtro de Promoções só funciona no Gmail.")
                return False
        elif self.dados["valor"] == "":
            messagebox.showwarning("Atenção", "Preencha o valor do filtro.")
            return False

        return True

    def clicar_contar(self):
        if self.ler_campos():
            threading.Thread(target=self.executar, args=(False,), daemon=True).start()

    def clicar_deletar(self):
        if not self.ler_campos():
            return
        confirmou = messagebox.askyesno(
            "Confirmar", "Tem certeza? Os emails encontrados serão deletados.")
        if confirmou:
            threading.Thread(target=self.executar, args=(True,), daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()