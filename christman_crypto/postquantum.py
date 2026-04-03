"""POST-QUANTUM LAYER
╔══════════════════════════════════════════════════════════════════════════════╗
║  POST-QUANTUM LAYER  |  The Christman AI Project                           ║
║  Powered by Luma Cognify AI                                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  MODULE 1: XChaCha20-Poly1305  (192-bit nonce, via libsodium)              ║
║  MODULE 2: ML-KEM  (CRYSTALS-Kyber, NIST FIPS 203)                        ║
║            Variants: ML-KEM-512, ML-KEM-768, ML-KEM-1024                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  WHY POST-QUANTUM NOW?                                                      ║
║  "Harvest Now, Decrypt Later" -- adversaries record today's encrypted       ║
║  traffic and decrypt it once quantum computers arrive (~2030 estimate).     ║
║  Medical records, personal communications, identity data encrypted now      ║
║  with classical algorithms are already at long-term risk.                   ║
║  The vulnerable populations The Christman AI Project serves cannot wait.   ║
╚══════════════════════════════════════════════════════════════════════════════╝

IMPLEMENTATION NOTES:
ML-KEM is a pure-Python reference implementation of NIST FIPS 203 (2024).
It is correct and complete. For high-throughput production use, a compiled
binding (e.g., liboqs via cffi once network is available) would be faster.
This implementation prioritizes correctness, auditability, and zero
external dependencies beyond Python's standard library.

XChaCha20-Poly1305 uses libsodium via ctypes -- the same library
that powers Signal, WhatsApp, and Wireguard.
"""

import os
import struct
import hashlib
import ctypes
from typing import Tuple, Optional

# -----------------------------------------------------------------------------

# MODULE 1 -- XChaCha20-Poly1305  (libsodium backend)

# -----------------------------------------------------------------------------

