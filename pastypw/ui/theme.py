"""Visual theme: palette, fonts and the global stylesheet.

The palette was tuned to match the reference design: near-black window,
slightly lighter cards, indigo accent (#6366F1), 12-14 px corner radii.

Creator: PastyNew
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont, QFontDatabase


@dataclass(frozen=True)
class Palette:
    """Every colour used by the interface."""

    window: str = "#0F0F0F"
    titlebar: str = "#151515"
    titlebar_border: str = "#242424"
    card: str = "#151515"
    card_border: str = "#262626"
    field: str = "#1E1E1E"
    field_border: str = "#2A2A2A"
    field_hover: str = "#232323"
    spin: str = "#171717"

    accent: str = "#6366F1"
    accent_hover: str = "#7577F3"
    accent_pressed: str = "#5355DE"
    accent_soft: str = "#1E1F3D"

    text: str = "#E4E4E4"
    text_strong: str = "#F2F2F2"
    text_dim: str = "#B4B4B4"
    text_muted: str = "#7E7E7E"
    icon: str = "#A3A3A3"
    icon_hover: str = "#E4E4E4"

    track: str = "#2C2C2C"
    track_filled: str = "#6366F1"
    handle: str = "#FFFFFF"
    handle_ring: str = "#6366F1"

    danger: str = "#E5484D"
    warning: str = "#E0A800"
    fair: str = "#D2A106"
    good: str = "#46A758"
    very_good: str = "#30C48D"
    excellent: str = "#00C2A8"

    scrollbar: str = "#3A3A3A"


PALETTE = Palette()

STRENGTH_COLORS = {
    "danger": PALETTE.danger,
    "warning": PALETTE.warning,
    "fair": PALETTE.fair,
    "good": PALETTE.good,
    "very_good": PALETTE.very_good,
    "excellent": PALETTE.excellent,
}

SANS_STACK = ("Inter", "Segoe UI Variable", "Segoe UI", "SF Pro Text",
              "Ubuntu", "Cantarell", "Lato", "DejaVu Sans", "Arial")
MONO_STACK = ("JetBrains Mono", "Cascadia Mono", "Cascadia Code", "SF Mono",
              "Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New")


def _first_available(stack: tuple[str, ...], fallback: str) -> str:
    available = set(QFontDatabase.families())
    for family in stack:
        if family in available:
            return family
    return fallback


def sans_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont(_first_available(SANS_STACK, "sans-serif"), size)
    font.setWeight(weight)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return font


def mono_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    font = QFont(_first_available(MONO_STACK, "monospace"), size)
    font.setWeight(weight)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def qcolor(value: str, alpha: int = 255) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


def stylesheet() -> str:
    """Global QSS for the parts that Qt styles natively."""
    p = PALETTE
    return f"""
    * {{
        font-family: "{_first_available(SANS_STACK, "sans-serif")}";
        outline: none;
    }}
    QToolTip {{
        background: {p.field};
        color: {p.text};
        border: 1px solid {p.card_border};
        border-radius: 8px;
        padding: 6px 10px;
    }}

    /* ------------------------------------------------------ title bar --- */
    QWidget#TitleBar {{
        background: {p.titlebar};
        border-bottom: 1px solid {p.titlebar_border};
    }}
    QLabel#WindowTitle {{
        color: {p.text_strong};
        font-size: 19px;
        font-weight: 500;
    }}
    QPushButton#ChromeButton,
    QPushButton#CloseButton {{
        background: transparent;
        border: none;
        border-radius: 8px;
    }}
    QPushButton#ChromeButton:hover,
    QPushButton#CloseButton:hover {{
        background: {p.field};
    }}
    QPushButton#CloseButton:hover {{
        background: {p.danger};
    }}

    /* --------------------------------------------------------- labels --- */
    QLabel#CardTitle   {{ color: {p.text}; font-size: 19px; }}
    QLabel#Hint        {{ color: {p.text_muted}; font-size: 13px; }}
    QLabel#FieldHint   {{ color: {p.text_dim}; font-size: 15px; }}
    QLabel#Footer      {{ color: {p.text_muted}; font-size: 13px; }}

    /* ------------------------------------------------------- password --- */
    QLineEdit#PasswordField {{
        background: {p.field};
        border: 1px solid {p.field_border};
        border-radius: 12px;
        color: {p.text};
        font-size: 27px;
        padding: 0 26px;
        selection-background-color: {p.accent};
    }}
    QLineEdit#PasswordField:hover {{
        border-color: {p.card_border};
    }}
    QLineEdit#PasswordField:focus {{
        border-color: {p.accent};
    }}
    QPushButton#CopyButton {{
        background: {p.field};
        border: 1px solid {p.field_border};
        border-radius: 12px;
    }}
    QPushButton#CopyButton:hover {{
        background: {p.field_hover};
        border-color: {p.accent};
    }}

    /* --------------------------------------------------------- button --- */
    QPushButton#GenerateButton {{
        background: {p.accent};
        border: none;
        border-radius: 12px;
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 500;
        padding: 18px;
    }}
    QPushButton#GenerateButton:hover  {{ background: {p.accent_hover}; }}
    QPushButton#GenerateButton:pressed{{ background: {p.accent_pressed}; }}
    QPushButton#GenerateButton:disabled {{
        background: #2A2B4A;
        color: #6C6E8C;
    }}

    /* ------------------------------------------------------------ card --- */
    QWidget#Card {{
        background: {p.card};
        border: 1px solid {p.card_border};
        border-radius: 14px;
    }}

    /* ---------------------------------------------------------- spinbox --- */
    QSpinBox#NumberField {{
        background: {p.spin};
        border: 1px solid {p.field_border};
        border-radius: 12px;
        color: {p.text};
        font-size: 20px;
        padding: 4px 6px;
    }}
    QSpinBox#NumberField:hover {{ border-color: #343434; }}
    QSpinBox#NumberField:focus {{ border-color: {p.accent}; }}
    QSpinBox#NumberField::up-button,
    QSpinBox#NumberField::down-button {{
        width: 0px;
        height: 0px;
        border: none;
        background: none;
    }}

    /* ------------------------------------------------------- segmented --- */
    QWidget#Segmented {{
        background: {p.field};
        border: 1px solid {p.field_border};
        border-radius: 11px;
    }}
    QPushButton#Segment {{
        background: transparent;
        border: none;
        border-radius: 9px;
        color: {p.text_muted};
        font-size: 15px;
        font-weight: 500;
        padding: 9px 18px;
    }}
    QPushButton#Segment:hover {{ color: {p.text}; }}
    QPushButton#Segment:checked {{
        background: {p.accent};
        color: #FFFFFF;
    }}

    /* --------------------------------------------------------- ghost btns --- */
    QPushButton#GhostButton {{
        background: transparent;
        border: 1px solid {p.field_border};
        border-radius: 10px;
        color: {p.text_dim};
        font-size: 14px;
        font-weight: 500;
        padding: 8px 14px;
    }}
    QPushButton#GhostButton:hover {{
        color: {p.text};
        border-color: #3A3A3A;
        background: {p.field};
    }}
    QPushButton#GhostButton:disabled {{
        color: #4D4D4D;
        border-color: #242424;
    }}

    /* ------------------------------------------------------- scroll area --- */
    QScrollArea#Body {{
        background: transparent;
        border: none;
    }}
    QScrollArea#Body > QWidget > QWidget {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px 2px 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {p.scrollbar};
        border-radius: 5px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{ background: #4A4A4A; }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{ height: 0px; background: none; }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{ width: 0px; background: none; }}
    QScrollBar::handle:horizontal {{ background: none; min-width: 0px; height: 0px; }}

    /* --------------------------------------------------------- toast --- */
    QLabel#Toast {{
        background: {p.field};
        border: 1px solid {p.field_border};
        border-radius: 10px;
        color: {p.text};
        font-size: 14px;
        font-weight: 500;
        padding: 10px 18px;
    }}
    """