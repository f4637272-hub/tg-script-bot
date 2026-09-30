from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CHANNEL_URL, CHAT_URL

# ---------- ПОДПИСКА ----------
def sub_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Канал", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="💬 Чат", url=CHAT_URL)],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")],
    ])

# ---------- ГЛАВНАЯ АДМИНКА ----------
def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 Скрипты", callback_data="menu_scripts")],
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="admin_post_custom")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="menu_users")],
        [InlineKeyboardButton(text="👮 Админы", callback_data="menu_admins")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")],
    ])

def back_admin():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ В админ-панель", callback_data="admin_back")],
    ])

# ---------- СКРИПТЫ ----------
def scripts_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="script_add")],
        [InlineKeyboardButton(text="📋 Список", callback_data="script_list")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def scripts_list_kb(scripts):
    btns = [
        [InlineKeyboardButton(
            text=f"📜 {n} — 👁 {v} [{c}]",
            callback_data=f"script_view_{sid}")]
        for sid, n, c, v in scripts
    ]
    btns.append([InlineKeyboardButton(text="⬅ Назад", callback_data="menu_scripts")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def script_actions_kb(sid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Имя", callback_data=f"script_editname_{sid}")],
        [InlineKeyboardButton(text="📝 Текст", callback_data=f"script_editcontent_{sid}")],
        [InlineKeyboardButton(text="🏷 Категория", callback_data=f"script_editcat_{sid}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"script_del_{sid}")],
        [InlineKeyboardButton(text="⬅ К списку", callback_data="script_list")],
    ])

def script_del_confirm(sid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"script_delconfirm_{sid}")],
        [InlineKeyboardButton(text="⬅ Отмена", callback_data=f"script_view_{sid}")],
    ])

# ---------- ПОСТЫ ----------
def post_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 С фото", callback_data="post_with_photo")],
        [InlineKeyboardButton(text="📄 Без фото", callback_data="post_no_photo")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def skip_photo_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_photo")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def scripts_select_kb(scripts, selected):
    btns = []
    for sid, n, c, v in scripts:
        mark = "✅" if sid in selected else "⬜"
        btns.append([InlineKeyboardButton(text=f"{mark} {n}", callback_data=f"toggle_{sid}")])
    btns.append([InlineKeyboardButton(text="🚀 Далее", callback_data="show_preview")])
    btns.append([InlineKeyboardButton(text="⬅ Отмена", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def post_preview_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm_publish")],
        [InlineKeyboardButton(text="✏️ Изменить текст", callback_data="edit_post_text")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="edit_post_photo")],
        [InlineKeyboardButton(text="⬅ Отмена", callback_data="admin_back")],
    ])

# ---------- ЮЗЕРЫ ----------
def users_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast_start")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="users_ban")],
        [InlineKeyboardButton(text="✅ Разбанить", callback_data="users_unban")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def broadcast_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="⬅ Отмена", callback_data="admin_back")],
    ])

# ---------- АДМИНЫ ----------
def admins_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="admin_add_user")],
        [InlineKeyboardButton(text="📋 Список", callback_data="admin_list_users")],
        [InlineKeyboardButton(text="➖ Удалить", callback_data="admin_del_user")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])

def del_admins_kb(db_admins):
    btns = [
        [InlineKeyboardButton(text=f"➖ {u} ({i})", callback_data=f"rmadmin_{i}")]
        for i, u in db_admins
    ]
    btns.append([InlineKeyboardButton(text="⬅ Назад", callback_data="menu_admins")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

# ---------- НАСТРОЙКИ ----------
def settings_menu(maintenance):
    st = "🟢 ВКЛ" if maintenance else "🔴 ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔧 Обслуживание: {st}", callback_data="toggle_maintenance")],
        [InlineKeyboardButton(text="📝 Приветствие", callback_data="edit_welcome")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="admin_back")],
    ])