from dotenv import load_dotenv
from os import getenv

# ssh -i ~/.ssh/ssh_p student@158.160.134.86
# curl -H Metadata-Flavor:Google 169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
MAX_USERS = 3
MAX_TOKENS_PER_MESSAGE = 100
MAX_TOKENS_PER_USER = 700
ADMINS_ID = [1999763430]
IAM_TOKEN_PATH = '~/jarvis_bot/other/token.json'
IAM_TOKEN_ENDPOINT = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
STT_BLOCKS_PER_MESSAGE = 2
MAX_STT_BLOCKS_PER_USER = 20
TTS_SIMBOLS_PER_MESSAGE = 130
TTS_SIMBOLS_PER_USER = 500
MAX_STORY_LEN = 100

load_dotenv()
TOKEN = getenv('TOKEN')
IAM_TOKEN = getenv('IAM_TOKEN')
FOLDER_ID = getenv('FOLDER_ID')

DB_NAME = 'sqlite3.db'
