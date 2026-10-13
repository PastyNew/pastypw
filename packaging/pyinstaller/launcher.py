"""Entry point used by PyInstaller (both Linux and Windows specs).

The application itself lives in the ``pastypw`` package; this tiny script
avoids running ``python -m pastypw`` semantics inside the frozen binary.
"""

from __future__ import annotations

import multiprocessing
import sys

from pastypw.app import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())