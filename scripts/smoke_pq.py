#!/usr/bin/env python3
"""PQ-only vault smoke — safe to run; no pip, no tier6/liboqs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from christman_crypto.postquantum import HybridPQCipher  # noqa: E402


def main() -> int:
    pq = HybridPQCipher(768)
    ek, dk = pq.keygen()
    bundle = pq.encrypt(ek, b"smoke")
    if pq.decrypt(dk, bundle) != b"smoke":
        print("FAIL: PQ round-trip")
        return 1
    print("PQ OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())