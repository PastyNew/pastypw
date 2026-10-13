"""Reusable, fully custom-painted widgets of the interface.

Creator: PastyNew
"""

from __future__ import annotations

import time

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import icons
from .i18n import format_duration
from .theme import PALETTE, mono_font, sans_font


def _q(value: str, alpha: float = 1.0) -> QColor:
    color = QColor(value)
    color.setAlphaF(alpha)
    return color


class PlainScrollArea(QScrollArea):
    """Scroll area whose viewport does not paint the light Qt background."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PlainScroll")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)


class Card(QWidget):
    """Rounded panel (1 px border, 14 px radius)."""

    def __init__(self, parent: QWidget | None = None, padding: int = 32) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(16)

    def body(self) -> QVBoxLayout:
        return self._layout

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(PALETTE.card))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(_q(PALETTE.card_border), 1))
        painter.drawRoundedRect(rect, 14, 14)
        painter.end()


class IconButton(QPushButton):
    """Borderless square button that paints an icon with hover feedback."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        size: int = 38,
        icon_px: int = 19,
        color: str = PALETTE.icon,
        checkable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GhostButton")
        self._icon_name = icon_name
        self._icon_px = icon_px
        self._color = color
        self.setFixedSize(size, size)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(checkable)
        self.setFlat(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            f"QPushButton#GhostButton{{background:transparent;border:none;"
            f"border-radius:{size // 3}px;padding:0;}}"
            f"QPushButton#GhostButton:hover{{background:{PALETTE.field};}}"
            f"QPushButton#GhostButton:checked{{background:{PALETTE.accent_soft};}}"
        )
        if tooltip:
            self.setToolTip(tooltip)
        self._refresh_icon()

    def set_color(self, color: str) -> None:
        self._color = color
        self._refresh_icon()

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        color = PALETTE.accent if self.isChecked() else self._color
        self.setIcon(icons.render(self._icon_name, self._icon_px, color))

    def setChecked(self, checked: bool) -> None:  # noqa: N802 (Qt naming)
        super().setChecked(checked)
        self._refresh_icon()


class ChromeButton(QPushButton):
    """Title-bar button (minimise / close) with a flat icon."""

    def __init__(self, icon_name: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChromeButton")
        self.setFixedSize(46, 36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setIcon(icons.render(icon_name, 18, PALETTE.icon))
        self.setIconSize(QSize(18, 18))
        self.setToolTip(tooltip)


class Slider(QSlider):
    """Slider with a pill-shaped track, an indigo fill and a round handle."""

    def __init__(self, minimum: int, maximum: int, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setFixedHeight(26)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self._hover = False
        self._pressed = False

    # -- events ---------------------------------------------------------
    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._pressed = True
        super().mousePressEvent(event)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._pressed = False
        super().mouseReleaseEvent(event)
        self.update()

    def _handle_center(self) -> float:
        span = self.maximum() - self.minimum()
        ratio = 0.0 if span == 0 else (self.value() - self.minimum()) / span
        radius = 9.0
        usable = self.width() - 2 * radius
        return radius + ratio * usable

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self._handle_center()
        track_y = self.height() / 2.0
        track_h = 6.0
        radius = track_h / 2.0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(PALETTE.track))
        painter.drawRoundedRect(QRectF(0, track_y - radius, self.width(), track_h), radius, radius)
        if center_x > 0:
            painter.setBrush(_q(PALETTE.accent))
            painter.drawRoundedRect(QRectF(0, track_y - radius, center_x, track_h), radius, radius)

        if self.hasFocus():
            painter.setBrush(_q(PALETTE.accent, 0.28))
            painter.drawEllipse(QRectF(center_x - 15, track_y - 15, 30, 30))

        handle_r = 9.0 if not (self._hover or self._pressed) else 10.5
        painter.setBrush(_q(PALETTE.handle))
        painter.drawEllipse(QRectF(center_x - handle_r, track_y - handle_r,
                                   handle_r * 2, handle_r * 2))
        painter.setPen(QPen(_q(PALETTE.accent), 2.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(center_x - handle_r, track_y - handle_r,
                                   handle_r * 2, handle_r * 2))
        painter.end()


class NumberField(QWidget):
    """Read-only-looking spin box: a rounded field with a custom value text."""

    valueChanged = Signal(int)

    def __init__(self, minimum: int, maximum: int, value: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(104, 56)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._min, self._max = minimum, maximum
        self._value = value
        self._hover = False
        self._dragging = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._label = QLabel(str(value), self)
        font = sans_font(20, QFont.Weight.Medium)
        self._label.setFont(font)
        self._label.setStyleSheet(f"color:{PALETTE.text};background:transparent;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._label.setGeometry(0, 0, 104, 56)

        self.setToolTip(self.tr("Scroll or drag to change the value"))
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(110)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def value(self) -> int:
        return self._value

    def set_value(self, value: int) -> None:
        value = max(self._min, min(self._max, int(value)))
        if value == self._value:
            return
        self._stop_anim()
        self._anim.setStartValue(self._value)
        self._anim.setEndValue(value)
        self._anim.finished.connect(lambda: self._apply(int(self._anim.endValue())))
        self._anim.start()

    def _stop_anim(self) -> None:
        if self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()
            self._apply(int(self._anim.currentValue()))

    def _apply(self, value: int) -> None:
        value = max(self._min, min(self._max, value))
        if value != self._value:
            self._value = value
            self._label.setText(str(value))
            self.valueChanged.emit(value)

    def _step(self, delta: int) -> None:
        self.set_value(self._value + delta)

    # -- interaction ----------------------------------------------------
    def wheelEvent(self, event) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta:
            self._step(1 if delta > 0 else -1)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.setFocus()
            if self.rect().contains(event.position().toPoint()):
                self._step(1)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._step(1)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging:
            self._step(-1 if event.position().x() < self.width() / 2 else 1)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._dragging = False

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Up, Qt.Key.Key_Right):
            self._step(1)
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_Left):
            self._step(-1)
        elif key in (Qt.Key.Key_PageUp,):
            self._step(5)
        elif key in (Qt.Key.Key_PageDown,):
            self._step(-5)
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(PALETTE.spin))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)
        border = PALETTE.accent if self.hasFocus() else (
            "#3A3A3A" if self._hover else PALETTE.field_border
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(_q(border), 1))
        painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 12, 12)
        painter.end()


