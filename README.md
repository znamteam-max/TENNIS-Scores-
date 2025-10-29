# Telegram-бот: теннис, результаты дня + плашки (Vercel + GitHub Actions)

- Интерактивный бот (команды `/start`, `/set`, `/today`, `/plaque`) — через **Vercel** (вебхук).
- Ежедневная текстовая сводка — через **GitHub Actions** (бесплатно).
- Плашки (Pillow) — в ответ на `/plaque` с парами матчей (по одной в строке).

## Быстрый старт локально (опционально)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # заполните TELEGRAM_TOKEN, TZ
python -m bot.bot      # long polling
```

## Деплой на Vercel (вебхук)
1. Импортируйте репозиторий в Vercel.
2. Переменные окружения проекта:
   - `TELEGRAM_TOKEN` — токен вашего бота;
   - `TZ` — например `Europe/Moscow`.
3. Deploy. Конечная точка вебхука: `https://<project>.vercel.app/api/telegram`.
4. Пропишите вебхук:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<project>.vercel.app/api/telegram
   ```
5. Проверка:
   ```
   https://api.telegram.org/bot<TOKEN>/getWebhookInfo
   ```

## Команды в Telegram
- `/set <url>` — укажите **мобильную** ссылку Flashscore на страницу **Results** турнира:  
  `https://m.flashscorekz.com/tennis/.../results/`
- `/today` — текст «Результаты игрового дня».
- `/plaque` + список пар ниже (или реплаем на сообщение со списком) — получаете плашки.
  Пример:
  ```
  /plaque
  Рублёв — Тьен
  Медведев — Мунар
  ```

## Ежедневная сводка через GitHub Actions
1. В GitHub → Settings → Secrets and variables → Actions добавьте:
   - `TELEGRAM_TOKEN` — токен;
   - `CHAT_ID` — id чата/канала (добавьте бота админом; узнайте id у @userinfobot);
   - `TOURNAMENT_URL` — мобильная страница Results турнира.
2. По умолчанию cron `30 19 * * *` (19:30 UTC). Меняйте в `.github/workflows/daily.yml`.
3. Скрипт: `scripts/push_today.py`. Можно вызвать вручную из вкладки **Actions** (Run workflow).

## Кастомизация плашки
- Фон: `assets/plaque_template.png` (замените на ваш).
- Цвета/шрифты: `bot/config.py`. Можно указать свои TTF через env:
  ```env
  FONT_BOLD=/path/to/Your-Bold.ttf
  FONT_REGULAR=/path/to/Your-Regular.ttf
  ```

## Замечания по Vercel
- Файловая система read-only — бот сохраняет изображения во **временную папку** `/tmp` и сразу отправляет их в Telegram.
- Таймаут выполнения функции ограничен (~10 с). Обычно достаточно.

## Структура
```
api/telegram.py          # вебхук (FastAPI) для Vercel
bot/bot.py               # бот-логика и команды
bot/flashscore.py        # парсер Flashscore
bot/plaque.py            # генерация плашек
bot/modules/formatter.py # категоризация и формат сообщения
assets/plaque_template.png
scripts/push_today.py    # ежедневная рассылка (GitHub Actions)
.github/workflows/daily.yml
requirements.txt
vercel.json
```
