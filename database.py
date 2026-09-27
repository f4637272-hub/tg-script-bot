import aiosqlite
from config import DB_PATH, ADMIN_IDS

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ==================== СКРИПТЫ ====================
async def add_script(name: str, content: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO scripts (name, content) VALUES (?, ?)",
            (name, content)
        )
        await db.commit()
        return cur.lastrowid

async def get_script(script_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name, content FROM scripts WHERE id=?",
            (script_id,)
        ) as cur:
            return await cur.fetchone()

async def get_all_scripts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name FROM scripts ORDER BY id") as cur:
            return await cur.fetchall()

async def delete_script(script_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scripts WHERE id=?", (script_id,))
        await db.commit()

# ==================== АДМИНЫ ====================
async def is_admin(user_id: int) -> bool:
    """Проверяет, админ ли пользователь (супер из .env или из БД)"""
    if user_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM admins WHERE user_id=?", (user_id,)
        ) as cur:
            return await cur.fetchone() is not None

async def add_admin(user_id: int, username: str, added_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, username, added_by) VALUES (?, ?, ?)",
            (user_id, username, added_by)
        )
        await db.commit()

async def remove_admin(user_id: int) -> bool:
    """Удаляет админа, но НЕ супер-админа из .env"""
    if user_id in ADMIN_IDS:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM admins WHERE user_id=?", (user_id,)
        )
        await db.commit()
        return cur.rowcount > 0

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username FROM admins ORDER BY added_at"
        ) as cur:
            return await cur.fetchall()