"""Vector icons rendered on the fly (no image files needed at runtime).

Every icon is a 24x24 stroke icon; the colour is injected at render time so
the same source works for the title bar, buttons and menus.

Creator: PastyNew
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .theme import PALETTE

_SVG: dict[str, str] = {
    "lock": (
        '<rect x="4.5" y="10.5" width="15" height="9.5" rx="2.6"/>'
        '<path d="M8 10.5V7.8a4 4 0 0 1 8 0v2.7"/>'
    ),
    "copy": (
        '<rect x="9" y="9" width="11.5" height="11.5" rx="3"/>'
        '<path d="M15 5.6A2.6 2.6 0 0 0 12.4 3H6.6A2.6 2.6 0 0 0 4 5.6v5.8'
        'A2.6 2.6 0 0 0 6.6 14"/>'
    ),
    "refresh": (
        '<path d="M20.5 12a8.5 8.5 0 1 1-2.6-6.2"/>'
        '<path d="M20.8 4.2v5.4h-5.4"/>'
    ),
    "star": (
        '<path d="M12 3.4l2.65 5.6 6.1.8-4.5 4.2 1.2 6.1L12 17.2l-5.45 2.9'
        '1.2-6.1-4.5-4.2 6.1-.8z"/>'
    ),
    "star_filled": (
        '<path d="M12 3.4l2.65 5.6 6.1.8-4.5 4.2 1.2 6.1L12 17.2l-5.45 2.9'
        '1.2-6.1-4.5-4.2 6.1-.8z" fill="currentColor"/>'
    ),
    "trash": (
        '<path d="M4.5 7h15"/><path d="M9.5 7V4.8h5V7"/>'
        '<path d="M6.5 7l1 12.2h9L17.5 7"/><path d="M10.5 10.6v5.8M13.5 10.6v5.8"/>'
    ),
    "download": (
        '<path d="M12 4v10.5"/><path d="M8 11l4 4 4-4"/><path d="M4.5 19.5h15"/>'
    ),
    "minus": '<path d="M6.5 12h11"/>',
    "close": '<path d="M7 7l10 10"/><path d="M17 7L7 17"/>',
    "clock": (
        '<circle cx="12" cy="12" r="8.2"/><path d="M12 7.6V12l3.1 1.9"/>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="8.2"/><path d="M3.8 12h16.4"/>'
        '<path d="M12 3.8c2.4 2.6 3.6 5.3 3.6 8.2s-1.2 5.6-3.6 8.2'
        'c-2.4-2.6-3.6-5.3-3.6-8.2S9.6 6.4 12 3.8z"/>'
    ),
    "eye": (
        '<path d="M2.8 12S6.2 5.6 12 5.6 21.2 12 21.2 12 17.8 18.4 12 18.4'
        ' 2.8 12 2.8 12z"/><circle cx="12" cy="12" r="3.1"/>'
    ),
    "eye_off": (
        '<path d="M9.9 5.9A9.6 9.6 0 0 1 12 5.6c5.8 0 9.2 6.4 9.2 6.4a17 17 0 0 1-3.3 4.1"/>'
        '<path d="M6.3 7.3A17.3 17.3 0 0 0 2.8 12S6.2 18.4 12 18.4c1.6 0 3-.4 4.2-1"/>'
        '<path d="M4 4l16 16"/>'
    ),
    "chevron": '<path d="M7.5 10.5l4.5 4.5 4.5-4.5"/>',
    "shield": (
        '<path d="M12 3.5l7 2.7v5.3c0 4.3-2.9 7.6-7 9-4.1-1.4-7-4.7-7-9V6.2z"/>'
        '<path d="M9 12l2.2 2.2L15.4 10"/>'
    ),
    "list": (
        '<path d="M9 6.5h11"/><path d="M9 12h11"/><path d="M9 17.5h11"/>'
        '<path d="M4.5 6.5h.01"/><path d="M4.5 12h.01"/><path d="M4.5 17.5h.01"/>'
    ),
    "dice": (
        '<rect x="4" y="4" width="16" height="16" rx="4.5"/>'
        '<circle cx="9" cy="9" r="1.3" fill="currentColor" stroke="none"/>'
        '<circle cx="15" cy="15" r="1.3" fill="currentColor" stroke="none"/>'
        '<circle cx="15" cy="9" r="1.3" fill="currentColor" stroke="none"/>'
        '<circle cx="9" cy="15" r="1.3" fill="currentColor" stroke="none"/>'
    ),
}


def svg_source(name: str) -> str:
    """Return the raw SVG body for ``name`` (used by the icon export script)."""
    body = _SVG.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="24" height="24" fill="none" stroke="currentColor" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )


def svg_document(name: str, color: str = "#FFFFFF") -> str:
    return svg_source(name).replace("currentColor", color)

def render(name: str, size: int, color: str = "#FFFFFF", ratio: float = 2.0) -> QIcon:
    """Render an icon at ``size`` logical pixels with a crisp pixel ratio."""
    return QIcon(pixmap(name, size, color, ratio))


def pixmap(name: str, size: int, color: str, ratio: float = 2.0) -> QPixmap:
    """Render ``name`` into a transparent pixmap of ``size`` logical pixels."""
    px = max(1, int(round(size * ratio)))
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    QSvgRenderer(svg_document(name, color).encode("utf-8")).render(
        painter, QRectF(0, 0, px, px)
    )
    painter.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def app_icon(size: int = 256, ratio: float = 1.0) -> QIcon:
    """Application icon: rounded indigo square with a white lock glyph."""
    px = max(1, int(round(size * ratio)))
    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    plate = QPainterPath()
    plate.addRoundedRect(QRectF(0, 0, px, px), px * 0.22, px * 0.22)
    painter.fillPath(plate, QColor(PALETTE.accent))
    QSvgRenderer(svg_document("lock", "#FFFFFF").encode("utf-8")).render(
        painter, QRectF(px * 0.23, px * 0.23, px * 0.54, px * 0.54)
    )
    painter.end()

    pm.setDevicePixelRatio(ratio)
    return QIcon(pm)
