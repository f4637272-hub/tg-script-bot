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
        [InlineKeyboardButton(text="📝 Создать пост в канал", callback_data="admin_post_custom")],
        [InlineKeyboardButton(text="🗑 Удалить скрипт", callback_data="admin_del")],
        [InlineKeyboardButton(text="👥 Управление админами", callback_data="admin_manage")],
    ])

def back_to_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад в админ-панель", callback_data="admin_back")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Назад в админ-панель", callback_data="admin_back")]
    ])

def del_scripts_keyboard(scripts):
    buttons = [
        [InlineKeyboardButton(text=f"🗑 {name} (ID:{sid})", callback_data=f"del_{sid}")]
        for sid, name in scripts
    ]
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def post_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 Пост с фото", callback_data="post_with_photo")],
        [InlineKeyboardButton(text="📄 Пост без фото", callback_data="post_no_photo")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")]
    ])

def skip_photo_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить фото", callback_data="skip_photo")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")]
    ])

def scripts_select_keyboard(scripts, selected_ids):
    buttons = []
    for sid, name in scripts:
        mark = "✅" if sid in selected_ids else "⬜"
        buttons.append([
            InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"toggle_{sid}")
        ])
    buttons.append([InlineKeyboardButton(text="🚀 Далее", callback_data="show_preview")])
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def post_preview_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm_publish")],
        [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="edit_post_text")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="edit_post_photo")],
        [InlineKeyboardButton(text="⬅ Отмена", callback_data="admin_back")]
    ])

# ==================== АДМИНЫ ====================
def admins_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_user")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admin_list_users")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_del_user")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def del_admins_keyboard(db_admins):
    buttons = [
        [InlineKeyboardButton(
            text=f"➖ {uname} ({uid})",
            callback_data=f"rmadmin_{uid}"
        )]
        for uid, uname in db_admins
    ]
    buttons.append([InlineKeyboardButton(text="⬅ Назад", callback_data="admin_manage")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)