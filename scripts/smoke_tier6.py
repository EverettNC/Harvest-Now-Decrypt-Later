#!/usr/bin/env python3
"""Tier 6 hybrid smoke — optional; needs liboqs-python in env."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from christman_crypto.tiers.tier6_signatures import HybridSigner  # noqa: E402


def main() -> int:
    signer = HybridSigner(use_pq=True)
    sig = signer.sign(b"smoke")
    ok = signer.verify(
        b"smoke",
        sig,
        signer.classic.export_public_pem(),
        signer._pq_pk,
    )
    if not ok:
        print("FAIL: tier6 verify")
        return 1
    print("Tier6 hybrid OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())