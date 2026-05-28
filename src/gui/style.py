"""Apple Music-style dark theme.

Single source of truth for colors + QSS. Designed to play well with
Windows 11 Mica/Acrylic backdrop (so most surfaces are subtly
translucent and pure black is avoided).
"""
from pathlib import Path


# Dark palette modeled on Apple Music for Windows.
COLORS = {
    # Surfaces
    "bg":          "#1c1c1e",
    "sidebar":     "rgba(28, 28, 30, 200)",  # slight transparency for Mica
    "header":      "rgba(28, 28, 30, 180)",
    "card":        "#2c2c2e",
    "card_hover":  "#3a3a3c",
    "card_alt":    "#242426",
    "input_bg":    "#2c2c2e",

    # Strokes
    "border":      "#3a3a3c",
    "border_d":    "#48484a",

    # Type
    "text":        "#f5f5f7",
    "text_dim":    "#aeaeb2",
    "text_xdim":   "#8e8e93",

    # Brand
    "accent":      "#fc3c44",
    "accent_h":    "#ff5a62",
    "accent_p":    "#cf2e35",
    "accent_bg":   "rgba(252, 60, 68, 32)",

    # Status
    "ok":          "#30d158",
    "warn":        "#ff9f0a",
    "info":        "#0a84ff",
    "danger":      "#ff453a",
}


def checkbox_check_extra_qss(resources_dir: str | None) -> str:
    """White checkmark image overlay for :checked indicators."""
    if not resources_dir:
        return ""
    p = Path(resources_dir) / "check.png"
    if not p.exists():
        return ""
    return f"""
QCheckBox::indicator:checked {{
    image: url({p.as_posix()});
}}
"""


