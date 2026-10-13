#!/usr/bin/env python3
"""Export a Windows .ico file (used by the .exe build and by the installer).

Only the standard library plus PySide6 (for rendering) are needed:

    python scripts/make_windows_icon.py

Windows 10/11 accept PNG-compressed ICO entries, so the frames are embedded
as PNG - the file stays small and keeps crisp edges on high-DPI screens.
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtGui import QImage  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from pastypw.ui import icons  # noqa: E402

OUT_DIR = ROOT / "build" / "icons"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def png_frame(size: int, directory: Path) -> bytes:
    image = icons.app_icon(size).pixmap(QSize(size, size)).toImage()
    if image.isNull():
        image = QImage(size, size, QImage.Format.Format_ARGB32)
    target = directory / f"pastypw-{size}.png"
    if not image.save(str(target), "PNG"):
        raise SystemExit(f"error: cannot write {target}")
    return target.read_bytes()


def write_ico(frames: list[tuple[int, bytes]], path: Path) -> None:
    offset = 6 + 16 * len(frames)
    header = struct.pack("<HHH", 0, 1, len(frames))
    entries = b""
    payload = b""
    for size, data in frames:
        entries += struct.pack(
            "<BBBBHHII",
            0 if size >= 256 else size,
            0 if size >= 256 else size,
            0,          # palette
            0,          # reserved
            1,          # colour planes
            32,         # bits per pixel
            len(data),
            offset,
        )
        payload += data
        offset += len(data)
    path.write_bytes(header + entries + payload)


def main() -> int:
    app = QApplication(sys.argv[:1])
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        frames = [(size, png_frame(size, directory)) for size in SIZES]

    ico_path = OUT_DIR / "pastypw.ico"
    write_ico(frames, ico_path)

    print(f"  {str(ico_path.relative_to(ROOT)):28s} {ico_path.stat().st_size:>8d} B "
          f"({len(frames)} размеров: {', '.join(str(s) for s in SIZES)})")
    _ = app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())