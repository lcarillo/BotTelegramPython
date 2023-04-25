import re
import pandas as pd
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import sqlite3
import unidecode
import os
import datetime

def start(update, context):

    """Função que é chamada quando o usuário digita /start ou envia uma mensagem sem comando."""
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Olá, digite uma loja, grupo e marca. ATENÇÃO: O nome da loja precisa ser completo e igual ao Vetor. Exemplo: ARACAJU AEROPORTO / AX / FIAT')


def search(update, context):
    """Função que é chamada quando o usuário envia uma mensagem."""
    # Obtém a mensagem enviada pelo usuário
    message = update.message.text
    user_name = update.effective_user.username

    if message.count('/') != 2:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Por favor, digite uma loja, grupo e marca separados por duas barras "/". Caso não queira filtrar a marca, deixe em branco, porém coloque duas "/". Exemplo: SÃO PAULO - BARRA FUNDA / AX /')

        return

    # Divide a mensagem em três partes: loja, grupo e modelo
    message = message.replace('-', '')
    message = message.replace('Ç', 'C')
    message = message.replace('ç', 'c')
    words = message.lower().split('/')
    words = [unidecode.unidecode(word.strip()) for word in words]
    marca = words[-1].replace('-', ' ')
    grupo = words[-2].replace('-', ' ')
    loja = ' '.join([word.replace(' - ', ' ').replace('  ', ' ') for word in words[:-2]])

    if len(words[0]) < 7 :
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Por favor, digite uma loja, grupo e marca separados por duas barras "/". Caso não queira filtrar a marca, deixe em branco, porém coloque duas "/". Exemplo: SÃO PAULO - BARRA FUNDA / AX /')
        with open(r'C:\Users\lcarillo\Dropbox\bottelegram\NomeLojas.csv') as csv_file:
            context.bot.send_document(chat_id=update.effective_chat.id, document=csv_file)

        return


        return
    #registra no banco de dados 2h a mais.

    conn = sqlite3.connect('messages.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, message_text, user_name, date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (update.effective_chat.id, message, user_name))
    id = c.lastrowid
    conn.commit()
    conn.close()


    # Lê o arquivo CSV e cria um DataFrame com os dados
    df = pd.read_csv(r'C:\Users\lcarillo\Dropbox\bottelegram\frotas.csv', encoding='latin1', sep=";")

    # Remove acentos das colunas relevantes do DataFrame
    df['Filial Atual'] = df['Filial Atual'].apply(lambda x: unidecode.unidecode(x))
    df['GR'] = df['GR'].apply(lambda x: unidecode.unidecode(x))
    df['Marca'] = df['Marca'].apply(lambda x: unidecode.unidecode(x))

    df['Filial Atual'] = df['Filial Atual'].str.replace(' - ', ' ')
    df['Filial Atual'] = df['Filial Atual'].str.replace('Ç', 'C')
    df['Filial Atual'] = df['Filial Atual'].str.replace('ç', 'c')

    loja_regex = re.escape(loja.lower())

    # Filtra as linhas que correspondem às opções selecionadas pelo usuário
    if marca:
        filtered_df = df.loc[
            (df['Filial Atual'].str.lower().str.contains(loja_regex, regex=True)) &
            (df['GR'].str.lower() == grupo.lower()) &
            (df['Marca'].str.lower() == marca.lower())
            ]
    else:
        filtered_df = df.loc[
            (df['Filial Atual'].str.lower().str.contains(loja_regex, regex=True)) &
            (df['GR'].str.lower() == grupo.lower())
            ]

    # Verifica se há pelo menos uma linha que corresponde aos critérios de busca
    if not filtered_df.empty:
        # Lê o arquivo CSV de filiais e cria um DataFrame com os dados
        filiais = pd.read_csv(r'C:\Users\lcarillo\Dropbox\bottelegram\calendario.csv', encoding='latin1', sep=";")

       # filiais.columns = filiais.iloc[0]
       # filiais = filiais.drop(filiais.index[0])

        # Reseta o índice do DataFrame
        #filiais = filiais.reset_index(drop=True)

        loja_regex = re.escape(loja.lower())

        filiais['filial_id'] = filiais['filial_id'].apply(lambda x: unidecode.unidecode(x) if isinstance(x, str) else x)
        #filiais['grupo'] = filiais['grupo'].apply(lambda x: unidecode.unidecode(x))
        filiais['filial_id'] = filiais['filial_id'].astype(str)
        filiais['filial_id'] = filiais['filial_id'].str.replace(' - ', ' ')
        filiais['filial_id'] = filiais['filial_id'].str.replace('Ç', 'C')
        filiais['filial_id'] = filiais['filial_id'].str.replace('ç', 'c')

        #filiais = filiais[~filiais['Filial'].isin(['Total', 'Ocupacao'])]

        # Remove acentos das colunas "Filial" e "Grupo"

        filiais.iloc[:, 2] = filiais.iloc[:, 2].fillna(0).astype(float)  # coluna número 2
        filiais.iloc[:, 3] = filiais.iloc[:, 3].fillna(0).astype(float)  # coluna número 5

        #filiais_df = filiais.loc[
           #filiais.iloc['efetiva'] > 0 & (filiais.iloc['colunadepois'] > 0)] # filtrar pela coluna 2 e coluna 5

        # Filtra as linhas que correspondem às opções selecionadas pelo usuário
        filtered_filiais = filiais.loc[
            (filiais['filial_id'].str.lower().str.contains(loja_regex, regex=True)) &
            (filiais['grupo'].str.lower().str.replace(' ', '').str.contains(grupo))
            ]

        # Verifica se há pelo menos uma linha que corresponde aos critérios de busca nas filiais
        if not filtered_filiais.empty and (filtered_filiais.iloc[:, 2].fillna(0).astype(float) > 0).all() and (
                filtered_filiais.iloc[:, 3].fillna(0).astype(float) > 0).all():

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Disponível para reservas nas próximas 48h na loja {loja_formatada}, grupo {grupo_formatado}. ID: {id}'.format(
                                         loja_formatada=loja.title(), grupo_formatado=grupo.upper(),id=id))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text='Indisponível para reservas nas próximas 48h na loja {loja_formatada}, grupo {grupo_formatado}. ID: {id}'.format(
                                         loja_formatada=loja.title(), grupo_formatado=grupo.upper(),id=id))
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Indisponível para reservas nas próximas 48h na loja {loja_formatada}, grupo {grupo_formatado}. ID: {id}'.format(
                                     loja_formatada=loja.title(), grupo_formatado=grupo.upper(), id=id))
