import math

import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from speach import speech_to_text
from config import TOKEN, MAX_USERS, MAX_TOKENS_PER_MESSAGE, MAX_STT_BLOCKS_PER_USER
from data import actions, get_table_data, get_user_data, is_user_in_table, add_new_user

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
    if not is_user_in_table(chat_id):
        if len(get_table_data()) <= MAX_USERS:
            add_new_user(chat_id)
            bot.send_message(chat_id, 'добро пожаловать')
            bot.send_message(chat_id,
                             'Привет! Я ваш голосовой помощник, вот что я могу:',
                             reply_markup=gen_main_markup(chat_id))
        else:
            bot.send_message(chat_id, 'база данных переполнена, сейчас вы не можете использовать бота')
    else:
        bot.send_message(chat_id, 'вы уже зарегистрированы')

# endregion


@bot.callback_query_handler(func=lambda call: call.data == 'dialogue')
def dialogue(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    msg = bot.send_message(user_id, 'Ты можешь отправлять как голосовые, так и обычный текст, но помни о лимитах. '
                           'Так о чем же мы пообщаемся?')
    bot.register_next_step_handler(msg, t_or_v)


def t_or_v(message):
    user_id = message.chat.id
    if message.text:
        text_processing(message)
    elif message.voice:
        voice_processing(message)
    else:
        msg = bot.send_message(user_id, 'Это... Не могу прочесть...')
        bot.register_next_step_handler(msg, t_or_v)


def text_processing(message):
    user_id = message.chat.id
    data = get_user_data(user_id)
    if data[2] >= MAX_TOKENS_PER_MESSAGE:
        if message.text == '/stop':
            bot.send_message(user_id, 'диалог приостановлен')
        elif message.text.startswith('/'):
            msg = bot.send_message(user_id, 'чтобы использовать команды, используйте /stop')
            bot.register_next_step_handler(msg, t_or_v)
        else:
            gen_gpt_answer(user_id, message.text, 'text')

    else:
        bot.send_message(user_id, 'ваши токены для общения закончились')


def voice_processing(message):
    user_id = message.chat.id
    data = data = get_user_data(user_id)
    blocks = data[3]
    tts_simbols = data[4]
    dur = message.voice.duration
    if dur == 0:
        dur = 1
    blocks_duration = math.ceil(dur / 15)

    if dur > 30:
        msg = bot.send_message(user_id, 'гс слишком длинное, запишите новое')
        bot.register_next_step_handler(msg, t_or_v)
    elif blocks + blocks_duration > MAX_STT_BLOCKS_PER_USER:
        bot.send_message(user_id, 'ваш лимит на распознавание речи исчерпан')
    elif tts_simbols >= 0:
        text = s_to_t(message)
        gen_gpt_answer(user_id, text, 'voice')
    else:
        bot.send_message(user_id, 'ваш лимит на синтез речи исчерпан')


def s_to_t(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    user_id = message.chat.id
    result = speech_to_text(file)
    text = result[1]

    if result[0]:
        update_story(text, user_id)
        return result[1]

    else:
        bot.send_message(user_id, result[1])


def gen_gpt_answer(user_id, text, message_format):

    ...

    if message_format == 'voice':
        send_voice_answer(text, user_id)
    else:
        send_text_answer(text, user_id)


def send_voice_answer(text, user_id):
    ...


def send_text_answer(text, user_id):
    ...
