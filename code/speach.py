from log import logger
import requests
from config import IAM_TOKEN, FOLDER_ID


def text_to_speach(user_text: str):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }
    data = {
        "text": user_text,
        'lang': 'ru-RU',
        'voice': 'filipp',
        'folderId': f'{FOLDER_ID}'
    }
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content, len(user_text)
    else:
        error_msg = f'ошибка SpeachKit: {response.content}'
        logger.error(error_msg)
        return False, error_msg, 0


def speech_to_text(data):

    params = "&".join([
        "topic=general",
        f"folderId={FOLDER_ID}",
        "lang=ru-RU"
    ])

    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }

    url = f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}"

    response = requests.post(
        url=url,
        headers=headers,
        data=data
    )

    decoded_data = response.json()
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")

    else:
        error_msg = f'ошибка SpeachKit: {decoded_data.get("error_code")}'
        logger.error(error_msg)
        return False, error_msg
