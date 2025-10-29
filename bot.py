import asyncio
import logging
import os
from datetime import datetime, timedelta
import zoneinfo

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import TELEGRAM_TOKEN, TZ
from .storage import init_db, set_tournament, get_tournament, set_override, get_overrides
from .flashscore import scrape_tournament, Match
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
        "/today — прислать результаты за сегодня (и черновик сообщения)\n"
        "/plaque (в ответ на список пар строками) — сделаю плашки для указанных матчей\n"
        "Пример: 'Рублёв — Тьен'\n\n"
        "Можно запланировать ежедневную рассылку: /subscribe 22:30"
    )

@dp.message(Command("set"))
async def set_cmd(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Пришлите ссылку на турнир после команды /set")
        return
    url = parts[1].strip()
    set_tournament(message.chat.id, url, title=None)
    await message.reply("Ок! Турнир сохранён. Теперь используйте /today или /subscribe HH:MM.")

@dp.message(Command("subscribe"))
async def subscribe(message: Message):
    parts = message.text.split()
    if len(parts) < 2 or ":" not in parts[1]:
        await message.reply("Укажите время в формате HH:MM, например /subscribe 22:30")
        return
    hh, mm = parts[1].split(":", 1)
    try:
        hh, mm = int(hh), int(mm)
    except ValueError:
        await message.reply("Неверный формат времени.")
        return
    # Один джоб на чат
    job_id = f"daily_{message.chat.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(send_today, CronTrigger(hour=hh, minute=mm), args=[message.chat.id], id=job_id)
    await message.reply(f"Готово! Буду присылать результаты ежедневно в {hh:02d}:{mm:02d} ({TZ}).")


async def send_today(chat_id: int):
    info = get_tournament(chat_id)
    if not info:
        await bot.send_message(chat_id, "Сначала задайте турнир: /set <ссылка>")
        return
    url, saved_title = info
    matches = scrape_tournament(url)
    if not matches:
        await bot.send_message(chat_id, "Не нашёл завершённых матчей сегодня. (Возможно, турнир не идёт или страница изменилась.)")
        return
    # Заголовок
    title = saved_title or (matches[0].tournament or "Турнир") + (", " + matches[0].round_text if matches[0].round_text else "")
    grouped = naive_categorize(matches)
    text = format_message(title, grouped)
    await bot.send_message(chat_id, text)

@dp.message(Command("today"))
async def today(message: Message):
    await send_today(message.chat.id)

@dp.message(Command("plaque"))
async def plaque(message: Message):
    # Пользователь должен отправить список строк с парами ПОСЛЕ команды или в ответ на сообщение
    info = get_tournament(message.chat.id)
    if not info:
        await message.reply("Сначала задайте турнир: /set <ссылка>")
        return
    url, saved_title = info
    matches = scrape_tournament(url)
    if not matches:
        await message.reply("Не нашёл завершённых матчей сегодня.")
        return

    # Соберём строки кандидатов: либо текст после команды, либо реплаем
    raw = message.text.split("\n", 1)
    payload = raw[1] if len(raw) > 1 else (message.reply_to_message.text if message.reply_to_message else "")
    if not payload.strip():
        await message.reply("Пришлите список строк с парами вида: 'Игрок1 — Игрок2' каждая с новой строки (после /plaque или ответом на сообщение)." )
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
        tmp = f"/mnt/data/_plaque_{m.key}.png"
        img.save(tmp)
        await message.answer_photo(photo=FSInputFile(tmp), caption=m.to_line())
        created += 1

    if created == 0:
        await message.answer("Плашки не созданы. Проверьте, что пары написаны так же, как в результатах.")

async def main():
    ensure_token()
    init_db()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
