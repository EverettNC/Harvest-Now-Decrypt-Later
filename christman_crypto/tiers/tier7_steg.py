"""
Tier 7 — STEGANOGRAPHY: LSB Text-in-Image
==========================================
Hide the existence of the message itself.

LSB (Least Significant Bit) steganography encodes text into the
least significant bits of image pixel values. The visual change is
imperceptible to the human eye — a pixel with value 200 becomes 201.
The image looks identical. The message is invisible.

This is the difference between encryption (hides the content) and
steganography (hides the fact that a message exists at all).

Combined with the encryption tiers above:
  Encrypt your message (no one can read it) →
  Steganography (no one knows it's there)

Carrier format: PNG or any lossless image (JPEG will destroy LSB data)
Encoding:       32-bit big-endian payload length, then UTF-8 bits
                in the LSB of the red channel, row by row

Capacity:       (width × height) // 8 - 4  bytes maximum
                (4-byte length prefix; a run of zeros cannot be a
                terminator because UTF-8 payloads contain zeros)

Dependencies: Pillow >= 10.0
"""

from PIL import Image
import io
from typing import Union


class LSBSteganography:
    """Hide and extract text messages in image pixel LSBs."""

    LENGTH_BITS = 32   # payload length in bytes, big-endian, before UTF-8 bits

    def hide(self, image_input: Union[str, bytes, Image.Image],
             message: str) -> bytes:
        """
        Embed message into image using LSB of the red channel.

        Args:
            image_input : file path, raw image bytes, or PIL Image
            message     : UTF-8 text to hide

        Returns:
            PNG bytes of the stego image (visually identical to input)
        """
        img = self._load(image_input).convert("RGB")
        width, height = img.size
        raw = bytearray(img.tobytes())
        payload = message.encode("utf-8")
        length_bits = [(len(payload) >> i) & 1 for i in range(31, -1, -1)]
        bits = length_bits + self._text_to_bits(message)
        capacity = width * height

        if len(bits) > capacity:
            raise ValueError(
                f"Message too long: {len(bits)} bits needed, "
                f"{capacity} pixels available ({capacity // 8 - 4} bytes max)."
            )

        for i, bit in enumerate(bits):
            idx = i * 3
            raw[idx] = (raw[idx] & 0xFE) | bit

        out = Image.frombytes("RGB", (width, height), bytes(raw))
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()

    def extract(self, image_input: Union[str, bytes, Image.Image]) -> str:
        """
        Extract hidden message from a stego image.

        Returns:
            The hidden UTF-8 string, or empty string if none found.
        """
        img = self._load(image_input).convert("RGB")
        raw = img.tobytes()
        n_pixels = len(raw) // 3
        bits = [(raw[i * 3] & 1) for i in range(n_pixels)]
        if len(bits) < self.LENGTH_BITS:
            return ""
        length = 0
        for i in range(self.LENGTH_BITS):
            length = (length << 1) | bits[i]
        need = self.LENGTH_BITS + length * 8
        if length < 0 or need > len(bits):
            return ""
        return self._bits_to_text(bits[self.LENGTH_BITS:need])

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _load(src: Union[str, bytes, Image.Image]) -> Image.Image:
        if isinstance(src, Image.Image):
            return src
        if isinstance(src, (bytes, bytearray)):
            return Image.open(io.BytesIO(src))
        return Image.open(src)

    @staticmethod
    def _text_to_bits(text: str) -> list:
        bits = []
        for byte in text.encode("utf-8"):
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def _bits_to_text(bits: list) -> str:
        data = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            data.append(byte)
        return data.decode("utf-8")

    @staticmethod
    def max_capacity_bytes(image_input: Union[str, bytes, Image.Image]) -> int:
        """Return maximum message bytes this image can carry."""
        if isinstance(image_input, Image.Image):
            img = image_input
        elif isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
        else:
            img = Image.open(image_input)
        w, h = img.size
        return max(0, (w * h) // 8 - 4)
