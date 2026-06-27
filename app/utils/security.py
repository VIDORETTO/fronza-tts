import os
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.utils.logging import logger


def _derive_key(secret: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return key


def encrypt_value(plain_text: str, secret_key: str | None = None) -> str:
    if secret_key is None:
        secret_key = os.getenv("APP_SECRET_KEY", "insecure-default-key-change-me")
    salt = os.urandom(16)
    key = _derive_key(secret_key, salt)
    f = Fernet(key)
    token = f.encrypt(plain_text.encode())
    return salt.hex() + ":" + token.decode()


def decrypt_value(encrypted: str, secret_key: str | None = None) -> str:
    if secret_key is None:
        secret_key = os.getenv("APP_SECRET_KEY", "insecure-default-key-change-me")
    try:
        salt_hex, token = encrypted.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = _derive_key(secret_key, salt)
        f = Fernet(key)
        return f.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt value: {e}")
        return ""


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
