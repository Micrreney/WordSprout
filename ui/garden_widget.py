"""植物花园可视化：QPainter 绘制各阶段植物 + 水滴/阳光进度条。"""

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
from PyQt5.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from database.models import PlantState
from gamification import plant_growth


class GardenWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # 标题
        title = QLabel("🌻 我的花园")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 16px;")
        layout.addWidget(title)

        # 植物绘制区
        self.canvas = _PlantCanvas()
        layout.addWidget(self.canvas, 1)

        # 信息区
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        self.lbl_stage = QLabel("")
        self.lbl_stage.setAlignment(Qt.AlignCenter)
        self.lbl_stage.setStyleSheet("font-size: 18px; font-weight: bold; padding: 4px;")
        info_layout.addWidget(self.lbl_stage)

        # 水滴进度
        water_row = QVBoxLayout()
        water_label = QLabel("💧 水滴")
        water_label.setStyleSheet("font-size: 13px;")
        water_row.addWidget(water_label)
        self.water_bar = QProgressBar()
        self.water_bar.setStyleSheet(_PROGRESS_BLUE)
        self.water_bar.setTextVisible(True)
        water_row.addWidget(self.water_bar)
        info_layout.addLayout(water_row)

        # 阳光进度
        sun_row = QVBoxLayout()
        sun_label = QLabel("☀️ 阳光")
        sun_label.setStyleSheet("font-size: 13px;")
        sun_row.addWidget(sun_label)
        self.sun_bar = QProgressBar()
        self.sun_bar.setStyleSheet(_PROGRESS_GOLD)
        self.sun_bar.setTextVisible(True)
        sun_row.addWidget(self.sun_bar)
        info_layout.addLayout(sun_row)

        layout.addLayout(info_layout)

        self.refresh()

    def refresh(self) -> None:
        plant_growth.update_stage()
        current = plant_growth.get_current_stage()
        next_info = plant_growth.get_next_stage_info()
        ps = PlantState.get()

        self.lbl_stage.setText(f"阶段 {current['index'] + 1}: {current['icon']} {current['name']}")

        if next_info.get("is_max"):
            self.water_bar.setMaximum(1)
            self.water_bar.setValue(1)
            self.water_bar.setFormat("已满级")
            self.sun_bar.setMaximum(1)
            self.sun_bar.setValue(1)
            self.sun_bar.setFormat("已满级")
        else:
            self.water_bar.setMaximum(next_info["water_total"])
            self.water_bar.setValue(next_info["current_water"])
            self.water_bar.setFormat(
                f"{next_info['current_water']}/{next_info['water_total']} "
                f"(还需 {next_info['water_needed']})"
            )
            self.sun_bar.setMaximum(max(next_info["sunshine_total"], 1))
            self.sun_bar.setValue(next_info["current_sunshine"])
            self.sun_bar.setFormat(
                f"{next_info['current_sunshine']}/{next_info['sunshine_total']} "
                f"(还需 {next_info['sunshine_needed']})"
            )

        self.canvas.set_stage(current["index"])
        self.canvas.update()


_PROGRESS_BLUE = """
QProgressBar {
    border: 1px solid #b0c4de;
    border-radius: 6px;
    text-align: center;
    height: 22px;
    min-width: 300px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a90d9, stop:1 #7ab8f5);
    border-radius: 5px;
}
"""

_PROGRESS_GOLD = """
QProgressBar {
    border: 1px solid #daa520;
    border-radius: 6px;
    text-align: center;
    height: 22px;
    min-width: 300px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f0ad4e, stop:1 #ffd700);
    border-radius: 5px;
}
"""


