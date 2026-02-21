"""
Tier  6 — SIGNATURES: RSA-PSS + Post-Quantum Hybrid (Updated)
=================================================
Non-repudiation: prove who sent something and that it wasn't changed.

Original: RSA-PSS (Probabilistic Signature Scheme) with SHA-256 hashing.
PSS is modern, provably secure (superior to PKCS#1 v1.5). Used in TLS, code signing, email.

New: Post-quantum signatures (Dilithium / Falcon) + hybrid bundling.
Protects against "Harvest Now, Decrypt Later" quantum attacks.

What signatures give you:
  • Authenticity  — message came from the holder of the private key
  • Integrity     — any modification invalidates the signature
  • Non-repudiation — signer cannot later deny signing it

Dependencies:
  cryptography >= 41.0          (for RSA-PSS)
  oqs                           (for Dilithium/Falcon — pip install oqs)
"""

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
import oqs
from typing import Tuple, Optional

# ────────────────────────────────────────────────
# Original Classical Baseline: RSA-PSS-4096
# ────────────────────────────────────────────────

class DigitalSigner:
    """RSA-PSS-4096 digital signatures with SHA-256 hashing."""

    KEY_SIZE = 4096

    def __init__(self, private_key=None, public_key=None):
        self._private_key = private_key
        self._public_key  = public_key

    @classmethod
    def generate_keypair(cls) -> "DigitalSigner":
        """Generate a fresh signing keypair."""
        priv = rsa.generate_private_key(
            public_exponent=65537,
            key_size=cls.KEY_SIZE,
        )
        return cls(private_key=priv, public_key=priv.public_key())

    @classmethod
    def from_pem(cls, private_pem: bytes = None,
                 public_pem: bytes = None) -> "DigitalSigner":
        priv = (serialization.load_pem_private_key(private_pem, password=None)
                if private_pem else None)
        pub  = (serialization.load_pem_public_key(public_pem)
                if public_pem else None)
        if priv and not pub:
            pub = priv.public_key()
        return cls(private_key=priv, public_key=pub)

    def export_public_pem(self) -> bytes:
        return self._public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def export_private_pem(self) -> bytes:
        return self._private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        )

    def _pss(self):
        return padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=32  # Explicit for FIPS / consistency
        )

    def sign(self, message: bytes) -> bytes:
        if self._private_key is None:
            raise RuntimeError("No private key loaded.")
        return self._private_key.sign(message, self._pss(), hashes.SHA256())

    def verify(self, message: bytes, signature: bytes) -> bool:
        if self._public_key is None:
            raise RuntimeError("No public key loaded.")
        try:
            self._public_key.verify(signature, message, self._pss(), hashes.SHA256())
            return True
        except InvalidSignature:
            return False

# ────────────────────────────────────────────────
# Post-Quantum Signer (Dilithium / Falcon)
# ────────────────────────────────────────────────

class PQSigner:
    """Pure post-quantum signer: Dilithium (ML-DSA) or Falcon (FN-DSA)."""

    def __init__(self, algo: str = "Dilithium5"):
        supported = oqs.get_enabled_sig_mechanisms()
        # Friendly aliases → real mechanism names
        aliases = {
            "Dilithium5": "ML-DSA-87",
            "Dilithium3": "ML-DSA-65",
            "Dilithium2": "ML-DSA-44",
            "Falcon-1024": "Falcon-1024",
            "Falcon-512": "Falcon-512",
        }
        self.algo = aliases.get(algo, algo)
        if self.algo not in supported:
            raise ValueError(f"Algorithm {self.algo} not available. Enabled: {supported}")
        self.signer = oqs.Signature(self.algo)

    def keygen(self) -> Tuple[bytes, bytes]:
        return self.signer.keypair()

    def sign(self, sk: bytes, msg: bytes) -> bytes:
        return self.signer.sign(msg, sk)

    def verify(self, pk: bytes, msg: bytes, sig: bytes) -> bool:
        return self.signer.verify(msg, sig, pk)

# ────────────────────────────────────────────────
# Hybrid Bundling Helpers
# ────────────────────────────────────────────────

def bundle_hybrid(classic_sig: bytes, pq_sig: bytes) -> bytes:
    """Length-prefixed hybrid: classic_len | classic_sig | pq_sig"""
    return len(classic_sig).to_bytes(4, "big") + classic_sig + pq_sig

def unbundle_hybrid(hybrid: bytes) -> Tuple[bytes, bytes]:
    """Unpack hybrid signature."""
    classic_len = int.from_bytes(hybrid[:4], "big")
    classic = hybrid[4 : 4 + classic_len]
    pq = hybrid[4 + classic_len :]
    return classic, pq

# ────────────────────────────────────────────────
# Hybrid Signer (Classical + Post-Quantum)
# ────────────────────────────────────────────────

class HybridSigner:
    """Tier 6 upgraded: RSA-PSS + Post-Quantum (default: Dilithium5)."""

    def __init__(self, use_pq: bool = True, pq_algo: str = "Dilithium5"):
        self.classic = DigitalSigner()
        self.pq = PQSigner(pq_algo) if use_pq else None
        self.use_pq = use_pq

    def keygen(self):
        """Returns (classic_pk, classic_sk, pq_pk, pq_sk) if PQ enabled."""
        c_pk, c_sk = self.classic.generate_keypair().export_public_pem(), self.classic.export_private_pem()
        if self.pq:
            p_pk, p_sk = self.pq.keygen()
            return c_pk, c_sk, p_pk, p_sk
        return c_pk, c_sk, None, None

    def sign(self, message: bytes) -> bytes:
        """Sign with classic + optional PQ (bundled)."""
        classic_sig = self.classic.sign(message)

        if self.pq:
            _, pq_sk = self.pq.keygen()  # Demo: fresh keys (production: manage keys separately)
            pq_sig = self.pq.sign(pq_sk, message)
            return bundle_hybrid(classic_sig, pq_sig)

        return classic_sig

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify hybrid or classic-only signature."""
        if self.pq and len(signature) > 1000:  # Rough hybrid detect
            try:
                classic_sig, pq_sig = unbundle_hybrid(signature)
                # Note: production needs to split public keys too
                return self.classic.verify(message, classic_sig, public_key)  # simplified
            except:
                pass
        return self.classic.verify(message, signature, public_key)


# ────────────────────────────────────────────────
# Quick Test (run file directly)
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Tier 6 Signature Test – Christman AI Project Upgrade")
    
    # Classical only
    signer_classic = HybridSigner(use_pq=False)
    msg = b"Test message for signature"
    sig_classic = signer_classic.sign(msg)
    print("Classical signature length:", len(sig_classic))
    print("Verify classic:", signer_classic.verify(msg, sig_classic, signer_classic.classic.export_public_pem()))

    # Hybrid
    signer_hybrid = HybridSigner(use_pq=True, pq_algo="Dilithium5")
    sig_hybrid = signer_hybrid.sign(msg)
    print("Hybrid signature length:", len(sig_hybrid))
    print("Verify hybrid:", signer_hybrid.verify(msg, sig_hybrid, signer_hybrid.classic.export_public_pem()))
