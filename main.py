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
    CHANNEL_ID, CHAT_ID, PROXY_URL, LOG_CHANNEL_ID
)
from database import (
    init_db, add_script, get_script, get_all_scripts, update_script, delete_script,
    increment_views, is_admin, add_admin, remove_admin, get_all_admins,
    register_user, is_banned, ban_user, get_all_user_ids, get_user,
    get_setting, set_setting, get_stats
)
from keyboards import (
    sub_keyboard, admin_keyboard, back_admin,
    scripts_menu, scripts_list_kb, script_actions_kb, script_del_confirm,
    post_type_kb, skip_photo_kb, scripts_select_kb, post_preview_kb,
    users_menu, broadcast_confirm_kb,
    admins_menu, del_admins_kb, settings_menu
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

if PROXY_URL:
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=BOT_TOKEN, session=session)
else:
    bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

class S(StatesGroup):
    script_name = State()
    script_content = State()
    script_category = State()
    script_edit = State()
    post_photo = State()
    post_text = State()
    post_select = State()
    admin_new = State()
    broadcast = State()
    ban = State()
    unban = State()
    welcome = State()

# ============== УТИЛИТЫ ==============
async def is_subscribed(uid):
    try:
        m1 = await bot.get_chat_member(CHANNEL_ID, uid)
        m2 = await bot.get_chat_member(CHAT_ID, uid)
        ok = ["member", "administrator", "creator"]
        return m1.status in ok and m2.status in ok
    except Exception as e:
        logger.error(f"Подписка: {e}")
        return False

async def log_action(text):
    if not LOG_CHANNEL_ID:
        return
    try:
        await bot.send_message(LOG_CHANNEL_ID, f"📋 {text}", parse_mode="HTML")
    except Exception:
        pass

async def admin_guard(event):
    uid = event.from_user.id
    if not await is_admin(uid):
        if isinstance(event, types.CallbackQuery):
            await event.answer("⛔ Нет доступа.", show_alert=True)
        return False
    return True

# ============== /start ==============
@dp.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext):
    await state.clear()
    u = msg.from_user

    if await is_banned(u.id):
        await msg.answer("🚫 Ты забанен.")
        return

    await register_user(u.id, u.username, u.first_name)

    if await get_setting("maintenance") == "1" and not await is_admin(u.id):
        await msg.answer("🔧 Бот на обслуживании. Зайди позже.")
        return

    args = msg.text.split()
    payload = args[1] if len(args) > 1 else None

    if not await is_subscribed(u.id):
        await msg.answer("🔒 Подпишись на канал и чат:", reply_markup=sub_keyboard())
        return

    if payload and payload.startswith("script_"):
        try:
            sid = int(payload.split("_")[1])
        except (ValueError, IndexError):
            await msg.answer("❌ Неверная ссылка.")
            return
        sc = await get_script(sid)
        if not sc:
            await msg.answer("❌ Скрипт не найден.")
            return
        await increment_views(sid, u.id)
        _, name, content, cat, _ = sc
        await msg.answer(
            f"📜 <b>{name}</b>\n🏷 {cat}\n\n<code>{content}</code>",
            parse_mode="HTML"
        )
    else:
        welcome = await get_setting("welcome_text", "👋 Привет!")
        await msg.answer(welcome)

@dp.callback_query(F.data == "check_sub")
async def check_sub(cb: types.CallbackQuery):
    if await is_subscribed(cb.from_user.id):
        await cb.message.edit_text("✅ Подписка подтверждена! Жми кнопку в канале.")
    else:
        await cb.answer("❌ Не подписан!", show_alert=True)

