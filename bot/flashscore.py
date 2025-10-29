from __future__ import annotations
import re, time, random
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

@dataclass
class Match:
    key: str                   # стабильный ключ матча (напр., Flashscore event id)
    player1: str
    player2: str
    score_sets: List[Tuple[int,int]]
    finished: bool
    round_text: str = ""
    tournament: str = ""
    country_city: str = ""
    atp_level: str = ""

    @property
    def full_score(self) -> str:
        parts = [f"{a}:{b}" for a,b in self.score_sets]
        return ", ".join(parts)

    @property
    def display_pair(self) -> str:
        return f"{self.player1} — {self.player2}"

    def to_line(self) -> str:
        return f"{self.display_pair} {self.full_score}"

def _extract_sets(score_cell: str) -> List[Tuple[int,int]]:
    # e.g. '6-4 6-3' or '7-6(5) 6-2' -> parse into pairs (6,4),(6,3)
    tokens = re.findall(r"(\d+)[^\d]+(\d+)", score_cell)
    return [(int(a), int(b)) for a,b in tokens]

def _normalize_name(name: str) -> str:
    # Remove seed/ranking markers and extra spaces
    name = re.sub(r"\(\d+\)", "", name)  # (5)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def _event_id(tag) -> Optional[str]:
    # Flashscore wraps matches in tags with data-event-id or id like 'g_1_xxxxx'
    if not tag:
        return None
    for attr in ("data-event-id", "id"):
        if tag.has_attr(attr):
            val = tag[attr]
            m = re.search(r"([a-zA-Z0-9]{8,})", val)
            if m:
                return m.group(1)
    return None

def scrape_tournament(url: str) -> List[Match]:
    """Возвращает список матчей (сыграны/завершены) с турнира Flashscore.
    Поддерживаются как полная так и мобильная версия сайта.
    Разметка у Flashscore меняется — селекторы ниже собраны максимально устойчиво.
    """
    session = requests.Session()
    html = session.get(url, headers=HEADERS, timeout=25).text

    # Если пользователь дал десктопную ссылку, попробуем также мобильную (она проще)
    if "m.flashscore" not in url and "www.flashscore" in url:
        m_url = url.replace("www.flashscore", "m.flashscore")
        try:
            html_m = session.get(m_url, headers=HEADERS, timeout=25).text
            if html_m and len(html_m) > 1000:
                html = html_m
        except Exception:
            pass

    soup = BeautifulSoup(html, "lxml")

    # Попытка вытащить заголовок и стадию
    heading = soup.find("h1")
    tournament = heading.get_text(strip=True) if heading else ""
    round_text = ""
    atp_level = ""
    # в ня некоторых страницах турнир/раунд присутствуют в подзаголовках
    sub = soup.find("div", class_=re.compile("tournament-header|heading|subtitle")) or soup.find("h2")
    if sub:
        round_text = sub.get_text(" ", strip=True)

    matches: List[Match] = []

    # Общий паттерн карточек матчей
    candidates = soup.select('[id^="g_"]') or soup.select(".event__match, .sportName .stage-content .event")
    if not candidates:
        # fallback – для мобильной версии бывают простые списки <a>
        candidates = soup.select("a[href*='/match/']")

    for tag in candidates:
        text = tag.get_text(" ", strip=True)
        # Игроки
        p = soup if tag is None else tag
        p1 = p.find(class_=re.compile("participant|team|p1|home|player1|event__participant--home"))
        p2 = p.find(class_=re.compile("participant|team|p2|away|player2|event__participant--away"))
        if not p1 or not p2:
            # Попытка через сплит текста
            m = re.split(r"\s{2,}|\s—\s| - ", text)
            if len(m) >= 2:
                player1, player2 = m[0], m[1]
            else:
                continue
        else:
            player1 = p1.get_text(strip=True)
            player2 = p2.get_text(strip=True)

        player1 = _normalize_name(player1)
        player2 = _normalize_name(player2)

        # Счёт
        score_node = p.find(class_=re.compile("(score|result|event__scores|tennis)"))
        cell = score_node.get_text(" ", strip=True) if score_node else ""
        score_sets = _extract_sets(cell)

        # Статус
        finished = True if re.search(r"Finished|Завершён|FT|End|Завершен", text, re.I) else False
        # На мобильной версии есть '—' в счёте и флаг завершения отсутствует – проверим по количеству сетов
        if not finished and score_sets and len(score_sets) >= 2:
            finished = True

        key = _event_id(tag) or f"{player1}_{player2}_{cell}"

        matches.append(Match(
            key=key, player1=player1, player2=player2, score_sets=score_sets,
            finished=finished, round_text=round_text, tournament=tournament, atp_level=atp_level
        ))

    # Фильтруем только завершённые и со счётом
    matches = [m for m in matches if m.finished and m.score_sets]
    return matches
