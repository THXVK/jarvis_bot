import math

import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from GPT import gpt_ask
from speach import speech_to_text, text_to_speach
from config import TOKEN, MAX_USERS, MAX_TOKENS_PER_MESSAGE, TTS_SIMBOLS_PER_MESSAGE
from data import actions, get_table_data, get_user_data, is_user_in_table, add_new_user, update_story, tokens_update

bot = telebot.TeleBot(token=TOKEN)


# region markups
def gen_main_markup():
    markup = InlineKeyboardMarkup()
    for action in actions:
        markup.add(InlineKeyboardButton(action, callback_data=actions[action]))

    return markup

# endregion


# region commands


@bot.message_handler(commands=['actions'])
def send_main_menu(message: Message):
    chat_id = message.chat.id
    if is_user_in_table(chat_id):
        bot.send_message(chat_id,
                         'Что вы хотите сделать?', reply_markup=gen_main_markup())
    else:
        bot.send_message(chat_id, 'вы не в базе')


@bot.message_handler(commands=['help'])
def send_help_message(message: Message):
    bot.send_message(message.chat.id, """
/start - начало диалога
/help - список команд
/stop - останавливает диалог
/actions - показывает меню действий
/debug - присылает лог файл
    """)


@bot.message_handler(commands=['debug'])
def debug(message: Message):
    user_id = message.chat.id
    with open('logConfig.log', 'rb') as file:
        f = file.read()
    bot.send_document(message.chat.id, f, visible_file_name='logConfig.log')


@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    if not is_user_in_table(chat_id):
        if len(get_table_data()) <= MAX_USERS:
            add_new_user(chat_id)
            bot.send_message(chat_id, 'добро пожаловать')
            bot.send_message(chat_id,
                             'Привет! Я ваш голосовой помощник, вот что я могу:', reply_markup=gen_main_markup())
        else:
            bot.send_message(chat_id, 'база данных переполнена, сейчас вы не можете использовать бота')
    else:
        bot.send_message(chat_id, 'вы уже зарегистрированы')

# endregion

# region actions


