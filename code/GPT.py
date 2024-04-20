import requests
import json
import time
from config import IAM_TOKEN_ENDPOINT, IAM_TOKEN_PATH
from log import logger


def create_new_iam_token():
    """
    Получает новый IAM-TOKEN и дату истечения его срока годности и записывает полученные данные в json
    """
    headers = {"Metadata-Flavor": "Google"}
    try:
        response = requests.get(IAM_TOKEN_ENDPOINT, headers=headers)

    except Exception as e:
        error_msg = f"Ошибка в create_new_iam_token: {e}"
        logger.error(error_msg)

    else:
        if response.status_code == 200:
            token_data = {
                "access_token": response.json().get("access_token"),
                "expires_at": response.json().get("expires_in") + time.time()
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

        expires_at = token_data.get("expires_at")

        if expires_at <= time.time():
            create_new_iam_token()

    except FileNotFoundError:
        create_new_iam_token()
    with open(IAM_TOKEN_PATH, "r") as token_file:
        token_data = json.load(token_file)
    return token_data.get("access_token")