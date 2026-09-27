import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession

from config import (
    BOT_TOKEN, BOT_USERNAME, ADMIN_IDS,
    CHANNEL_ID, CHAT_ID, PROXY_URL,
    WEBHOOK_URL, WEBHOOK_PATH, WEBHOOK_SECRET,
    WEB_SERVER_HOST, WEB_SERVER_PORT
)
from database import (
    init_db, add_script, get_script,
    get_all_scripts, delete_script,
    is_admin, add_admin, remove_admin, get_all_admins
)
from keyboards import (
    sub_keyboard, admin_keyboard, back_to_admin_keyboard,
    cancel_keyboard, del_scripts_keyboard,
    post_type_keyboard, skip_photo_keyboard,
    scripts_select_keyboard, post_preview_keyboard,
    admins_menu_keyboard, del_admins_keyboard
)
from webhook_server import run_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

if PROXY_URL:
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
else:
    bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

# ==================== FSM ====================
class AdminStates(StatesGroup):
    waiting_name = State()
    waiting_content = State()
    waiting_post_photo = State()
    waiting_post_text = State()
    selecting_scripts = State()
    waiting_new_admin = State()

# ==================== ПРОВЕРКА ПОДПИСОК ====================
async def is_subscribed(user_id: int) -> bool:
    try:
        m1 = await bot.get_chat_member(CHANNEL_ID, user_id)
        m2 = await bot.get_chat_member(CHAT_ID, user_id)
        valid = ["member", "administrator", "creator"]
        return m1.status in valid and m2.status in valid
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# ==================== /start ====================
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    args = message.text.split()
    payload = args[1] if len(args) > 1 else None

    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Для доступа подпишись на канал и чат:",
            reply_markup=sub_keyboard()
        )
        return

    if payload and payload.startswith("script_"):
        try:
            script_id = int(payload.split("_")[1])
        except (ValueError, IndexError):
            await message.answer("❌ Неверная ссылка.")
            return
        script = await get_script(script_id)
        if not script:
            await message.answer("❌ Скрипт не найден.")
            return
        name, content = script
        await message.answer(
            f"📜 <b>{name}</b>\n\n<code>{content}</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer("👋 Привет! Выбери скрипт в канале.")

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text("✅ Подписка подтверждена!")
    else:
        await callback.answer("❌ Не подписан!", show_alert=True)

# ==================== АДМИН-ПАНЕЛЬ ====================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🛠 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🛠 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

# ==================== ДОБАВЛЕНИЕ СКРИПТА ====================
@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📝 Введи <b>название</b> скрипта:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_name)
    await callback.answer()

