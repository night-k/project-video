import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QWidget,
    QSizePolicy,
)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(12)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)


class PathPicker(QWidget):
    """单行路径选择：徽章 + 标题 + 路径 + 按钮"""

    path_selected = pyqtSignal(str)

    def __init__(self, badge_text, badge_object_name, title, hint, parent=None):
        super().__init__(parent)
        self._path = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)
        self.badge = QLabel(badge_text)
        self.badge.setObjectName(badge_object_name)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("section_title")
        header.addWidget(self.badge)
        header.addWidget(title_lbl)
        header.addStretch()
        root.addLayout(header)

        if hint:
            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("section_hint")
            root.addWidget(hint_lbl)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.path_label = QLabel("点击右侧按钮选择文件…")
        self.path_label.setObjectName("path_display")
        self.path_label.setWordWrap(True)
        self.path_label.setMinimumHeight(40)
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.btn = QPushButton("浏览…")
        self.btn.setObjectName("ghost_btn")
        self.btn.clicked.connect(self._on_browse)
        row.addWidget(self.path_label, 1)
        row.addWidget(self.btn)
        root.addLayout(row)

    def _on_browse(self):
        pass  # 由 MainWindow 绑定

    def set_path(self, path: str):
        self._path = path
        if path:
            display = path
            if len(display) > 72:
                display = "…" + display[-69:]
            self.path_label.setText(display)
            self.path_label.setProperty("pathSet", True)
        else:
            self.path_label.setText("点击右侧按钮选择文件…")
            self.path_label.setProperty("pathSet", False)
        self.path_label.style().unpolish(self.path_label)
        self.path_label.style().polish(self.path_label)

    def path(self) -> str:
        return self._path


class StrengthCard(QFrame):
    """可点击的去重强度卡片"""

    clicked_card = pyqtSignal()

    def __init__(self, pct: str, fps: str, desc: str, radio: QRadioButton, parent=None):
        super().__init__(parent)
        self.radio = radio
        self.setObjectName("strength_card")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("selected", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        pct_lbl = QLabel(pct)
        pct_lbl.setObjectName("strength_pct")
        fps_lbl = QLabel(fps)
        fps_lbl.setObjectName("strength_fps")
        desc_lbl = QLabel(desc)
        desc_lbl.setObjectName("strength_desc")
        desc_lbl.setWordWrap(True)

        layout.addWidget(pct_lbl)
        layout.addWidget(fps_lbl)
        layout.addWidget(desc_lbl)
        layout.addWidget(radio, alignment=Qt.AlignCenter)

        radio.toggled.connect(self._sync_selected)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.radio.setChecked(True)
            self.clicked_card.emit()
        super().mousePressEvent(event)

    def _sync_selected(self, checked: bool):
        self.setProperty("selected", checked)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("section_title")
        layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("section_hint")
            layout.addWidget(s)
