"""Apple Music-inspired Qt Style Sheet (light grey base, pink accent)."""

# Brand colors lifted from Apple Music's web player.
COLORS = {
    "bg":         "#f5f5f7",   # window background
    "card":       "#ffffff",   # card / panel surface
    "card_hover": "#fafafc",
    "border":     "#e5e5ea",
    "text":       "#1d1d1f",
    "text_dim":   "#6e6e73",
    "accent":     "#fc3c44",   # Apple Music red/pink
    "accent_h":   "#e6353d",   # hover
    "accent_p":   "#cf2e35",   # pressed
    "tab_active": "#1d1d1f",
    "input_bg":   "#ffffff",
    "log_bg":     "#ffffff",
}


QSS = f"""
* {{
    font-family: "SF Pro Display", "Segoe UI", "Yu Gothic UI", sans-serif;
    font-size: 14px;
    color: {COLORS['text']};
}}

QMainWindow, QWidget#central {{
    background: {COLORS['bg']};
}}

/* ---------- Tab bar ---------- */
QTabWidget::pane {{
    border: none;
    background: {COLORS['bg']};
    top: -1px;
}}
QTabBar {{
    background: {COLORS['bg']};
    qproperty-drawBase: 0;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLORS['text_dim']};
    padding: 10px 22px;
    margin-right: 4px;
    border: none;
    font-weight: 500;
    font-size: 14px;
}}
QTabBar::tab:selected {{
    color: {COLORS['tab_active']};
    border-bottom: 2px solid {COLORS['accent']};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {COLORS['text']};
}}

/* ---------- Cards ---------- */
QFrame#card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 4px;
}}

QLabel#heading {{
    font-size: 22px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 4px 0 2px 0;
}}
QLabel#subheading {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['text']};
    padding: 4px 0;
}}
QLabel#hint {{
    color: {COLORS['text_dim']};
    font-size: 12px;
}}
QLabel#status_ok {{
    color: #1f8a37;
    font-weight: 600;
}}
QLabel#status_warn {{
    color: #b46100;
    font-weight: 600;
}}

/* ---------- Inputs ---------- */
QLineEdit {{
    background: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {COLORS['accent']};
    selection-color: white;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['accent']};
}}

QComboBox {{
    background: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 6px 12px;
    min-width: 140px;
}}
QComboBox:focus {{
    border: 1px solid {COLORS['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    selection-background-color: {COLORS['accent']};
    selection-color: white;
    outline: none;
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {COLORS['accent_h']};
}}
QPushButton:pressed {{
    background: {COLORS['accent_p']};
}}
QPushButton:disabled {{
    background: #d2d2d7;
    color: #8e8e93;
}}
QPushButton#secondary {{
    background: transparent;
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#secondary:hover {{
    background: {COLORS['card_hover']};
    border: 1px solid #c7c7cc;
}}
QPushButton#secondary:pressed {{
    background: #eeeef1;
}}

/* ---------- Sliders ---------- */
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {COLORS['border']};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {COLORS['accent']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: white;
    border: 1px solid {COLORS['border']};
    width: 16px;
    height: 16px;
    margin: -7px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    border: 1px solid {COLORS['accent']};
}}

/* ---------- Checkbox ---------- */
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background: {COLORS['card']};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {COLORS['accent']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
    image: none;
}}

/* ---------- Progress bar ---------- */
QProgressBar {{
    background: {COLORS['border']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {COLORS['accent']};
    border-radius: 4px;
}}

/* ---------- List / Log ---------- */
QListWidget {{
    background: {COLORS['log_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    background: {COLORS['card_hover']};
    color: {COLORS['text']};
}}

/* ---------- ScrollBar ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #c7c7cc;
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #aeaeb2;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ---------- Drop overlay hint ---------- */
QLabel#drop_target {{
    background: {COLORS['card']};
    border: 2px dashed #c7c7cc;
    border-radius: 12px;
    padding: 28px;
    color: {COLORS['text_dim']};
    font-size: 14px;
}}
"""
