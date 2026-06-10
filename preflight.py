#!/usr/bin/env python3
"""Başlamadan önce kamera, Arduino ve Python paketlerini kontrol eder."""
from __future__ import annotations

import os
import sys

from src.utils import check_arduino, check_cameras, check_imports


def main() -> int:
    print("=== Ön kontrol ===\n")
    check_imports()
    print("  Paketler .............. OK")

    if os.environ.get("DROWSINESS_SKIP_CAMERA_PREFLIGHT", "").strip() == "1":
        print("  Kameralar ............. ATLANDI  seçili indeks doğrudan açılacak")
    else:
        cameras = check_cameras()
        if cameras:
            print(f"  Kameralar ............. OK  indeksler {cameras}")
        else:
            print("  Kameralar ............. UYARI  hiç kamera yok")
            return 1

    if os.environ.get("DROWSINESS_SKIP_ARDUINO", "").strip() == "1":
        print("  Arduino ............... ATLANDI  DROWSINESS_SKIP_ARDUINO=1")
    else:
        port = check_arduino()
        if port:
            print(f"  Arduino ............... OK  {port}")
        else:
            print("  Arduino ............... UYARI  port yok (DROWSINESS_SKIP_ARDUINO=1 ile atlanabilir)")
            return 1

    print("\nHazır. Çalıştır: ./run.sh\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
