"""
christman_crypto — Full Seven-Tier + PQ Test Suite
===================================================
Run with:  python -m pytest tests/ -v
       or:  python tests/test_all_tiers.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from christman_crypto.tiers.tier1_vigenere   import VigenereCipher
from christman_crypto.tiers.tier2_aes        import AESCipher
from christman_crypto.tiers.tier3_chacha     import ChaChaCipher
from christman_crypto.tiers.tier4_rsa        import RSACipher
from christman_crypto.tiers.tier5_hybrid     import HybridCipher
from christman_crypto.tiers.tier6_signatures import DigitalSigner, HybridSigner
from christman_crypto.postquantum            import XChaCha20Cipher, MLKEM, HybridPQCipher
from christman_crypto.kyber                  import KyberHandshake

MSG   = b"The Christman AI Project - Protecting the vulnerable."
MSG_S = "The Christman AI Project"

# ── Tier 1 ────────────────────────────────────────────────────────────────────
def test_tier1_vigenere_roundtrip():
    v = VigenereCipher("CHRISTMAN")
    ct = v.encrypt(MSG_S)
    assert ct != MSG_S
    assert v.decrypt(ct) == MSG_S.upper()

def test_tier1_vigenere_george_loop():
    # George-loop means same key, different positions → non-repeating stream
    v = VigenereCipher("KEY")
    ct = v.encrypt("A" * 100)
    # Should NOT be all the same letter (loop is extending the key)
    assert len(set(ct)) > 1

# ── Tier 2 ────────────────────────────────────────────────────────────────────
def test_tier2_aes_roundtrip():
    a = AESCipher()
    ct = a.encrypt(MSG)
    assert a.decrypt(ct) == MSG

def test_tier2_aes_with_aad():
    a = AESCipher()
    ct = a.encrypt(MSG, aad=b"christman")
    assert a.decrypt(ct, aad=b"christman") == MSG

def test_tier2_aes_tamper_detected():
    a = AESCipher()
    ct = bytearray(a.encrypt(MSG))
    ct[20] ^= 0xFF
    with pytest.raises(Exception):
        a.decrypt(bytes(ct))

# ── Tier 3 ────────────────────────────────────────────────────────────────────
def test_tier3_chacha_roundtrip():
    c = ChaChaCipher()
    ct = c.encrypt(MSG)
    assert c.decrypt(ct) == MSG

def test_tier3_chacha_tamper_detected():
    c = ChaChaCipher()
    ct = bytearray(c.encrypt(MSG))
    ct[15] ^= 0xFF
    with pytest.raises(Exception):
        c.decrypt(bytes(ct))

# ── Tier 4 ────────────────────────────────────────────────────────────────────
def test_tier4_rsa_roundtrip():
    r = RSACipher.generate_keypair()
    ct = r.encrypt(b"short message")
    assert r.decrypt(ct) == b"short message"

def test_tier4_rsa_pem_export_import():
    r    = RSACipher.generate_keypair()
    pub  = r.export_public_pem()
    priv = r.export_private_pem()
    r2   = RSACipher.from_pem(private_pem=priv, public_pem=pub)
    ct   = r2.encrypt(b"round trip via PEM")
    assert r2.decrypt(ct) == b"round trip via PEM"

# ── Tier 5 ────────────────────────────────────────────────────────────────────
def test_tier5_hybrid_roundtrip():
    h  = HybridCipher.generate()
    ct = h.encrypt(MSG)
    assert h.decrypt(ct) == MSG

def test_tier5_hybrid_large_payload():
    h    = HybridCipher.generate()
    big  = b"X" * 100_000
    ct   = h.encrypt(big)
    assert h.decrypt(ct) == big

# ── Tier 6 ────────────────────────────────────────────────────────────────────
def test_tier6_sign_verify():
    s   = DigitalSigner.generate_keypair()
    sig = s.sign(MSG)
    assert s.verify(MSG, sig) is True

def test_tier6_tamper_detected():
    s   = DigitalSigner.generate_keypair()
    sig = s.sign(MSG)
    assert s.verify(b"tampered message", sig) is False

def test_tier6_pem_roundtrip():
    s    = DigitalSigner.generate_keypair()
    pub  = s.export_public_pem()
    sig  = s.sign(MSG)
    verifier = DigitalSigner.from_pem(public_pem=pub)
    assert verifier.verify(MSG, sig) is True

def _require_oqs():
    try:
        import oqs  # noqa: F401
    except ImportError:
        pytest.skip("liboqs-python not installed")

def test_tier6_hybrid_sign_verify():
    _require_oqs()
    s = HybridSigner(use_pq=True)
    sig = s.sign(MSG)
    assert s.verify(MSG, sig, s.classic.export_public_pem(), s._pq_pk) is True

def test_tier6_hybrid_tamper_detected():
    _require_oqs()
    s = HybridSigner(use_pq=True)
    sig = s.sign(MSG)
    assert s.verify(b"tampered message", sig, s.classic.export_public_pem(), s._pq_pk) is False

# ── XChaCha20 (PQ layer Module 1) ────────────────────────────────────────────
def test_xchacha20_roundtrip():
    x   = XChaCha20Cipher()
    key = x.generate_key()
    ct  = x.encrypt(key, MSG, aad=b"test")
    assert x.decrypt(key, ct, aad=b"test") == MSG

def test_xchacha20_tamper_detected():
    x   = XChaCha20Cipher()
    key = x.generate_key()
    ct  = bytearray(x.encrypt(key, MSG))
    ct[30] ^= 0xFF
    with pytest.raises(Exception):
        x.decrypt(key, bytes(ct))

# ── ML-KEM (PQ layer Module 2) ───────────────────────────────────────────────
@pytest.mark.parametrize("level", [512, 768, 1024])
def test_mlkem_roundtrip(level):
    kem = MLKEM(level)
    ek, dk = kem.keygen()
    ct, ss_sender = kem.encapsulate(ek)
    ss_receiver = kem.decapsulate(dk, ct)
    assert ss_sender == ss_receiver

@pytest.mark.parametrize("level", [512, 768, 1024])
def test_mlkem_implicit_rejection(level):
    kem = MLKEM(level)
    ek, dk = kem.keygen()
    ct, ss = kem.encapsulate(ek)
    bad_ct = bytes(b ^ 0xFF for b in ct)
    ss_bad = kem.decapsulate(dk, bad_ct)
    assert ss_bad != ss

# ── HybridPQCipher ───────────────────────────────────────────────────────────
def test_hybrid_pq_roundtrip():
    pq = HybridPQCipher(768)
    ek, dk = pq.keygen()
    bundle = pq.encrypt(ek, MSG)
    assert pq.decrypt(dk, bundle) == MSG

# ── KyberHandshake ───────────────────────────────────────────────────────────
def test_kyber_handshake():
    hs = KyberHandshake(768)
    ek, dk = hs.generate_keys()
    ss1, ct = hs.encapsulate(ek)
    ss2 = hs.decapsulate(dk, ct)
    assert ss1 == ss2

def test_kyber_session_key_derivation():
    hs = KyberHandshake(768)
    ek, dk = hs.generate_keys()
    ss, ct = hs.encapsulate(ek)
    key = hs.derive_session_key(ss, info=b"test-session")
    assert len(key) == 32

# ── run directly ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import time
    tests = [
        ("Tier 1 — Vigenère roundtrip",       test_tier1_vigenere_roundtrip),
        ("Tier 1 — George-loop",               test_tier1_vigenere_george_loop),
        ("Tier 2 — AES-256-GCM roundtrip",     test_tier2_aes_roundtrip),
        ("Tier 2 — AES AAD",                   test_tier2_aes_with_aad),
        ("Tier 2 — AES tamper detection",      test_tier2_aes_tamper_detected),
        ("Tier 3 — ChaCha20 roundtrip",        test_tier3_chacha_roundtrip),
        ("Tier 3 — ChaCha20 tamper detection", test_tier3_chacha_tamper_detected),
        ("Tier 4 — RSA-4096 roundtrip",        test_tier4_rsa_roundtrip),
        ("Tier 4 — RSA PEM export/import",     test_tier4_rsa_pem_export_import),
        ("Tier 5 — Hybrid RSA+AES roundtrip",  test_tier5_hybrid_roundtrip),
        ("Tier 5 — Hybrid 100KB payload",      test_tier5_hybrid_large_payload),
        ("Tier 6 — RSA-PSS sign/verify",       test_tier6_sign_verify),
        ("Tier 6 — RSA-PSS tamper detected",   test_tier6_tamper_detected),
        ("Tier 6 — RSA-PSS PEM roundtrip",     test_tier6_pem_roundtrip),
        ("Tier 6 — Hybrid PQ sign/verify",     test_tier6_hybrid_sign_verify),
        ("Tier 6 — Hybrid PQ tamper detected", test_tier6_hybrid_tamper_detected),
        ("PQ    — XChaCha20 roundtrip",        test_xchacha20_roundtrip),
        ("PQ    — XChaCha20 tamper detected",  test_xchacha20_tamper_detected),
        ("PQ    — ML-KEM-512",                 lambda: test_mlkem_roundtrip(512)),
        ("PQ    — ML-KEM-768",                 lambda: test_mlkem_roundtrip(768)),
        ("PQ    — ML-KEM-1024",               lambda: test_mlkem_roundtrip(1024)),
        ("PQ    — ML-KEM implicit rejection",  lambda: test_mlkem_implicit_rejection(768)),
        ("PQ    — HybridPQCipher roundtrip",   test_hybrid_pq_roundtrip),
        ("PQ    — KyberHandshake",             test_kyber_handshake),
        ("PQ    — Session key derivation",     test_kyber_session_key_derivation),
    ]

    print("\n" + "═" * 70)
    print("  christman_crypto — Full Test Suite")
    print("  The Christman AI Project")
    print("═" * 70)
    passed = failed = 0
    for name, fn in tests:
        t0 = time.perf_counter()
        try:
            fn()
            elapsed = time.perf_counter() - t0
            print(f"  ✓  {name:<45} {elapsed:.3f}s")
            passed += 1
        except Exception as e:
            print(f"  ✗  {name:<45} FAILED: {e}")
            failed += 1
    print("═" * 70)
    print(f"  {passed} passed  |  {failed} failed")
    print("═" * 70 + "\n")
    sys.exit(0 if failed == 0 else 1)
