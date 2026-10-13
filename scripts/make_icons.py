#!/usr/bin/env python3
"""Export application icons (SVG + PNG) used by the packages and the README.

    python scripts/make_icons.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSize, Qt  # noqa: E402
from PySide6.QtGui import QIcon, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pastypw.ui import icons  # noqa: E402

OUT = ROOT / "build" / "icons"
SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def save_png(icon: QIcon, size: int, path: Path) -> None:
    """Render the icon into a PNG file of exactly ``size`` x ``size``."""
    image = icon.pixmap(QSize(size, size)).toImage()
    if image.isNull():  # platform without pixmap support
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        renderer = QSvgRenderer(
            (OUT / "pastypw.svg").read_bytes() if (OUT / "pastypw.svg").exists()
            else b""
        )
        if renderer.isValid():
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
    image.save(str(path), "PNG")


def main() -> int:
    app = QApplication(sys.argv[:1])
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. the application icon in every size
    for size in SIZES:
        save_png(icons.app_icon(size), size, OUT / f"pastypw-{size}.png")
    icons.app_icon(512).pixmap(QSize(512, 512)).save(str(OUT / "pastypw.png"), "PNG")

    # 2. plain SVG sources for the packaging scripts
    lock_body = icons.svg_source("lock")
    lock_body = lock_body[lock_body.index(">") + 1 : lock_body.rindex("</svg>")]
    (OUT / "pastypw.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512"'
        ' height="512">'
        '<rect x="0" y="0" width="512" height="512" rx="112" ry="112" fill="#6366F1"/>'
        f'<g transform="translate(118 118) scale(11.5)" fill="none" stroke="#FFFFFF"'
        f' stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{lock_body}</g>'
        "</svg>",
        encoding="utf-8",
    )
    (OUT / "pastypw-monochrome.svg").write_text(
        icons.svg_document("lock", "#FFFFFF"), encoding="utf-8"
    )

    print(f"icons written to {OUT.relative_to(ROOT)}:")
    for item in sorted(OUT.iterdir()):
        print(f"  {item.name:28s} {item.stat().st_size:>8d} B")
    _ = app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())