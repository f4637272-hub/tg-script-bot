import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.webhook.aiohttp_server import setup_application

from config import (
    BOT_TOKEN, BOT_USERNAME, ADMIN_ID,
    CHANNEL_ID, CHAT_ID, PROXY_URL,
    WEBHOOK_URL, WEBHOOK_PATH, WEBHOOK_SECRET,
    WEB_SERVER_HOST, WEB_SERVER_PORT
)
from database import (
    init_db, add_script, get_script,
    get_all_scripts, delete_script
)
from keyboards import sub_keyboard, admin_keyboard, cancel_keyboard
from webhook_server import run_server

# ==================== ЛОГИ ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== БОТ ====================
if PROXY_URL:
    logger.info(f"🌐 Прокси: {PROXY_URL.split('@')[-1]}")
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
else:
    logger.info("🌐 Без прокси (прямое подключение)")
    bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

# ==================== FSM ====================
class AdminStates(StatesGroup):
    waiting_name = State()
    waiting_content = State()

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
async def cmd_start(message: types.Message):
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
            await message.answer("❌ Скрипт не найден или удалён.")
            return

        name, content = script
        await message.answer(
            f"📜 <b>{name}</b>\n\n<code>{content}</code>",
            parse_mode="HTML"
        )
    else:
        await message.answer("👋 Привет! Выбери скрипт в канале и нажми на кнопку.")

# ==================== ПРОВЕРКА ПОДПИСКИ ====================
@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Подписка подтверждена!\nТеперь жми кнопку с нужным скриптом в канале."
        )
    else:
        await callback.answer("❌ Ты ещё не подписался на всё!", show_alert=True)

# ==================== АДМИН-ПАНЕЛЬ ====================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 <b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()

@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
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
    if message.from_user.id != ADMIN_ID:
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
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    script_id = await add_script(data["name"], message.text)
    link = f"https://t.me/{BOT_USERNAME}?start=script_{script_id}"

    await message.answer(
        f"✅ <b>Скрипт сохранён!</b>\n\n"
        f"🆔 ID: <code>{script_id}</code>\n"
        f"📛 Название: {data['name']}\n\n"
        f"🔗 <b>Ссылка:</b>\n<code>{link}</code>",
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(F.data == "admin_list")
async def admin_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    scripts = await get_all_scripts()
    if not scripts:
        await callback.answer("Скриптов пока нет.", show_alert=True)
        return

    text = "📋 <b>Все скрипты:</b>\n\n"
    for sid, name in scripts:
        text += (
            f"🆔 <code>{sid}</code> — <b>{name}</b>\n"
            f"🔗 <code>https://t.me/{BOT_USERNAME}?start=script_{sid}</code>\n\n"
        )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_del")
async def admin_del_prompt(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    scripts = await get_all_scripts()
    if not scripts:
        await callback.answer("Нечего удалять.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {name} (ID:{sid})", callback_data=f"del_{sid}")]
        for sid, name in scripts
    ] + [[InlineKeyboardButton(text="⬅ Назад", callback_data="admin_cancel")]])

    await callback.message.edit_text("Выбери скрипт для удаления:", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def admin_del(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    sid = int(callback.data.split("_")[1])
    await delete_script(sid)
    await callback.message.edit_text(f"✅ Скрипт <code>{sid}</code> удалён.", parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "admin_post")
async def admin_post(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    scripts = await get_all_scripts()
    if not scripts:
        await callback.answer("Сначала создай скрипт.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🐙 {name}",
            url=f"https://t.me/{BOT_USERNAME}?start=script_{sid}"
        )]
        for sid, name in scripts
    ])

    await bot.send_message(
        CHANNEL_ID,
        "🔥 <b>Ink Game</b> 🔥\n"
        "+без ключа / no key\n"
        "+без бана / no ban\n\n"
        "👇 Жми кнопку ниже:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.message.edit_text("✅ Пост опубликован в канал!")
    await callback.answer()

# ==================== ЗАПУСК С ВЕБХУКОМ ====================
async def on_startup(bot: Bot):
    await init_db()
    await bot.set_webhook(
        url=WEBHOOK_URL,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True
    )
    logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("🛑 Вебхук удалён")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем веб-сервер параллельно
    runner = await run_server(dp, bot)

    # Ждём бесконечно
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())