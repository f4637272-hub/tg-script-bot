import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key, required=True, default=None):
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"❌ Переменная {key} не задана!")
    return value

BOT_TOKEN = get_env("BOT_TOKEN")
BOT_USERNAME = get_env("BOT_USERNAME")

ADMIN_IDS = [
    int(x.strip())
    for x in get_env("ADMIN_IDS", default="").split(",")
    if x.strip()
]

CHANNEL_ID = int(get_env("CHANNEL_ID"))
CHAT_ID = int(get_env("CHAT_ID"))
CHANNEL_URL = get_env("CHANNEL_URL")
CHAT_URL = get_env("CHAT_URL")

LOG_CHANNEL_ID = int(get_env("LOG_CHANNEL_ID", required=False, default="0")) or None
PROXY_URL = get_env("PROXY_URL", required=False, default="") or None

DB_PATH = "scripts.db"