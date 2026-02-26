# Harvest Now, Decrypt Later

> *"Adversaries are recording your encrypted traffic today.  
> When quantum computers arrive, they will decrypt it.  
> The vulnerable populations we serve cannot wait."* > — Everett Christman

**christman-crypto** is a seven-tier hybrid cryptographic stack — from a Vigenère cipher written in 1553 to NIST FIPS 203 post-quantum ML-KEM published in 2024 — built as the security layer for the Christman AI Project.

This is not a toy. Every tier is a real, working implementation. The PQ layer is a pure-Python FIPS 203 reference implementation with zero dependencies beyond Python's standard library.

---

## ⚡ THE RUST INJECTION: Constant-Time Armor (NEW)

We proved the NIST FIPS 203 post-quantum math in pure Python. It’s readable, it's auditable, and it works. But pure Python is vulnerable to microsecond timing attacks. We leave zero doors unlocked.

So we ripped the reference engine out and injected **raw, memory-safe, constant-time Rust**.

Using `PyO3` and `maturin`, the ML-KEM handshake is now bound directly to compiled silicon. 
* **Zero Timing Leaks:** You can't measure our microseconds. 
* **Memory-Safe Execution:** Rust guarantees no buffer overflows or memory vulnerabilities.
* **Impenetrable Vault:** "Harvest Now, Decrypt Later" adversaries can keep knocking, but you absolutely cannot get inside this hole.

We built the empathy in carbon. We forged the armor in silicon. Good luck breaking it.

---

## The Seven Tiers

```text
Tier 1  │ LEGACY        │ Vigenère Polyalphabetic  (George-loop enhanced)
Tier 2  │ SYMMETRIC     │ AES-256-GCM              (authenticated encryption)
Tier 3  │ STREAM        │ ChaCha20-Poly1305        (high-speed authenticated stream)
Tier 4  │ ASYMMETRIC    │ RSA-4096 + OAEP          (public-key encryption)
Tier 5  │ HYBRID        │ RSA + AES-256-GCM        (envelope encryption)
Tier 6  │ SIGNATURES    │ RSA-PSS                  (non-repudiation)
Tier 7  │ STEGANOGRAPHY │ LSB Text-in-Image        (hide the existence)
────────┼───────────────┼──────────────────────────────────────────────────
PQ      │ POST-QUANTUM  │ ML-KEM-768 + XChaCha20-Poly1305  (NIST FIPS 203)
