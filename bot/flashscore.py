from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple, Optional
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

@dataclass
class Match:
    key: str
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
        return ", ".join([f"{a}:{b}" for a,b in self.score_sets])

    @property
    def display_pair(self) -> str:
        return f"{self.player1} — {self.player2}"

    def to_line(self) -> str:
        return f"{self.display_pair} {self.full_score}"

def _extract_sets(score_cell: str) -> List[Tuple[int,int]]:
    tokens = re.findall(r"(\d+)[^\d]+(\d+)", score_cell)
    return [(int(a), int(b)) for a,b in tokens]

def _normalize_name(name: str) -> str:
    name = re.sub(r"\(\d+\)", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def _event_id(tag) -> Optional[str]:
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
    session = requests.Session()
    html = session.get(url, headers=HEADERS, timeout=25).text

    if "m.flashscore" not in url and "www.flashscore" in url:
        m_url = url.replace("www.flashscore", "m.flashscore")
        try:
            html_m = session.get(m_url, headers=HEADERS, timeout=25).text
            if html_m and len(html_m) > 1000:
                html = html_m
        except Exception:
            pass

    soup = BeautifulSoup(html, "lxml")

    heading = soup.find("h1")
    tournament = heading.get_text(strip=True) if heading else ""
    round_text = ""
    sub = soup.find("div", class_=re.compile("tournament-header|heading|subtitle")) or soup.find("h2")
    if sub:
        round_text = sub.get_text(" ", strip=True)

    matches: List[Match] = []
    candidates = soup.select('[id^="g_"]') or soup.select(".event__match, .sportName .stage-content .event")
    if not candidates:
        candidates = soup.select("a[href*='/match/']")

    for tag in candidates:
        p = soup if tag is None else tag
        p1 = p.find(class_=re.compile("participant|team|p1|home|player1|event__participant--home"))
        p2 = p.find(class_=re.compile("participant|team|p2|away|player2|event__participant--away"))
        if not p1 or not p2:
            text = tag.get_text(" ", strip=True)
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

        score_node = p.find(class_=re.compile("(score|result|event__scores|tennis)"))
        cell = score_node.get_text(" ", strip=True) if score_node else ""
        score_sets = _extract_sets(cell)

        finished = True if re.search(r"Finished|Заверш[её]н|FT|End", tag.get_text(" ", strip=True), re.I) else False
        if not finished and score_sets and len(score_sets) >= 2:
            finished = True

        key = _event_id(tag) or f"{player1}_{player2}_{cell}"

        matches.append(Match(
            key=key, player1=player1, player2=player2, score_sets=score_sets,
            finished=finished, round_text=round_text, tournament=tournament
        ))

    matches = [m for m in matches if m.finished and m.score_sets]
    return matches
