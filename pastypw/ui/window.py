"""Main application window of PastyNew Password Generator.

Creator: PastyNew
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QKeySequence,
    QPainter,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizeGrip,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..core.generator import PasswordError, PasswordOptions, generate_many
from ..core.storage import Entry, Storage
from ..core.strength import CrackScenario, crack_time, rate_pool
from . import icons
from .i18n import RU, Translator, format_duration
from .theme import PALETTE, STRENGTH_COLORS, mono_font, sans_font
from .titlebar import TitleBar
from .widgets import (
    Card,
    CardWithHeader,
    CheckRow,
    HistoryRow,
    IconButton,
    NumberField,
    PasswordRow,
    PlainScrollArea,
    Segmented,
    Slider,
    StrengthMeter,
    Toast,
)

MAX_BATCH = 50
MIN_LENGTH = 4
MAX_LENGTH = 64

# Transparent padding around the window plate, used to draw a soft shadow.
SHADOW_PAD = 46
WINDOW_RADIUS = 18


@dataclass
class SliderRow:
    """A titled slider with a numeric field next to it."""

    key: str
    label: QLabel
    slider: Slider
    number: NumberField

    def retranslate(self, tr: Translator) -> None:
        text = tr.get(self.key)
        self.label.setText(text)
        self.number.setToolTip(text)


class MainWindow(QWidget):
    """Frameless, rounded, dark window with the full generator workflow."""

    def __init__(self, storage: Storage | None = None, language: str = RU) -> None:
        super().__init__()
        self.tr_strings = Translator(language)
        # NB: Storage implements __len__, so "storage or Storage()" would
        # silently build a second store - always compare against None.
        self.storage = storage if storage is not None else Storage()
        self._settings = self.storage.load_settings()
        self._dragging = False
        self._passwords: list[str] = []
        self._masked = bool(self._settings.get("masked", True))
        self._history_tab = 0
        self._bits = 0.0
        self._slider_rows: list[SliderRow] = []
        self._shadow: QPixmap | None = None

        self.tr_strings.set_language(str(self._settings.get("language", language)))

        self.setWindowTitle(f"PastyNew — {self.tr_strings.get('app.title')}")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(icons.app_icon(256))
        self.setMinimumSize(QSize(660, 680))
        self.resize(QSize(1060, 920))

        self._build()
        self._apply_settings()
        self._retranslate()
        self._install_shortcuts()
        self.generate()

    # =================================================================== UI
    def _build(self) -> None:
        self.setObjectName("Root")

        root = QVBoxLayout(self)
        root.setContentsMargins(SHADOW_PAD, SHADOW_PAD, SHADOW_PAD, SHADOW_PAD)
        root.setSpacing(0)

        self.titlebar = TitleBar(
            self.tr_strings.get("app.title"),
            self.tr_strings.language.upper(),
            self,
        )
        self.titlebar.minimizeRequested.connect(self.showMinimized)
        self.titlebar.closeRequested.connect(self.close)
        self.titlebar.languageToggled.connect(self.toggle_language)
        root.addWidget(self.titlebar)

        self.toast = Toast(self)

        scroll = QScrollArea(self)
        scroll.setObjectName("Body")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)
        self.scroll = scroll

        content = QWidget()
        scroll.setWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(46, 38, 46, 24)
        outer.setSpacing(20)

        outer.addLayout(self._build_password_row())
        outer.addWidget(self._build_strength())
        outer.addWidget(self._build_generate_button())
        outer.addWidget(self._build_options_card())
        outer.addWidget(self._build_batch_card())
        outer.addWidget(self._build_history_card())
        outer.addLayout(self._build_footer())

    def _build_password_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)

        self.password_field = QLineEdit(self)
        self.password_field.setObjectName("PasswordField")
        self.password_field.setReadOnly(True)
        self.password_field.setFont(mono_font(26))
        self.password_field.setCursor(Qt.CursorShape.IBeamCursor)
        self.password_field.setMinimumHeight(76)
        row.addWidget(self.password_field, 1)

        self.copy_button = QPushButton(self)
        self.copy_button.setObjectName("CopyButton")
        self.copy_button.setFixedSize(76, 76)
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setIcon(icons.render("copy", 24, PALETTE.text_dim))
        self.copy_button.setIconSize(QSize(24, 24))
        self.copy_button.clicked.connect(self.copy_current)
        row.addWidget(self.copy_button)
        return row

    def _build_strength(self) -> QWidget:
        self.strength = StrengthMeter(self)
        return self.strength

    def _build_generate_button(self) -> QWidget:
        self.generate_button = QPushButton(self)
        self.generate_button.setObjectName("GenerateButton")
        self.generate_button.setFixedHeight(64)
        self.generate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_button.setIcon(icons.render("refresh", 21, "#FFFFFF"))
        self.generate_button.setIconSize(QSize(21, 21))
        self.generate_button.clicked.connect(self.generate)
        return self.generate_button

    def _build_options_card(self) -> QWidget:
        card = Card(self, padding=30)
        body = card.body()
        body.setSpacing(16)

        length_row = self._make_slider_row(
            "option.length", MIN_LENGTH, MAX_LENGTH, int(self._settings.get("length", 16))
        )
        amount_row = self._make_slider_row(
            "option.amount", 1, MAX_BATCH, int(self._settings.get("amount", 1))
        )
        body.addLayout(length_row.layout)
        body.addLayout(amount_row.layout)
        self._length_row = length_row
        self._amount_row = amount_row

        self.check_digits = CheckRow("", bool(self._settings.get("use_digits", True)))
        self.check_upper = CheckRow("", bool(self._settings.get("use_uppercase", True)))
        self.check_lower = CheckRow("", bool(self._settings.get("use_lowercase", True)))
        self.check_symbols = CheckRow("", bool(self._settings.get("use_symbols", True)))
        self._check_rows = [self.check_digits, self.check_upper, self.check_lower, self.check_symbols]
        for row in self._check_rows:
            row.toggled.connect(self._on_options_changed)
            body.addWidget(row)

        self.options_warning = QLabel("")
        self.options_warning.setStyleSheet(f"color:{PALETTE.danger};font-size:14px;")
        self.options_warning.setVisible(False)
        body.addWidget(self.options_warning)
        return card

    def _make_slider_row(self, key: str, minimum: int, maximum: int, value: int) -> SliderRow:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        label = QLabel("")
        label.setObjectName("CardTitle")
        label.setFont(sans_font(17, QFont.Weight.Medium))
        header.addWidget(label)
        header.addStretch(1)

        number = NumberField(minimum, maximum, value)
        header.addWidget(number)
        layout.addLayout(header)

        slider = Slider(minimum, maximum)
        slider.setValue(value)
        layout.addWidget(slider)

        row = SliderRow(key=key, label=label, slider=slider, number=number)
        row.layout = layout  # type: ignore[attr-defined]
        self._slider_rows.append(row)

        slider.valueChanged.connect(lambda v, n=number: self._sync(n, v))
        number.valueChanged.connect(lambda v, s=slider: self._sync(s, v))
        return row

    @staticmethod
    def _sync(companion: Slider | NumberField, value: int) -> None:
        """Keep a slider and its number field in sync without signal loops."""
        if companion.value() == value:
            return
        companion.blockSignals(True)
        if isinstance(companion, NumberField):
            companion.set_value(value)
        else:
            companion.setValue(value)
        companion.blockSignals(False)

    def _build_batch_card(self) -> QWidget:
        card = CardWithHeader("", self, padding=26)
        card.title.setFont(sans_font(16, QFont.Weight.Medium))

        self.batch_copy_all = IconButton("copy", "", 36, 17)
        self.batch_copy_all.clicked.connect(self.copy_all)
        self.batch_export = IconButton("download", "", 36, 17)
        self.batch_export.clicked.connect(self.export_batch)
        card.header.addWidget(self.batch_copy_all)
        card.header.addWidget(self.batch_export)

        scroll = PlainScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(256)  # four 58 px rows + gaps, nothing cut in half
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)
        scroll.setWidget(container)

        card.body().addWidget(scroll)
        self.batch_card = card
        self.batch_scroll = scroll
        self.batch_layout = layout
        self.batch_container = container
        card.setVisible(False)
        return card

    def _build_history_card(self) -> QWidget:
        card = CardWithHeader("", self, padding=26)
        card.title.setFont(sans_font(16, QFont.Weight.Medium))

        self.segment = Segmented(("History", "Favourites"))
        self.segment.changed.connect(self._on_tab_changed)
        card.header.addWidget(self.segment)

        self.reveal_button = IconButton("eye", "", 36, 17)
        self.reveal_button.setCheckable(True)
        self.reveal_button.clicked.connect(self._toggle_mask)
        self.history_export = IconButton("download", "", 36, 17)
        self.history_export.clicked.connect(self.export_history)
        self.history_clear = IconButton("trash", "", 36, 17, color="#6E6E6E")
        self.history_clear.clicked.connect(self.clear_history)
        for button in (self.reveal_button, self.history_export, self.history_clear):
            card.header.addWidget(button)

        scroll = PlainScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setMaximumHeight(216)  # three 64 px rows + gaps
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)
        scroll.setWidget(container)

        self.history_empty = QLabel("")
        self.history_empty.setStyleSheet(f"color:{PALETTE.text_muted};font-size:14px;")
        self.history_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_empty.setWordWrap(True)

        body = card.body()
        body.setSpacing(12)
        body.addWidget(scroll)
        body.addWidget(self.history_empty)

        self.history_card = card
        self.history_scroll = scroll
        self.history_layout = layout
        self.history_empty_label = self.history_empty
        return card

    # =============================================================== painting
    def content_height(self) -> int:
        """Window height that shows the whole body without scrolling."""
        content = self.scroll.widget()
        if content is None:
            return self.height()
        return content.sizeHint().height() + self.titlebar.height() + 2 * SHADOW_PAD + 26

    def _plate_rect(self) -> QRectF:
        return QRectF(
            SHADOW_PAD,
            SHADOW_PAD,
            max(1, self.width() - 2 * SHADOW_PAD),
            max(1, self.height() - 2 * SHADOW_PAD),
        )

    def _make_shadow(self) -> QPixmap:
        """Soft drop shadow rendered once per resize (cheap, cached)."""
        ratio = self.devicePixelRatioF()
        pm = QPixmap(self.size())
        pm.setDevicePixelRatio(ratio)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(ratio, ratio)
        rect = self._plate_rect()
        steps = 24
        for index in range(steps, 0, -1):
            ratio_step = index / steps
            grow = ratio_step * SHADOW_PAD
            alpha = int(38 * (1.0 - ratio_step) ** 2.2) + 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(
                rect.adjusted(-grow, -grow, grow, grow),
                WINDOW_RADIUS + grow,
                WINDOW_RADIUS + grow,
            )
        painter.end()
        return pm

    def paintEvent(self, event) -> None:  # noqa: N802
        if self._shadow is None or self._shadow.size() != self.size():
            self._shadow = self._make_shadow()
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._shadow)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._plate_rect()
        painter.setBrush(QColor(PALETTE.window))
        painter.setPen(QPen(QColor(PALETTE.card_border), 1))
        painter.drawRoundedRect(
            rect.adjusted(0.5, 0.5, -0.5, -0.5), WINDOW_RADIUS, WINDOW_RADIUS
        )
        painter.end()

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._shadow = None
        super().resizeEvent(event)

    def _build_footer(self) -> QHBoxLayout:
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 0, 0, 0)

        self.footer_credit = QLabel("")
        self.footer_credit.setStyleSheet(f"color:{PALETTE.text_muted};font-size:13px;")
        footer.addWidget(self.footer_credit)

        self.footer_info = QLabel("")
        self.footer_info.setStyleSheet(f"color:{PALETTE.text_muted};font-size:13px;")
        footer.addStretch(1)
        footer.addWidget(self.footer_info)

        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        footer.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom)
        return footer

    # ============================================================== options
    @property
    def options(self) -> PasswordOptions:
        return PasswordOptions(
            length=self._length_row.slider.value(),
            use_digits=self.check_digits.isChecked(),
            use_uppercase=self.check_upper.isChecked(),
            use_lowercase=self.check_lower.isChecked(),
            use_symbols=self.check_symbols.isChecked(),
        )

    @property
    def amount(self) -> int:
        return self._amount_row.slider.value()

    def _on_options_changed(self, *_args) -> None:
        enabled = bool(self.options.char_classes)
        self.options_warning.setVisible(not enabled)
        self.generate_button.setEnabled(enabled)
        self._refresh_strength()
        self._save_settings()

    # ============================================================== actions
    def generate(self) -> None:
        options = self.options
        if not options.can_generate:
            return
        try:
            self._passwords = generate_many(options, self.amount)
        except PasswordError:
            return

        self.password_field.setText(self._passwords[0])
        self.password_field.setCursorPosition(0)
        self._refresh_strength(options)
        self._render_batch()
        for password in self._passwords:
            self.storage.add(password, bits=self._bits)
        self._render_history()
        self._save_settings()

    def _refresh_strength(self, options: PasswordOptions | None = None) -> None:
        options = options or self.options
        if not options.can_generate:
            self.strength.clear(PALETTE.danger)
            self._bits = 0.0
            return

        tr = self.tr_strings
        bits = options.length * math.log2(max(2, len(options.alphabet)))
        self._bits = bits
        rating = rate_pool(bits)
        seconds = crack_time(bits, CrackScenario.OFFLINE_FAST_HASH)
        self.strength.set_strength(
            percent=rating.percent,
            color=STRENGTH_COLORS[rating.color_key],
            rating_text=tr.get(rating.label_key),
            bits_text=tr.get("strength.bits", bits=round(bits)),
            crack_text=format_duration(seconds, tr),
        )

    def _render_batch(self) -> None:
        _clear_layout(self.batch_layout)
        visible = self.amount > 1
        self.batch_card.setVisible(visible)
        if not visible:
            return
        self.batch_card.title.setText(
            self.tr_strings.get("list.title", n=len(self._passwords))
        )
        for index, password in enumerate(self._passwords, start=1):
            row = PasswordRow(password, index)
            row.copyRequested.connect(lambda p=password: self._copy_text(p))
            self.batch_layout.addWidget(row)

    def _render_history(self) -> None:
        _clear_layout(self.history_layout)
        entries = self.storage.entries(favorites_only=self._history_tab == 1)
        for entry in entries:
            row = HistoryRow(entry, masked=self._masked, tr=self.tr_strings)
            row.copyRequested.connect(lambda e=entry: self._copy_text(e.password))
            row.favoriteToggled.connect(lambda e=entry: self._toggle_favorite(e))
            row.deleteRequested.connect(lambda e=entry: self._delete_entry(e))
            self.history_layout.addWidget(row)

        has_entries = bool(entries)
        self.history_empty_label.setVisible(not has_entries)
        self.history_empty_label.setText(
            self.tr_strings.get(
                "history.empty_fav" if self._history_tab else "history.empty"
            )
        )
        self.history_clear.setEnabled(has_entries or self._history_tab == 1)
        self.history_export.setEnabled(has_entries)
        self.reveal_button.setEnabled(has_entries)

    # ------------------------------------------------------------ clipboard
    def _copy_text(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)
        self.toast.show_message(self.tr_strings.get("action.copied"))

    def copy_current(self) -> None:
        text = self.password_field.text()
        if text:
            self._copy_text(text)

    def copy_all(self) -> None:
        if self._passwords:
            self._copy_text("\n".join(self._passwords))

    # -------------------------------------------------------------- history
    def _toggle_favorite(self, entry: Entry) -> None:
        updated = self.storage.toggle_favorite(entry.id)
        if updated is not None:
            self.toast.show_message(
                self.tr_strings.get(
                    "toast.favorite_removed" if not updated.favorite else "toast.favorite_added"
                )
            )
        self._render_history()

    def _delete_entry(self, entry: Entry) -> None:
        self.storage.remove(entry.id)
        self.toast.show_message(self.tr_strings.get("toast.deleted"))
        self._render_history()

    def clear_history(self) -> None:
        self.storage.clear(favorites_only=self._history_tab == 1)
        self._render_history()
        self.toast.show_message(
            self.tr_strings.get(
                "history.cleared_fav" if self._history_tab else "history.cleared"
            )
        )

    def _on_tab_changed(self, index: int) -> None:
        self._history_tab = index
        self._render_history()

    def _toggle_mask(self) -> None:
        self._masked = not self._masked
        self.reveal_button.set_icon_name("eye" if self._masked else "eye_off")
        self.reveal_button.setChecked(not self._masked)
        for index in range(self.history_layout.count()):
            widget = self.history_layout.itemAt(index).widget()
            if isinstance(widget, HistoryRow):
                widget.set_masked(self._masked)
        self._save_settings()

    # --------------------------------------------------------------- export
    def _default_export_name(self) -> str:
        return str(Path.home() / f"pastypw_{time.strftime('%Y%m%d_%H%M%S')}.txt")

    def _ask_export_path(self) -> str:
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr_strings.get("action.export"),
            self._default_export_name(),
            "Text files (*.txt);;All files (*)",
        )
        return path

    def export_batch(self) -> None:
        if not self._passwords:
            return
        path = self._ask_export_path()
        if not path:
            return
        Path(path).write_text("\n".join(self._passwords) + "\n", encoding="utf-8")
        self.toast.show_message(self.tr_strings.get("toast.exported"))

    def export_history(self) -> None:
        entries = self.storage.entries(favorites_only=self._history_tab == 1)
        if not entries:
            return
        path = self._ask_export_path()
        if not path:
            return
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        header = [
            f"# PastyNew Password Generator ({self.tr_strings.language})",
            f"# {stamp}",
            "",
        ]
        lines = [
            f"{'*' if entry.favorite else ' '} {entry.password}"
            f"  ({time.strftime('%Y-%m-%d %H:%M', time.localtime(entry.created_at))})"
            for entry in entries
        ]
        Path(path).write_text("\n".join(header + lines) + "\n", encoding="utf-8")
        self.toast.show_message(self.tr_strings.get("toast.exported"))

    # ----------------------------------------------------------------- i18n
    def toggle_language(self) -> None:
        self.tr_strings.toggle()
        self._retranslate()
        self._save_settings()

    def _retranslate(self) -> None:
        tr = self.tr_strings
        self.setWindowTitle(f"PastyNew — {tr.get('app.title')}")
        self.titlebar.set_title(tr.get("app.title"))
        self.titlebar.set_language_label(tr.language.upper(), "Русский / English")
        self.titlebar.set_tooltips(tr.get("action.minimize"), tr.get("action.close"))

        self.copy_button.setToolTip(f"{tr.get('action.copy')}  (Ctrl+C)")
        self.generate_button.setText(f"  {tr.get('action.generate')}")
        self.batch_copy_all.setToolTip(tr.get("action.copy_all"))
        self.batch_export.setToolTip(tr.get("action.export"))
        self.reveal_button.setToolTip(
            tr.get("action.reveal") if self._masked else tr.get("action.hide")
        )
        self.history_export.setToolTip(tr.get("action.export"))
        self.history_clear.setToolTip(tr.get("action.clear"))

        for row in self._slider_rows:
            row.retranslate(tr)

        self.check_digits.setText(tr.get("option.digits"))
        self.check_upper.setText(tr.get("option.uppercase"))
        self.check_lower.setText(tr.get("option.lowercase"))
        self.check_symbols.setText(tr.get("option.symbols"))
        self.options_warning.setText(tr.get("option.warning"))

        self.segment.set_labels(tr.get("history.title"), tr.get("history.favorites"))
        self.history_card.title.setText(tr.get("history.title"))
        self.footer_credit.setText(tr.get("footer.made_by"))
        self.footer_info.setText(tr.get("footer.offline", version=__version__))

        self._refresh_strength()
        self._render_batch()
        self._render_history()

    # ---------------------------------------------------------- persistence
    def _apply_settings(self) -> None:
        self.reveal_button.set_icon_name("eye" if self._masked else "eye_off")
        self.reveal_button.setChecked(not self._masked)

    def _save_settings(self) -> None:
        options = self.options
        self.storage.save_settings(
            {
                "length": options.length,
                "amount": self.amount,
                "use_digits": options.use_digits,
                "use_uppercase": options.use_uppercase,
                "use_lowercase": options.use_lowercase,
                "use_symbols": options.use_symbols,
                "language": self.tr_strings.language,
                "masked": self._masked,
            }
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_settings()
        super().closeEvent(event)

    # ------------------------------------------------------------ shortcuts
    def _install_shortcuts(self) -> None:
        bindings = {
            "Ctrl+G": self.generate,
            "Ctrl+C": self.copy_current,
            "Ctrl+L": self.toggle_language,
            "Ctrl+E": self.export_batch,
        }
        for sequence, slot in bindings.items():
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.activated.connect(slot)

    # -------------------------------------------------------------- events
    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.copy_current()


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()