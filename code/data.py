import sqlite3
from config import DB_NAME, MAX_STORY_LEN, MAX_TOKENS_PER_USER, MAX_STT_BLOCKS_PER_USER, TTS_SIMBOLS_PER_USER
from log import logger


# region python_data
actions = {
    'пообщаемся?': 'dialogue',
    'мои токены': 'status',
    'распознавание': 'stt',
    'синтез': 'tts'
}


# endregion


# region sql
def create_db():
    connection = sqlite3.connect(DB_NAME)
    connection.close()


def execute_query(func_name: str, query: str, data: tuple | None = None, db_name: str = DB_NAME):
    try:
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
            connection.commit()
        else:
            cursor.execute(query)

    except sqlite3.Error as e:
        error_msg = f"Ошибка в {func_name}: {e}"
        logger.error(error_msg)

    else:
        result = cursor.fetchall()
        connection.close()
        return result


def create_users_data_table():
    sql_query = (
        "CREATE TABLE IF NOT EXISTS users_data "
        "(id INTEGER PRIMARY KEY, "
        "user_id INTEGER, "
        "gpt_tokens INTEGER, "
        "stt_blocks INTEGER, "
        "tts_simbols INTEGER, "
        "dialogue_story TEXT);"
    )
    execute_query('create_users_data_table', sql_query)


def add_new_user(user_id: int) -> bool:
    if not is_user_in_table(user_id):
        sql_query = (
            "INSERT INTO users_data "
            "(user_id, gpt_tokens, stt_blocks, tts_simbols, dialogue_story) "
            "VALUES (?, ?, ?, ?, ?);"
        )

        execute_query('add_new_user', sql_query, (user_id, MAX_TOKENS_PER_USER, MAX_STT_BLOCKS_PER_USER, TTS_SIMBOLS_PER_USER, ''))
        return True
    else:
        return False


def is_user_in_table(user_id: int) -> bool:
    sql_query = (
        'SELECT * '
        'FROM users_data '
        'WHERE user_id = ?;'
    )
    return bool(execute_query('is_user_in_table', sql_query, (user_id,)))


def get_user_data(user_id: int):
    if is_user_in_table(user_id):
        sql_query = (
            f'SELECT * '
            f'FROM users_data '
            f'WHERE user_id = {user_id};'
        )
        row = execute_query('get_user_data', sql_query)[0]
        return row


def update_row(user_id: int, column_name: str, new_value: str | int | None) -> bool:
    if is_user_in_table(user_id):
        sql_query = (
            f"UPDATE users_data "
            f"SET {column_name} = ? "
            f"WHERE user_id = ?;"
        )

        execute_query('update_row', sql_query, (new_value, user_id))
        return True
    else:
        return False


def get_table_data():
    sql_query = (
        f'SELECT * '
        f'FROM users_data;'
    )
    res = execute_query('get_table_data', sql_query)
    if not res:
        res = []
    return res


def update_story(user_id, text):
    old_story = get_user_data(user_id)[5]

    if old_story:
        story_text = old_story + ' ' + text
    else:
        story_text = text

    story_list = story_text.split(' ')
    story_len = len(story_list)

    if story_len > MAX_STORY_LEN:
        new_story = ' '.join([story_list[x] for x in range(story_len - 1 - MAX_STORY_LEN, story_len - 1)])
    else:
        new_story = story_text

    update_row(user_id, 'dialogue_story', new_story)


def tokens_update(user_id, num, token_type):
    if token_type == 'gpt_tokens':
        x = 2
    elif token_type == 'stt_blocks':
        x = 3
    else:
        x = 4

    old_tokens_num = get_user_data(user_id)[x]
    new_tokens_num = old_tokens_num - num

    update_row(user_id, token_type, new_tokens_num)


create_db()
create_users_data_table()
# endregion