def infobot(update, context):
    """Função que é chamada quando o usuário digita /infobot."""
    # Obtém a data de modificação do arquivo CSV
    filename = r'C:\Users\lcarillo\Dropbox\bottelegram\frotas.csv'
    mod_time = os.path.getmtime(filename)
    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%d/%m/%Y %H:%M:%S')

    # Envia a mensagem com a data de modificação do arquivo CSV
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'A última atualização do arquivo Relatório de Frotas CSV foi em {mod_time_str}.')

    filename = r'C:\Users\lcarillo\Dropbox\bottelegram\calendario.csv'
    mod_time = os.path.getmtime(filename)
    mod_time_str = datetime.datetime.fromtimestamp(mod_time).strftime('%d/%m/%Y %H:%M:%S')

    # Envia a mensagem com a data de modificação do arquivo CSV
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f'A última atualização do arquivo Previsão Frota Calendário 48h CSV foi em {mod_time_str}.')


def main():
    # Cria um objeto Updater com o token do seu bot
    updater = Updater(token='XX', use_context=True)

    # Obtém o objeto Dispatcher do Updater
    dispatcher = updater.dispatcher

    # Cria um objeto CommandHandler para o comando /start
    start_handler = CommandHandler('start', start)

    updater.dispatcher.add_handler(CommandHandler('infobot', infobot))  # Adiciona o comando /infobot

    # Cria um objeto MessageHandler para lidar com as mensagens enviadas pelo usuário
    message_handler = MessageHandler(Filters.text & (~Filters.command), search)

    # Adiciona os handlers ao Dispatcher
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(message_handler)

    # Inicia o bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
