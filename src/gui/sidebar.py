"""Apple Music-style sidebar with brand, primary action, nav, and footer."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from .. import settings


NAV_ITEMS: list[tuple[str, str]] = [
    ("📥", "取り込み"),
    ("🎚",  "音質"),
    ("⚙️", "設定"),
    ("📋", "ログ"),
]


class Sidebar(QFrame):
    nav_clicked = pyqtSignal(int)
    new_import_clicked = pyqtSignal()
    open_output_clicked = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 12)
        outer.setSpacing(0)

        brand = QLabel("🎵  Apple Music")
        brand.setObjectName("sidebar_brand")
        outer.addWidget(brand)
        sub = QLabel("Library Helper")
        sub.setObjectName("sidebar_brand_sub")
        outer.addWidget(sub)

        # Prominent primary action (mirrors Apple Music's search bar slot).
        self.new_btn = QPushButton("+  新規取り込み")
        self.new_btn.setObjectName("sidebar_primary")
        self.new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_btn.clicked.connect(self.new_import_clicked.emit)
        outer.addWidget(self.new_btn)

        section = QLabel("MENU")
        section.setObjectName("sidebar_section")
        outer.addWidget(section)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for index, (icon, label) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}    {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if index == 0:
                btn.setChecked(True)
            self._group.addButton(btn, index)
            outer.addWidget(btn)

        outer.addStretch(1)

        # Footer: current preset + open-folder shortcut (like Apple Music's
        # "now playing" + sign-in chip at the bottom of its sidebar).
        section2 = QLabel("NOW USING")
        section2.setObjectName("sidebar_section")
        outer.addWidget(section2)

        self.preset_value = QLabel(settings.preset_name())
        self.preset_value.setObjectName("sidebar_footer_title")
        outer.addWidget(self.preset_value)
        self.preset_label = QLabel("音質プリセット")
        self.preset_label.setObjectName("sidebar_footer_sub")
        outer.addWidget(self.preset_label)

        self.open_folder_btn = QPushButton("📂   出力フォルダを開く")
        self.open_folder_btn.setObjectName("nav_btn")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self.open_output_clicked.emit)
        outer.addWidget(self.open_folder_btn)

        self._group.idClicked.connect(self.nav_clicked.emit)

    def select(self, index: int) -> None:
        btn = self._group.button(index)
        if btn:
            btn.setChecked(True)

    def set_current_preset(self, name: str) -> None:
        self.preset_value.setText(name)