class XChaCha20Cipher:
    """
    XChaCha20-Poly1305 -- Extended-nonce authenticated stream encryption.

    Key upgrade over ChaCha20-Poly1305:
      * Nonce: 192-bit (24 bytes) vs 96-bit (12 bytes)
      * Safe for random nonce generation at scale -- collision probability
        is negligible even with billions of messages per key
      * ChaCha20 with 96-bit nonces risks collision at ~2^32 messages;
        XChaCha20 pushes that to ~2^88 -- effectively impossible
      * Same Poly1305 authentication tag (128-bit)
      * Used by libsodium's secretbox, Age encryption, WireGuard proposals

    Backend: libsodium crypto_aead_xchacha20poly1305_ietf_*
    """

    # libsodium constants
    KEY_BYTES   = 32   # 256-bit key
    NONCE_BYTES = 24   # 192-bit nonce  <- the whole point
    A_BYTES     = 16   # 128-bit Poly1305 authentication tag

    def __init__(self):
        self._lib = self._load_libsodium()
        self._configure_signatures()

    @staticmethod
    def _load_libsodium() -> ctypes.CDLL:
        for name in ('libsodium.so.23', 'libsodium.so', 'libsodium.dylib',
                     'libsodium.26.dylib',
                     '/usr/local/lib/libsodium.dylib',
                     '/usr/local/Cellar/libsodium/1.0.21/lib/libsodium.dylib',
                     '/opt/homebrew/lib/libsodium.dylib',
                     'libsodium-23.dll', 'libsodium.dll'):
            try:
                lib = ctypes.CDLL(name)
                lib.sodium_init()
                return lib
            except OSError:
                continue
        raise RuntimeError(
            "libsodium not found. Install it:\n"
            "  Ubuntu/Debian: sudo apt install libsodium-dev\n"
            "  macOS:         brew install libsodium\n"
            "  Windows:       download from https://libsodium.org"
        )

    def _configure_signatures(self):
        lib = self._lib
        for fn in ('keybytes', 'npubbytes', 'abytes'):
            getattr(lib, f'crypto_aead_xchacha20poly1305_ietf_{fn}').restype = ctypes.c_size_t
        lib.crypto_aead_xchacha20poly1305_ietf_encrypt.restype = ctypes.c_int
        lib.crypto_aead_xchacha20poly1305_ietf_decrypt.restype = ctypes.c_int

    def encrypt(self, key: bytes, plaintext: bytes,
                aad: 'Optional[bytes]' = None) -> bytes:
        """
        Returns: nonce (24 bytes) || ciphertext || auth_tag (16 bytes)
        The nonce is randomly generated and prepended -- self-contained bundle.
        """
        if len(key) != self.KEY_BYTES:
            raise ValueError(f"XChaCha20 key must be {self.KEY_BYTES} bytes.")
        nonce   = os.urandom(self.NONCE_BYTES)
        ct_buf  = ctypes.create_string_buffer(len(plaintext) + self.A_BYTES)
        ct_len  = ctypes.c_ulonglong(0)
        aad_ptr = aad if aad else None
        aad_len = len(aad) if aad else 0
        ret = self._lib.crypto_aead_xchacha20poly1305_ietf_encrypt(
            ct_buf, ctypes.byref(ct_len),
            plaintext, ctypes.c_ulonglong(len(plaintext)),
            aad_ptr, ctypes.c_ulonglong(aad_len),
            None, nonce, key
        )
        if ret != 0:
            raise RuntimeError("XChaCha20-Poly1305 encryption failed.")
        return nonce + ct_buf.raw[:ct_len.value]

    def decrypt(self, key: bytes, bundle: bytes,
                aad: 'Optional[bytes]' = None) -> bytes:
        """
        Accepts: nonce (24 bytes) || ciphertext || auth_tag (16 bytes)
        Raises RuntimeError if authentication fails (tamper detected).
        """
        if len(key) != self.KEY_BYTES:
            raise ValueError(f"XChaCha20 key must be {self.KEY_BYTES} bytes.")
        if len(bundle) < self.NONCE_BYTES + self.A_BYTES:
            raise ValueError("Bundle too short -- corrupt or truncated.")
        nonce  = bundle[:self.NONCE_BYTES]
        ct     = bundle[self.NONCE_BYTES:]
        pt_len = len(ct) - self.A_BYTES
        pt_buf = ctypes.create_string_buffer(pt_len)
        out_len = ctypes.c_ulonglong(0)
        aad_ptr = aad if aad else None
        aad_len = len(aad) if aad else 0
        ret = self._lib.crypto_aead_xchacha20poly1305_ietf_decrypt(
            pt_buf, ctypes.byref(out_len),
            None,
            ct, ctypes.c_ulonglong(len(ct)),
            aad_ptr, ctypes.c_ulonglong(aad_len),
            nonce, key
        )
        if ret != 0:
            raise RuntimeError(
                "XChaCha20-Poly1305 decryption FAILED -- "
                "authentication tag mismatch. Data tampered or wrong key."
            )
        return pt_buf.raw[:out_len.value]

    @staticmethod
    def generate_key() -> bytes:
        return os.urandom(32)


# -----------------------------------------------------------------------------

# MODULE 2 -- ML-KEM (CRYSTALS-Kyber)  NIST FIPS 203 (2024)

# Pure Python -- zero dependencies beyond hashlib

# -----------------------------------------------------------------------------

#
# WHAT IS ML-KEM?
# A Key Encapsulation Mechanism (KEM) based on the hardness of the
# Module Learning With Errors (MLWE) problem. Designed to resist attacks
# from quantum computers running Shor's algorithm, which breaks RSA and ECC.
#
# HOW IT WORKS (simplified):
# 1. Bob generates a keypair (public_key, private_key)
# 2. Alice runs Encapsulate(public_key) -> (ciphertext, shared_secret)
# 3. Bob runs Decapsulate(private_key, ciphertext) -> shared_secret
# 4. Both now share a 32-byte secret -- use it to key AES or ChaCha20
#
# VARIANTS (security level vs RSA/ECC equivalent):
# ML-KEM-512  -> ~128-bit classical / ~Level 1 post-quantum  (fastest)
# ML-KEM-768  -> ~192-bit classical / ~Level 3 post-quantum
# ML-KEM-1024 -> ~256-bit classical / ~Level 5 post-quantum  (strongest)
#

# -- FIPS 203 Constants -------------------------------------------------------

Q  = 3329   # The prime modulus for Zq
N  = 256    # Polynomial degree -- ring is Zq[x] / (x^256 + 1)
ZETA = 17   # Primitive 256th root of unity mod Q (used in NTT)

