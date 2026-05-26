"""Apple Music-inspired Qt Style Sheet (light grey base, pink accent)."""

# Brand colors lifted from Apple Music's web player.
COLORS = {
    "bg":         "#f5f5f7",   # window background
    "sidebar":    "#fafafc",   # left navigation rail
    "card":       "#ffffff",   # card / panel surface
    "card_hover": "#fafafc",
    "border":     "#e5e5ea",
    "border_d":   "#d2d2d7",   # darker for separators
    "text":       "#1d1d1f",
    "text_dim":   "#6e6e73",
    "text_xdim":  "#86868b",
    "accent":     "#fc3c44",   # Apple Music red/pink
    "accent_h":   "#e6353d",
    "accent_p":   "#cf2e35",
    "accent_bg":  "#fff0f1",   # tinted background for selected nav
    "tab_active": "#1d1d1f",
    "input_bg":   "#ffffff",
    "log_bg":     "#ffffff",
    "ok":         "#1f8a37",
    "warn":       "#b46100",
    "info":       "#3478f6",
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

/* ---------- Drop overlay hint (inside cards) ---------- */
QLabel#drop_target {{
    background: {COLORS['card']};
    border: 2px dashed #c7c7cc;
    border-radius: 12px;
    padding: 28px;
    color: {COLORS['text_dim']};
    font-size: 14px;
}}

/* ---------- Sidebar ---------- */
QFrame#sidebar {{
    background: {COLORS['sidebar']};
    border-right: 1px solid {COLORS['border']};
}}
QLabel#sidebar_brand {{
    font-size: 16px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 18px 18px 4px 18px;
}}
QLabel#sidebar_brand_sub {{
    font-size: 11px;
    color: {COLORS['text_xdim']};
    padding: 0 18px 18px 18px;
}}
QPushButton#nav_btn {{
    background: transparent;
    color: {COLORS['text']};
    text-align: left;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 11px 18px 11px 15px;
    font-weight: 500;
    font-size: 14px;
}}
QPushButton#nav_btn:hover {{
    background: rgba(0, 0, 0, 0.04);
}}
QPushButton#nav_btn:checked {{
    background: {COLORS['accent_bg']};
    color: {COLORS['accent']};
    border-left: 3px solid {COLORS['accent']};
    font-weight: 600;
}}
QLabel#sidebar_section {{
    color: {COLORS['text_xdim']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 18px 18px 6px 18px;
}}
QLabel#sidebar_preset {{
    color: {COLORS['text']};
    font-size: 13px;
    font-weight: 600;
    padding: 0 18px;
}}
QLabel#sidebar_preset_label {{
    color: {COLORS['text_xdim']};
    font-size: 11px;
    padding: 0 18px 18px 18px;
}}

/* ---------- Job / import-item card ---------- */
QFrame#job_card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
QLabel#job_title {{
    font-weight: 600;
    color: {COLORS['text']};
    font-size: 13px;
}}
QLabel#job_status {{
    color: {COLORS['text_dim']};
    font-size: 11px;
}}
QLabel#job_status_ok {{
    color: {COLORS['ok']};
    font-weight: 600;
    font-size: 11px;
}}
QLabel#job_status_err {{
    color: {COLORS['accent']};
    font-weight: 600;
    font-size: 11px;
}}
QProgressBar#job_progress {{
    background: {COLORS['border']};
    border: none;
    border-radius: 2px;
    height: 4px;
    text-align: center;
    color: transparent;
}}
QProgressBar#job_progress::chunk {{
    background: {COLORS['accent']};
    border-radius: 2px;
}}

/* ---------- Empty-state placeholder in queue ---------- */
QLabel#empty_state {{
    color: {COLORS['text_xdim']};
    font-size: 13px;
    padding: 40px;
    qproperty-alignment: AlignCenter;
}}

/* ---------- Status bar ---------- */
QStatusBar {{
    background: {COLORS['sidebar']};
    border-top: 1px solid {COLORS['border']};
    color: {COLORS['text_dim']};
    font-size: 12px;
}}
QStatusBar QLabel {{
    padding: 0 12px;
    color: {COLORS['text_dim']};
}}
QStatusBar::item {{
    border: none;
}}

/* ---------- Preset cards ---------- */
QFrame#preset_card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
}}
QFrame#preset_card:hover {{
    background: {COLORS['card_hover']};
    border: 1px solid #c7c7cc;
}}
QFrame#preset_card[selected="true"] {{
    background: {COLORS['accent_bg']};
    border: 2px solid {COLORS['accent']};
}}
QLabel#preset_card_icon {{
    font-size: 26px;
}}
QLabel#preset_card_title {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text']};
}}
QLabel#preset_card_tag {{
    font-size: 11px;
    color: {COLORS['text_dim']};
}}
QFrame#preset_card[selected="true"] QLabel#preset_card_title {{
    color: {COLORS['accent']};
}}

/* ---------- EQ visualization ---------- */
QFrame#eq_panel {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}

/* ---------- Toast notification ---------- */
QFrame#toast {{
    background: rgba(29, 29, 31, 240);
    border-radius: 12px;
    color: white;
}}
QLabel#toast_title {{
    color: white;
    font-weight: 600;
    font-size: 13px;
    padding: 0;
}}
QLabel#toast_body {{
    color: #d2d2d7;
    font-size: 12px;
    padding: 0;
}}

/* ---------- Full-window drop overlay ---------- */
QFrame#drop_overlay {{
    background: rgba(252, 60, 68, 0.10);
    border: 3px dashed {COLORS['accent']};
    border-radius: 16px;
}}
QLabel#drop_overlay_label {{
    color: {COLORS['accent']};
    font-size: 28px;
    font-weight: 700;
    background: transparent;
}}
QLabel#drop_overlay_sub {{
    color: {COLORS['accent']};
    font-size: 14px;
    background: transparent;
}}
"""
