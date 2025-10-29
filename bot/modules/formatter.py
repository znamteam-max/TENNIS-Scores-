from typing import List, Dict
from dataclasses import dataclass
from rapidfuzz import fuzz, process

from .flashscore import Match

@dataclass
class Grouped:
    sensations: List[Match]
    expected: List[Match]
    fifty: List[Match]

def naive_categorize(matches: List[Match]) -> Grouped:
    """Хайуристика: если суммарный счёт по сетам 2:0 и фаворит победил — 'ожидаемо'.
    Если выиграл тот, у кого меньше геймов по сетам/или 3 сета при близком счёте — '50/50'.
    Если явный апсет (например, проиграл в сухую тот, у кого больше геймов в сетах), — 'сенсация'.
    Упрощённо, без коэффициентов. Категории можно переопределять вручную командой /setcat.
    """
    sens, exp, fifty = [], [], []
    for m in matches:
        w1 = sum(1 for a,b in m.score_sets if a>b)
        w2 = sum(1 for a,b in m.score_sets if b>a)
        total_a = sum(a for a,b in m.score_sets)
        total_b = sum(b for a,b in m.score_sets)
        # очень грубо
        if (w1==0 or w2==0) and abs(total_a - total_b) >= 6:
            sens.append(m)
        elif abs(total_a-total_b) <= 2 or (w1==w2):
            fifty.append(m)
        else:
            exp.append(m)
    return Grouped(sensations=sens, expected=exp, fifty=fifty)

def format_message(title: str, grouped: Grouped) -> str:
    lines = ["📊 Результаты игрового дня", "", f"🙋🏼‍♂️ {title}", ""]
    if grouped.sensations:
        lines.append("🤯 Сенсации")
        lines.append("")
        for m in grouped.sensations:
            lines.append(m.to_line())
        lines.append("")
    if grouped.expected:
        lines.append("👌🏼 Ожидаемо")
        lines.append("")
        for m in grouped.expected:
            lines.append(m.to_line())
        lines.append("")
    if grouped.fifty:
        lines.append("🟰 Когда шансы 50/50")
        lines.append("")
        for m in grouped.fifty:
            lines.append(m.to_line())
        lines.append("")
    return "\n".join(lines).strip()

def match_lookup(query: str, matches: List[Match]):
    """Возвращает лучшую пару по строке типа 'Рублёв — Тьен' или 'Rublev - Thiem'"""
    # нормализуем дефисы
    q = query.replace("—", "-").replace("–", "-")
    parts = [p.strip() for p in q.split("-") if p.strip()]
    if len(parts) < 2:
        return None
    a, b = parts[0].lower(), parts[1].lower()
    best = None
    best_score = -1
    for m in matches:
        cand1 = f"{m.player1.lower()} {m.player2.lower()}"
        cand2 = f"{m.player2.lower()} {m.player1.lower()}"
        s = max(fuzz.token_set_ratio(a+" "+b, cand1), fuzz.token_set_ratio(a+" "+b, cand2))
        if s > best_score:
            best_score, best = s, m
    return best if best_score >= 70 else None
