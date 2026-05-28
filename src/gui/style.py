"""Apple Music-style dark theme — v2, rebuilt around standard Qt widgets.

Lessons from the v0.5–v0.7 iterations:

  * QSS `padding` on QFrame containers does NOT propagate into Qt's
    layout-size calculations, so any container that adds padding via
    QSS ends up rendering bigger than its parent layout expects and
    overlaps neighbouring widgets.
  * Hand-rolled "card" QFrames with nested layouts compound the above
    problem. QGroupBox is a battle-tested Qt widget for the same
    purpose and gives us a free title slot, sensible internal
    margins, and proper layout cooperation.
  * Custom row layouts (label + control) drift out of alignment when
    label widths vary. QFormLayout is designed for exactly this case.

The new stylesheet therefore styles QGroupBox / QFormLayout /
QToolButton heavily and minimises QFrame customisation.
"""
from pathlib import Path


COLORS = {
    "bg":         "#1c1c1e",
    "bg_alt":     "#242426",
    "panel":      "#2c2c2e",
    "panel_hi":   "#3a3a3c",
    "border":     "#3a3a3c",
    "border_d":   "#48484a",

    "text":       "#f5f5f7",
    "text_dim":   "#aeaeb2",
    "text_xdim":  "#8e8e93",

    "accent":     "#fc3c44",
    "accent_h":   "#ff5a62",
    "accent_p":   "#cf2e35",
    "accent_bg":  "rgba(252, 60, 68, 38)",

    "ok":         "#30d158",
    "warn":       "#ff9f0a",
    "danger":     "#ff453a",
    "info":       "#0a84ff",
}


def checkbox_check_extra_qss(resources_dir: str | None) -> str:
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

QMainWindow, QWidget#central, QScrollArea, QScrollArea > QWidget > QWidget {{
    background: {COLORS['bg']};
}}

QToolTip {{
    background: #1c1c1e;
    color: #f5f5f7;
    border: 1px solid {COLORS['border']};
    padding: 4px 8px;
}}

/* ===============================================================
   Sidebar
   =============================================================== */
QFrame#sidebar {{
    background: rgba(28, 28, 30, 220);
    border-right: 1px solid {COLORS['border']};
}}
/* Padding rules below are on QLabel / QPushButton (text widgets, not
 * QFrame containers) so they do NOT trigger the layout-arithmetic
 * mismatch that bit us in the previous iterations. */
QLabel#sidebar_brand {{
    font-size: 15px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 18px 18px 2px 18px;
}}
QLabel#sidebar_brand_sub {{
    font-size: 11px;
    color: {COLORS['text_xdim']};
    padding: 0 18px 14px 18px;
}}
QLabel#sidebar_section {{
    color: {COLORS['text_xdim']};
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
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
    min-height: 24px;
}}
QPushButton#nav_btn:hover {{
    background: rgba(255, 255, 255, 14);
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
    margin: 0 14px 4px 14px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 13px;
    min-height: 24px;
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
    padding: 0 18px 10px 18px;
}}

/* ===============================================================
   Header bar
   =============================================================== */
QFrame#header {{
    background: rgba(28, 28, 30, 200);
    border-bottom: 1px solid {COLORS['border']};
}}
QLabel#header_title {{
    font-size: 22px;
    font-weight: 700;
    color: {COLORS['text']};
    padding: 18px 28px;
}}
QLabel#chip {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 11px;
    color: {COLORS['text_dim']};
    font-size: 11px;
    padding: 4px 10px;
}}
QLabel#chip_ok {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['ok']};
    border-radius: 11px;
    color: {COLORS['ok']};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
}}
QLabel#chip_warn {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['warn']};
    border-radius: 11px;
    color: {COLORS['warn']};
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
}}

/* ===============================================================
   GroupBox-based sections (replaces the old custom #card frame)
   =============================================================== */
QGroupBox {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    margin-top: 16px;
    font-size: 13px;
    font-weight: 600;
    color: {COLORS['text']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 0px;
    padding: 0 6px;
    color: {COLORS['text']};
    background: transparent;
}}

/* ===============================================================
   Typography
   =============================================================== */
QLabel#heading {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['text']};
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

/* ===============================================================
   Inputs
   =============================================================== */
QLineEdit {{
    background: {COLORS['bg_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 7px 10px;
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent']};
    selection-color: white;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['accent']};
}}

QComboBox {{
    background: {COLORS['bg_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 5px 10px;
    color: {COLORS['text']};
    min-height: 22px;
}}
QComboBox:focus {{
    border: 1px solid {COLORS['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {COLORS['panel']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent']};
    selection-color: white;
    outline: none;
    padding: 4px;
}}

QPlainTextEdit {{
    background: {COLORS['bg_alt']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    selection-background-color: {COLORS['accent']};
    selection-color: white;
}}

/* ===============================================================
   Buttons
   =============================================================== */
QPushButton {{
    background: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 8px;
    padding: 7px 14px;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
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
    background: {COLORS['panel_hi']};
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

/* ===============================================================
   Preset selection tool buttons (audio tab grid)
   =============================================================== */
QToolButton#preset_btn {{
    background: {COLORS['bg_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    padding: 10px 12px;
    color: {COLORS['text']};
    text-align: left;
    font-weight: 600;
    min-height: 56px;
}}
QToolButton#preset_btn:hover {{
    background: {COLORS['panel_hi']};
}}
QToolButton#preset_btn:checked {{
    background: {COLORS['accent_bg']};
    border: 2px solid {COLORS['accent']};
    color: {COLORS['accent']};
}}

/* ===============================================================
   Sliders
   =============================================================== */
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

/* ===============================================================
   Checkbox
   =============================================================== */
QCheckBox {{
    spacing: 8px;
    color: {COLORS['text']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border_d']};
    border-radius: 4px;
    background: {COLORS['bg_alt']};
}}
QCheckBox::indicator:hover {{
    border: 1px solid {COLORS['accent']};
}}
QCheckBox::indicator:checked {{
    background: {COLORS['accent']};
    border: 1px solid {COLORS['accent']};
}}

/* ===============================================================
   Progress bars
   =============================================================== */
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

/* ===============================================================
   Scrollbars
   =============================================================== */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
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
    height: 10px;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #48484a;
    border-radius: 4px;
    min-width: 24px;
}}

/* ===============================================================
   Drop overlay and empty state
   =============================================================== */
QLabel#drop_target {{
    background: {COLORS['bg_alt']};
    border: 2px dashed {COLORS['border_d']};
    border-radius: 12px;
    padding: 24px;
    color: {COLORS['text_dim']};
    font-size: 13px;
}}
QLabel#empty_state {{
    color: {COLORS['text_xdim']};
    font-size: 13px;
    padding: 40px;
}}

/* ===============================================================
   Job card (import queue)
   =============================================================== */
QFrame#job_card {{
    background: {COLORS['bg_alt']};
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

/* ===============================================================
   Toast
   =============================================================== */
QFrame#toast {{
    background: rgba(44, 44, 46, 245);
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

/* ===============================================================
   Full-window drop overlay
   =============================================================== */
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
