"""单词复习界面：翻转卡片 + 评分按钮 + 新词学习模式。"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from database.models import ReviewRecord, Word
from engine.scheduler import get_due_count, get_new_word_count_today, get_review_queue, NEW_WORDS_PER_DAY
from engine.spaced_repetition import sm2_update
from gamification import reward_system


class ReviewWidget(QWidget):
    # 信号：通知主窗口刷新状态栏
    review_done = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._queue: list[dict] = []
        self._current_idx = 0
        self._is_flipped = False
        self._is_new_word_mode = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # --- 进度标签 ---
        self.lbl_progress = QLabel("加载中...")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        self.lbl_progress.setStyleSheet("font-size: 16px; color: #666; padding: 12px;")
        layout.addWidget(self.lbl_progress)

        # --- 卡片区域 ---
        self.card = _FlipCard()
        layout.addWidget(self.card, 1, Qt.AlignCenter)

        # --- 提示 ---
        self.lbl_hint = QLabel("点击卡片翻转查看释义")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        self.lbl_hint.setStyleSheet("font-size: 12px; color: #999; padding: 4px;")
        layout.addWidget(self.lbl_hint)

        # --- 新词模式：学习按钮 ---
        self.learn_bar = QHBoxLayout()
        self.btn_got_it = QPushButton("已记住，开始评分")
        self.btn_got_it.clicked.connect(self._start_rating)
        self.btn_got_it.setMinimumHeight(40)
        self.btn_got_it.setStyleSheet(_GREEN_BTN)
        self.learn_bar.addStretch()
        self.learn_bar.addWidget(self.btn_got_it)
        self.learn_bar.addStretch()
        self.learn_widget = QWidget()
        self.learn_widget.setLayout(self.learn_bar)
        self.learn_widget.hide()
        layout.addWidget(self.learn_widget)

        # --- 评分按钮栏 ---
        self.rating_bar = QHBoxLayout()
        self.rating_buttons: list[QPushButton] = []
        labels = [
            ("0\n完全忘记", "#d9534f"),
            ("1\n模糊印象", "#f0ad4e"),
            ("2\n勉强想起", "#f0ad4e"),
            ("3\n有困难", "#5bc0de"),
            ("4\n正确犹豫", "#5cb85c"),
            ("5\n完美掌握", "#4cae4c"),
        ]
        for i, (text, color) in enumerate(labels):
            btn = QPushButton(text)
            btn.setMinimumSize(90, 56)
            btn.clicked.connect(lambda checked, q=i: self._rate(q))
            btn.setStyleSheet(_rating_style(color))
            self.rating_buttons.append(btn)
            self.rating_bar.addWidget(btn)

        self.rating_widget = QWidget()
        self.rating_widget.setLayout(self.rating_bar)
        self.rating_widget.hide()
        layout.addWidget(self.rating_widget)

        # --- 空状态 ---
        self.lbl_empty = QLabel("🎉 今日没有需要复习的单词！\n去词库添加新单词，或休息一下~")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet("font-size: 18px; color: #888; padding: 60px;")
        self.lbl_empty.hide()
        layout.addWidget(self.lbl_empty)

        layout.addStretch()

    def load_queue(self) -> None:
        self._queue = get_review_queue()
        self._current_idx = 0
        if not self._queue:
            self._show_empty()
        else:
            self._show_current()

    def _show_empty(self) -> None:
        self.card.hide()
        self.lbl_hint.hide()
        self.learn_widget.hide()
        self.rating_widget.hide()
        self.lbl_empty.show()
        due = get_due_count()
        new_today = get_new_word_count_today()
        self.lbl_progress.setText(
            f"待复习: {due} | 今日新词: {new_today}/{NEW_WORDS_PER_DAY}"
        )

    def _show_current(self) -> None:
        self.lbl_empty.hide()
        self.card.show()
        self.lbl_hint.show()
        self._is_flipped = False

        item = self._queue[self._current_idx]
        word: Word = item["word"]
        is_new = item["is_new"]

        self.card.set_front(word.word)
        self.card.set_back(f"{word.definition}\n\n{word.phonetic}" if word.phonetic else word.definition)
        self.card.show_front()

        due = get_due_count()
        new_today = get_new_word_count_today()
        self.lbl_progress.setText(
            f"第 {self._current_idx + 1}/{len(self._queue)} 个 | "
            f"待复习: {due} | 今日新词: {new_today}/{NEW_WORDS_PER_DAY}"
        )

        if is_new:
            self._is_new_word_mode = True
            self.lbl_hint.setText("新词学习模式：先查看单词和释义，然后点击下方按钮开始评分")
            self.card.show_back()  # 新词直接展示释义
            self._is_flipped = True
            self.rating_widget.hide()
            self.learn_widget.show()
        else:
            self._is_new_word_mode = False
            self.lbl_hint.setText("点击卡片翻转查看释义")
            self.learn_widget.hide()
            self.rating_widget.show()

    def _start_rating(self) -> None:
        self._is_new_word_mode = False
        self.lbl_hint.setText("请给出评分（0-5）")
        self.learn_widget.hide()
        self.rating_widget.show()

    def _rate(self, quality: int) -> None:
        item = self._queue[self._current_idx]
        word: Word = item["word"]
        rec: ReviewRecord | None = item["record"]

        # 更新 SM-2 状态
        if rec is None:
            current_interval = 0
            current_ef = 2.5
            current_reps = 0
        else:
            current_interval = rec.interval
            current_ef = rec.ease_factor
            current_reps = rec.repetitions

        result = sm2_update(quality, current_interval, current_ef, current_reps)

        if rec is None:
            rec = ReviewRecord(word_id=word.id)
        rec.ease_factor = result.ease_factor
        rec.interval = result.interval
        rec.repetitions = result.repetitions
        rec.next_review_date = result.next_review_date
        rec.last_review_date = __import__("datetime").date.today().isoformat()
        rec.last_quality = quality
        rec.save()

        # 发放奖励
        reward_system.record_review(quality, is_new_word=item["is_new"])
        reward_system.apply_daily_sunshine()
        reward_system.apply_water_decay()

        # 下一个
        self._current_idx += 1
        if self._current_idx >= len(self._queue):
            self._queue = []
            self._show_empty()
        else:
            self._show_current()

        self.review_done.emit()


class _FlipCard(QFrame):
    """可翻转的单词卡片。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(340, 220)
        self.setMaximumSize(500, 300)
        self.setStyleSheet(_CARD_STYLE)
        self.setCursor(Qt.PointingHandCursor)

        self._front_text = ""
        self._back_text = ""
        self._showing_front = True

        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("font-size: 28px; padding: 24px; border: none; background: transparent;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.mousePressEvent = self._on_click  # type: ignore

    def set_front(self, text: str) -> None:
        self._front_text = text

    def set_back(self, text: str) -> None:
        self._back_text = text.replace("\n", "<br>")

    def show_front(self) -> None:
        self._showing_front = True
        self.label.setTextFormat(Qt.PlainText)
        self.label.setText(self._front_text)

    def show_back(self) -> None:
        self._showing_front = False
        self.label.setTextFormat(Qt.RichText)
        self.label.setText(self._back_text)

    def _on_click(self, event) -> None:
        if self._showing_front:
            self.show_back()
        else:
            self.show_front()


_CARD_STYLE = """
QFrame {
    background: #ffffff;
    border: 2px solid #d0d0d0;
    border-radius: 16px;
}
QFrame:hover {
    border-color: #4a90d9;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
"""


def _rating_style(color: str) -> str:
    return f"""
    QPushButton {{
        background: white;
        border: 2px solid {color};
        border-radius: 8px;
        font-size: 12px;
        font-weight: bold;
        color: #333;
    }}
    QPushButton:hover {{
        background: {color};
        color: white;
    }}
    """


_GREEN_BTN = """
QPushButton {
    background: #5cb85c;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: bold;
    padding: 8px 32px;
}
QPushButton:hover {
    background: #4cae4c;
}
"""