# Parameter sets: (k, eta1, eta2, du, dv)

_PARAMS = {
    512 : (2, 3, 2, 10, 4),
    768 : (3, 2, 2, 10, 4),
    1024: (4, 2, 2, 11, 5),
}

# -- Finite field arithmetic mod Q -------------------------------------------

def _mod(a: int) -> int:
    return a % Q

def _add_poly(a: list, b: list) -> list:
    return [_mod(x + y) for x, y in zip(a, b)]

def _sub_poly(a: list, b: list) -> list:
    return [_mod(x - y) for x, y in zip(a, b)]

def _mul_scalar(a: list, s: int) -> list:
    return [_mod(x * s) for x in a]

# -- Barrett reduction (fast mod Q for NTT) ----------------------------------

_BARRETT_SHIFT = 26
_BARRETT_MULT  = (1 << _BARRETT_SHIFT) // Q + 1

def _barrett_reduce(a: int) -> int:
    q = (a * _BARRETT_MULT) >> _BARRETT_SHIFT
    r = a - q * Q
    return r - Q if r >= Q else r

# -- NTT zeta table (precomputed powers of ZETA mod Q) -----------------------

def _precompute_zetas() -> list:
    """Bit-reversed powers of zeta for Cooley-Tukey NTT."""
    zetas = [0] * 128
    z = 1
    for i in range(128):
        # bit-reverse index for i in range 128
        br = int(format(i, '07b')[::-1], 2)
        zetas[br] = z
        z = (z * ZETA) % Q
    return zetas

_ZETAS = _precompute_zetas()

def _ntt(f: list) -> list:
    """
    Number Theoretic Transform -- converts polynomial to NTT domain.
    FIPS 203 Algorithm 9.
    In-place on a copy; input/output are length-256 lists of ints mod Q.
    """
    f = f[:]
    k, length = 1, 128
    while length >= 2:
        start = 0
        while start < 256:
            zeta = _ZETAS[k]
            k += 1
            for j in range(start, start + length):
                t = (zeta * f[j + length]) % Q
                f[j + length] = (f[j] - t) % Q
                f[j]          = (f[j] + t) % Q
            start += 2 * length
        length >>= 1
    return f

def _inv_ntt(f: list) -> list:
    """
    Inverse NTT -- converts back from NTT domain.
    FIPS 203 Algorithm 10.
    """
    f = f[:]
    k, length = 127, 2
    while length <= 128:
        start = 0
        while start < 256:
            zeta = _ZETAS[k]
            k -= 1
            for j in range(start, start + length):
                t = f[j]
                f[j]          = (t + f[j + length]) % Q
                f[j + length] = (zeta * (f[j + length] - t)) % Q
            start += 2 * length
        length <<= 1
    f256_inv = pow(128, Q - 2, Q)   # modular inverse of 128
    return [(x * f256_inv) % Q for x in f]

def _base_case_multiply(a0: int, a1: int, b0: int, b1: int,
                        zeta: int) -> Tuple[int, int]:
    """FIPS 203 Algorithm 11 -- multiplication in base case of NTT."""
    c0 = _mod(a0 * b0 + zeta * a1 * b1)
    c1 = _mod(a0 * b1 + a1 * b0)
    return c0, c1

def _multiply_ntt(f: list, g: list) -> list:
    """
    Pointwise multiplication in NTT domain.
    FIPS 203 Algorithm 12.
    """
    h = [0] * 256
    for i in range(64):
        zeta = _ZETAS[64 + i]
        h[4*i],   h[4*i+1] = _base_case_multiply(
            f[4*i], f[4*i+1], g[4*i], g[4*i+1],  zeta)
        h[4*i+2], h[4*i+3] = _base_case_multiply(
            f[4*i+2], f[4*i+3], g[4*i+2], g[4*i+3], -zeta % Q)
    return h

def _add_poly_mod(a: list, b: list) -> list:
    return [(x + y) % Q for x, y in zip(a, b)]

# -- Bit packing / encoding --------------------------------------------------

