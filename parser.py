import feedparser
import httpx
import asyncio
import re
from aiogram import Bot

# --- ТВОЙ КЛЮЧ ВСТАВЛЕН ПРЯМО СЮДА ---
DEEPSEEK_KEY = "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"
BOT_TOKEN = "8948057154:AAEKXLKi4i5i7x_1dh1kd_JBc7lAMUBVi3I"
CHANNEL_ID = "-1004456666498"

bot = Bot(token=BOT_TOKEN)

RSS_SOURCES = [
    "https://lenta.ru/rss/news",
    "https://ria.ru/export/rss2/index.xml",
    "https://tass.ru/rss/v2/economic.xml"
]

published_links = set()

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
    if len(text) < 80:
        return f"{title}\n\n{text[:300]}"

    prompt = f"""
Ты — автор новостного канала. Напиши эту новость С НУЛЯ, полностью своими словами.

Задача:
- Передай суть события простым, понятным языком.
- Измени структуру, порядок фактов, формулировки.
- Добавь логику: что произошло, почему это важно, что будет дальше.
- Убери всё, что напоминает оригинал.
- Текст должен быть новым, не похожим на исходник.
- Факты сохрани (даты, имена, цифры).
- Не добавляй ссылки, источники, пометки.

Заголовок: {title}
Исходный текст: {text[:1000]}
"""

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                    "HTTP-Referer": "https://t.me/your_bot",
                    "X-Title": "NewsBot"
                },
                json={
                    "model": "deepseek/deepseek-chat:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500
                }
            )
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Ошибка рерайта: {e}")
            return f"{title}\n\n{text[:300]}"

async def check_feeds():
    global published_links
    for url in RSS_SOURCES:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            link = entry.link
            if link in published_links:
                continue
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
                published_links.add(link)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Ошибка отправки: {e}")
