import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN
from data import actions
bot = telebot.TeleBot(token=TOKEN)


# region markups
def gen_main_markup(chat_id):
    markup = InlineKeyboardMarkup()
    for action in actions:
        markup.add(InlineKeyboardButton(actions[action], callback_data=action))

    return markup

# endregion


# region commands
@bot.message_handler(comands=['help'])
def help_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     """
/start - начало диалога
/help - список команд
/stop - останавливает сессию
/tts - запускает сессию
                     """
                     )


@bot.message_handler(commands=['tts'])
def tts(message: Message):
    pass
    # message_register(message.chat.id)


@bot.message_handler(commands=['stt'])
def stt(message: Message):
    pass
    # voice_register(message.chat.id)


@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     'Привет! Я ваш голосовой помощник, вот что я могу:',
                     reply_markup=gen_main_markup(chat_id))
# endregion




@bot.callback_query_handler(func=lambda call: call.data == 'dialogue')
def dialogue(call):
    pass