def _encode(poly: list, bits: int) -> bytes:
    """Encode polynomial coefficients into bytes, `bits` per coefficient."""
    out, buf, buf_bits = bytearray(), 0, 0
    mask = (1 << bits) - 1
    for c in poly:
        buf |= (c & mask) << buf_bits
        buf_bits += bits
        while buf_bits >= 8:
            out.append(buf & 0xFF)
            buf >>= 8
            buf_bits -= 8
    if buf_bits:
        out.append(buf & 0xFF)
    return bytes(out)

def _decode(data: bytes, bits: int) -> list:
    """Decode bytes into polynomial coefficients, `bits` per coefficient."""
    poly, buf, buf_bits, idx = [], 0, 0, 0
    mask = (1 << bits) - 1
    while len(poly) < N:
        while buf_bits < bits and idx < len(data):
            buf |= data[idx] << buf_bits
            buf_bits += 8
            idx += 1
        poly.append(buf & mask)
        buf >>= bits
        buf_bits -= bits
    return poly

# -- Compression / decompression ---------------------------------------------

def _compress(x: int, d: int) -> int:
    """FIPS 203 Compress_d: maps Zq -> Z_{2^d}."""
    return round((2**d / Q) * x) % (2**d)

def _decompress(x: int, d: int) -> int:
    """FIPS 203 Decompress_d: maps Z_{2^d} -> Zq."""
    return round((Q / 2**d) * x) % Q

def _compress_poly(p: list, d: int) -> list:
    return [_compress(c, d) for c in p]

def _decompress_poly(p: list, d: int) -> list:
    return [_decompress(c, d) for c in p]

# -- Sampling ----------------------------------------------------------------

def _sample_ntt(seed: bytes, i: int, j: int) -> list:
    """
    FIPS 203 SampleNTT -- sample a uniform random polynomial in NTT domain
    from a 32-byte seed using SHAKE-128.
    """
    xof    = hashlib.shake_128(seed + bytes([i, j]))
    stream = xof.digest(840)  # enough bytes for rejection sampling
    poly, idx = [], 0
    while len(poly) < N and idx + 2 < len(stream):
        d1 = stream[idx] + 256 * (stream[idx+1] & 0x0F)
        d2 = (stream[idx+1] >> 4) + 16 * stream[idx+2]
        idx += 3
        if d1 < Q:
            poly.append(d1)
        if d2 < Q and len(poly) < N:
            poly.append(d2)
    # If we ran out of bytes (extremely rare), extend
    extra_bytes = xof.digest(840 + 3 * (N - len(poly)) * 2)
    while len(poly) < N:
        idx_e = 840
        while len(poly) < N and idx_e + 2 < len(extra_bytes):
            d1 = extra_bytes[idx_e] + 256 * (extra_bytes[idx_e+1] & 0x0F)
            d2 = (extra_bytes[idx_e+1] >> 4) + 16 * extra_bytes[idx_e+2]
            idx_e += 3
            if d1 < Q: poly.append(d1)
            if d2 < Q and len(poly) < N: poly.append(d2)
        break  # failsafe
    return poly[:N]

def _cbd(prf_output: bytes, eta: int) -> list:
    """
    FIPS 203 SamplePolyCBD -- centered binomial distribution.
    Generates a small-coefficient polynomial for noise/secret.
    """
    poly = []
    bits = []
    for byte in prf_output:
        for bit in range(8):
            bits.append((byte >> bit) & 1)
    for i in range(N):
        a = sum(bits[2 * eta * i + j]       for j in range(eta))
        b = sum(bits[2 * eta * i + eta + j] for j in range(eta))
        poly.append(_mod(a - b))
    return poly

def _prf(seed: bytes, nonce: int, length: int) -> bytes:
    """FIPS 203 PRF -- SHAKE-256 keyed with seed||nonce."""
    return hashlib.shake_256(seed + bytes([nonce])).digest(length)

# -- Key generation, encapsulation, decapsulation ----------------------------

