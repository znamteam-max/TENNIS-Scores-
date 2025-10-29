# api/telegram.py
# Vercel запускает этот FastAPI-эндпоинт как /api/telegram
import os
from fastapi import FastAPI, Request
from aiogram.types import Update
from bot.bot import dp, bot   # тут уже подключены все ваши хэндлеры и фильтры

app = FastAPI()

@app.get("/")
async def health():
    return {"ok": True}

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)  # aiogram v3 + pydantic v2
    await dp.feed_update(bot, update)     # отдать апдейт вашему Dispatcher’у
    return {"ok": True}
