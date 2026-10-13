"""Application bootstrap: high-DPI setup, stylesheet, main window.

Creator: PastyNew
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from .core.storage import Storage
from .ui import icons
from .ui.i18n import RU
from .ui.theme import stylesheet
from .ui.window import MainWindow

APP_ID = "io.github.pastypw.generator"


def apply_dark_palette(app: QApplication) -> None:
    """Make the whole Fusion palette dark, not only the styled widgets."""
    from PySide6.QtGui import QPalette

    from .ui.theme import PALETTE

    palette = app.palette()
    roles = {
        QPalette.ColorRole.Window: PALETTE.window,
        QPalette.ColorRole.WindowText: PALETTE.text,
        QPalette.ColorRole.Base: PALETTE.window,
        QPalette.ColorRole.AlternateBase: PALETTE.card,
        QPalette.ColorRole.Text: PALETTE.text,
        QPalette.ColorRole.Button: PALETTE.field,
        QPalette.ColorRole.ButtonText: PALETTE.text,
        QPalette.ColorRole.BrightText: "#FF6B6B",
        QPalette.ColorRole.Highlight: PALETTE.accent,
        QPalette.ColorRole.HighlightedText: "#FFFFFF",
        QPalette.ColorRole.ToolTipBase: PALETTE.field,
        QPalette.ColorRole.ToolTipText: PALETTE.text,
        QPalette.ColorRole.PlaceholderText: PALETTE.text_muted,
        QPalette.ColorRole.Link: PALETTE.accent,
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    disabled = QPalette.ColorGroup.Disabled
    palette.setColor(disabled, QPalette.ColorRole.Text, QColor(PALETTE.text_muted))
    palette.setColor(disabled, QPalette.ColorRole.ButtonText, QColor(PALETTE.text_muted))
    app.setPalette(palette)


def create_app(argv: list[str] | None = None) -> QApplication:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("PastyNew Password Generator")
    app.setApplicationDisplayName("PastyNew Password Generator")
    app.setOrganizationName("PastyNew")
    app.setOrganizationDomain("github.com")
    app.setDesktopFileName("pastypw")
    app.setStyle("Fusion")
    app.setWindowIcon(icons.app_icon(256))

    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    apply_dark_palette(app)
    app.setStyleSheet(stylesheet())
    return app


def main(argv: list[str] | None = None) -> int:
    app = create_app(argv)
    storage = Storage()
    language = str(storage.load_settings().get("language", RU))
    window = MainWindow(storage=storage, language=language)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())