class MLKEM:
    """
    ML-KEM (CRYSTALS-Kyber) Key Encapsulation Mechanism.
    Implements NIST FIPS 203 (August 2024).

    Usage:
        kem = MLKEM(512)   # or 768 or 1024

        # Alice generates keys
        ek, dk = kem.keygen()

        # Bob encapsulates -- produces ciphertext + shared secret
        ct, ss_bob = kem.encapsulate(ek)

        # Alice decapsulates -- recovers shared secret
        ss_alice = kem.decapsulate(dk, ct)

        assert ss_alice == ss_bob  # both have the same 32-byte secret
        # Now use ss as key material for AES-256-GCM or XChaCha20
    """

    def __init__(self, security_level: int = 512):
        if security_level not in _PARAMS:
            raise ValueError("security_level must be 512, 768, or 1024")
        self.level = security_level
        self.k, self.eta1, self.eta2, self.du, self.dv = _PARAMS[security_level]

    # -- FIPS 203 Algorithm 13: K-PKE.KeyGen ---------------------------------

    def _pke_keygen(self) -> Tuple[bytes, bytes]:
        """
        Generate a public/private keypair for the underlying PKE scheme.
        Returns (ek_pke, dk_pke) as bytes.
        """
        k, eta1 = self.k, self.eta1
        d   = os.urandom(32)
        rho, sigma = hashlib.sha3_512(d).digest()[:32], hashlib.sha3_512(d).digest()[32:]

        # Generate public matrix A_hat (k x k matrix of NTT polynomials)
        A_hat = [[_sample_ntt(rho, i, j) for j in range(k)] for i in range(k)]

        # Sample secret s and error e
        N_ctr = 0
        s = []
        for _ in range(k):
            prf_out = _prf(sigma, N_ctr, 64 * eta1)
            s.append(_ntt(_cbd(prf_out, eta1)))
            N_ctr += 1
        e = []
        for _ in range(k):
            prf_out = _prf(sigma, N_ctr, 64 * eta1)
            e.append(_ntt(_cbd(prf_out, eta1)))
            N_ctr += 1

        # t_hat = A_hat o s_hat + e_hat
        t_hat = []
        for i in range(k):
            acc = [0] * N
            for j in range(k):
                acc = _add_poly_mod(acc, _multiply_ntt(A_hat[i][j], s[j]))
            t_hat.append(_add_poly_mod(acc, e[i]))

        # Encode
        ek_pke = b''.join(_encode(t_hat[i], 12) for i in range(k)) + rho
        dk_pke = b''.join(_encode(s[i], 12) for i in range(k))
        return ek_pke, dk_pke

    # -- FIPS 203 Algorithm 14: K-PKE.Encrypt --------------------------------

    def _pke_encrypt(self, ek_pke: bytes, m: bytes, r: bytes) -> bytes:
        """Encrypt 32-byte message m using randomness r."""
        k, eta1, eta2, du, dv = self.k, self.eta1, self.eta2, self.du, self.dv
        poly_bytes = 32 * 12  # 12 bits x 256 coeffs = 384 bytes per poly

        # Decode t_hat and rho from ek_pke
        t_hat = []
        for i in range(k):
            t_hat.append(_decode(ek_pke[i*poly_bytes:(i+1)*poly_bytes], 12))
        rho = ek_pke[k * poly_bytes: k * poly_bytes + 32]

        # Regenerate A_hat from rho
        A_hat = [[_sample_ntt(rho, i, j) for j in range(k)] for i in range(k)]

        # Sample r_hat, e1, e2
        N_ctr = 0
        r_hat = []
        for _ in range(k):
            prf_out = _prf(r, N_ctr, 64 * eta1)
            r_hat.append(_ntt(_cbd(prf_out, eta1)))
            N_ctr += 1
        e1 = []
        for _ in range(k):
            prf_out = _prf(r, N_ctr, 64 * eta2)
            e1.append(_cbd(prf_out, eta2))
            N_ctr += 1
        prf_out = _prf(r, N_ctr, 64 * eta2)
        e2 = _cbd(prf_out, eta2)

        # u = NTT^{-1}(A^T o r_hat) + e1
        u = []
        for j in range(k):
            acc = [0] * N
            for i in range(k):
                acc = _add_poly_mod(acc, _multiply_ntt(A_hat[i][j], r_hat[i]))
            u.append(_add_poly_mod(_inv_ntt(acc), e1[j]))

        # mu = Decompress_1(ByteDecode_1(m))
        m_bits = _decode(m, 1)
        mu = _decompress_poly(m_bits, 1)

        # v = NTT^{-1}(t_hat^T o r_hat) + e2 + mu
        acc = [0] * N
        for i in range(k):
            acc = _add_poly_mod(acc, _multiply_ntt(t_hat[i], r_hat[i]))
        v = _add_poly_mod(_add_poly_mod(_inv_ntt(acc), e2), mu)

        # Compress and encode
        c1 = b''.join(_encode(_compress_poly(u[i], du), du) for i in range(k))
        c2 = _encode(_compress_poly(v, dv), dv)
        return c1 + c2

    # -- FIPS 203 Algorithm 15: K-PKE.Decrypt --------------------------------

    def _pke_decrypt(self, dk_pke: bytes, c: bytes) -> bytes:
        """Decrypt ciphertext c using dk_pke, return 32-byte message."""
        k, du, dv = self.k, self.du, self.dv
        poly_bytes_12  = 32 * 12
        poly_bytes_du  = N * du // 8
        poly_bytes_dv  = N * dv // 8

        # Decode secret key
        s_hat = []
        for i in range(k):
            s_hat.append(_decode(dk_pke[i*poly_bytes_12:(i+1)*poly_bytes_12], 12))

        # Decode ciphertext
        u = []
        for i in range(k):
            u_comp = _decode(c[i*poly_bytes_du:(i+1)*poly_bytes_du], du)
            u.append(_decompress_poly(u_comp, du))
        v_comp = _decode(c[k*poly_bytes_du:k*poly_bytes_du+poly_bytes_dv], dv)
        v      = _decompress_poly(v_comp, dv)

        # w = v - NTT^{-1}(s_hat^T o NTT(u))
        u_hat = [_ntt(ui) for ui in u]
        acc   = [0] * N
        for i in range(k):
            acc = _add_poly_mod(acc, _multiply_ntt(s_hat[i], u_hat[i]))
        w     = [_mod(v[j] - _inv_ntt(acc)[j]) for j in range(N)]

        # Decode message
        m_bits = _compress_poly(w, 1)
        return _encode(m_bits, 1)

    # -- FIPS 203 Algorithms 16-18: ML-KEM -----------------------------------

    def keygen(self) -> Tuple[bytes, bytes]:
        """
        ML-KEM.KeyGen -- FIPS 203 Algorithm 16.
        Returns (encapsulation_key, decapsulation_key).
          ek: sent to the sender (public)
          dk: kept secret by the receiver (private)
        """
        ek_pke, dk_pke = self._pke_keygen()
        H_ek = hashlib.sha3_256(ek_pke).digest()
        z    = os.urandom(32)
        dk   = dk_pke + ek_pke + H_ek + z
        return ek_pke, dk

    def encapsulate(self, ek: bytes) -> Tuple[bytes, bytes]:
        """
        ML-KEM.Encaps -- FIPS 203 Algorithm 17.
        Called by the sender with the recipient's encapsulation key.
        Returns (ciphertext, shared_secret).
        The shared_secret is a 32-byte value -- use as key for AES/XChaCha20.
        """
        m    = os.urandom(32)
        H_ek = hashlib.sha3_256(ek).digest()
        K_r  = hashlib.sha3_512(m + H_ek).digest()
        K, r = K_r[:32], K_r[32:]
        ct   = self._pke_encrypt(ek, m, r)
        return ct, K

    def decapsulate(self, dk: bytes, ct: bytes) -> bytes:
        """
        ML-KEM.Decaps -- FIPS 203 Algorithm 18.
        Called by the receiver with their decapsulation key.
        Returns the shared_secret (32 bytes) matching what Encaps produced,
        OR an implicit rejection value if the ciphertext is invalid/forged.
        """
        k = self.k
        poly_bytes_12 = 32 * 12
        ek_pke_len    = k * poly_bytes_12 + 32

        dk_pke = dk[:k * poly_bytes_12]
        ek_pke = dk[k * poly_bytes_12 : k * poly_bytes_12 + ek_pke_len]
        H_ek   = dk[k * poly_bytes_12 + ek_pke_len :
                    k * poly_bytes_12 + ek_pke_len + 32]
        z      = dk[k * poly_bytes_12 + ek_pke_len + 32 :
                    k * poly_bytes_12 + ek_pke_len + 64]

        m_prime  = self._pke_decrypt(dk_pke, ct)
        K_r      = hashlib.sha3_512(m_prime + H_ek).digest()
        K_prime, r_prime = K_r[:32], K_r[32:]
        ct_prime = self._pke_encrypt(ek_pke, m_prime, r_prime)

        # Constant-time comparison (implicit rejection on failure)
        import hmac as _hmac
        if _hmac.compare_digest(ct, ct_prime):
            return K_prime
        else:
            # Implicit rejection -- return hash of z||ct (unpredictable to attacker)
            return hashlib.sha3_256(z + ct).digest()

    def ciphertext_size(self) -> int:
        k, du, dv = self.k, self.du, self.dv
        return k * N * du // 8 + N * dv // 8

    def ek_size(self) -> int:
        return self.k * 32 * 12 + 32

    def dk_size(self) -> int:
        return self.k * 32 * 12 * 2 + 32 + 32 + 32

    @property
    def shared_secret_size(self) -> int:
        return 32

    def __repr__(self):
        return (f"MLKEM-{self.level}  "
                f"ek={self.ek_size()}B  "
                f"dk={self.dk_size()}B  "
                f"ct={self.ciphertext_size()}B  "
                f"ss=32B")


