"""Tests for envault.crypto encryption/decryption module."""

import pytest
from envault.crypto import encrypt, decrypt, derive_key


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_encrypt_produces_different_ciphertexts():
    """Each call should produce a unique ciphertext due to random salt/nonce."""
    c1 = encrypt(PLAINTEXT, PASSPHRASE)
    c2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert c1 != c2


def test_decrypt_roundtrip():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    result = decrypt(encoded, PASSPHRASE)
    assert result == PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(encoded, "wrong-passphrase")


def test_decrypt_corrupted_payload_raises():
    encoded = encrypt(PLAINTEXT, PASSPHRASE)
    # Flip a character near the end of the ciphertext
    corrupted = encoded[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid base64"):
        decrypt("!!!not-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSPHRASE)


def test_derive_key_deterministic():
    salt = b"0123456789abcdef"
    k1 = derive_key(PASSPHRASE, salt)
    k2 = derive_key(PASSPHRASE, salt)
    assert k1 == k2
    assert len(k1) == 32


def test_derive_key_different_salts():
    k1 = derive_key(PASSPHRASE, b"salt_one________")
    k2 = derive_key(PASSPHRASE, b"salt_two________")
    assert k1 != k2