# ============== /admin ==============
@dp.message(Command("admin"))
async def admin_panel(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.clear()
    await msg.answer("🛠 <b>Админ-панель</b>", parse_mode="HTML", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_back")
async def admin_back(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await state.clear()
    try:
        await cb.message.delete()
    except Exception:
        pass
    await cb.message.answer("🛠 <b>Админ-панель</b>",
                            parse_mode="HTML", reply_markup=admin_keyboard())
    await cb.answer()

# ============== СКРИПТЫ ==============
@dp.callback_query(F.data == "menu_scripts")
async def menu_scripts(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("📜 <b>Управление скриптами</b>",
                               parse_mode="HTML", reply_markup=scripts_menu())
    await cb.answer()

@dp.callback_query(F.data == "script_add")
async def script_add(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("📝 Введи <b>название</b> скрипта:",
                               parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.script_name)
    await cb.answer()

@dp.message(S.script_name)
async def s_name(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.update_data(name=msg.text)
    await msg.answer("📝 Отправь <b>текст скрипта</b>:", parse_mode="HTML",
                     reply_markup=back_admin())
    await state.set_state(S.script_content)

@dp.message(S.script_content)
async def s_content(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.update_data(content=msg.text)
    await msg.answer("🏷 Введи <b>категорию</b> (или напиши «Общее»):",
                     parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.script_category)

@dp.message(S.script_category)
async def s_cat(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    d = await state.get_data()
    sid = await add_script(d["name"], d["content"], msg.text, msg.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start=script_{sid}"
    await msg.answer(
        f"✅ <b>Скрипт сохранён!</b>\n\n🆔 <code>{sid}</code>\n"
        f"📛 {d['name']}\n🏷 {msg.text}\n🔗 <code>{link}</code>",
        parse_mode="HTML", reply_markup=back_admin())
    await log_action(f"➕ Скрипт #{sid} «{d['name']}» от {msg.from_user.id}")
    await state.clear()

@dp.callback_query(F.data == "script_list")
async def script_list(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    scripts = await get_all_scripts()
    if not scripts:
        await cb.answer("Пусто.", show_alert=True)
        return
    await cb.message.edit_text("📋 <b>Все скрипты:</b>",
                               parse_mode="HTML",
                               reply_markup=scripts_list_kb(scripts))
    await cb.answer()

@dp.callback_query(F.data.startswith("script_view_"))
async def script_view(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    sc = await get_script(sid)
    if not sc:
        await cb.answer("Не найден.", show_alert=True)
        return
    _, n, content, cat, v = sc
    txt = f"📜 <b>{n}</b>\n🏷 {cat}\n👁 {v}\n\n<code>{content[:500]}</code>"
    await cb.message.edit_text(txt, parse_mode="HTML",
                               reply_markup=script_actions_kb(sid))
    await cb.answer()

@dp.callback_query(F.data.startswith("script_editname_"))
async def script_edit_name(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    await state.update_data(sid=sid, field="name")
    await cb.message.answer("✏️ Отправь <b>новое название</b>:",
                            parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.script_edit)
    await cb.answer()

@dp.callback_query(F.data.startswith("script_editcontent_"))
async def script_edit_content(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    await state.update_data(sid=sid, field="content")
    await cb.message.answer("📝 Отправь <b>новый текст</b>:",
                            parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.script_edit)
    await cb.answer()

@dp.callback_query(F.data.startswith("script_editcat_"))
async def script_edit_cat(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    await state.update_data(sid=sid, field="category")
    await cb.message.answer("🏷 Отправь <b>новую категорию</b>:",
                            parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.script_edit)
    await cb.answer()

@dp.message(S.script_edit)
async def s_edit(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    d = await state.get_data()
    await update_script(d["sid"], **{d["field"]: msg.text})
    await msg.answer("✅ Обновлено.", reply_markup=back_admin())
    await state.clear()

@dp.callback_query(F.data.startswith("script_del_"))
async def script_del(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    await cb.message.edit_text(f"🗑 Удалить скрипт <code>{sid}</code>?",
                               parse_mode="HTML",
                               reply_markup=script_del_confirm(sid))
    await cb.answer()

@dp.callback_query(F.data.startswith("script_delconfirm_"))
async def script_del_ok(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[2])
    await delete_script(sid)
    await cb.message.edit_text(f"✅ Удалён #{sid}.", reply_markup=back_admin())
    await cb.answer()

# ============== СОЗДАНИЕ ПОСТА ==============
@dp.callback_query(F.data == "admin_post_custom")
async def post_start(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await state.clear()
    await cb.message.edit_text("📝 <b>Создание поста</b>\n\nВыбери тип:",
                               parse_mode="HTML", reply_markup=post_type_kb())
    await cb.answer()

@dp.callback_query(F.data == "post_with_photo")
async def post_photo(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("📷 Отправь <b>фото</b>:",
                               parse_mode="HTML", reply_markup=skip_photo_kb())
    await state.set_state(S.post_photo)
    await cb.answer()

@dp.callback_query(F.data == "post_no_photo")
async def post_no_photo(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await state.update_data(photo_id=None)
    await cb.message.edit_text("📝 Отправь <b>текст поста</b>:",
                               parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.post_text)
    await cb.answer()

@dp.callback_query(F.data == "skip_photo")
async def skip_photo(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await state.update_data(photo_id=None)
    await cb.message.edit_text("📝 Отправь <b>текст поста</b>:",
                               parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.post_text)
    await cb.answer()

@dp.message(S.post_photo, F.photo)
async def post_get_photo(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.update_data(photo_id=msg.photo[-1].file_id)
    await msg.answer("✅ Фото получено. Отправь <b>текст</b>:", parse_mode="HTML",
                     reply_markup=back_admin())
    await state.set_state(S.post_text)

@dp.message(S.post_photo)
async def post_photo_bad(msg: types.Message):
    if not await is_admin(msg.from_user.id):
        return
    await msg.answer("❌ Это не фото.")

@dp.message(S.post_text)
async def post_get_text(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.update_data(post_text=msg.html_text, selected=[])
    scripts = await get_all_scripts()
    if not scripts:
        await msg.answer("❌ Сначала создай скрипт.", reply_markup=back_admin())
        await state.clear()
        return
    await msg.answer("📎 <b>Выбери скрипты:</b>", parse_mode="HTML",
                     reply_markup=scripts_select_kb(scripts, []))
    await state.set_state(S.post_select)

@dp.callback_query(F.data.startswith("toggle_"), S.post_select)
async def post_toggle(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    sid = int(cb.data.split("_")[1])
    d = await state.get_data()
    sel = d.get("selected", [])
    if sid in sel:
        sel.remove(sid)
    else:
        sel.append(sid)
    await state.update_data(selected=sel)
    scripts = await get_all_scripts()
    try:
        await cb.message.edit_reply_markup(reply_markup=scripts_select_kb(scripts, sel))
    except Exception:
        pass
    await cb.answer()

@dp.callback_query(F.data == "show_preview", S.post_select)
async def show_preview(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    d = await state.get_data()
    text = d.get("post_text", "")
    sel = d.get("selected", [])
    photo = d.get("photo_id")
    if not sel:
        await cb.answer("Выбери хотя бы один скрипт!", show_alert=True)
        return
    scripts = await get_all_scripts()
    selected_scripts = [(sid, n) for sid, n, c, v in scripts if sid in sel]
    await state.update_data(selected_scripts=selected_scripts)
    preview = (f"👁 <b>Превью</b>\nКнопок: {len(selected_scripts)}\n"
               f"Фото: {'есть' if photo else 'нет'}\n\n———\n\n{text}")
    try:
        await cb.message.delete()
    except Exception:
        pass
    if photo:
        await cb.message.answer_photo(photo=photo, caption=preview,
                                      parse_mode="HTML", reply_markup=post_preview_kb())
    else:
        await cb.message.answer(preview, parse_mode="HTML", reply_markup=post_preview_kb())
    await cb.answer()

@dp.callback_query(F.data == "edit_post_text")
async def edit_text(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.answer("📝 Новый текст поста:", reply_markup=back_admin())
    await state.set_state(S.post_text)
    await cb.answer()

@dp.callback_query(F.data == "edit_post_photo")
async def edit_photo(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.answer("📷 Отправь новое фото:", reply_markup=skip_photo_kb())
    await state.set_state(S.post_photo)
    await cb.answer()

@dp.callback_query(F.data == "confirm_publish")
async def confirm_publish(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    d = await state.get_data()
    text = d.get("post_text", "")
    photo = d.get("photo_id")
    selected = d.get("selected_scripts", [])
    if not selected:
        await cb.answer("Ошибка.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🐙 {n}", url=f"https://t.me/{BOT_USERNAME}?start=script_{sid}")]
        for sid, n in selected
    ])
    try:
        if photo:
            await bot.send_photo(CHANNEL_ID, photo, caption=text, parse_mode="HTML", reply_markup=kb)
        else:
            await bot.send_message(CHANNEL_ID, text, parse_mode="HTML", reply_markup=kb)
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("✅ Пост опубликован!", reply_markup=back_admin())
        await log_action(f"📝 Пост опубликован админом {cb.from_user.id}")
    except Exception as e:
        await cb.message.answer(f"❌ {e}", reply_markup=back_admin())
    await state.clear()
    await cb.answer()

# ============== ЮЗЕРЫ ==============
@dp.callback_query(F.data == "menu_users")
async def menu_users(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("👥 <b>Пользователи</b>", parse_mode="HTML",
                               reply_markup=users_menu())
    await cb.answer()

@dp.callback_query(F.data == "broadcast_start")
async def broadcast_start(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("📢 Отправь <b>текст рассылки</b>:",
                               parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.broadcast)
    await cb.answer()

@dp.message(S.broadcast)
async def broadcast_text(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await state.update_data(bcast=msg.html_text)
    cnt = len(await get_all_user_ids())
    await msg.answer(f"📢 Отправить <b>{cnt}</b> юзерам?",
                     parse_mode="HTML", reply_markup=broadcast_confirm_kb())

@dp.callback_query(F.data == "broadcast_confirm")
async def broadcast_go(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    d = await state.get_data()
    text = d.get("bcast", "")
    users = await get_all_user_ids()
    ok = fail = 0
    status = await cb.message.answer(f"⏳ Рассылка... 0/{len(users)}")
    for i, uid in enumerate(users, 1):
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            ok += 1
        except Exception:
            fail += 1
        if i % 20 == 0:
            try:
                await status.edit_text(f"⏳ {i}/{len(users)}")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Готово!\n✔️ {ok} | ❌ {fail}", reply_markup=back_admin())
    await state.clear()
    await cb.answer()

@dp.callback_query(F.data == "users_ban")
async def users_ban(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("🚫 Отправь <b>ID</b> для бана:", parse_mode="HTML",
                               reply_markup=back_admin())
    await state.set_state(S.ban)
    await cb.answer()

@dp.message(S.ban)
async def do_ban(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Не число.")
        return
    await ban_user(uid, True)
    await msg.answer(f"🚫 <code>{uid}</code> забанен.", parse_mode="HTML",
                     reply_markup=back_admin())
    await state.clear()

@dp.callback_query(F.data == "users_unban")
async def users_unban(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("✅ Отправь <b>ID</b> для разбана:", parse_mode="HTML",
                               reply_markup=back_admin())
    await state.set_state(S.unban)
    await cb.answer()

@dp.message(S.unban)
async def do_unban(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("❌ Не число.")
        return
    await ban_user(uid, False)
    await msg.answer(f"✅ <code>{uid}</code> разбанен.", parse_mode="HTML",
                     reply_markup=back_admin())
    await state.clear()

# ============== АДМИНЫ ==============
@dp.callback_query(F.data == "menu_admins")
async def menu_admins(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text("👮 <b>Управление админами</b>", parse_mode="HTML",
                               reply_markup=admins_menu())
    await cb.answer()

@dp.callback_query(F.data == "admin_add_user")
async def add_adm(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    await cb.message.edit_text(
        "➕ Отправь <b>ID</b> или <b>перешли сообщение</b>:",
        parse_mode="HTML", reply_markup=back_admin())
    await state.set_state(S.admin_new)
    await cb.answer()

@dp.message(S.admin_new)
async def do_add_adm(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    target = None
    uname = ""
    if msg.forward_from:
        target = msg.forward_from.id
        uname = msg.forward_from.username or msg.forward_from.full_name
    elif msg.text and msg.text.strip().isdigit():
        target = int(msg.text.strip())
        uname = f"id{target}"
    if not target:
        await msg.answer("❌ Не понял.")
        return
    if await is_admin(target):
        await msg.answer(f"⚠️ Уже админ.", reply_markup=back_admin())
        await state.clear()
        return
    await add_admin(target, uname, msg.from_user.id)
    await msg.answer(f"✅ Добавлен <code>{target}</code>", parse_mode="HTML",
                     reply_markup=back_admin())
    await log_action(f"👮 Новый админ: {target} (добавил {msg.from_user.id})")
    await state.clear()

@dp.callback_query(F.data == "admin_list_users")
async def list_adms(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    text = "📋 <b>Админы:</b>\n\n🌟 <b>Супер:</b>\n"
    for u in ADMIN_IDS:
        text += f"• <code>{u}</code>\n"
    text += "\n👥 <b>Обычные:</b>\n"
    dbs = await get_all_admins()
    if not dbs:
        text += "<i>пусто</i>"
    else:
        for i, u in dbs:
            text += f"• <code>{i}</code> — {u}\n"
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=back_admin())
    await cb.answer()

@dp.callback_query(F.data == "admin_del_user")
async def del_adm(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    dbs = await get_all_admins()
    if not dbs:
        await cb.answer("Нет админов.", show_alert=True)
        return
    await cb.message.edit_text("Выбери:", reply_markup=del_admins_kb(dbs))
    await cb.answer()

@dp.callback_query(F.data.startswith("rmadmin_"))
async def rm_adm(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    uid = int(cb.data.split("_")[1])
    if uid in ADMIN_IDS:
        await cb.answer("Супер-админа нельзя удалить!", show_alert=True)
        return
    ok = await remove_admin(uid)
    await cb.message.edit_text(
        f"{'✅ Удалён' if ok else '❌ Не найден'} <code>{uid}</code>",
        parse_mode="HTML", reply_markup=back_admin())
    await cb.answer()

# ============== НАСТРОЙКИ ==============
@dp.callback_query(F.data == "menu_settings")
async def menu_settings(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    m = await get_setting("maintenance") == "1"
    await cb.message.edit_text("⚙️ <b>Настройки</b>", parse_mode="HTML",
                               reply_markup=settings_menu(m))
    await cb.answer()

@dp.callback_query(F.data == "toggle_maintenance")
async def toggle_m(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    current = await get_setting("maintenance") == "1"
    await set_setting("maintenance", "0" if current else "1")
    m = await get_setting("maintenance") == "1"
    await cb.message.edit_reply_markup(reply_markup=settings_menu(m))
    await cb.answer("Переключено.")

@dp.callback_query(F.data == "edit_welcome")
async def edit_welcome(cb: types.CallbackQuery, state: FSMContext):
    if not await admin_guard(cb):
        return
    cur = await get_setting("welcome_text")
    await cb.message.edit_text(f"📝 Текущий:\n\n{cur}\n\nОтправь новый:",
                               reply_markup=back_admin())
    await state.set_state(S.welcome)
    await cb.answer()

@dp.message(S.welcome)
async def set_welcome(msg: types.Message, state: FSMContext):
    if not await is_admin(msg.from_user.id):
        return
    await set_setting("welcome_text", msg.html_text)
    await msg.answer("✅ Приветствие обновлено.", reply_markup=back_admin())
    await state.clear()

# ============== СТАТИСТИКА ==============
@dp.callback_query(F.data == "show_stats")
async def show_stats(cb: types.CallbackQuery):
    if not await admin_guard(cb):
        return
    s = await get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Юзеров: <b>{s['users']}</b>\n"
        f"🚫 Забанено: <b>{s['banned']}</b>\n"
        f"📜 Скриптов: <b>{s['scripts']}</b>\n"
        f"👁 Просмотров: <b>{s['views']}</b>"
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=back_admin())
    await cb.answer()

# ============== ЗАПУСК ==============
async def on_startup(bot: Bot):
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ БД инициализирована, polling готов")

async def main():
    dp.startup.register(on_startup)
    logger.info("🚀 Бот запущен (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())