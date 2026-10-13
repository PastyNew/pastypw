"""Frameless title bar: window icon, title, language switch, window buttons.

Creator: PastyNew
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QMouseEvent, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from . import icons
from .theme import PALETTE, sans_font


class TitleBar(QWidget):
    """Custom (frameless) window header that also acts as the drag handle."""

    minimizeRequested = Signal()
    closeRequested = Signal()
    languageToggled = Signal()

    HEIGHT = 66

    def __init__(self, title: str, language: str = "RU", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(self.HEIGHT)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self._drag_offset: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 14, 0)
        layout.setSpacing(10)

        self._icon = QLabel(self)
        self._icon.setFixedSize(22, 22)
        self._icon.setPixmap(icons.pixmap("lock", 21, PALETTE.text_dim, ratio=self.devicePixelRatioF()))
        layout.addWidget(self._icon)

        self._title = QLabel(title, self)
        self._title.setObjectName("WindowTitle")
        self._title.setFont(sans_font(19))
        layout.addWidget(self._title)

        layout.addStretch(1)

        self._language = QPushButton(language, self)
        self._language.setObjectName("ChromeButton")
        self._language.setFixedSize(52, 34)
        self._language.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._language.setFont(sans_font(14))
        self._language.setStyleSheet(
            f"QPushButton#ChromeButton{{background:transparent;border:none;"
            f"border-radius:8px;color:{PALETTE.icon};letter-spacing:0.5px;}}"
            f"QPushButton#ChromeButton:hover{{background:{PALETTE.field};color:{PALETTE.text};}}"
        )
        self._language.setToolTip("Русский / English")
        self._language.clicked.connect(self.languageToggled.emit)
        layout.addWidget(self._language)

        self._minimize = QPushButton(self)
        self._minimize.setObjectName("ChromeButton")
        self._minimize.setFixedSize(46, 34)
        self._minimize.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._minimize.setIcon(icons.render("minus", 18, PALETTE.icon))
        self._minimize.setToolTip("Свернуть")
        self._minimize.clicked.connect(self.minimizeRequested.emit)
        layout.addWidget(self._minimize)

        self._close = QPushButton(self)
        self._close.setObjectName("CloseButton")
        self._close.setFixedSize(46, 34)
        self._close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._close.setIcon(icons.render("close", 18, PALETTE.icon))
        self._close.setIconSize(self._close.iconSize())
        self._close.setToolTip("Закрыть")
        self._close.clicked.connect(self.closeRequested.emit)
        layout.addWidget(self._close)

    # ------------------------------------------------------------------ api
    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_language_label(self, label: str, tooltip: str) -> None:
        self._language.setText(label)
        self._language.setToolTip(tooltip)

    def set_tooltips(self, minimize: str, close: str) -> None:
        self._minimize.setToolTip(minimize)
        self._close.setToolTip(close)

    # -------------------------------------------------------------- dragging
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window()
            self._drag_offset = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
            window._dragging = True  # type: ignore[attr-defined]

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_offset is not None and self.window()._dragging:  # type: ignore[attr-defined]
            window = self.window()
            window.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_offset = None
        if hasattr(self.window(), "_dragging"):
            self.window()._dragging = False  # type: ignore[attr-defined]

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.minimizeRequested.emit()

    # ---------------------------------------------------------------- paint
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Rounded top corners only, so the title bar merges with the window.
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.0, 0.0, self.width(), self.height() + 18), 18, 18)
        path.addRect(QRectF(0.0, self.height() - 18, self.width(), 18))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PALETTE.titlebar))
        painter.drawPath(path)
        painter.end()


def clip_icon_widget(size: int, color: str) -> QPixmap:
    return icons.pixmap("lock", size, color)