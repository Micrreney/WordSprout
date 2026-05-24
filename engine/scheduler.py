"""每日复习调度管理：获取今日待复习单词、新词分配。"""

from datetime import date
from typing import Optional

from database.models import Word, ReviewRecord


NEW_WORDS_PER_DAY = 10


def get_due_words(limit: int = 999) -> list[tuple[ReviewRecord, Word]]:
    """获取今日待复习单词列表，按逾期天数降序排列。"""
    records = ReviewRecord.get_due_reviews(limit)
    result = []
    for rec in records:
        word = Word.get_by_id(rec.word_id)
        if word:
            result.append((rec, word))
    return result


def get_due_count() -> int:
    return ReviewRecord.count_due_today()


def get_new_word_count_today() -> int:
    """今天已经学了多少新词（interval=1 表示第一次学完）。"""
    conn = __import__("database.connection", fromlist=["get_connection"]).get_connection()
    row = conn.execute(
        """SELECT COUNT(*) as cnt FROM review_records
           WHERE repetitions = 1 AND last_review_date = date('now')"""
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_new_words_available(list_id: Optional[int] = None, limit: int = NEW_WORDS_PER_DAY) -> list[Word]:
    """获取可学习的新词（还没有复习记录的单词）。"""
    already = get_new_word_count_today()
    remaining = max(0, limit - already)
    if remaining == 0:
        return []

    conn = __import__("database.connection", fromlist=["get_connection"]).get_connection()
    query = """SELECT w.* FROM words w
               LEFT JOIN review_records r ON w.id = r.word_id
               WHERE r.id IS NULL"""
    params: tuple = ()
    if list_id is not None:
        query += " AND w.list_id = ?"
        params = (list_id,)
    query += " ORDER BY w.created_at ASC LIMIT ?"
    params = params + (remaining,)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [
        Word(
            id=r["id"], list_id=r["list_id"], word=r["word"],
            definition=r["definition"], phonetic=r["phonetic"], created_at=r["created_at"],
        )
        for r in rows
    ]


def get_review_queue() -> list[dict]:
    """返回今天完整的复习队列：复习词 + 新词。"""
    result = []

    due = get_due_words()
    for rec, word in due:
        result.append({
            "word": word,
            "record": rec,
            "is_new": False,
        })

    new_words = get_new_words_available()
    for word in new_words:
        result.append({
            "word": word,
            "record": None,
            "is_new": True,
        })

    return result
