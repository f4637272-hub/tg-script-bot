import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHAT_ID = int(os.getenv("CHAT_ID"))
CHANNEL_URL = os.getenv("CHANNEL_URL")
CHAT_URL = os.getenv("CHAT_URL")

# Прокси (на Render не нужен, оставь пустым)
PROXY_URL = os.getenv("PROXY_URL", "").strip() or None

# ===== ВЕБХУК =====
# На Render подставляется автоматически из переменной RENDER_EXTERNAL_URL
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-app.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Локальный порт для веб-сервера (Render даёт свой через PORT)
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

# Секретный токен для верификации вебхука
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change_me_123456")

DB_PATH = "scripts.db"