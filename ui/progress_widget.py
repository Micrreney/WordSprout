"""学习进度统计与数据可视化。"""

from datetime import date, timedelta

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

import matplotlib
import matplotlib.font_manager as fm

# 使用系统可用的中文字体
_cjk_fonts = [f.name for f in fm.fontManager.ttflist
              if any(k in f.name for k in ("Microsoft YaHei", "SimHei", "Noto Sans CJK", "WenQuanYi"))]
if _cjk_fonts:
    matplotlib.rcParams["font.family"] = _cjk_fonts[0]
matplotlib.rcParams["axes.unicode_minus"] = False

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from database.models import DailyReward, ReviewRecord


class ProgressWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("📊 学习统计")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 12px;")
        layout.addWidget(title)

        # 概览卡片
        overview = QHBoxLayout()
        self.lbl_total = _stat_card()
        self.lbl_learned = _stat_card()
        self.lbl_mastered = _stat_card()
        self.lbl_streak = _stat_card()
        overview.addWidget(self.lbl_total)
        overview.addWidget(self.lbl_learned)
        overview.addWidget(self.lbl_mastered)
        overview.addWidget(self.lbl_streak)
        layout.addLayout(overview)

        # Matplotlib 图表
        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas, 1)

        self.refresh()

    def refresh(self) -> None:
        # 更新概览
        total = ReviewRecord.count_due_today() + ReviewRecord.count_learned()
        learned = ReviewRecord.count_learned()
        mastered = ReviewRecord.count_mastered()
        streak = DailyReward.get_streak()

        self.lbl_total.setText(f"📖 总单词\n{total}")
        self.lbl_learned.setText(f"🧠 已学习\n{learned}")
        self.lbl_mastered.setText(f"✅ 已掌握\n{mastered}")
        self.lbl_streak.setText(f"🔥 连续打卡\n{streak} 天")

        # 绘制图表
        self.figure.clear()

        # 左图：近30天复习柱状图
        ax1 = self.figure.add_subplot(1, 2, 1)
        self._plot_monthly_reviews(ax1)

        # 右图：掌握度分布
        ax2 = self.figure.add_subplot(1, 2, 2)
        self._plot_mastery_distribution(ax2)

        self.figure.tight_layout(pad=3)
        self.canvas.draw()

    def _plot_monthly_reviews(self, ax) -> None:
        end = date.today()
        start = end - timedelta(days=29)
        stats = ReviewRecord.get_reviews_between(start.isoformat(), end.isoformat())

        data = {}
        for s in stats:
            data[s["date"]] = s["count"]

        dates = []
        counts = []
        d = start
        while d <= end:
            ds = d.isoformat()
            dates.append(d.strftime("%m/%d"))
            counts.append(data.get(ds, 0))
            d += timedelta(days=1)

        ax.bar(dates, counts, color="#4a90d9", width=0.7)
        ax.set_title("近30天复习统计", fontsize=12)
        ax.set_xlabel("日期")
        ax.set_ylabel("复习单词数")
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    def _plot_mastery_distribution(self, ax) -> None:
        """按间隔区间统计掌握度分布。"""
        conn = __import__("database.connection", fromlist=["get_connection"]).get_connection()
        rows = conn.execute(
            "SELECT interval FROM review_records WHERE interval > 0"
        ).fetchall()
        conn.close()

        intervals = [r["interval"] for r in rows]
        bins = [0, 1, 3, 7, 14, 30, 60, 120]
        labels = ["1天", "2-3天", "4-7天", "8-14天", "15-30天", "31-60天", "61-120天", "120天+"]
        groups = [0] * len(labels)
        for iv in intervals:
            for i in range(len(bins)):
                if i == len(bins) - 1:
                    if iv >= bins[i]:
                        groups[i] += 1
                    break
                if bins[i] <= iv < bins[i + 1]:
                    groups[i] += 1
                    break

        colors = ["#d9534f", "#f0ad4e", "#f0ad4e", "#5bc0de", "#5cb85c", "#4cae4c", "#2d8b2d", "#1a5c1a"]
        ax.barh(labels, groups, color=colors)
        ax.set_title("复习间隔分布", fontsize=12)
        ax.set_xlabel("单词数")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


def _stat_card() -> QLabel:
    label = QLabel("--")
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("""
        QLabel {
            font-size: 15px;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
        }
    """)
    return label
