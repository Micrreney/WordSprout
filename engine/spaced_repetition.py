"""SM-2 间隔重复算法，初始间隔对齐艾宾浩斯遗忘曲线节点。"""

from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil


@dataclass
class ReviewResult:
    interval: int
    ease_factor: float
    repetitions: int
    next_review_date: str


def sm2_update(
    quality: int,
    current_interval: int = 0,
    current_ef: float = 2.5,
    current_repetitions: int = 0,
) -> ReviewResult:
    """
    quality: 0-5 评分
        5 = 完美掌握
        4 = 正确但犹豫
        3 = 正确但有困难
        2 = 错误但识别后想起
        1 = 错误，看到答案后才想起
        0 = 完全忘记
    """
    q = max(0, min(5, quality))

    if q >= 3:
        # 通过
        if current_repetitions == 0:
            new_interval = 1
        elif current_repetitions == 1:
            new_interval = 2
        elif current_repetitions == 2:
            new_interval = 4
        elif current_repetitions == 3:
            new_interval = 7
        elif current_repetitions == 4:
            new_interval = 15
        else:
            new_interval = ceil(current_interval * current_ef)

        new_ef = current_ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, new_ef)
        new_repetitions = current_repetitions + 1
    else:
        # 未通过，重置
        new_interval = 1
        new_ef = current_ef
        new_repetitions = 1  # 不计为0次，但重新学习

    next_date = (date.today() + timedelta(days=new_interval)).isoformat()

    return ReviewResult(
        interval=new_interval,
        ease_factor=new_ef,
        repetitions=new_repetitions,
        next_review_date=next_date,
    )
