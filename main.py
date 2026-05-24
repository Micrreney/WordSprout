"""WordBloom — 基于艾宾浩斯记忆曲线的单词背诵软件。"""

import sys

from PyQt5.QtWidgets import QApplication

from database import init_db
from ui.main_window import MainWindow
from ui.review_widget import ReviewWidget
from ui.word_list_widget import WordListWidget
from ui.garden_widget import GardenWidget
from ui.progress_widget import ProgressWidget
from gamification import reward_system, plant_growth


def main() -> None:
    init_db()

    # 每日水滴衰减
    reward_system.apply_water_decay()
    plant_growth.update_stage()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 全局样式
    app.setStyleSheet("""
        QMainWindow {
            background: #fafafa;
        }
        QLabel {
            color: #333;
        }
    """)

    window = MainWindow()

    # 创建实际页面
    review_widget = ReviewWidget()
    review_widget.review_done.connect(window.refresh_status_bar)

    words_widget = WordListWidget()
    garden_widget = GardenWidget()
    progress_widget = ProgressWidget()

    # 替换占位页面
    window.set_review_widget(review_widget)
    window.set_words_widget(words_widget)
    window.set_garden_widget(garden_widget)
    window.set_stats_widget(progress_widget)

    # 初始加载复习队列
    review_widget.load_queue()
    window.refresh_status_bar()

    # 切换到词库页面时刷新花园和统计
    def on_page_changed(idx: int) -> None:
        if idx == 2:  # 花园
            garden_widget.refresh()
            window.refresh_status_bar()
        elif idx == 3:  # 统计
            progress_widget.refresh()
        elif idx == 0:  # 复习
            review_widget.load_queue()

    window.stack.currentChanged.connect(on_page_changed)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
