# Deletor de Emails

Programa em Python com interface gráfica moderna para deletar emails em massa por **remetente**, **assunto**, **data** ou **categoria Promoções** (Gmail). Feito com [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) e a biblioteca `imaplib`, que já vem com o Python.

## Funcionalidades

- Interface escura e moderna (Tkinter com visual atualizado)
- Escolha da pasta: `INBOX`, `Spam` ou `Lixeira`
- Filtros de busca:
  - **Remetente**: todos os emails de um endereço
  - **Assunto**: emails que contêm um texto no assunto
  - **Antes da data**: emails anteriores a uma data (DD/MM/AAAA)
  - **Promoções (Gmail)**: emails da aba Promoções, com opção de filtrar por idade em dias
- Botão **Contar**, que mostra quantos emails o filtro encontrou sem deletar nada
- Confirmação antes de deletar
- Barra de progresso e log das operações
- A interface não trava durante a exclusão (usa threads)

## Requisitos

- Python 3.8 ou superior
- Tkinter (já vem com o Python no Windows e no macOS; no Linux pode ser preciso instalar o pacote `python3-tk`)
- CustomTkinter

## Instalação

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
cd SEU-REPOSITORIO
pip install customtkinter
py deletor_emails.py
```

## Configuração do Gmail

O Gmail não aceita mais a senha normal em aplicativos. Você precisa de uma **senha de app**:

1. Ative a **verificação em duas etapas** na sua conta Google.
2. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Gere uma senha de app e use ela no campo de senha do programa.

O servidor padrão já vem preenchido com `imap.gmail.com`.

### Outros provedores

Troque o servidor IMAP no campo correspondente:

| Provedor | Servidor IMAP |
|----------|---------------|
| Outlook / Hotmail | `outlook.office365.com` |
| Yahoo | `imap.mail.yahoo.com` |

> O filtro de **Promoções** funciona apenas no Gmail.

## Como usar

1. Preencha o servidor, o e-mail e a senha de app.
2. Escolha a **pasta** (INBOX, Spam ou Lixeira).
3. Escolha o **filtro** e digite o valor:
   - Remetente: `newsletter@exemplo.com`
   - Assunto: `promoção`
   - Antes da data: `01/01/2025`
   - Promoções: número de dias (ex.: `30`) ou vazio para todas
4. Clique em **Contar** para conferir quantos emails serão afetados.
5. Clique em **Deletar** e confirme.

## Avisos importantes

- **Teste sempre com o botão Contar antes de deletar.**
- No Gmail, emails deletados da **INBOX** vão primeiro para a lixeira. Já os deletados das pastas **Spam** e **Lixeira** são **removidos permanentemente**.
- Se a pasta não for encontrada (por exemplo, em contas com idioma diferente), ajuste os nomes na lista `PASTAS_POSSIVEIS` no código.
- Nunca coloque sua senha de app direto no código nem suba ela para o GitHub.
- Use por sua conta e risco: emails deletados permanentemente não podem ser recuperados.

## Como funciona

O programa conecta ao servidor por IMAP com SSL (`imaplib.IMAP4_SSL`), faz a busca com os critérios escolhidos, marca os emails com a flag `\Deleted` e executa `expunge` para removê-los. No Gmail, a categoria Promoções é buscada com `X-GM-RAW`.

## Licença

Defina aqui a licença do projeto (por exemplo, MIT).