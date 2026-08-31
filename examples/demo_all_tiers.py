"""
christman_crypto — Live Demo: All Seven Tiers + Post-Quantum
=============================================================
Run:  python examples/demo_all_tiers.py

Shows every tier encrypting and decrypting a real message,
with timing, key sizes, and bundle sizes printed for each.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from christman_crypto.tiers.tier1_vigenere   import VigenereCipher
from christman_crypto.tiers.tier2_aes        import AESCipher
from christman_crypto.tiers.tier3_chacha     import ChaChaCipher
from christman_crypto.tiers.tier4_rsa        import RSACipher
from christman_crypto.tiers.tier5_hybrid     import HybridCipher
from christman_crypto.tiers.tier6_signatures import DigitalSigner
from christman_crypto.postquantum            import XChaCha20Cipher, MLKEM, HybridPQCipher
from christman_crypto.kyber                  import KyberHandshake

LINE = "═" * 70
MSG  = b"Harvest Now, Decrypt Later -- The Christman AI Project."

def header(tier, name):
    print(f"\n{LINE}")
    print(f"  Tier {tier} — {name}")
    print(LINE)

def ok(label, value=""):
    print(f"  ✓  {label}{f': {value}' if value else ''}")

# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{LINE}")
print("  christman_crypto — Seven-Tier + Post-Quantum Demo")
print("  The Christman AI Project  |  Apache 2.0")
print(LINE)
print(f"  Message: {MSG.decode()}\n")

# ── TIER 1 ───────────────────────────────────────────────────────────────────
header(1, "LEGACY — Vigenère (George-loop enhanced)")
v  = VigenereCipher("CHRISTMAN")
ct = v.encrypt(MSG.decode())
pt = v.decrypt(ct)
ok("Encrypted", ct[:40] + "...")
ok("Decrypted", pt[:40] + "...")
ok("George-loop key extension active — period = message length")

# ── TIER 2 ───────────────────────────────────────────────────────────────────
header(2, "SYMMETRIC — AES-256-GCM")
t0  = time.perf_counter()
a   = AESCipher()
ct  = a.encrypt(MSG, aad=b"christman-demo")
pt  = a.decrypt(ct,  aad=b"christman-demo")
elapsed = time.perf_counter() - t0
ok("Key size",    f"256 bits")
ok("Bundle size", f"{len(ct)} bytes (nonce=12 + data + tag=16)")
ok("Round-trip",  f"{elapsed*1000:.2f} ms")
ok("Decrypted",   pt.decode())

# ── TIER 3 ───────────────────────────────────────────────────────────────────
header(3, "STREAM — ChaCha20-Poly1305")
t0  = time.perf_counter()
c   = ChaChaCipher()
ct  = c.encrypt(MSG, aad=b"christman-demo")
pt  = c.decrypt(ct,  aad=b"christman-demo")
elapsed = time.perf_counter() - t0
ok("Key size",    "256 bits")
ok("Bundle size", f"{len(ct)} bytes (nonce=12 + data + tag=16)")
ok("Round-trip",  f"{elapsed*1000:.2f} ms")
ok("Decrypted",   pt.decode())

# ── TIER 4 ───────────────────────────────────────────────────────────────────
header(4, "ASYMMETRIC — RSA-4096 + OAEP")
print("  (Generating 4096-bit keypair — takes a moment...)")
t0  = time.perf_counter()
r   = RSACipher.generate_keypair()
ct  = r.encrypt(MSG)
pt  = r.decrypt(ct)
elapsed = time.perf_counter() - t0
ok("Key size",    "4096 bits")
ok("Ciphertext",  f"{len(ct)} bytes")
ok("Round-trip",  f"{elapsed*1000:.0f} ms")
ok("Decrypted",   pt.decode())

# ── TIER 5 ───────────────────────────────────────────────────────────────────
header(5, "HYBRID — RSA-4096 + AES-256-GCM (Envelope)")
print("  (Reusing RSA keypair from Tier 4...)")
t0  = time.perf_counter()
h   = HybridCipher(r)
ct  = h.encrypt(MSG, aad=b"christman-demo")
pt  = h.decrypt(ct,  aad=b"christman-demo")
elapsed = time.perf_counter() - t0
ok("Bundle",     f"{len(ct)} bytes (RSA-wrapped AES key + GCM data)")
ok("Round-trip", f"{elapsed*1000:.0f} ms")
ok("Decrypted",  pt.decode())

# ── TIER 6 ───────────────────────────────────────────────────────────────────
header(6, "SIGNATURES — RSA-PSS Digital Signatures")
print("  (Generating signing keypair...)")
t0  = time.perf_counter()
s   = DigitalSigner.generate_keypair()
sig = s.sign(MSG)
ok_  = s.verify(MSG, sig)
bad  = s.verify(b"tampered", sig)
elapsed = time.perf_counter() - t0
ok("Signature size",       f"{len(sig)} bytes")
ok("Valid message",        str(ok_))
ok("Tampered message",     str(bad))
ok("Round-trip",           f"{elapsed*1000:.0f} ms")

# ── TIER 7 ───────────────────────────────────────────────────────────────────
header(7, "STEGANOGRAPHY — LSB Text-in-Image")
try:
    from christman_crypto.tiers.tier7_steg import LSBSteganography
    from PIL import Image
    import io
    # Create a small test image (100x100 white PNG)
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    carrier = buf.getvalue()

    steg    = LSBSteganography()
    secret  = "Harvest Now. Decrypt Later. — Everett Christman"
    t0      = time.perf_counter()
    stego   = steg.hide(carrier, secret)
    extracted = steg.extract(stego)
    elapsed = time.perf_counter() - t0
    ok("Carrier image",  f"{len(carrier):,} bytes (100×100 PNG)")
    ok("Stego image",    f"{len(stego):,} bytes (visually identical)")
    ok("Hidden message", secret)
    ok("Extracted",      extracted)
    ok("Round-trip",     f"{elapsed*1000:.2f} ms")
except ImportError:
    print("  (Pillow not installed — pip install Pillow)")
    print("  Skipping Tier 7 demo.")

# ── POST-QUANTUM — XChaCha20 ─────────────────────────────────────────────────
header("PQ-A", "POST-QUANTUM — XChaCha20-Poly1305 (192-bit nonce)")
t0  = time.perf_counter()
x   = XChaCha20Cipher()
key = x.generate_key()
ct  = x.encrypt(key, MSG, aad=b"christman-pq")
pt  = x.decrypt(key, ct,  aad=b"christman-pq")
elapsed = time.perf_counter() - t0
ok("Key",        f"256 bits")
ok("Nonce",      f"192 bits (random, collision-safe at any scale)")
ok("Bundle",     f"{len(ct)} bytes")
ok("Round-trip", f"{elapsed*1000:.3f} ms")
ok("Decrypted",  pt.decode())

# ── POST-QUANTUM — ML-KEM ────────────────────────────────────────────────────
header("PQ-B", "POST-QUANTUM — ML-KEM-768 (NIST FIPS 203, 2024)")
print("  (Pure-Python FIPS 203 implementation — correct & auditable)")
for level in [512, 768, 1024]:
    t0          = time.perf_counter()
    kem         = MLKEM(level)
    ek, dk      = kem.keygen()
    ct, ss_send = kem.encapsulate(ek)
    ss_recv     = kem.decapsulate(dk, ct)
    elapsed     = time.perf_counter() - t0
    match       = "✓" if ss_send == ss_recv else "✗"
    print(f"  {match}  ML-KEM-{level:<4}  "
          f"ek={len(ek)}B  ct={len(ct)}B  ss={len(ss_send)}B  "
          f"{elapsed*1000:.0f}ms")

# ── POST-QUANTUM — Hybrid PQ Cipher ─────────────────────────────────────────
header("PQ-C", "POST-QUANTUM HYBRID — ML-KEM-768 + XChaCha20-Poly1305")
print("  (The Kaiser Handshake: quantum-safe key exchange + stream encryption)")
t0      = time.perf_counter()
pq      = HybridPQCipher(768)
ek, dk  = pq.keygen()
bundle  = pq.encrypt(ek, MSG)
pt      = pq.decrypt(dk, bundle)
elapsed = time.perf_counter() - t0
ok("Protocol",   "ML-KEM.Encapsulate → HKDF-SHA256 → XChaCha20-Poly1305")
ok("Bundle",     f"{len(bundle)} bytes (KEM ciphertext + encrypted data)")
ok("Round-trip", f"{elapsed*1000:.0f} ms")
ok("Decrypted",  pt.decode())

# ── KyberHandshake ───────────────────────────────────────────────────────────
header("PQ-D", "KYBER HANDSHAKE — Session Key Derivation")
hs      = KyberHandshake(768)
ek, dk  = hs.generate_keys()
ss, ct  = hs.encapsulate(ek)
ss2     = hs.decapsulate(dk, ct)
skey    = hs.derive_session_key(ss, info=b"christman-ai-session")
ok("Shared secret match", str(ss == ss2))
ok("Derived session key", skey.hex()[:32] + "...")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{LINE}")
print("  ALL TIERS COMPLETE")
print(f"  {LINE}")
print("  Tier 1  Vigenère + George-loop          — Legacy foundation")
print("  Tier 2  AES-256-GCM                      — Symmetric workhorse")
print("  Tier 3  ChaCha20-Poly1305                — Stream speed")
print("  Tier 4  RSA-4096 + OAEP                  — Asymmetric identity")
print("  Tier 5  RSA + AES-256-GCM Envelope       — Hybrid classical")
print("  Tier 6  RSA-PSS Signatures               — Non-repudiation")
print("  Tier 7  LSB Steganography                — Hide the existence")
print("  PQ      ML-KEM-768 + XChaCha20-Poly1305  — Quantum resistant")
print(f"  {LINE}")
print("  'Harvest Now, Decrypt Later' — we're not waiting for the threat.")
print("  The Christman AI Project  |  Apache 2.0")
print(LINE + "\n")