QSS = f"""
* {{
    font-family: "Segoe UI Variable", "Segoe UI", "Yu Gothic UI", sans-serif;
    font-size: 13px;
    color: {COLORS['text']};
}}

QMainWindow, QWidget#central {{
    background: {COLORS['bg']};
}}

QToolTip {{
    background: #1c1c1e;
    color: #f5f5f7;
    border: 1px solid {COLORS['border']};
    padding: 4px 8px;
}}

/* ============================================================
   Sidebar
   ============================================================ */
QFrame#sidebar {{
    background: {COLORS['sidebar']};
    border-right: 1px solid {COLORS['border']};
}}
QLabel#sidebar_brand {{
    font-size: 15px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 18px 18px 2px 18px;
}}
QLabel#sidebar_brand_sub {{
    font-size: 11px;
    color: {COLORS['text_xdim']};
    padding: 0 18px 16px 18px;
}}
QLabel#sidebar_section {{
    color: {COLORS['text_xdim']};
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.0px;
    padding: 14px 18px 4px 18px;
}}
QPushButton#nav_btn {{
    background: transparent;
    color: {COLORS['text_dim']};
    text-align: left;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    padding: 9px 18px 9px 15px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#nav_btn:hover {{
    background: rgba(255, 255, 255, 12);
    color: {COLORS['text']};
}}
QPushButton#nav_btn:checked {{
    color: {COLORS['accent']};
    border-left: 3px solid {COLORS['accent']};
    font-weight: 600;
    background: {COLORS['accent_bg']};
}}
QPushButton#sidebar_primary {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 0 14px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton#sidebar_primary:hover {{
    background: {COLORS['accent_h']};
}}
QPushButton#sidebar_primary:pressed {{
    background: {COLORS['accent_p']};
}}
QLabel#sidebar_footer_title {{
    color: {COLORS['text']};
    font-size: 12px;
    font-weight: 600;
    padding: 0 18px;
}}
QLabel#sidebar_footer_sub {{
    color: {COLORS['text_xdim']};
    font-size: 10px;
    padding: 0 18px 12px 18px;
}}

/* ============================================================
   Header bar (top of content area)
   ============================================================ */
QFrame#header {{
    background: {COLORS['header']};
    border-bottom: 1px solid {COLORS['border']};
}}
QLabel#header_title {{
    font-size: 24px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 18px 28px 12px 28px;
}}
QLabel#chip {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 4px 10px;
    color: {COLORS['text_dim']};
    font-size: 11px;
}}
QLabel#chip_ok {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['ok']};
    border-radius: 12px;
    padding: 4px 10px;
    color: {COLORS['ok']};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#chip_warn {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['warn']};
    border-radius: 12px;
    padding: 4px 10px;
    color: {COLORS['warn']};
    font-size: 11px;
    font-weight: 600;
}}

/* ============================================================
   Cards (content sections)
   ============================================================ */
QFrame#card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}

QLabel#heading {{
    font-size: 20px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 0;
}}
QLabel#subheading {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text']};
    padding: 0;
}}
QLabel#hint {{
    color: {COLORS['text_dim']};
    font-size: 12px;
}}
QLabel#status_ok {{
    color: {COLORS['ok']};
    font-weight: 600;
}}
QLabel#status_warn {{
    color: {COLORS['warn']};
    font-weight: 600;
}}

/* ============================================================
   Inputs
   ============================================================ */
QLineEdit {{
    background: {COLORS['input_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 12px;
    color: {COLORS['text']};
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
    color: {COLORS['text']};
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
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent']};
    selection-color: white;
    outline: none;
}}

QPlainTextEdit {{
    background: {COLORS['card_alt']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px;
    selection-background-color: {COLORS['accent']};
    selection-color: white;
}}

/* ============================================================
   Buttons
   ============================================================ */
QPushButton {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {COLORS['accent_h']};
}}
QPushButton:pressed {{
    background: {COLORS['accent_p']};
}}
QPushButton:disabled {{
    background: #3a3a3c;
    color: #6e6e73;
}}
QPushButton#secondary {{
    background: {COLORS['card_hover']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#secondary:hover {{
    background: #48484a;
    border: 1px solid {COLORS['border_d']};
}}
QPushButton#secondary:pressed {{
    background: #3a3a3c;
}}

/* ============================================================
   Sliders
   ============================================================ */
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
    background: {COLORS['text']};
    border: none;
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: white;
}}

/* ============================================================
   Checkbox
   ============================================================ */
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_d']};
    border-radius: 4px;
    background: {COLORS['card_alt']};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {COLORS['accent']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}

/* ============================================================
   Progress bar
   ============================================================ */
QProgressBar {{
    background: {COLORS['border']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {COLORS['accent']};
    border-radius: 4px;
}}

/* ============================================================
   Scrollbars
   ============================================================ */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #48484a;
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #6e6e73;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 2px 4px;
}}
QScrollBar::handle:horizontal {{
    background: #48484a;
    border-radius: 4px;
    min-width: 24px;
}}

/* ============================================================
   Drag drop card placeholder (in ImportTab)
   ============================================================ */
QLabel#drop_target {{
    background: {COLORS['card_alt']};
    border: 2px dashed {COLORS['border_d']};
    border-radius: 12px;
    padding: 24px;
    color: {COLORS['text_dim']};
    font-size: 13px;
}}

/* ============================================================
   Empty state
   ============================================================ */
QLabel#empty_state {{
    color: {COLORS['text_xdim']};
    font-size: 13px;
    padding: 40px;
}}

/* ============================================================
   Job card (import queue)
   ============================================================ */
QFrame#job_card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
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

/* ============================================================
   Preset cards (audio tab grid)
   ============================================================ */
QFrame#preset_card {{
    background: {COLORS['card']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}
QFrame#preset_card:hover {{
    background: {COLORS['card_hover']};
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

/* ============================================================
   Toast
   ============================================================ */
QFrame#toast {{
    background: rgba(44, 44, 46, 240);
    border: 1px solid {COLORS['border_d']};
    border-radius: 12px;
    color: white;
}}
QLabel#toast_title {{
    color: white;
    font-weight: 600;
    font-size: 13px;
}}
QLabel#toast_body {{
    color: {COLORS['text_dim']};
    font-size: 12px;
}}

/* ============================================================
   Full-window drop overlay
   ============================================================ */
QFrame#drop_overlay {{
    background: rgba(252, 60, 68, 30);
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