class _PlantCanvas(QWidget):
    """用 QPainter 绘制不同阶段的植物。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(300, 280)
        self._stage = 0

    def set_stage(self, stage: int) -> None:
        self._stage = stage

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f0f8e8"))

        w = self.width()
        h = self.height()
        cx = w // 2
        base_y = h - 40

        stage = self._stage

        # 花盆
        painter.setPen(QPen(QColor("#8B4513"), 2))
        painter.setBrush(QBrush(QColor("#CD853F")))
        pot_w, pot_h = 70, 60
        painter.drawRect(int(cx - pot_w / 2), base_y - pot_h, pot_w, pot_h)

        # 土壤
        painter.setBrush(QBrush(QColor("#654321")))
        painter.drawRect(int(cx - pot_w / 2), base_y - pot_h, pot_w, 12)

        if stage >= 1:  # 发芽
            painter.setPen(QPen(QColor("#228B22"), 4))
            painter.drawLine(cx, base_y - pot_h, cx, base_y - pot_h - 30)
            painter.setPen(QPen(QColor("#32CD32"), 3))
            painter.drawLine(cx, base_y - pot_h - 15, cx + 15, base_y - pot_h - 30)
            painter.drawLine(cx, base_y - pot_h - 20, cx - 12, base_y - pot_h - 36)

        if stage >= 2:  # 幼苗
            painter.setPen(QPen(QColor("#228B22"), 6))
            stem_top = base_y - pot_h - 30
            painter.drawLine(cx, base_y - pot_h, cx, stem_top - 30)

            painter.setBrush(QBrush(QColor("#32CD32")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(cx - 18, stem_top - 10), 16, 10)
            painter.drawEllipse(QPoint(cx + 18, stem_top - 20), 14, 9)

        if stage >= 3:  # 成长
            painter.setPen(QPen(QColor("#2E7D32"), 8))
            stem_top = base_y - pot_h - 60
            painter.drawLine(cx, base_y - pot_h, cx, stem_top - 40)

            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.setPen(Qt.NoPen)
            for dx, dy, rx, ry in [(25, 10, 22, 13), (-22, 25, 20, 12),
                                     (18, 40, 18, 10), (-16, 55, 16, 10)]:
                painter.drawEllipse(QPoint(cx + dx, stem_top - dy), rx, ry)

        if stage >= 4:  # 开花
            painter.setPen(QPen(QColor("#1B5E20"), 10))
            stem_top = base_y - pot_h - 100
            painter.drawLine(cx, base_y - pot_h, cx, stem_top - 50)

            painter.setBrush(QBrush(QColor("#4CAF50")))
            painter.setPen(Qt.NoPen)
            for dx, dy, rx, ry in [(28, 15, 24, 14), (-26, 30, 22, 13),
                                     (20, 50, 20, 12), (-18, 65, 18, 11),
                                     (0, 20, 20, 13), (10, 40, 16, 10)]:
                painter.drawEllipse(QPoint(cx + dx, stem_top - dy), rx, ry)

            # 花瓣
            flower_cx, flower_cy = cx, stem_top - 70
            painter.setBrush(QBrush(QColor("#FF6B8A")))
            for angle in range(0, 360, 60):
                import math
                rad = math.radians(angle)
                fx = int(flower_cx + 14 * math.cos(rad))
                fy = int(flower_cy + 14 * math.sin(rad))
                painter.drawEllipse(QPoint(fx, fy), 8, 8)
            painter.setBrush(QBrush(QColor("#FFD700")))
            painter.drawEllipse(QPoint(flower_cx, flower_cy), 6, 6)

        if stage >= 5:  # 结果
            painter.setPen(QPen(QColor("#1B5E20"), 12))
            stem_top = base_y - pot_h - 150
            painter.drawLine(cx, base_y - pot_h, cx, stem_top - 50)

            painter.setBrush(QBrush(QColor("#388E3C")))
            painter.setPen(Qt.NoPen)
            for dx, dy, rx, ry in [(32, 20, 26, 15), (-30, 35, 24, 14),
                                     (22, 55, 22, 13), (-20, 70, 20, 12),
                                     (0, 25, 22, 14), (12, 45, 18, 11),
                                     (-8, 50, 18, 12)]:
                painter.drawEllipse(QPoint(cx + dx, stem_top - dy), rx, ry)

            # 果实
            painter.setBrush(QBrush(QColor("#FF6347")))
            painter.drawEllipse(QPoint(cx + 20, stem_top - 40), 10, 10)
            painter.drawEllipse(QPoint(cx - 18, stem_top - 60), 9, 9)
            painter.setBrush(QBrush(QColor("#FFD700")))
            painter.drawEllipse(QPoint(cx + 5, stem_top - 55), 8, 8)

        if stage >= 6:  # 大树
            painter.setPen(QPen(QColor("#1B5E20"), 16))
            stem_top = base_y - pot_h - 180
            painter.drawLine(cx, base_y - pot_h, cx, stem_top - 60)

            # 粗树干
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#5D4037")))
            painter.drawRect(int(cx - 12), stem_top - 30, 24, 60)

            painter.setBrush(QBrush(QColor("#2E7D32")))
            for dx, dy, rx, ry in [(40, 10, 35, 22), (-35, 20, 33, 20),
                                     (30, 35, 30, 20), (-28, 50, 28, 19),
                                     (0, 15, 32, 20), (15, 45, 25, 17),
                                     (-15, 40, 25, 17), (5, 60, 22, 15)]:
                painter.drawEllipse(QPoint(cx + dx, stem_top - dy), rx, ry)

            # 树冠
            painter.setBrush(QBrush(QColor("#43A047")))
            painter.drawEllipse(QPoint(cx, stem_top - 40), 50, 45)
            painter.setBrush(QBrush(QColor("#66BB6A")))
            painter.drawEllipse(QPoint(cx - 18, stem_top - 50), 30, 25)
            painter.drawEllipse(QPoint(cx + 22, stem_top - 48), 28, 24)

        painter.end()
