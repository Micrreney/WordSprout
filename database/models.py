from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from .connection import get_connection


@dataclass
class WordList:
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[str] = None

    def save(self) -> None:
        conn = get_connection()
        if self.id is None:
            cur = conn.execute(
                "INSERT INTO word_lists (name) VALUES (?)", (self.name,)
            )
            self.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE word_lists SET name = ? WHERE id = ?", (self.name, self.id)
            )
        conn.commit()
        conn.close()

    def delete(self) -> None:
        if self.id is None:
            return
        conn = get_connection()
        conn.execute("DELETE FROM word_lists WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all() -> list[WordList]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, name, created_at FROM word_lists ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [WordList(id=r["id"], name=r["name"], created_at=r["created_at"]) for r in rows]

    @staticmethod
    def get_by_id(list_id: int) -> Optional[WordList]:
        conn = get_connection()
        row = conn.execute(
            "SELECT id, name, created_at FROM word_lists WHERE id = ?", (list_id,)
        ).fetchone()
        conn.close()
        if row:
            return WordList(id=row["id"], name=row["name"], created_at=row["created_at"])
        return None


@dataclass
class Word:
    id: Optional[int] = None
    list_id: int = 0
    word: str = ""
    definition: str = ""
    phonetic: str = ""
    created_at: Optional[str] = None

    def save(self) -> None:
        conn = get_connection()
        if self.id is None:
            cur = conn.execute(
                "INSERT INTO words (list_id, word, definition, phonetic) VALUES (?, ?, ?, ?)",
                (self.list_id, self.word, self.definition, self.phonetic),
            )
            self.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE words SET list_id=?, word=?, definition=?, phonetic=? WHERE id=?",
                (self.list_id, self.word, self.definition, self.phonetic, self.id),
            )
        conn.commit()
        conn.close()

    def delete(self) -> None:
        if self.id is None:
            return
        conn = get_connection()
        conn.execute("DELETE FROM words WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_list(list_id: int, search: str = "") -> list[Word]:
        conn = get_connection()
        if search:
            rows = conn.execute(
                "SELECT * FROM words WHERE list_id=? AND (word LIKE ? OR definition LIKE ?) ORDER BY created_at DESC",
                (list_id, f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM words WHERE list_id=? ORDER BY created_at DESC", (list_id,)
            ).fetchall()
        conn.close()
        return [_row_to_word(r) for r in rows]

    @staticmethod
    def get_by_id(word_id: int) -> Optional[Word]:
        conn = get_connection()
        row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        conn.close()
        return _row_to_word(row) if row else None

    @staticmethod
    def count_by_list(list_id: int) -> int:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM words WHERE list_id=?", (list_id,)
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0


def _row_to_word(row) -> Word:
    return Word(
        id=row["id"],
        list_id=row["list_id"],
        word=row["word"],
        definition=row["definition"],
        phonetic=row["phonetic"],
        created_at=row["created_at"],
    )


@dataclass
class ReviewRecord:
    id: Optional[int] = None
    word_id: int = 0
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0
    next_review_date: Optional[str] = None
    last_review_date: Optional[str] = None
    last_quality: Optional[int] = None

    def save(self) -> None:
        conn = get_connection()
        if self.id is None:
            cur = conn.execute(
                """INSERT INTO review_records (word_id, ease_factor, interval, repetitions,
                   next_review_date, last_review_date, last_quality)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.word_id, self.ease_factor, self.interval, self.repetitions,
                    self.next_review_date, self.last_review_date, self.last_quality,
                ),
            )
            self.id = cur.lastrowid
        else:
            conn.execute(
                """UPDATE review_records SET ease_factor=?, interval=?, repetitions=?,
                   next_review_date=?, last_review_date=?, last_quality=? WHERE id=?""",
                (
                    self.ease_factor, self.interval, self.repetitions,
                    self.next_review_date, self.last_review_date, self.last_quality, self.id,
                ),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_word(word_id: int) -> Optional[ReviewRecord]:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM review_records WHERE word_id = ?", (word_id,)
        ).fetchone()
        conn.close()
        if row:
            return ReviewRecord(
                id=row["id"], word_id=row["word_id"], ease_factor=row["ease_factor"],
                interval=row["interval"], repetitions=row["repetitions"],
                next_review_date=row["next_review_date"], last_review_date=row["last_review_date"],
                last_quality=row["last_quality"],
            )
        return None

    @staticmethod
    def get_due_reviews(limit: int = 999) -> list[ReviewRecord]:
        """返回 next_review_date <= today 的复习记录，按逾期天数降序"""
        conn = get_connection()
        rows = conn.execute(
            """SELECT r.* FROM review_records r
               WHERE r.next_review_date <= date('now')
               ORDER BY r.next_review_date ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        return [
            ReviewRecord(
                id=r["id"], word_id=r["word_id"], ease_factor=r["ease_factor"],
                interval=r["interval"], repetitions=r["repetitions"],
                next_review_date=r["next_review_date"], last_review_date=r["last_review_date"],
                last_quality=r["last_quality"],
            )
            for r in rows
        ]

    @staticmethod
    def count_due_today() -> int:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM review_records WHERE next_review_date <= date('now')"
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    @staticmethod
    def count_learned() -> int:
        """已学过（有复习记录且 interval > 0）的单词数"""
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM review_records WHERE interval > 0"
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    @staticmethod
    def count_mastered() -> int:
        """已掌握（interval >= 21 天）的单词数"""
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM review_records WHERE interval >= 21"
        ).fetchone()
        conn.close()
        return row["cnt"] if row else 0

    @staticmethod
    def get_reviews_between(start_date: str, end_date: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """SELECT last_review_date, COUNT(*) as cnt FROM review_records
               WHERE last_review_date BETWEEN ? AND ?
               GROUP BY last_review_date ORDER BY last_review_date""",
            (start_date, end_date),
        ).fetchall()
        conn.close()
        return [{"date": r["last_review_date"], "count": r["cnt"]} for r in rows]


@dataclass
class DailyReward:
    date: str = ""
    words_reviewed: int = 0
    water_drops: int = 0
    sunshine: int = 0
    streak_days: int = 0

    def save(self) -> None:
        conn = get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO daily_rewards (date, words_reviewed, water_drops, sunshine, streak_days)
               VALUES (?, ?, ?, ?, ?)""",
            (self.date, self.words_reviewed, self.water_drops, self.sunshine, self.streak_days),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_date(d: str) -> Optional[DailyReward]:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM daily_rewards WHERE date = ?", (d,)
        ).fetchone()
        conn.close()
        if row:
            return DailyReward(
                date=row["date"], words_reviewed=row["words_reviewed"],
                water_drops=row["water_drops"], sunshine=row["sunshine"],
                streak_days=row["streak_days"],
            )
        return None

    @staticmethod
    def get_today() -> Optional[DailyReward]:
        today = date.today().isoformat()
        return DailyReward.get_by_date(today)

    @staticmethod
    def get_yesterday_streak() -> int:
        yesterday = date.today().replace(day=date.today().day - 1).isoformat() if date.today().day > 1 else ""
        conn = get_connection()
        row = conn.execute(
            "SELECT streak_days FROM daily_rewards WHERE date = ?", (yesterday,)
        ).fetchone()
        conn.close()
        return row["streak_days"] if row else 0

    @staticmethod
    def get_streak() -> int:
        """计算当前连续打卡天数（向前追溯到第一个缺失的日期）"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT date FROM daily_rewards WHERE words_reviewed > 0 ORDER BY date DESC LIMIT 365"
        ).fetchall()
        conn.close()
        if not rows:
            return 0
        streak = 0
        expected = date.today()
        for r in rows:
            rd = date.fromisoformat(r["date"])
            if rd == expected:
                streak += 1
                expected = expected.replace(day=expected.day - 1) if expected.day > 1 else expected
            elif rd == expected.replace(day=expected.day - 1) if expected.day > 1 else expected:
                # 允许1天间隔
                streak += 1
                expected = rd.replace(day=rd.day - 1) if rd.day > 1 else rd
            else:
                break
        return streak

    @staticmethod
    def get_monthly_stats(year: int, month: int) -> list[dict]:
        start = f"{year}-{month:02d}-01"
        if month == 12:
            end = f"{year}-12-31"
        else:
            end = f"{year}-{month+1:02d}-01"
        conn = get_connection()
        rows = conn.execute(
            """SELECT date, words_reviewed, water_drops, sunshine FROM daily_rewards
               WHERE date >= ? AND date < ? ORDER BY date""",
            (start, end),
        ).fetchall()
        conn.close()
        return [{"date": r["date"], "words_reviewed": r["words_reviewed"],
                 "water_drops": r["water_drops"], "sunshine": r["sunshine"]} for r in rows]


@dataclass
class PlantState:
    id: int = 1
    stage: int = 0
    total_water: int = 0
    total_sunshine: int = 0
    plant_type: str = "default"
    last_water_decay_date: str = ""

    def save(self) -> None:
        conn = get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO plant_state (id, stage, total_water, total_sunshine, plant_type, last_water_decay_date)
               VALUES (1, ?, ?, ?, ?, ?)""",
            (self.stage, self.total_water, self.total_sunshine, self.plant_type, self.last_water_decay_date),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get() -> PlantState:
        conn = get_connection()
        row = conn.execute("SELECT * FROM plant_state WHERE id = 1").fetchone()
        conn.close()
        if row:
            return PlantState(
                id=1, stage=row["stage"], total_water=row["total_water"],
                total_sunshine=row["total_sunshine"], plant_type=row["plant_type"],
                last_water_decay_date=row["last_water_decay_date"] or "",
            )
        return PlantState()
