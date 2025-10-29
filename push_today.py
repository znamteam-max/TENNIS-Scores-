import os, asyncio
from aiogram import Bot
from bot.flashscore import scrape_tournament
from bot.modules.formatter import naive_categorize, format_message

async def main():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = int(os.environ["CHAT_ID"])
    url = os.environ["TOURNAMENT_URL"]

    bot = Bot(token)
    matches = scrape_tournament(url)
    if not matches:
        await bot.send_message(chat_id, "Сегодня завершённых матчей не найдено.")
        return

    title = os.environ.get("TITLE_OVERRIDE") or (matches[0].tournament or "Турнир") + (", " + matches[0].round_text if matches[0].round_text else "")
    text = format_message(title, naive_categorize(matches))
    await bot.send_message(chat_id, text, disable_web_page_preview=True)

asyncio.run(main())
