from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Tuple, List
from .config import PLAQUE_TEMPLATE, PRIMARY_HEX, ACCENT_HEX, TEXT_HEX, SEMI_ALPHA, FONT_BOLD, FONT_REGULAR

def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size, layout_engine=ImageFont.LAYOUT_RAQM)
    except Exception:
        return ImageFont.truetype(FONT_REGULAR, size=size)

def _draw_centered_text(draw: ImageDraw.ImageDraw, box: Tuple[int,int,int,int], text: str, font: ImageFont.ImageFont, fill: str):
    w = draw.textlength(text, font=font)
    x0, y0, x1, y1 = box
    x = x0 + (x1-x0 - w)//2
    y = y0 + (y1-y0 - font.size)//2 - 5
    draw.text((x,y), text, font=font, fill=fill)

def render_plaque(player1: str, player2: str, sets: List[Tuple[int,int]], tournament_line: str="") -> Image.Image:
    base = Image.open(PLAQUE_TEMPLATE).convert("RGBA")
    W, H = base.size

    # Полупрозрачная подложка внизу
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    bottom_h = int(H*0.20)
    draw.rectangle((int(W*0.03), H-bottom_h-10, W-int(W*0.03), H-20), fill=(20, 16, 38, SEMI_ALPHA), outline=None)

    # Текст слева: имена
    f_title = _load_font(FONT_BOLD, size=int(H*0.055))
    f_sub = _load_font(FONT_REGULAR, size=int(H*0.03))

    left_x = int(W*0.07)
    top_y = H - bottom_h
    draw.text((left_x, top_y+10), player1.upper(), font=f_title, fill=ACCENT_HEX)
    draw.text((left_x, top_y+10 + int(H*0.07)), player2.upper(), font=f_title, fill=TEXT_HEX)

    # Турнир/круг
    if tournament_line:
        draw.text((left_x, top_y - int(H*0.045)), tournament_line, font=f_sub, fill=TEXT_HEX)

    # Счёт справа двум строкам
    f_score_big = _load_font(FONT_BOLD, size=int(H*0.09))
    f_score_small = _load_font(FONT_BOLD, size=int(H*0.06))

    # суммарный счёт по сетам (кто выиграл больше сетов)
    sets_w1 = sum([1 for a,b in sets if a>b])
    sets_w2 = sum([1 for a,b in sets if b>a])
    right_x = W - int(W*0.12)
    y1 = top_y + 10
    y2 = y1 + int(H*0.09) + 8

    _draw_centered_text(draw, (right_x-40, y1, right_x+40, y1+int(H*0.09)), str(sets_w1), f_score_big, TEXT_HEX)
    _draw_centered_text(draw, (right_x-40, y2, right_x+40, y2+int(H*0.09)), str(sets_w2), f_score_big, TEXT_HEX)

    # Таблица сетов
    grid_x = right_x + int(W*0.055)
    grid_w = int(W*0.20)
    cell_w = grid_w // max(3, len(sets))
    # Вертикальные линии
    for i in range(len(sets)+1):
        x = grid_x + i*cell_w
        draw.line((x, y1-5, x, y2+int(H*0.09)), fill=ACCENT_HEX, width=2)
    # Горизонтальные
    draw.line((grid_x, y1+int(H*0.09), grid_x+cell_w*len(sets), y1+int(H*0.09)), fill=ACCENT_HEX, width=2)

    # Цифры сетов
    for i, (a,b) in enumerate(sets):
        cx = grid_x + i*cell_w + cell_w//2
        # Верхняя строка – player1
        _draw_centered_text(draw, (cx-30, y1, cx+30, y1+int(H*0.09)), str(a), f_score_small, TEXT_HEX)
        # Нижняя строка – player2
        _draw_centered_text(draw, (cx-30, y2, cx+30, y2+int(H*0.09)), str(b), f_score_small, TEXT_HEX)

    result = Image.alpha_composite(base, overlay)
    return result
