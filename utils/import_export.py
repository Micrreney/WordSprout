"""CSV / JSON 导入导出工具。"""

import csv
import json
import os

from database.models import Word


def export_words_csv(list_id: int, filepath: str) -> int:
    """导出指定列表的单词到 CSV 文件，返回导出数量。"""
    words = Word.get_by_list(list_id)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "definition", "phonetic"])
        for w in words:
            writer.writerow([w.word, w.definition, w.phonetic])
    return len(words)


def import_words_csv(list_id: int, filepath: str) -> int:
    """从 CSV 文件导入单词到指定列表，返回导入数量。"""
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("word", "").strip()
            if not word:
                continue
            w = Word(
                list_id=list_id,
                word=word,
                definition=row.get("definition", "").strip(),
                phonetic=row.get("phonetic", "").strip(),
            )
            w.save()
            count += 1
    return count


def export_words_json(list_id: int, filepath: str) -> int:
    """导出指定列表的单词到 JSON 文件，返回导出数量。"""
    words = Word.get_by_list(list_id)
    data = [
        {"word": w.word, "definition": w.definition, "phonetic": w.phonetic}
        for w in words
    ]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(words)


def import_words_json(list_id: int, filepath: str) -> int:
    """从 JSON 文件导入单词到指定列表，返回导入数量。"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for item in data:
        word = item.get("word", "").strip()
        if not word:
            continue
        w = Word(
            list_id=list_id,
            word=word,
            definition=item.get("definition", "").strip(),
            phonetic=item.get("phonetic", "").strip(),
        )
        w.save()
        count += 1
    return count