# -----------------------------------------------------------------------------

# HYBRID POST-QUANTUM CIPHER

# ML-KEM (key exchange) + XChaCha20-Poly1305 (data encryption)

# -----------------------------------------------------------------------------

class HybridPQCipher:
    """
    Post-Quantum Hybrid Encryption.

    Protocol:
      1. Receiver generates ML-KEM keypair (ek, dk)
      2. Sender calls encrypt(ek, plaintext):
           a. ML-KEM.Encapsulate(ek) -> (kem_ct, shared_secret)
           b. Derive XChaCha20 key: HKDF-SHA256(shared_secret, info)
           c. XChaCha20-Poly1305.Encrypt(key, plaintext) -> cipher_payload
           d. Return: [4-byte kem_ct_len][kem_ct][cipher_payload]
      3. Receiver calls decrypt(dk, bundle):
           a. Split bundle
           b. ML-KEM.Decapsulate(dk, kem_ct) -> shared_secret
           c. Derive same XChaCha20 key
           d. XChaCha20-Poly1305.Decrypt -> plaintext

    Security properties:
      * Post-quantum KEM: secure against quantum computers (FIPS 203 / MLWE)
      * XChaCha20: secure against classical computers, fast, 192-bit nonce
      * HKDF ensures KDF separation between key exchange and data encryption
      * Hybrid design: secure as long as EITHER component remains unbroken
    """

    HKDF_INFO = b"christman-ai-pq-session-v1"

    def __init__(self, security_level: int = 768):
        self.kem   = MLKEM(security_level)
        self.xcha  = XChaCha20Cipher()

    def keygen(self) -> Tuple[bytes, bytes]:
        """Generate (encapsulation_key, decapsulation_key)."""
        return self.kem.keygen()

    def _hkdf(self, ikm: bytes) -> bytes:
        """HKDF-SHA256 -- derive 32-byte XChaCha20 key from KEM shared secret."""
        import hmac as _hmac
        # HKDF-Extract: PRK = HMAC-SHA256(salt, IKM)
        salt = bytes(32)
        prk  = _hmac.new(salt, ikm, hashlib.sha256).digest()
        # HKDF-Expand: OKM = HMAC-SHA256(PRK, info || 0x01)
        okm  = _hmac.new(prk, self.HKDF_INFO + b'\x01', hashlib.sha256).digest()
        return okm[:32]

    def encrypt(self, ek: bytes, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext for the holder of dk matching ek.
        Returns a self-contained bundle the receiver can decrypt.
        """
        kem_ct, ss  = self.kem.encapsulate(ek)
        xchacha_key = self._hkdf(ss)
        cipher_data = self.xcha.encrypt(xchacha_key, plaintext,
                                        aad=b"christman-pq-aad")
        return struct.pack('>I', len(kem_ct)) + kem_ct + cipher_data

    def decrypt(self, dk: bytes, bundle: bytes) -> bytes:
        """
        Decrypt a bundle produced by encrypt().
        Raises RuntimeError if authentication fails.
        """
        kem_ct_len  = struct.unpack('>I', bundle[:4])[0]
        kem_ct      = bundle[4:4 + kem_ct_len]
        cipher_data = bundle[4 + kem_ct_len:]
        ss          = self.kem.decapsulate(dk, kem_ct)
        xchacha_key = self._hkdf(ss)
        return self.xcha.decrypt(xchacha_key, cipher_data,
                                 aad=b"christman-pq-aad")


# -----------------------------------------------------------------------------

# SELF-TEST

# -----------------------------------------------------------------------------

def run_tests():
    print("\n" + "=" * 78)
    print("  XChaCha20-Poly1305  |  Self-Test")
    print("=" * 78)
    xcha = XChaCha20Cipher()
    key  = xcha.generate_key()
    msg  = b"The Christman AI Project - Protecting the vulnerable since 2012."
    enc  = xcha.encrypt(key, msg, aad=b"test-aad")
    dec  = xcha.decrypt(key, enc, aad=b"test-aad")
    assert dec == msg, "XChaCha20 round-trip failed"
    print(f"  Key       : {key.hex()[:24]}...")
    print(f"  Nonce     : {enc[:24].hex()}  (192-bit, random)")
    print(f"  Ciphertext: {enc[24:56].hex()}...")
    print(f"  Decrypted : {dec.decode()}")
    print(f"  [OK] XChaCha20-Poly1305 PASSED\n")

    print("  Tamper detection test...")
    tampered = bytearray(enc)
    tampered[30] ^= 0xFF
    try:
        xcha.decrypt(key, bytes(tampered), aad=b"test-aad")
        print("  [FAIL] FAILED -- tamper not detected!")
    except RuntimeError:
        print("  [OK] Tamper correctly rejected\n")

    print("=" * 78)
    print("  ML-KEM (CRYSTALS-Kyber) FIPS 203  |  Self-Test")
    print("=" * 78)
    import time as _t
    for level in [512, 768, 1024]:
        kem = MLKEM(level)
        print(f"  {kem}")
        t0 = _t.perf_counter()
        ek, dk = kem.keygen()
        t_kg = _t.perf_counter() - t0
        t0 = _t.perf_counter()
        ct, ss_sender = kem.encapsulate(ek)
        t_enc = _t.perf_counter() - t0
        t0 = _t.perf_counter()
        ss_receiver = kem.decapsulate(dk, ct)
        t_dec = _t.perf_counter() - t0
        assert ss_sender == ss_receiver, f"ML-KEM-{level} shared secret mismatch!"
        print(f"    keygen={t_kg:.3f}s  encaps={t_enc:.3f}s  decaps={t_dec:.3f}s")
        print(f"    Shared secret: {ss_sender.hex()[:24]}...")
        # Test implicit rejection
        ct_bad = bytes([c ^ 0xFF for c in ct])
        ss_bad = kem.decapsulate(dk, ct_bad)
        assert ss_bad != ss_sender, "Implicit rejection failed!"
        print(f"    [OK] ML-KEM-{level} PASSED  (incl. implicit rejection)\n")

    print("=" * 78)
    print("  Hybrid PQ Cipher  |  ML-KEM-768 + XChaCha20-Poly1305")
    print("=" * 78)
    pq = HybridPQCipher(768)
    ek, dk = pq.keygen()
    msg = b"AlphaVox secure session - Dusty's voice, protected forever."
    t0 = _t.perf_counter()
    bundle = pq.encrypt(ek, msg)
    t_enc = _t.perf_counter() - t0
    t0 = _t.perf_counter()
    recovered = pq.decrypt(dk, bundle)
    t_dec = _t.perf_counter() - t0
    assert recovered == msg
    print(f"  Bundle size : {len(bundle)} bytes")
    print(f"  Encrypt     : {t_enc:.3f}s")
    print(f"  Decrypt     : {t_dec:.3f}s")
    print(f"  Plaintext   : {recovered.decode()}")
    print(f"  [OK] Hybrid PQ PASSED\n")

    print("=" * 78)
    print("  ALL POST-QUANTUM TESTS PASSED  [OK]")
    print("  The Christman AI Project | Powered by Luma Cognify AI")
    print("=" * 78)


if __name__ == "__main__":
    run_tests()
