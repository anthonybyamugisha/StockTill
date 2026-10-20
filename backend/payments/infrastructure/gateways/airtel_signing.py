import base64
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


@dataclass(frozen=True)
class SignedPayload:
    body: bytes
    signature: str
    key: str

    @property
    def headers(self) -> dict[str, str]:
        return {"x-signature": self.signature, "x-key": self.key}


def sign_payload(public_key: str, payload: Mapping[str, Any]) -> SignedPayload:
    """Sign an Airtel Money write request as required by the Uganda API."""
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    aes_key = os.urandom(32)
    iv = os.urandom(16)

    padder = padding.PKCS7(128).padder()
    padded = padder.update(body) + padder.finalize()
    encryptor = Cipher(algorithms.AES(aes_key), modes.CBC(iv)).encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()

    key_material = f"{_encode(aes_key)}:{_encode(iv)}".encode()
    encrypted_key = _load_public_key(public_key).encrypt(
        key_material, asymmetric_padding.PKCS1v15()
    )

    return SignedPayload(
        body=body,
        signature=_encode(encrypted),
        key=_encode(encrypted_key),
    )


def _load_public_key(value: str) -> RSAPublicKey:
    text = value.strip()
    if "-----BEGIN" in text:
        key = serialization.load_pem_public_key(text.encode())
    else:
        key = serialization.load_der_public_key(base64.b64decode(text))
    if not isinstance(key, RSAPublicKey):
        raise ValueError("Airtel Money returned a non-RSA public key")
    return key


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")
