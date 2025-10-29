import asyncio
import logging
import tempfile
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import TELEGRAM_TOKEN, TZ
from .storage import init_db, set_tournament, get_tournament
from .flashscore import scrape_tournament
from .plaque import render_plaque
from .modules.formatter import naive_categorize, format_message, match_lookup

logging.basicConfig(level=logging.INFO)
bot = Bot(TELEGRAM_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TZ)

def ensure_token():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN не задан в окружении")

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я соберу результаты матчей турнира и сделаю плашки.\n\n"
        "Команды:\n"
        "/set <ссылка_на_турнир_Flashscore> — выбрать турнир\n"
        "/today — прислать результаты за сегодня\n"
        "/plaque — сделать плашки для указанных пар (внизу списка)\n"
        "Пример: 'Рублёв — Тьен'\n\n"
        "Для ежедневной рассылки на сервере используйте GitHub Actions."
    )

@dp.message(Command("set"))
async def set_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Пришлите ссылку на турнир после команды /set")
        return
    url = parts[1].strip()
    set_tournament(message.chat.id, url, title=None)
    await message.reply("Ок! Турнир сохранён. Используйте /today или /plaque.")

async def send_today(chat_id: int):
    info = get_tournament(chat_id)
    if not info:
        await bot.send_message(chat_id, "Сначала задайте турнир: /set <ссылка>")
        return
    url, saved_title = info
    matches = scrape_tournament(url)
    if not matches:
        await bot.send_message(chat_id, "Не нашёл завершённых матчей сегодня.")
        return
    title = saved_title or (matches[0].tournament or "Турнир") + (", " + matches[0].round_text if matches[0].round_text else "")
    text = format_message(title, naive_categorize(matches))
    await bot.send_message(chat_id, text)

@dp.message(Command("today"))
async def today(message: Message):
    await send_today(message.chat.id)

@dp.message(Command("plaque"))
async def plaque(message: Message):
    info = get_tournament(message.chat.id)
    if not info:
        await message.reply("Сначала задайте турнир: /set <ссылка>")
        return
    url, saved_title = info
    matches = scrape_tournament(url)
    if not matches:
        await message.reply("Не нашёл завершённых матчей сегодня.")
        return

    raw = message.text.split("\n", 1)
    payload = raw[1] if len(raw) > 1 else (message.reply_to_message.text if message.reply_to_message else "")
    if not payload.strip():
        await message.reply("Пришлите список строк с парами вида: 'Игрок1 — Игрок2' каждая с новой строки (после /plaque или ответом на сообщение).")
        return

    pairs = [line.strip() for line in payload.splitlines() if line.strip()]
    created = 0
    for line in pairs:
        m = match_lookup(line, matches)
        if not m:
            await message.answer(f"Не нашёл матч по строке: {line}")
            continue
        tour_line = saved_title or (m.tournament or "")
        img = render_plaque(m.player1, m.player2, m.score_sets, tournament_line=tour_line)
        fd, tmp = tempfile.mkstemp(prefix=f"plaque_{m.key}_", suffix=".png")
        os.close(fd)
        img.save(tmp)
        await message.answer_photo(photo=FSInputFile(tmp), caption=m.to_line())
        created += 1

    if created == 0:
        await message.answer("Плашки не созданы. Проверьте написание пар.")

async def main():
    ensure_token()
    init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
