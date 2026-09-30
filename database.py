import aiosqlite
from config import DB_PATH, ADMIN_IDS

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'Общее',
                views INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            )""")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )""")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS script_views (
                user_id INTEGER,
                script_id INTEGER,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
        await db.execute("INSERT OR IGNORE INTO settings VALUES ('maintenance','0')")
        await db.execute("INSERT OR IGNORE INTO settings VALUES ('welcome_text','👋 Привет! Выбери скрипт в канале.')")
        await db.commit()

# ============== СКРИПТЫ ==============
async def add_script(name, content, category="Общее", created_by=0):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO scripts (name,content,category,created_by) VALUES (?,?,?,?)",
            (name, content, category, created_by))
        await db.commit()
        return cur.lastrowid

async def get_script(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id,name,content,category,views FROM scripts WHERE id=?", (sid,)) as cur:
            return await cur.fetchone()

async def get_all_scripts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id,name,category,views FROM scripts ORDER BY id") as cur:
            return await cur.fetchall()

async def update_script(sid, name=None, content=None, category=None):
    async with aiosqlite.connect(DB_PATH) as db:
        if name:
            await db.execute("UPDATE scripts SET name=? WHERE id=?", (name, sid))
        if content:
            await db.execute("UPDATE scripts SET content=? WHERE id=?", (content, sid))
        if category:
            await db.execute("UPDATE scripts SET category=? WHERE id=?", (category, sid))
        await db.commit()

async def delete_script(sid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scripts WHERE id=?", (sid,))
        await db.commit()

async def increment_views(sid, uid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE scripts SET views=views+1 WHERE id=?", (sid,))
        await db.execute("INSERT INTO script_views VALUES (?,?,CURRENT_TIMESTAMP)", (uid, sid))
        await db.commit()

# ============== АДМИНЫ ==============
async def is_admin(uid):
    if uid in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admins WHERE user_id=?", (uid,)) as cur:
            return await cur.fetchone() is not None

async def add_admin(uid, uname, by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO admins VALUES (?,?,?,CURRENT_TIMESTAMP)",
                         (uid, uname, by))
        await db.commit()

async def remove_admin(uid):
    if uid in ADMIN_IDS:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM admins WHERE user_id=?", (uid,))
        await db.commit()
        return cur.rowcount > 0

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id,username FROM admins ORDER BY added_at") as cur:
            return await cur.fetchall()

# ============== ЮЗЕРЫ ==============
async def register_user(uid, uname, fname):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id,username,first_name) VALUES (?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_activity=CURRENT_TIMESTAMP""", (uid, uname or "", fname or ""))
        await db.commit()

async def is_banned(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,)) as cur:
            r = await cur.fetchone()
            return bool(r and r[0])

async def ban_user(uid, ban=True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned=? WHERE user_id=?",
                         (1 if ban else 0, uid))
        await db.commit()

async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE is_banned=0") as cur:
            return [r[0] for r in await cur.fetchall()]

async def get_user(uid):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id,username,first_name,is_banned,joined_at FROM users WHERE user_id=?",
            (uid,)) as cur:
            return await cur.fetchone()

# ============== НАСТРОЙКИ ==============
async def get_setting(key, default=""):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            r = await cur.fetchone()
            return r[0] if r else default

async def set_setting(key, value):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO settings VALUES (?,?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value""", (key, value))
        await db.commit()

# ============== СТАТИСТИКА ==============
async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_banned=1") as c:
            banned = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM scripts") as c:
            scripts = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM script_views") as c:
            views = (await c.fetchone())[0]
        return {"users": users, "banned": banned, "scripts": scripts, "views": views}