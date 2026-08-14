import feedparser
import httpx
import asyncio
import re
from aiogram import Bot
from config import BOT_TOKEN, CHANNEL_ID, DEEPSEEK_KEY

bot = Bot(token=BOT_TOKEN)

RSS_SOURCES = [
    "https://lenta.ru/rss/news",
    "https://ria.ru/export/rss2/index.xml",
    "https://tass.ru/rss/v2/economic.xml"
]

def get_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0]['url']
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.type:
                return enc.href
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.type and 'image' in link.type:
                return link.href
    if hasattr(entry, 'summary'):
        match = re.search(r'<img.*?src=["\'](.*?)["\']', entry.summary)
        if match:
            return match.group(1)
    return None

async def rewrite_news(title, text):
    if not DEEPSEEK_KEY or len(text) < 80:
        return f"{title}\n\n{text[:300]}..."
    prompt = f"Перепиши эту новость кратко, нейтрально, своими словами:\n{title}\n{text[:600]}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 250
                }
            )
            return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            return f"{title}\n\n{text[:250]}..."

async def check_feeds():
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            image = get_image(entry)
            if not image:
                continue
            title = entry.title
            desc = entry.get("summary", "")
            text = await rewrite_news(title, desc)
            try:
                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=text
                )
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Ошибка отправки: {e}")