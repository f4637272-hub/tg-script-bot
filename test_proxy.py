import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector

# Все прокси для проверки
PROXIES = [
    ("http",   "http://138.2.64.185:8118"),
    ("socks5", "socks5://138.2.64.185:8118"),
    ("http",   "http://41.33.219.140:1976"),
    ("socks5", "socks5://41.33.219.140:1976"),
    ("http",   "http://45.61.133.104:7777"),
    ("socks5", "socks5://45.61.133.104:7777"),
    ("http",   "http://47.236.86.147:443"),
    ("https",  "https://47.236.86.147:443"),
    ("socks5", "socks5://47.236.86.147:443"),
]

async def check(proxy_type, proxy_url):
    print(f"\n🔍 {proxy_url}")
    try:
        if proxy_type == "socks5":
            connector = ProxyConnector.from_url(proxy_url)
            session = aiohttp.ClientSession(connector=connector)
            async with session:
                async with session.get(
                    "https://api.telegram.org",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    print(f"   ✅ Работает! Статус: {resp.status}")
                    return True
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.telegram.org",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    print(f"   ✅ Работает! Статус: {resp.status}")
                    return True
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {e}")
        return False

async def main():
    print("=" * 55)
    print("ТЕСТ ПРОКСИ ДЛЯ TELEGRAM-БОТА")
    print("=" * 55)
    working = []
    for ptype, purl in PROXIES:
        if await check(ptype, purl):
            working.append(purl)
    print("\n" + "=" * 55)
    if working:
        print("🎯 РАБОЧИЕ ПРОКСИ:")
        for w in working:
            print(f"   PROXY_URL={w}")
    else:
        print("😢 Ни один прокси не работает.")
        print("Купи на proxy6.net — 25-50₽, и всё заработает.")
    print("=" * 55)

asyncio.run(main())