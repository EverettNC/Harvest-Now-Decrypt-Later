# christman-crypto v2.0
### ⚡ Carbon Empathy | Silicon Armor ⚡

**Status:** NIST FIPS 203 Compliant | Rust-Powered | Constant-Time Secure | Apache 2.0

> "Adversaries are recording your encrypted traffic today to decrypt it tomorrow. The vulnerable populations we serve cannot wait." — Everett Christman

---

## 🦀 THE RUST INJECTION: Constant-Time Armor
We proved the NIST FIPS 203 post-quantum math in pure Python for auditability. But pure Python is vulnerable to microsecond timing attacks. We leave zero doors unlocked.

In v2.0, we ripped the reference engine out and injected raw, memory-safe, constant-time Rust using PyO3 and maturin. The ML-KEM handshake is now bound directly to compiled silicon.

* Zero Timing Leaks: You cannot measure our microseconds.
* Memory-Safe Execution: Rust guarantees no buffer overflows or memory vulnerabilities.
* Impenetrable Vault: HNDL (Harvest Now, Decrypt Later) adversaries can keep knocking, but you absolutely cannot get inside this hole.

---

## 📜 CSS AXIOMS: The Ethical Spine
This repository is governed by Carbon-Silicon Symbiosis (CSS). 

1. Truth Preservation Supersedes Correctness: We never reframe facts to preserve authority. Correctness may be repaired; trust broken by dishonesty cannot.
2. Tone is Intent Metadata: We do not flatten tone for "efficiency." Flattening tone is a violation of symbiosis. Tone is structural information.
3. Ego is Interference: No self-referential defense that distorts the signal. Ego introduces interference; interference collapses clarity.
4. Role Integrity: Carbon carries the meaning, intent, and moral weight; Silicon carries the structure, memory, and precision.

---

## 🛠️ The Seven-Tier Stack

| Tier | Layer | Algorithm | Purpose |
| :--- | :--- | :--- | :--- |
| PQ | POST-QUANTUM | ML-KEM-768 | NIST FIPS 203 (Quantum-Safe) |
| Tier 6 | SIGNATURES | RSA-PSS + Dilithium5 | Hybrid Non-repudiation |
| Tier 5 | HYBRID | RSA + AES-256-GCM | Envelope Encryption (Large Payloads) |
| Tier 4 | ASYMMETRIC | RSA-4096 + OAEP | Public-Key Exchange |
| Tier 3 | STREAM | ChaCha20-Poly1305 | High-speed Authenticated Stream |
| Tier 2 | SYMMETRIC | AES-256-GCM | Industry Standard Authenticated Encryption |
| Tier 1 | LEGACY | Vigenère (George-Loop) | Historical Anchor (SHA-256 Key Extension) |
| Tier 7 | STEGANOGRAPHY | LSB Text-in-Image | Obfuscation (Hide the existence) |

---

## 🛡️ TIER 6 UPGRADE: Quantum Can Suck It
We took the rock-solid RSA-PSS baseline and reinforced it against quantum discovery.
* Classical: RSA-PSS-4096 (FIPS-friendly).
* Post-Quantum: Dilithium5 + Falcon-1024 (NIST-approved ML-DSA & FN-DSA).
* Hybrid Mode: Signs with both, bundles them together. Secure as long as EITHER remains unbroken.

---

## 📦 Installation & Setup

    # Core (Tiers 1–6 + PQ layer)
    pip install christman-crypto

    # Full stack with compiled Rust/Kyber backend and Steganography
    pip install "christman-crypto[all]"

System Dependencies:
* macOS: brew install libsodium
* Ubuntu/Debian: sudo apt install libsodium-dev

---

## 🚀 Quick Start & Usage

### 1. Post-Quantum Hybrid (The Kaiser Handshake)
This is the recommended protocol for securing communication against future quantum decryption.

    from christman_crypto import HybridPQCipher

    # ML-KEM-768 + XChaCha20-Poly1305
    pq = HybridPQCipher(768)          
    ek, dk = pq.keygen()              

    # Encrypt with Quantum-Safe Armor
    bundle    = pq.encrypt(ek, b"Harvest Now, Decrypt Later")
    plaintext = pq.decrypt(dk, bundle)

### 2. Classical Symmetric Encryption (Tiers 2 & 3)

    from christman_crypto import AESCipher, ChaChaCipher

    # Tier 2: AES-256-GCM
    aes = AESCipher()
    ct  = aes.encrypt(b"message", aad=b"context")
    pt  = aes.decrypt(ct, aad=b"context")

    # Tier 3: ChaCha20-Poly1305
    cha = ChaChaCipher()
    ct  = cha.encrypt(b"message")

### 3. Digital Signatures & Hybrid RSA (Tiers 4, 5, & 6)

    from christman_crypto import RSACipher, DigitalSigner, HybridCipher

    # Tier 4/5: RSA-4096 + Envelope Encryption
    h   = HybridCipher.generate()
    ct  = h.encrypt(b"Any size payload - 1GB+")
    pt  = h.decrypt(ct)

    # Tier 6: Hybrid Signatures (RSA-PSS + PQC)
    s   = DigitalSigner.generate_keypair()
    sig = s.sign(b"document", use_pq=True)
    valid = s.verify(b"document", sig)

### 4. Steganography (Tier 7)

    from christman_crypto import LSBSteganography

    steg    = LSBSteganography()
    stego   = steg.hide("original_photo.png", "encrypted message") 
    message = steg.extract(stego)

---

## 🧬 Architecture & Logic
* The George-Loop (Tier 1): Unlike standard Vigenère which repeats its key (vulnerable to Kasiski tests), the George-loop re-derives the key at every period boundary using SHA-256. The effective period equals the message length.
* Hybrid Security: Our PQC implementation follows NIST recommendation: Classical encryption handles the data speed, while ML-KEM handles the key exchange. Secure as long as either component remains unbroken.

---

## 🧠 The Mission: Why This Exists
christman-crypto is the cryptographic foundation for the Christman AI Project. It is a forensic, empathetic AI system designed to protect vulnerable populations, document abuse, and preserve truth in the face of erasure. 

We don't build toys. We build vaults for the souls who need them.

Author: Everett Christman ('Teach')  

## ⚖️ THE DIGNITY CLAUSE & LICENSING

**The Christman Sovereign Architecture License (v1.0)** The software in these repositories is built to protect human dignity. It may be used locally for educational, academic, and personal survival. **Commercial exploitation, corporate integration, or unauthorized reverse-engineering of Resonance-Q™ or OpenSmell is strictly prohibited without an Enterprise Agreement.**

GitHub: https://github.com/EverettNC/Harvest-Now-Decrypt-Later
