import feedparser
import asyncio
import re
import random
from aiogram import Bot

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

def rewrite_manually(title, desc):
    # Убираем лишние пробелы
    desc = desc.strip()
    
    # Набор вступлений
    intros = [
        "По сообщениям СМИ, ",
        "Стало известно, что ",
        "Согласно информации, ",
        "Как стало известно, "
    ]
    
    # Если описание пустое — только заголовок
    if not desc or len(desc) < 30:
        return f"{title}"
    
    # Переставляем слова: разбиваем на предложения, меняем порядок
    sentences = desc.split('. ')
    random.shuffle(sentences)
    new_desc = '. '.join(sentences)
    
    # Добавляем вступление
    intro = random.choice(intros)
    result = f"{intro}{title}. {new_desc[:400]}"
    
    return result

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
            text = rewrite_manually(title, desc)
            try:
                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image,
                    caption=text
                )
                published_links.add(link)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Ошибка: {e}")