class CheckRow(QWidget):
    """Rounded checkbox with an animated check mark and a clickable label."""

    toggled = Signal(bool)

    def __init__(self, text: str, checked: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self._hover = False
        self._box_hover = False
        self._progress = 1.0 if checked else 0.0
        self.setFixedHeight(40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._label = QLabel(text, self)
        self._label.setFont(sans_font(17))
        self._label.setStyleSheet(f"color:{PALETTE.text_dim};background:transparent;")
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout = QHBoxLayout(self)
        # 26 px box + 16 px gap so the label never overlaps the custom checkbox
        layout.setContentsMargins(42, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._label, 1)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_progress)

    # -- state ----------------------------------------------------------
    def isChecked(self) -> bool:  # noqa: N802
        return self._checked

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()
        self._label.setStyleSheet(
            f"color:{PALETTE.text if checked else PALETTE.text_dim};background:transparent;"
        )
        self.toggled.emit(checked)

    def setText(self, text: str) -> None:  # noqa: N802
        self._label.setText(text)

    def _on_progress(self, value) -> None:
        self._progress = float(value)
        self.update()

    # -- interaction ----------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.setChecked(not self._checked)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self._box_hover = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self._box_hover = False
        self.update()

    # -- painting -------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        box_size = 26.0
        box_x = 0.0
        box_y = (self.height() - box_size) / 2.0
        rect = QRectF(box_x, box_y, box_size, box_size)

        fill = QColor(PALETTE.accent)
        fill.setAlphaF(self._progress)
        bg = QColor(PALETTE.field)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg if self._progress < 0.5 else fill)
        if self._progress < 0.5:
            painter.drawRoundedRect(rect, 8, 8)
            border = "#3C3C3C" if self._hover else "#2F2F2F"
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(_q(border), 1))
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill)
            painter.drawRoundedRect(rect, 8, 8)
        else:
            painter.drawRoundedRect(rect, 8, 8)

        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(_q(PALETTE.accent, 0.6), 2))
            painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4), 11, 11)

        if self._progress > 0.01:
            path = QPainterPath()
            path.moveTo(box_x + 7.2, box_y + 13.4)
            path.lineTo(box_x + 11.0, box_y + 17.2)
            path.lineTo(box_x + 19.0, box_y + 8.8)
            pen = QPen(_q("#FFFFFF"), 2.4, Qt.PenStyle.SolidLine,
                       Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setOpacity(self._progress)
            painter.drawPath(path)
            painter.setOpacity(1.0)

        painter.end()


class StrengthMeter(QWidget):
    """Coloured bar + textual summary of the estimated password strength."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(58)
        self._percent = 0
        self._displayed = 0.0
        self._color = PALETTE.accent
        self._bits_text = ""
        self._rating_text = ""
        self._crack_text = ""
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_displayed)

    def set_strength(
        self,
        percent: int,
        color: str,
        rating_text: str,
        bits_text: str,
        crack_text: str,
    ) -> None:
        self._percent = max(2, min(100, percent))
        self._color = color
        self._rating_text = rating_text
        self._bits_text = bits_text
        self._crack_text = crack_text
        self._anim.stop()
        self._anim.setStartValue(self._displayed)
        self._anim.setEndValue(float(self._percent))
        self._anim.start()
        self.update()

    def clear(self, color: str = PALETTE.accent) -> None:
        self.set_strength(0, color, "", "", "")

    def _on_displayed(self, value) -> None:
        self._displayed = float(value)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if not self._rating_text:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_h = 7.0
        radius = bar_h / 2.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(PALETTE.track))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), bar_h), radius, radius)
        width = self.width() * (self._displayed / 100.0)
        if width > 1:
            painter.setBrush(_q(self._color))
            painter.drawRoundedRect(QRectF(0, 0, width, bar_h), radius, radius)

        text_y = bar_h + 22
        painter.setFont(sans_font(14, QFont.Weight.Medium))
        painter.setPen(_q(self._color))
        dot = QRectF(0, text_y - 5, 8, 8)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(self._color))
        painter.drawEllipse(dot)

        painter.setFont(sans_font(14, QFont.Weight.Medium))
        painter.setPen(_q(PALETTE.text))
        painter.drawText(QRectF(16, text_y - 11, 260, 22), Qt.AlignmentFlag.AlignVCenter,
                         self._rating_text)

        summary = f"{self._bits_text}  ·  {self._crack_text}" if self._bits_text else ""
        painter.setFont(sans_font(13))
        painter.setPen(_q(PALETTE.text_muted))
        painter.drawText(
            QRectF(self.width() - 360, text_y - 11, 360, 22),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            summary,
        )
        painter.end()


class PasswordRow(QWidget):
    """One password inside the batch list."""

    copyRequested = Signal()

    def __init__(self, password: str, index: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(58)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._hover = False
        self._password = password

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 12, 0)
        layout.setSpacing(12)

        self._index = QLabel(f"{index:02d}")
        self._index.setFont(mono_font(13))
        self._index.setStyleSheet(f"color:{PALETTE.text_muted};background:transparent;")
        self._index.setFixedWidth(26)

        self._text = QLabel(password)
        self._text.setFont(mono_font(18))
        self._text.setStyleSheet(f"color:{PALETTE.text};background:transparent;")

        self._copy = IconButton("copy", "Copy", 34, 17)
        self._copy.clicked.connect(self.copyRequested.emit)

        layout.addWidget(self._index)
        layout.addWidget(self._text, 1)
        layout.addWidget(self._copy)

    def password(self) -> str:
        return self._password

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q(PALETTE.field if self._hover else "#1A1A1A"))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 11, 11)
        if self._hover:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(_q(PALETTE.accent, 0.55), 1))
            painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 11, 11)
        painter.end()


class HistoryRow(QWidget):
    """History / favourites row with star, reveal, copy and delete actions."""

    copyRequested = Signal()
    favoriteToggled = Signal()
    deleteRequested = Signal()

    def __init__(
        self,
        entry,
        masked: bool = True,
        tr=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedHeight(64)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._hover = False
        self._entry = entry
        self._masked = masked
        self._tr = tr

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(10)

        self._star = IconButton("star_filled" if entry.favorite else "star",
                                "Favourite", 34, 17,
                                color=PALETTE.accent if entry.favorite else PALETTE.text_muted)
        self._star.setToolTip("")
        self._star.clicked.connect(self.favoriteToggled.emit)

        self._text = QLabel(self._display_text())
        self._text.setFont(mono_font(17))
        self._text.setStyleSheet(f"color:{PALETTE.text};background:transparent;")

        self._meta = QLabel(self._meta_text())
        self._meta.setFont(sans_font(12))
        self._meta.setStyleSheet(f"color:{PALETTE.text_muted};background:transparent;")

        side = QVBoxLayout()
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(2)
        side.addWidget(self._text)
        side.addWidget(self._meta)

        self._copy = IconButton("copy", "Copy", 34, 17)
        self._copy.clicked.connect(self.copyRequested.emit)
        self._delete = IconButton("trash", "Delete", 34, 17,
                                  color="#6E6E6E")
        self._delete.clicked.connect(self.deleteRequested.emit)

        layout.addWidget(self._star)
        layout.addLayout(side, 1)
        layout.addWidget(self._copy)
        layout.addWidget(self._delete)

    def _display_text(self) -> str:
        if not self._masked:
            return self._entry.password
        bullets = "•" * min(len(self._entry.password), 24)
        return f"{bullets}  ({len(self._entry.password)})"

    def _meta_text(self) -> str:
        from ..core.strength import CrackScenario, crack_time

        when = time.strftime("%d.%m.%Y %H:%M", time.localtime(self._entry.created_at))
        bits = self._entry.bits
        tr = self._tr
        if not bits or tr is None:
            return when
        estimate = format_duration(crack_time(bits, CrackScenario.OFFLINE_FAST_HASH), tr)
        return f"{when} · {tr.get('strength.bits', bits=round(bits))} · {estimate}"

    def set_masked(self, masked: bool) -> None:
        self._masked = masked
        self._text.setText(self._display_text())

    def entry(self):
        return self._entry

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover = False
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_q("#1A1A1A"))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)
        if self._hover:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(_q(PALETTE.field_border, 1.0), 1))
            painter.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 12, 12)
        painter.end()


class Segmented(QWidget):
    """Two-state segmented switch (История / Избранное)."""

    changed = Signal(int)

    def __init__(self, labels: tuple[str, str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Segmented")
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self._buttons: list[QPushButton] = []
        for index, label in enumerate(labels):
            button = QPushButton(label, self)
            button.setObjectName("Segment")
            button.setCheckable(True)
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.clicked.connect(lambda _=False, i=index: self.set_index(i, emit=True))
            layout.addWidget(button)
            self._buttons.append(button)
        self.set_index(0)

    def set_index(self, index: int, emit: bool = False) -> None:
        index = 0 if index >= len(self._buttons) else max(0, index)
        for position, button in enumerate(self._buttons):
            button.setChecked(position == index)
        self._index = index
        if emit:
            self.changed.emit(index)

    def index(self) -> int:
        return getattr(self, "_index", 0)

    def set_labels(self, first: str, second: str) -> None:
        self._buttons[0].setText(first)
        self._buttons[1].setText(second)


class Toast(QLabel):
    """Small floating notification shown at the bottom of the window."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setVisible(False)
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(160)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

    def show_message(self, text: str, icon_name: str | None = None) -> None:
        self.setText(text)
        self.adjustSize()
        self.setFixedWidth(max(180, self.sizeHint().width()))
        self.setFixedHeight(44)
        parent = self.parentWidget()
        if parent:
            x = (parent.width() - self.width()) // 2
            y = parent.height() - self.height() - 34
            self.move(x, y)
        self.raise_()
        self._timer.stop()
        self._anim.stop()
        self.setVisible(True)
        self._effect.setOpacity(0.0)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(1500)

    def _fade_out(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        try:
            self._anim.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._anim.finished.connect(lambda: self.setVisible(False))
        self._anim.start()


class CardWithHeader(Card):
    """Card with a title on the left and an action row on the right."""

    def __init__(self, title: str, parent: QWidget | None = None, padding: int = 28) -> None:
        super().__init__(parent, padding=padding)
        self.header = QHBoxLayout()
        self.header.setContentsMargins(0, 0, 0, 0)
        self.title = QLabel(title)
        self.title.setObjectName("CardTitle")
        self.title.setFont(sans_font(17, QFont.Weight.Medium))
        self.header.addWidget(self.title)
        self.header.addStretch(1)
        self._layout.addLayout(self.header)