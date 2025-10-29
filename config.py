import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TZ = os.getenv("TZ", "Europe/Moscow")

DB_PATH = os.getenv("DB_PATH", "bot.db")

# Цвета и шрифты для плашки
PRIMARY_HEX = "#141026"       # фон (тёмно-фиолетовый)
ACCENT_HEX  = "#D9FF3B"       # лаймовый акцент
TEXT_HEX    = "#FFFFFF"       # основной текст
SEMI_ALPHA  = 180             # прозрачность подложки (0..255)

# Файлы ассетов
PLAQUE_TEMPLATE = os.getenv("PLAQUE_TEMPLATE", "assets/plaque_template.png")
FONT_BOLD = os.getenv("FONT_BOLD", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_REGULAR = os.getenv("FONT_REGULAR", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
