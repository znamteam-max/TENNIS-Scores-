# api/telegram.py — чистый ASGI без FastAPI
import json
from aiogram.types import Update
from bot.bot import dp, bot  # все ваши хэндлеры уже зарегистрированы в bot/bot.py

async def app(scope, receive, send):
    if scope["type"] != "http":
        await send({"type": "http.response.start", "status": 400, "headers": []})
        await send({"type": "http.response.body", "body": b"Bad scope"})
        return

    if scope["method"] == "GET":
        body = b'{"ok": true}'
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"application/json")]
        })
        await send({"type": "http.response.body", "body": body})
        return

    # POST: читаем тело запроса
    body = b""
    while True:
        event = await receive()
        if event["type"] == "http.request":
            body += event.get("body", b"")
            if not event.get("more_body"):
                break

    try:
        data = json.loads(body.decode("utf-8") or "{}")
        update = Update.model_validate(data)  # pydantic v2
        await dp.feed_update(bot, update)
        resp = b'{"ok": true}'
        code = 200
    except Exception as e:
        resp = ('{"ok": false, "error": "%s"}' % str(e)).encode("utf-8")
        code = 500

    await send({
        "type": "http.response.start",
        "status": code,
        "headers": [(b"content-type", b"application/json")]
    })
    await send({"type": "http.response.body", "body": resp})
