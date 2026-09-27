import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        await db.commit()

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