@dp.message(AdminStates.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer(
        "📝 Теперь отправь <b>текст скрипта</b>:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_content)

@dp.message(AdminStates.waiting_content)
async def process_content(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    script_id = await add_script(data["name"], message.text)
    link = f"https://t.me/{BOT_USERNAME}?start=script_{script_id}"
    await message.answer(
        f"✅ <b>Скрипт сохранён!</b>\n\n"
        f"🆔 ID: <code>{script_id}</code>\n"
        f"📛 Название: {data['name']}\n"
        f"🔗 <code>{link}</code>",
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await state.clear()

# ==================== СПИСОК ====================
@dp.callback_query(F.data == "admin_list")
async def admin_list(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    scripts = await get_all_scripts()
    if not scripts:
        await callback.answer("Скриптов нет.", show_alert=True)
        return
    text = "📋 <b>Все скрипты:</b>\n\n"
    for sid, name in scripts:
        text += f"🆔 <code>{sid}</code> — {name}\n"
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await callback.answer()

# ==================== УДАЛЕНИЕ ====================
@dp.callback_query(F.data == "admin_del")
async def admin_del_prompt(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    scripts = await get_all_scripts()
    if not scripts:
        await callback.answer("Нечего удалять.", show_alert=True)
        return
    await callback.message.edit_text(
        "Выбери скрипт для удаления:",
        reply_markup=del_scripts_keyboard(scripts)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def admin_del(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    sid = int(callback.data.split("_")[1])
    await delete_script(sid)
    await callback.message.edit_text(
        f"✅ Скрипт <code>{sid}</code> удалён.",
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await callback.answer()

# ==================== СОЗДАНИЕ ПОСТА ====================
@dp.callback_query(F.data == "admin_post_custom")
async def admin_post_start(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "📝 <b>Создание поста</b>\n\nВыбери тип поста:",
        parse_mode="HTML",
        reply_markup=post_type_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "post_with_photo")
async def post_with_photo(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📷 Отправь <b>фото</b> для поста:",
        parse_mode="HTML",
        reply_markup=skip_photo_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_photo)
    await callback.answer()

@dp.callback_query(F.data == "post_no_photo")
async def post_no_photo(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.update_data(photo_id=None)
    await callback.message.edit_text(
        "📝 Отправь <b>текст поста</b>:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_text)
    await callback.answer()

@dp.callback_query(F.data == "skip_photo")
async def skip_photo(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await state.update_data(photo_id=None)
    await callback.message.edit_text(
        "📝 Отправь <b>текст поста</b>:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_text)
    await callback.answer()

@dp.message(AdminStates.waiting_post_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await message.answer(
        "✅ Фото получено!\n\n📝 Теперь отправь <b>текст поста</b>:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_text)

@dp.message(AdminStates.waiting_post_photo)
async def process_photo_invalid(message: types.Message):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("❌ Это не фото. Отправь картинку или нажми «Пропустить фото».")

@dp.message(AdminStates.waiting_post_text)
async def process_post_text(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(post_text=message.html_text, selected=[])
    scripts = await get_all_scripts()
    if not scripts:
        await message.answer(
            "❌ Сначала создай хотя бы один скрипт.",
            reply_markup=back_to_admin_keyboard()
        )
        await state.clear()
        return
    await message.answer(
        "📎 <b>Выбери скрипты</b>, которые прикрепить кнопками:",
        parse_mode="HTML",
        reply_markup=scripts_select_keyboard(scripts, [])
    )
    await state.set_state(AdminStates.selecting_scripts)

# ==================== ВЫБОР СКРИПТОВ ====================
@dp.callback_query(F.data.startswith("toggle_"), AdminStates.selecting_scripts)
async def toggle_script(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    sid = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected = data.get("selected", [])
    if sid in selected:
        selected.remove(sid)
    else:
        selected.append(sid)
    await state.update_data(selected=selected)
    scripts = await get_all_scripts()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=scripts_select_keyboard(scripts, selected)
        )
    except Exception:
        pass
    await callback.answer()

# ==================== ПРЕВЬЮ ====================
@dp.callback_query(F.data == "show_preview", AdminStates.selecting_scripts)
async def show_preview(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    post_text = data.get("post_text", "")
    selected = data.get("selected", [])
    photo_id = data.get("photo_id")

    if not selected:
        await callback.answer("Выбери хотя бы один скрипт!", show_alert=True)
        return

    scripts = await get_all_scripts()
    selected_scripts = [(sid, name) for sid, name in scripts if sid in selected]
    await state.update_data(selected_scripts=selected_scripts)

    preview_caption = (
        f"👁 <b>Превью поста</b>\n"
        f"Кнопок: {len(selected_scripts)}\n"
        f"Фото: {'есть' if photo_id else 'нет'}\n\n"
        f"———\n\n{post_text}"
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo_id:
        await callback.message.answer_photo(
            photo=photo_id,
            caption=preview_caption,
            parse_mode="HTML",
            reply_markup=post_preview_keyboard()
        )
    else:
        await callback.message.answer(
            preview_caption,
            parse_mode="HTML",
            reply_markup=post_preview_keyboard()
        )
    await callback.answer()

@dp.callback_query(F.data == "edit_post_text")
async def edit_post_text(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "📝 Отправь <b>новый текст</b> поста:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_text)
    await callback.answer()

@dp.callback_query(F.data == "edit_post_photo")
async def edit_post_photo(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.answer(
        "📷 Отправь <b>новое фото</b>:",
        parse_mode="HTML",
        reply_markup=skip_photo_keyboard()
    )
    await state.set_state(AdminStates.waiting_post_photo)
    await callback.answer()

# ==================== ПУБЛИКАЦИЯ ====================
@dp.callback_query(F.data == "confirm_publish")
async def confirm_publish(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    post_text = data.get("post_text", "")
    photo_id = data.get("photo_id")
    selected_scripts = data.get("selected_scripts", [])

    if not selected_scripts:
        await callback.answer("Ошибка: скрипты не выбраны.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🐙 {name}",
            url=f"https://t.me/{BOT_USERNAME}?start=script_{sid}"
        )]
        for sid, name in selected_scripts
    ])

    try:
        if photo_id:
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo_id,
                caption=post_text,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=post_text,
                parse_mode="HTML",
                reply_markup=kb
            )
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "✅ Пост опубликован в канал!",
            reply_markup=back_to_admin_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка публикации: {e}",
            reply_markup=back_to_admin_keyboard()
        )
    await state.clear()
    await callback.answer()

# ==================== УПРАВЛЕНИЕ АДМИНАМИ ====================
@dp.callback_query(F.data == "admin_manage")
async def admin_manage(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "👥 <b>Управление админами</b>\n\n"
        "<i>Супер-админы из .env не могут быть удалены.</i>",
        parse_mode="HTML",
        reply_markup=admins_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_add_user")
async def admin_add_user(callback: types.CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "➕ <b>Добавление админа</b>\n\n"
        "Отправь одно из:\n"
        "• Telegram ID (число)\n"
        "• Пересланное сообщение от нужного человека",
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.waiting_new_admin)
    await callback.answer()

@dp.message(AdminStates.waiting_new_admin)
async def process_new_admin(message: types.Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return

    target_id = None
    target_username = ""

    if message.forward_from:
        target_id = message.forward_from.id
        target_username = message.forward_from.username or message.forward_from.full_name
    elif message.text and message.text.strip().isdigit():
        target_id = int(message.text.strip())
        target_username = f"id{target_id}"
    else:
        await message.answer(
            "❌ Не понял. Отправь ID числом или перешли сообщение от человека.",
            reply_markup=back_to_admin_keyboard()
        )
        return

    if await is_admin(target_id):
        await message.answer(
            f"⚠️ <code>{target_id}</code> уже админ.",
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )
        await state.clear()
        return

    await add_admin(target_id, target_username, message.from_user.id)
    await message.answer(
        f"✅ <b>Админ добавлен!</b>\n\n"
        f"🆔 ID: <code>{target_id}</code>\n"
        f"👤 {target_username}",
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await state.clear()

@dp.callback_query(F.data == "admin_list_users")
async def admin_list_users(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    text = "📋 <b>Список админов:</b>\n\n"
    text += "🌟 <b>Супер-админы (из .env):</b>\n"
    for uid in ADMIN_IDS:
        text += f"• <code>{uid}</code>\n"
    text += "\n👥 <b>Обычные админы:</b>\n"
    db_admins = await get_all_admins()
    if not db_admins:
        text += "<i>пусто</i>\n"
    else:
        for uid, uname in db_admins:
            text += f"• <code>{uid}</code> — {uname}\n"
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_to_admin_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_del_user")
async def admin_del_user(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    db_admins = await get_all_admins()
    if not db_admins:
        await callback.answer("В БД нет админов.", show_alert=True)
        return
    await callback.message.edit_text(
        "Выбери, у кого забрать админку:",
        reply_markup=del_admins_keyboard(db_admins)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("rmadmin_"))
async def remove_admin_cb(callback: types.CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    uid = int(callback.data.split("_")[1])
    if uid in ADMIN_IDS:
        await callback.answer("Супер-админа удалить нельзя!", show_alert=True)
        return
    ok = await remove_admin(uid)
    if ok:
        await callback.message.edit_text(
            f"✅ Админ <code>{uid}</code> удалён.",
            parse_mode="HTML",
            reply_markup=back_to_admin_keyboard()
        )
    else:
        await callback.answer("Не найден.", show_alert=True)
    await callback.answer()

# ==================== ЗАПУСК ====================
async def on_startup(bot: Bot):
    await init_db()
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logger.info(f"✅ Вебхук: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    runner = await run_server(dp, bot)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())