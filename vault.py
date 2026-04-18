"""
bot/security/vault.py — AES-256-GCM encryption vault for API credentials.

Each field gets its own random 12-byte IV and a 16-byte GCM auth tag.
No secret ever touches the database in plaintext.
"""
import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_MASTER_KEY: bytes = bytes.fromhex(os.environ["VAULT_KEY_HEX"])  # 32 bytes
_CONTEXT = b"alphabot-api-vault-v1"   # authenticated additional data


def _gcm() -> AESGCM:
    return AESGCM(_MASTER_KEY)


def encrypt(plaintext: str) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt plaintext string.
    Returns (ciphertext, iv, tag).
    cryptography's AESGCM appends the 16-byte tag automatically — we split it.
    """
    iv = secrets.token_bytes(12)
    ct_and_tag = _gcm().encrypt(iv, plaintext.encode(), _CONTEXT)
    ciphertext, tag = ct_and_tag[:-16], ct_and_tag[-16:]
    return ciphertext, iv, tag


def decrypt(ciphertext: bytes, iv: bytes, tag: bytes) -> str:
    ct_and_tag = ciphertext + tag
    plaintext = _gcm().decrypt(iv, ct_and_tag, _CONTEXT)
    return plaintext.decode()


# ── High-level DB helpers ──────────────────────────────────────────────────────

async def store_api_keys(
    db,
    user_id: int,
    exchange: str,
    api_key: str,
    api_secret: str,
) -> None:
    enc_key,    iv_key,    tag_key    = encrypt(api_key)
    enc_secret, iv_secret, tag_secret = encrypt(api_secret)

    await db.execute(
        """
        INSERT INTO api_keys
            (user_id, exchange,
             encrypted_key, iv_key, tag_key,
             encrypted_secret, iv_secret, tag_secret)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        ON CONFLICT (user_id, exchange) WHERE is_active
        DO UPDATE SET
            encrypted_key    = EXCLUDED.encrypted_key,
            iv_key           = EXCLUDED.iv_key,
            tag_key          = EXCLUDED.tag_key,
            encrypted_secret = EXCLUDED.encrypted_secret,
            iv_secret        = EXCLUDED.iv_secret,
            tag_secret       = EXCLUDED.tag_secret
        """,
        user_id, exchange,
        enc_key, iv_key, tag_key,
        enc_secret, iv_secret, tag_secret,
    )


async def load_api_keys(db, user_id: int, exchange: str) -> tuple[str, str]:
    row = await db.fetchrow(
        """
        SELECT encrypted_key, iv_key, tag_key,
               encrypted_secret, iv_secret, tag_secret
        FROM   api_keys
        WHERE  user_id = $1 AND exchange = $2 AND is_active
        """,
        user_id, exchange,
    )
    if row is None:
        raise KeyError(f"No active keys for user {user_id} on {exchange}")

    api_key    = decrypt(row["encrypted_key"],    row["iv_key"],    row["tag_key"])
    api_secret = decrypt(row["encrypted_secret"], row["iv_secret"], row["tag_secret"])
    return api_key, api_secret


async def delete_api_keys(db, user_id: int, exchange: str) -> None:
    await db.execute(
        "UPDATE api_keys SET is_active = FALSE WHERE user_id = $1 AND exchange = $2",
        user_id, exchange,
    )
