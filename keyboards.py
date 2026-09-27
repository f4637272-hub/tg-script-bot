from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_URL, CHAT_URL

def sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="💬 Подписаться на чат", url=CHAT_URL)],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
    ])

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить скрипт", callback_data="admin_add")],
        [InlineKeyboardButton(text="📋 Список скриптов", callback_data="admin_list")],
        [InlineKeyboardButton(text="🗑 Удалить скрипт", callback_data="admin_del")],
        [InlineKeyboardButton(text="📤 Опубликовать в канал", callback_data="admin_post")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")]
    ])