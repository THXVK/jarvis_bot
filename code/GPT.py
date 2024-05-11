import requests
import json
import time
from config import IAM_TOKEN_ENDPOINT, IAM_TOKEN_PATH, FOLDER_ID, GPT_URL, MAX_TOKENS_PER_MESSAGE, IAM_TOKEN
from log import logger


def create_new_iam_token():
    """
    Получает новый IAM-TOKEN и дату истечения его срока годности и записывает полученные данные в json
    """
    headers = {
        "Metadata-Flavor": "Google"
    }
    try:
        response = requests.get(IAM_TOKEN_ENDPOINT, headers=headers)
        print(response.status_code)
    except Exception as e:
        error_msg = f"Ошибка в create_new_iam_token: {e}"
        logger.error(error_msg)

    else:
        if response.status_code == 200:
            token_data = {
                "access_token": response.json().get("access_token"),
                "expires_in": response.json().get("expires_in") + time.time()
            }
            with open(IAM_TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
        else:
            error_msg = f"Ошибка в create_new_iam_token: {response.status_code}"
            logger.error(error_msg)


def get_iam_token() -> str:
    """
    Получает действующий IAM-TOKEN и возвращает его
    """
    try:
        with open(IAM_TOKEN_PATH, "r") as token_file:
            token_data = json.load(token_file)
        print(token_data)
        expires_in = token_data.get("expires_in")
        if expires_in <= time.time():
            create_new_iam_token()

    except FileNotFoundError:
        create_new_iam_token()
    with open(IAM_TOKEN_PATH, "r") as token_file:
        token_data = json.load(token_file)

    print(token_data.get("access_token"))
    return token_data.get("access_token")


def gpt_ask(text, story):
    iam_token = get_iam_token()
    # iam_token = IAM_TOKEN
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.9,
            "maxTokens": f"{MAX_TOKENS_PER_MESSAGE}"
        },
        "messages": [
            {
                "role": "system",
                "text": 'Ты - дружелюбный помощник по любым вопросам. Если необходимо, пользуйся интернетом.'
                        ' Не говори пользователю о том, '
                        'что ты не понимаешь голосовые сообщения. Отвечай на вопросы пользователя, следуя образу,'
                        ' не отправляй пользователю историю сообщений и разъяснения о себе'
            },
            {
                "role": "user",
                "text": text
            },
            {
                "role": "assistant",
                "text": f'история сообщений: {story}'
            },
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
        "x-folder-id": f"{FOLDER_ID}",
    }

    response = requests.post(
        url=GPT_URL,
        headers=headers,
        json=data
    )
    if response.status_code == 200:
        result = response.json()['result']['alternatives'][0]['message']['text']
        tokens = response.json()['result']['usage']['completionTokens']

        return result, int(tokens)
    else:
        error_msg = f"Ошибка: {response.status_code}"
        logger.error(error_msg)
        return 'что то пошло не так', 0


