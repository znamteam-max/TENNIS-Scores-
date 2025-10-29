# api/telegram.py — Vercel serverless (ASGI/FastAPI)
import os
from fastapi import FastAPI, Request
from aiogram.types import Update
from bot.bot import dp, bot  # импортирует готовые хэндлеры

app = FastAPI()

@app.get("/")
async def health():
    return {"ok": True}

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
