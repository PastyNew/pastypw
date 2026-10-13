#!/usr/bin/env python3
"""Render the screenshots used in README.md / README.en.md.

Runs completely headless (Qt ``offscreen`` platform), so it works on a build
server as well:

    QT_QPA_PLATFORM=offscreen python scripts/render_screenshots.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QRectF  # noqa: E402
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter  # noqa: E402

from pastypw.app import create_app  # noqa: E402
from pastypw.core.generator import PasswordOptions, generate_many  # noqa: E402
from pastypw.core.storage import Storage  # noqa: E402
from pastypw.ui.window import MainWindow  # noqa: E402

OUT_DIR = ROOT / "docs" / "images"
SANDBOX = ROOT / "build" / "screenshot-sandbox"
MARGIN = 36


def _fresh_storage() -> Storage:
    data = SANDBOX / "data"
    config = SANDBOX / "config"
    for folder in (data, config):
        folder.mkdir(parents=True, exist_ok=True)
    return Storage(data_dir=data, config_dir=config)


def _seed_history(storage: Storage, amount: int = 7) -> None:
    """Fill the history card with plausible entries."""
    specs = [
        (16, dict(use_symbols=True)),
        (24, dict(use_symbols=True)),
        (12, dict(use_symbols=False, use_uppercase=False)),
        (20, dict(use_symbols=False)),
        (32, dict(use_symbols=True)),
        (10, dict(use_symbols=False, use_uppercase=False)),
        (18, dict(use_symbols=True)),
    ]
    for offset, (length, flags) in enumerate(specs[:amount]):
        options = PasswordOptions(length=length, use_digits=True, use_lowercase=True, **flags)
        entry = storage.add(generate_many(options, 1)[0], bits=round(length * 6.55, 1))
        entry.created_at = time.time() - offset * 3600 * 7
    storage._save_entries(storage._load_entries())


def _settle(app, seconds: float = 0.45) -> None:
    """Let animations (slider, strength bar, check marks) finish."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()


def _shot(app, window: MainWindow, name: str) -> Path:
    _settle(app)
    height = window.content_height()
    window.resize(1060, height)
    _settle(app)
    window.resize(1060, window.content_height())
    _settle(app, 0.2)

    pixmap = window.grab()
    image = QImage(pixmap.toImage())

    backdrop = QImage(image.width() + 2 * MARGIN, image.height() + 2 * MARGIN,
                      QImage.Format.Format_ARGB32)
    backdrop.fill(QColor("#0A0A0C"))
    painter = QPainter(backdrop)
    gradient = QLinearGradient(0, 0, 0, backdrop.height())
    gradient.setColorAt(0.0, QColor("#141419"))
    gradient.setColorAt(1.0, QColor("#08080A"))
    painter.fillRect(QRectF(0, 0, backdrop.width(), backdrop.height()), gradient)
    painter.drawPixmap(MARGIN, MARGIN, pixmap)
    painter.end()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    backdrop.save(str(path))
    print(f"  {path.relative_to(ROOT)}  {backdrop.width()}x{backdrop.height()}")
    return path


def main() -> int:
    app = create_app([sys.argv[0]])
    storage = _fresh_storage()
    storage.clear()
    _seed_history(storage)

    window = MainWindow(storage=storage, language="ru")
    window.show()
    _settle(app)
    storage.clear()
    window._render_history()
    print("rendering screenshots:")

    # 1. main window, Russian, single password, empty history
    window._amount_row.slider.setValue(1)
    window.generate()
    _shot(app, window, "main-ru.png")

    # 2. batch of five + history
    window._amount_row.slider.setValue(5)
    window.generate()
    _seed_history(storage)
    window._render_history()
    _shot(app, window, "batch-and-history-ru.png")

    # 3. English interface, revealed history
    window.tr_strings.set_language("en")
    window._retranslate()
    window._amount_row.slider.setValue(1)
    window.generate()
    if window._masked:
        window._toggle_mask()
    _shot(app, window, "main-en.png")

    # 4. compact window (minimum useful size)
    window.tr_strings.set_language("ru")
    window._retranslate()
    if not window._masked:
        window._toggle_mask()
    window._amount_row.slider.setValue(3)
    window.generate()
    window.resize(700, 980)
    _settle(app)
    pixmap = window.grab()
    image = QImage(pixmap.toImage())
    backdrop = QImage(image.width() + 2 * MARGIN, image.height() + 2 * MARGIN,
                      QImage.Format.Format_ARGB32)
    backdrop.fill(QColor("#0A0A0C"))
    painter = QPainter(backdrop)
    painter.drawPixmap(MARGIN, MARGIN, pixmap)
    painter.end()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backdrop.save(str(OUT_DIR / "compact.png"))
    print(f"  docs/images/compact.png  {backdrop.width()}x{backdrop.height()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())