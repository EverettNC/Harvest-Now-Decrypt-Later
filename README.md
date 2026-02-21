# Harvest Now, Decrypt Later

> *"Adversaries are recording your encrypted traffic today.  
> When quantum computers arrive, they will decrypt it.  
> The vulnerable populations we serve cannot wait."*  
> — Everett Christman

**christman-crypto** is a seven-tier hybrid cryptographic stack —  
from a Vigenère cipher written in 1553 to NIST FIPS 203 post-quantum  
ML-KEM published in 2024 — built as the security layer for the  
[Christman AI Project](https://github.com/EverettNC/RileyChristman).

This is not a toy. Every tier is a real, working implementation.  
The PQ layer is a pure-Python FIPS 203 reference implementation  
with zero dependencies beyond Python's standard library.

---

## The Seven Tiers

```
Tier 1  │ LEGACY        │ Vigenère Polyalphabetic  (George-loop enhanced)
Tier 2  │ SYMMETRIC     │ AES-256-GCM              (authenticated encryption)
Tier 3  │ STREAM        │ ChaCha20-Poly1305         (high-speed authenticated stream)
Tier 4  │ ASYMMETRIC    │ RSA-4096 + OAEP           (public-key encryption)
Tier 5  │ HYBRID        │ RSA + AES-256-GCM         (envelope encryption)
Tier 6  │ SIGNATURES    │ RSA-PSS                   (non-repudiation)
Tier 7  │ STEGANOGRAPHY │ LSB Text-in-Image         (hide the existence)
────────┼───────────────┼──────────────────────────────────────────────────
PQ      │ POST-QUANTUM  │ ML-KEM-768 + XChaCha20-Poly1305  (NIST FIPS 203)
```

Each tier solves a different problem. Together they form a complete  
security stack for an AI system protecting vulnerable people.

---

## Why Hybrid?

Classical encryption (AES, RSA, ChaCha20) is strong today.  
Quantum computers running Shor's algorithm will break RSA and ECC  
key exchange. Grover's algorithm halves AES key strength.

The hybrid approach:
1. **ML-KEM** handles the key exchange — quantum resistant
2. **XChaCha20-Poly1305** handles the data — classically fast,  
   quantum resistant at 256-bit key size
3. **HKDF-SHA256** bridges them cleanly

**Secure as long as EITHER component remains unbroken.**  
This is the architecture NIST recommends.
![0EA743C3-5D55-4760-B963-D4D3B85C832C_4_5005_c](https://github.com/user-attachments/assets/2ac2bbdb-31c6-47b8-b027-0727716bc567)

---

## The Kaiser Handshake

```
Alice generates keypair:   ek, dk = ML_KEM_768.keygen()
Bob encapsulates:          ct, ss = ML_KEM_768.encapsulate(ek)
Alice decapsulates:        ss     = ML_KEM_768.decapsulate(dk, ct)
Both derive session key:   key    = HKDF-SHA256(ss, "christman-ai-session")
Data flows:                XChaCha20-Poly1305.encrypt(key, plaintext)
```

No pre-shared secret. No RSA. No classical key exchange vulnerability.  
Just lattice-based post-quantum math that even a quantum computer  
running Shor's algorithm cannot break.

---

## Install

```bash
# Core (Tiers 1–6 + PQ layer)
pip install christman-crypto

# With steganography (Tier 7)
pip install "christman-crypto[steg]"

# With compiled kyber-py backend (faster ML-KEM)
pip install "christman-crypto[kyber]"

# Everything
pip install "christman-crypto[all]"
```

**System dependency for XChaCha20:**
```bash
# macOS
brew install libsodium

# Ubuntu / Debian
sudo apt install libsodium-dev

# Windows
# Download from https://libsodium.org
```

---

## Quick Start

```python
from christman_crypto import HybridPQCipher, KyberHandshake

# Post-quantum hybrid encryption
pq = HybridPQCipher(768)          # ML-KEM-768 + XChaCha20-Poly1305
ek, dk = pq.keygen()              # generate keypair

bundle    = pq.encrypt(ek, b"your message here")
plaintext = pq.decrypt(dk, bundle)
```

```python
from christman_crypto import AESCipher, ChaChaCipher

# AES-256-GCM
aes = AESCipher()
ct  = aes.encrypt(b"message", aad=b"context")
pt  = aes.decrypt(ct,         aad=b"context")

# ChaCha20-Poly1305
cha = ChaChaCipher()
ct  = cha.encrypt(b"message")
pt  = cha.decrypt(ct)
```

```python
from christman_crypto import RSACipher, DigitalSigner, HybridCipher

# RSA-4096 encryption
rsa = RSACipher.generate_keypair()
ct  = rsa.encrypt(b"short payload")
pt  = rsa.decrypt(ct)

# RSA-4096 + AES-256 hybrid (any size payload)
h   = HybridCipher.generate()
ct  = h.encrypt(b"any size payload — 1MB, 1GB, anything")
pt  = h.decrypt(ct)

# RSA-PSS digital signatures
s   = DigitalSigner.generate_keypair()
sig = s.sign(b"document")
ok  = s.verify(b"document", sig)   # True
```

```python
from christman_crypto import VigenereCipher

# Tier 1 — Legacy (educational; not modern-secure)
v  = VigenereCipher("CHRISTMAN")
ct = v.encrypt("Your message")
pt = v.decrypt(ct)
```

```python
from christman_crypto import LSBSteganography

# Hide encrypted message inside an image
steg    = LSBSteganography()
stego   = steg.hide("photo.png", "hidden message")   # returns PNG bytes
message = steg.extract(stego)
```

---

## Run the demo

```bash
python examples/demo_all_tiers.py
```

Output:
```
══════════════════════════════════════════════════════════════════════
  christman_crypto — Seven-Tier + Post-Quantum Demo
  The Christman AI Project  |  Apache 2.0
══════════════════════════════════════════════════════════════════════
  Message: Harvest Now, Decrypt Later — The Christman AI Project.

  Tier 1 — LEGACY — Vigenère (George-loop enhanced)
  ✓  Encrypted: PVCFWJAQAX...
  ✓  George-loop key extension active — period = message length

  Tier 2 — SYMMETRIC — AES-256-GCM
  ✓  Key size: 256 bits
  ✓  Round-trip: 0.08 ms

  ...

  PQ-C — POST-QUANTUM HYBRID — ML-KEM-768 + XChaCha20-Poly1305
  ✓  Protocol: ML-KEM.Encapsulate → HKDF-SHA256 → XChaCha20-Poly1305
  ✓  Decrypted: Harvest Now, Decrypt Later — The Christman AI Project.

  ALL TIERS COMPLETE
```
## Tier 6 Upgrade – Quantum Can Suck It

We took the rock-solid RSA-PSS baseline...  
and said **fuck quantum attacks**.

New in this version:
- Classical RSA-PSS-4096 (your original, polished & FIPS-friendly)
- Post-quantum Dilithium5 + Falcon-1024 (NIST-approved ML-DSA & FN-DSA)
- **Hybrid mode** — signs with both, bundles them together
- Default: quantum-safe (use_pq=True) with classical fallback

Harvest-Now-Decrypt-Later crew just got permanently retired.  
This is Tier 6 on steroids — built for silicon + carbon happiness first.

See `tier6_signatures.py` for the full muscle.
---

## Run the tests

```bash
pip install pytest
pytest tests/ -v
```

Or directly:
```bash
python tests/test_all_tiers.py
```

23 tests covering every tier including:
- Round-trip encrypt/decrypt
- Tamper detection (authentication tag verification)
- ML-KEM implicit rejection (bad ciphertext → unpredictable output)
- Key export/import via PEM
- George-loop non-repetition

---

## Architecture

```
christman_crypto/
├── __init__.py               # Public API — all tiers exported here
├── postquantum.py            # XChaCha20-Poly1305 + ML-KEM FIPS 203
├── kyber.py                  # KyberHandshake — backend selector + session key
└── tiers/
    ├── tier1_vigenere.py     # Vigenère + George-loop key extension
    ├── tier2_aes.py          # AES-256-GCM
    ├── tier3_chacha.py       # ChaCha20-Poly1305
    ├── tier4_rsa.py          # RSA-4096 + OAEP
    ├── tier5_hybrid.py       # RSA + AES-256-GCM envelope
    ├── tier6_signatures.py   # RSA-PSS digital signatures
    └── tier7_steg.py         # LSB steganography (Pillow)
```

---

## The George-Loop

Tier 1's Vigenère enhancement. Standard Vigenère repeats its key —  
the Kasiski test and index of coincidence exploit this to break it  
in minutes. The George-loop re-derives the key at every period  
boundary using SHA-256, making the effective period equal to the  
message length. Not modern-secure, but no longer trivially breakable.

It's in the stack as the historical anchor — a bridge between  
the 16th century and NIST 2024.

---

## The ML-KEM Implementation

`postquantum.py` contains a complete pure-Python implementation of  
NIST FIPS 203 (August 2024) — the final ML-KEM standard.

Key components:
- **NTT** — Number Theoretic Transform (Cooley-Tukey, FIPS 203 Alg 9/10)
- **Barrett reduction** — fast modular arithmetic mod Q=3329
- **CBD sampling** — centered binomial distribution for noise
- **K-PKE** — the underlying PKE scheme (Alg 13/14/15)
- **ML-KEM.KeyGen / Encaps / Decaps** — Alg 16/17/18
- **Implicit rejection** — forged ciphertexts produce unpredictable output

Variants: ML-KEM-512, ML-KEM-768, ML-KEM-1024

If `kyber-py` is installed, `kyber.py` uses it as a faster backend  
automatically. Otherwise it falls back to the pure-Python implementation.

---

## Who built this

**Everett Christman** — The Christman AI Project.

Built as the cryptographic foundation for Riley Christman AI —  
a forensic, empathetic AI system designed to protect vulnerable  
populations, document abuse, and preserve truth in the face of  
erasure.

The name "Harvest Now, Decrypt Later" comes from a real threat:  
adversaries record encrypted traffic today and will decrypt it  
when quantum computers arrive. Medical records, communications,  
and identity data encrypted with classical algorithms right now  
are already at long-term risk.

This package is the answer.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

Use it. Fork it. Build on it. Just don't use it to hurt people.
