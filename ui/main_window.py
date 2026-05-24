"""主窗口：导航框架与状态栏。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from database.models import PlantState
from gamification.plant_growth import get_current_stage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WordBloom — 艾宾浩斯单词背诵")
        self.resize(960, 680)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- 顶部导航 ---
        nav = QHBoxLayout()
        nav.setContentsMargins(12, 8, 12, 8)
        nav.setSpacing(8)

        self.btn_review = QPushButton("📖 复习")
        self.btn_words = QPushButton("📚 词库")
        self.btn_garden = QPushButton("🌻 花园")
        self.btn_stats = QPushButton("📊 统计")

        for btn in [self.btn_review, self.btn_words, self.btn_garden, self.btn_stats]:
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(_NAV_BTN_STYLE)
            nav.addWidget(btn)

        nav.addStretch()
        root.addLayout(nav)

        # --- 内容区 ---
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # 占位页面，后续替换为实际 widget
        self.review_page = QLabel("复习区域", alignment=Qt.AlignCenter)
        self.words_page = QLabel("词库区域", alignment=Qt.AlignCenter)
        self.garden_page = QLabel("花园区域", alignment=Qt.AlignCenter)
        self.stats_page = QLabel("统计区域", alignment=Qt.AlignCenter)

        self.stack.addWidget(self.review_page)   # index 0
        self.stack.addWidget(self.words_page)    # index 1
        self.stack.addWidget(self.garden_page)   # index 2
        self.stack.addWidget(self.stats_page)    # index 3

        # --- 底部状态栏 ---
        self.status_bar = QHBoxLayout()
        self.status_bar.setContentsMargins(12, 6, 12, 6)
        plant = get_current_stage()
        ps = PlantState.get()
        self.lbl_plant = QLabel(f"🌱 植物: {plant['name']}")
        self.lbl_water = QLabel(f"💧 水滴: {ps.total_water}")
        self.lbl_sunshine = QLabel(f"☀️ 阳光: {ps.total_sunshine}")
        self.lbl_plant.setStyleSheet("font-size: 14px; padding: 4px 12px;")
        self.lbl_water.setStyleSheet("font-size: 14px; padding: 4px 12px;")
        self.lbl_sunshine.setStyleSheet("font-size: 14px; padding: 4px 12px;")
        self.status_bar.addWidget(self.lbl_plant)
        self.status_bar.addWidget(self.lbl_water)
        self.status_bar.addWidget(self.lbl_sunshine)
        self.status_bar.addStretch()
        root.addLayout(self.status_bar)

        # --- 信号连接 ---
        self.btn_review.clicked.connect(lambda: self._switch_page(0))
        self.btn_words.clicked.connect(lambda: self._switch_page(1))
        self.btn_garden.clicked.connect(lambda: self._switch_page(2))
        self.btn_stats.clicked.connect(lambda: self._switch_page(3))

        # 默认选中复习
        self.btn_review.setChecked(True)
        self.stack.setCurrentIndex(0)

    def _switch_page(self, idx: int) -> None:
        for btn in [self.btn_review, self.btn_words, self.btn_garden, self.btn_stats]:
            btn.setChecked(False)
        [self.btn_review, self.btn_words, self.btn_garden, self.btn_stats][idx].setChecked(True)
        self.stack.setCurrentIndex(idx)

    def refresh_status_bar(self) -> None:
        plant = get_current_stage()
        ps = PlantState.get()
        self.lbl_plant.setText(f"{plant['icon']} 植物: {plant['name']}")
        self.lbl_water.setText(f"💧 水滴: {ps.total_water}")
        self.lbl_sunshine.setText(f"☀️ 阳光: {ps.total_sunshine}")

    def set_review_widget(self, widget: QWidget) -> None:
        self.stack.removeWidget(self.review_page)
        self.review_page.deleteLater()
        self.review_page = widget
        self.stack.insertWidget(0, widget)

    def set_words_widget(self, widget: QWidget) -> None:
        self.stack.removeWidget(self.words_page)
        self.words_page.deleteLater()
        self.words_page = widget
        self.stack.insertWidget(1, widget)

    def set_garden_widget(self, widget: QWidget) -> None:
        self.stack.removeWidget(self.garden_page)
        self.garden_page.deleteLater()
        self.garden_page = widget
        self.stack.insertWidget(2, widget)

    def set_stats_widget(self, widget: QWidget) -> None:
        self.stack.removeWidget(self.stats_page)
        self.stats_page.deleteLater()
        self.stats_page = widget
        self.stack.insertWidget(3, widget)


_NAV_BTN_STYLE = """
QPushButton {
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 14px;
    background: #f5f5f5;
}
QPushButton:checked {
    background: #4a90d9;
    color: white;
    border-color: #4a90d9;
}
QPushButton:hover:!checked {
    background: #e8e8e8;
}
"""
