import os.path
from db_script import SQLighter 
from threading import Thread
import time
import telebot
import requests
from bs4 import BeautifulSoup

TOKEN = '1811721730:AAHftD-W2m9uhTWin6hEMcZNXEWh_xrNKg8'
bot = telebot.TeleBot(TOKEN)


# THREAD 1    DATA PARSE

url = 'https://pk.mipt.ru/bachelor/2021_decree/admission/'
response = requests.get(url)

soup = BeautifulSoup(response.text, 'lxml')

db = SQLighter('username.db')

counter = 0
btn_url = ''
no_data = False
request_data = []
parser_request = []
decree_data = []
final_data = {
              'pmi' : [],
              'pmf' : [],
              'ivt' : [],
              'bt'  : []
              }
data = soup.find('div', class_='decree_season_block')
try:
    decree_data = data.find_all('a')
except:
    no_data = True
if not no_data:
    for i in decree_data:
        request_data.append(i.text.split())
        request_data[-1].append(i['href'])
    for a in request_data:
        if 'квота' in a:
            parser_request.append(a)
            if 'ПМИ' in a:
                final_data['pmi'].append(a)
            elif 'ПМФ' in a:
                final_data['pmf'].append(a)
            elif 'ИВТ' in a:
                final_data['ivt'].append(a)
            elif 'БТ' in a:
                final_data['bt'].append(a)


buttons = telebot.types.InlineKeyboardMarkup()
btn_pmi = telebot.types.InlineKeyboardButton(text = 'ПМИ', callback_data ='pmi')
btn_pmf = telebot.types.InlineKeyboardButton(text = 'ПМФ', callback_data ='pmf')
btn_ivt = telebot.types.InlineKeyboardButton(text = 'ИВТ', callback_data ='ivt')
btn_bt = telebot.types.InlineKeyboardButton(text = 'БТ', callback_data ='bt')
buttons.add(btn_pmi)
buttons.add(btn_pmf)
buttons.add(btn_ivt)
buttons.add(btn_bt)
download_btn = telebot.types.InlineKeyboardMarkup()
download_btn.add(telebot.types.InlineKeyboardButton(text = 'Скачать приказы', callback_data = 'files'))


button_pmi = telebot.types.InlineKeyboardMarkup()
btn_pmi = telebot.types.InlineKeyboardButton(text = 'Скачать данные', callback_data ='download_pmi')
#sub_pmi = telebot.types.InlineKeyboardButton(text = 'Подписаться на рассылку', callback_data ='subscribe_pmi')
button_pmi.add(btn_pmi)
#button_pmi.add(sub_pmi)
button_pmf = telebot.types.InlineKeyboardMarkup()
btn_pmf = telebot.types.InlineKeyboardButton(text = 'Скачать данные', callback_data ='download_pmf')
button_pmf.add(btn_pmf)
button_ivt = telebot.types.InlineKeyboardMarkup()
btn_ivt = telebot.types.InlineKeyboardButton(text = 'Скачать данные', callback_data ='download_ivt')
button_ivt.add(btn_ivt)
button_bt = telebot.types.InlineKeyboardMarkup()
btn_bt = telebot.types.InlineKeyboardButton(text = 'Скачать данные', callback_data ='download_bt')
button_bt.add(btn_bt)

restart_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
restart_btn = telebot.types.KeyboardButton('Обновить')
restart_button.add(restart_btn)

# THREAD 2   status_checker

parser_decree = []

def parse():

    #html = BeautifulSoup(response_checker.text, 'lxml')
    #data_checker = html.find('div', class_='decree_season_block')
    #parser_decree = data_checker.find_all('a')
    counterr = parser_request[-1][2]
    return counterr


def update_info(lastkey_file, counter):


    if(os.path.exists(lastkey_file)):

        lastkey = open(lastkey_file, 'r').read()
        if lastkey != counter:
            f = open(lastkey_file, 'w')
            f.write(str(counter))
            f.close()
            subscribtions = db.get_subscriptions()
            for s in subscribtions:
                try:
                    
                    bot.send_message(s[1], '⚡️ Обновление на сайте ПК по направлению {0}\n(Это тестовая рассылка, новых данных на самом деле нет)'.format(parser_request[-1][3]))

                except: print(s[1], 'blocked')


    else:
        f = open(lastkey_file, 'w')
        f.write(str(counter))
        f.close()


def start_session():
    while True:

        print(time.ctime())
        if not no_data:
            update_info('lastkey.txt', parse())
            time.sleep(30)

# Telegram Bot 
user_id = ''

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if no_data:
        bot.send_message(message.from_user.id, 'Сейчас приказы не выходят, попробуйте попозже!')
    else:
        bot.send_message(message.from_user.id, "Выберите направление", reply_markup = buttons)
        print(message.from_user.id)
        user_id = message.from_user.id
@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    if not no_data:
        if(not db.subscriber_exists(message.from_user.id)):
            # если юзера нет в базе, добавляем его
            db.add_subscriber(message.from_user.id)
            bot.send_message(message.from_user.id, 'Вы успешно подписались на рассылку')
        else:
            # если он уже есть, то просто обновляем ему статус подписки
            db.update_subscription(message.from_user.id, True)

    bot.send_message(message.from_user.id, 'Вы успешно подписались на рассылку')
@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    if not no_data:
        if(not db.subscriber_exists(message.from_user.id)):
            # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
            db.add_subscriber(message.from_user.id, False)


        else:
            # если он уже есть, то просто обновляем ему статус подписки
            db.update_subscription(message.from_user.id, False)

        bot.send_message(message.from_user.id, 'Вы успешно отписались от рассылки')
@bot.message_handler(content_types='text')
def send_message(message):
    if not no_data:
        if message.text=='Обновить':
            bot.send_message(message.from_user.id, "Выберите направление", reply_markup = buttons)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if not no_data:
        if call.data == 'pmi':
            bot.send_message(call.message.chat.id, 'Последний приказ вышел: {0}\nВсего вышло приказов: {1}'.format(final_data[call.data][-1][0], len(final_data[call.data])), reply_markup = button_pmi)
        elif call.data == 'pmf':
            bot.send_message(call.message.chat.id, 'Последний приказ вышел: {0}\nВсего вышло приказов: {1}'.format(final_data[call.data][-1][0], len(final_data[call.data])), reply_markup = button_pmf)
        elif call.data == 'ivt':
            bot.send_message(call.message.chat.id, 'Последний приказ вышел: {0}\nВсего вышло приказов: {1}'.format(final_data[call.data][-1][0], len(final_data[call.data])), reply_markup = button_ivt)
        elif call.data == 'bt':
            bot.send_message(call.message.chat.id, 'Последний приказ вышел: {0}\nВсего вышло приказов: {1}'.format(final_data[call.data][-1][0], len(final_data[call.data])), reply_markup = button_bt)
        else:
            for l in range(len(final_data[call.data[9:]])):
                bot.send_message(call.message.chat.id, 'Приказ от   {0}\nhttps://pk.mipt.ru/bachelor/2021_decree/admission/{1}'.format(final_data[call.data[9:]][l][0], final_data[call.data[9:]][l][-1]), reply_markup = restart_button)



#bot.send_message(user_id, 'Text')
def start_bot():
    bot.polling(none_stop = True)

first_thread = Thread(target = start_session)
second_thread = Thread(target = start_bot)

first_thread.start()
second_thread.start()

first_thread.join()
second_thread.join()






