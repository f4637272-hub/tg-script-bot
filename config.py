import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key: str, required: bool = True, default=None):
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"❌ Переменная {key} не задана в окружении!")
    return value

BOT_TOKEN = get_env("BOT_TOKEN")
BOT_USERNAME = get_env("BOT_USERNAME")

# Супер-админы (через запятую в ADMIN_IDS). Их нельзя удалить через бота.
ADMIN_IDS = [
    int(x.strip())
    for x in get_env("ADMIN_IDS", default="").split(",")
    if x.strip()
]

CHANNEL_ID = int(get_env("CHANNEL_ID"))
CHAT_ID = int(get_env("CHAT_ID"))
CHANNEL_URL = get_env("CHANNEL_URL")
CHAT_URL = get_env("CHAT_URL")

PROXY_URL = get_env("PROXY_URL", required=False, default="") or None

WEBHOOK_HOST = get_env("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

WEBHOOK_SECRET = get_env("WEBHOOK_SECRET")

DB_PATH = "scripts.db"