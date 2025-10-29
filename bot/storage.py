import sqlite3
from contextlib import contextmanager
from typing import Optional, Tuple, List
from .config import DB_PATH

@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.commit()
        con.close()

def init_db():
    with _conn() as con:
        con.execute("CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, tournament_url TEXT, title TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS overrides (chat_id INTEGER, match_key TEXT, category TEXT, PRIMARY KEY(chat_id, match_key))")

def set_tournament(chat_id: int, tournament_url: str, title: Optional[str] = None):
    with _conn() as con:
        con.execute("REPLACE INTO chats (chat_id, tournament_url, title) VALUES (?, ?, ?)", (chat_id, tournament_url, title))

def get_tournament(chat_id: int) -> Optional[Tuple[str, Optional[str]]]:
    with _conn() as con:
        cur = con.execute("SELECT tournament_url, title FROM chats WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        return (row["tournament_url"], row["title"]) if row else None

def set_override(chat_id: int, match_key: str, category: str):
    with _conn() as con:
        con.execute("REPLACE INTO overrides (chat_id, match_key, category) VALUES (?, ?, ?)", (chat_id, match_key, category))

def get_overrides(chat_id: int) -> List[sqlite3.Row]:
    with _conn() as con:
        cur = con.execute("SELECT match_key, category FROM overrides WHERE chat_id=?", (chat_id,))
        return cur.fetchall()