@bot.callback_query_handler(func=lambda call: call.data == 'tts')
def tts(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    msg = bot.send_message(user_id, 'напишите текст для озвучки')
    bot.register_next_step_handler(msg, tts_2)


def tts_2(message):
    user_id = message.chat.id
    tts_simbols = get_user_data(user_id)[4]

    if message.text.startswith('/'):
        bot.send_message(user_id, 'не используй команды здесь!')
        return

    if tts_simbols >= len(message.text):
        res = gen_voice_answer(user_id, message.text)
        if res[0]:
            bot.send_voice(user_id, res[1])
        else:
            bot.send_message(user_id, res[1])
    else:
        bot.send_message(user_id, 'ваш лимит на синтез речи исчерпан')


@bot.callback_query_handler(func=lambda call: call.data == 'stt')
def stt(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    msg = bot.send_message(user_id, 'пришлите голосовое сообщение')
    bot.register_next_step_handler(msg, stt_2)


def stt_2(message):
    user_id = message.chat.id
    dur = message.voice.duration
    if dur == 0:
        dur = 1
    blocks_duration = math.ceil(dur / 15)
    blocks = get_user_data(user_id)[3]

    if dur > 30:
        msg = bot.send_message(user_id, 'гс слишком длинное, запишите новое')
        bot.register_next_step_handler(msg, stt_2)
    elif blocks - blocks_duration <= 0:
        bot.send_message(user_id, 'ваш лимит на распознавание речи исчерпан')
    else:
        res = s_to_t(message)
        tokens_update(user_id, blocks_duration, 'stt_blocks')
        bot.send_message(user_id, f'вы сказали: {res[0]}')


@bot.callback_query_handler(func=lambda call: call.data == 'status')
def send_status(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    data = get_user_data(user_id)
    text = f"""
GPT токены: {data[2]}
stt блоки: {data[3]}
tts символы: {data[4]}
    """

    bot.send_message(user_id, text)
    text = 'ПРОВЕРОЧНЫЙ ТЕКСТ'

    update_story(user_id, f'пользователь: {text}')
    tokens_update(user_id, 5, 'stt_blocks')
    print(get_user_data(user_id))
    bot.send_message(user_id,  f'{get_user_data(user_id)}')


@bot.callback_query_handler(func=lambda call: call.data == 'dialogue')
def dialogue(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    msg = bot.send_message(user_id, 'Ты можешь мне отправлять как голосовые, так и обычный текст, но помни о лимитах. '
                           'Так о чем же мы поговорим?')
    bot.register_next_step_handler(msg, t_or_v)

# endregion
# region dialogue


def message_register(user_id):
    msg = bot.send_message(user_id, 'ваш ответ?')
    bot.register_next_step_handler(msg, t_or_v)


def t_or_v(message):
    user_id = message.chat.id
    msg = bot.send_message(user_id, 'обрабатываю ответ...')
    if message.text:
        text_processing(message, msg)
    elif message.voice:
        voice_processing(message, msg)
    else:
        mssg = bot.send_message(user_id, 'Это... Не могу прочесть...')
        bot.register_next_step_handler(mssg, t_or_v)


def text_processing(message, msg):
    user_id = message.chat.id
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text='проверяю лимиты...')
    data = get_user_data(user_id)
    if data[2] >= MAX_TOKENS_PER_MESSAGE:
        if message.text == '/stop':
            bot.delete_message(user_id, msg.id)
            bot.send_message(user_id, 'диалог приостановлен')
        elif message.text.startswith('/'):
            bot.delete_message(user_id, msg.id)
            msg = bot.send_message(user_id, 'чтобы использовать команды, используйте /stop')
            bot.register_next_step_handler(msg, t_or_v)
        else:
            gen_gpt_answer(user_id, message.text, 'text', msg)

    else:
        bot.delete_message(user_id, msg.id)
        bot.send_message(user_id, 'ваши токены для общения закончились')


def voice_processing(message, msg):
    user_id = message.chat.id
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text='проверяю лимиты...')
    data = get_user_data(user_id)
    blocks = data[3]
    tts_simbols = data[4]
    dur = message.voice.duration
    if dur == 0:
        dur = 1
    blocks_duration = math.ceil(dur / 15)

    if dur > 30:
        mssg = bot.send_message(user_id, 'гс слишком длинное, запишите новое')
        bot.register_next_step_handler(mssg, t_or_v)
    elif blocks - blocks_duration <= 0:
        bot.send_message(user_id, 'ваш лимит на распознавание речи исчерпан')
    elif tts_simbols >= TTS_SIMBOLS_PER_MESSAGE:
        bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text='распознаю речь...')
        res = s_to_t(message)
        if res[1]:
            tokens_update(user_id, blocks_duration, 'stt_blocks')
            gen_gpt_answer(user_id, res[0], 'voice', msg)
        else:
            bot.delete_message(user_id, msg.id)
            bot.send_message(user_id, res[0])
            return
    else:
        bot.send_message(user_id, 'ваш лимит на синтез речи исчерпан')


def s_to_t(message):
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    result = speech_to_text(file)

    if result[0]:
        return result[1], True
    else:
        return 'ошибка при распознавании', False


def gen_gpt_answer(user_id, text, message_format, msg):
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text='генерирую ответ...')

    story = get_user_data(user_id)[5]
    gpt_ans, tokens = gpt_ask(text, story)

    tokens_update(user_id, tokens, 'gpt_tokens')
    update_story(user_id, text)
    update_story(user_id, gpt_ans)

    if message_format == 'voice':
        send_voice_answer(gpt_ans, user_id, msg)
    else:
        bot.delete_message(user_id, msg.id)
        send_text_answer(gpt_ans, user_id)


def send_voice_answer(text, user_id, msg):
    bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, text='синтезирую речь...')
    answer = gen_voice_answer(user_id, text)
    bot.delete_message(user_id, msg.id)
    bot.send_voice(user_id, answer)
    message_register(user_id)


def gen_voice_answer(user_id, text):
    res = text_to_speach(text)
    tokens_update(user_id, len(text), 'tts_simbols')
    return res[1]


def send_text_answer(text, user_id):
    bot.send_message(user_id, text)
    message_register(user_id)

# endregion


bot.infinity_polling()
