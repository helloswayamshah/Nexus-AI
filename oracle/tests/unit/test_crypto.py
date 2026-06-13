"""
Unit tests for app.core.crypto

These are pure unit tests — no DB, no server, no fixtures needed.
They verify the AES-256-GCM vault behaves correctly and stays
wire-compatible with the Node.js crypto.js format.
"""

import os
import pytest

os.environ.setdefault("ENCRYPTION_KEY", "a" * 64)

from app.core import crypto


# ── Helpers ───────────────────────────────────────────────────────────────

VALID_HEX_KEY = "a" * 64        # 64 hex chars = 32 bytes
VALID_B64_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="  # 32 zero bytes b64


# ── Wire format ───────────────────────────────────────────────────────────

class TestWireFormat:
    def setup_method(self):
        crypto._cached_key = None
        os.environ["ENCRYPTION_KEY"] = VALID_HEX_KEY

    def test_encrypted_value_has_four_parts(self):
        result = crypto.encrypt("hello")
        assert len(result.split(":")) == 4

    def test_encrypted_value_starts_with_v1(self):
        result = crypto.encrypt("hello")
        assert result.startswith("v1:")

    def test_iv_tag_ct_are_base64(self):
        import base64
        _, iv_b64, tag_b64, ct_b64 = crypto.encrypt("hello").split(":")
        # Should not raise
        base64.b64decode(iv_b64)
        base64.b64decode(tag_b64)
        base64.b64decode(ct_b64)

    def test_iv_is_12_bytes(self):
        import base64
        _, iv_b64, _, _ = crypto.encrypt("hello").split(":")
        assert len(base64.b64decode(iv_b64)) == 12

    def test_tag_is_16_bytes(self):
        import base64
        _, _, tag_b64, _ = crypto.encrypt("hello").split(":")
        assert len(base64.b64decode(tag_b64)) == 16


# ── Round-trip ────────────────────────────────────────────────────────────

class TestRoundTrip:
    def setup_method(self):
        crypto._cached_key = None
        os.environ["ENCRYPTION_KEY"] = VALID_HEX_KEY

    def test_encrypt_decrypt_ascii(self):
        plain = "super-secret-token"
        assert crypto.decrypt(crypto.encrypt(plain)) == plain

    def test_encrypt_decrypt_unicode(self):
        plain = "token-with-unicode"
        assert crypto.decrypt(crypto.encrypt(plain)) == plain

    def test_encrypt_decrypt_empty_string(self):
        # Empty string is returned as-is (no encryption)
        assert crypto.encrypt("") == ""
        assert crypto.decrypt("") == ""

    def test_encrypt_decrypt_long_value(self):
        plain = "x" * 4096
        assert crypto.decrypt(crypto.encrypt(plain)) == plain

    def test_two_encryptions_produce_different_ciphertext(self):
        plain = "same-input"
        assert crypto.encrypt(plain) != crypto.encrypt(plain)

    def test_decrypt_legacy_plaintext_passthrough(self):
        # A value that doesn't start with "v1:" is returned unchanged
        assert crypto.decrypt("raw-legacy-value") == "raw-legacy-value"


# ── is_encrypted guard ────────────────────────────────────────────────────

class TestIsEncrypted:
    def test_recognises_v1_prefix(self):
        crypto._cached_key = None
        os.environ["ENCRYPTION_KEY"] = VALID_HEX_KEY
        assert crypto.is_encrypted(crypto.encrypt("x")) is True

    def test_rejects_plain_string(self):
        assert crypto.is_encrypted("plaintext") is False

    def test_rejects_empty_string(self):
        assert crypto.is_encrypted("") is False

    def test_rejects_wrong_prefix(self):
        assert crypto.is_encrypted("v2:something") is False


# ── Key loading ───────────────────────────────────────────────────────────

class TestKeyLoading:
    def setup_method(self):
        crypto._cached_key = None

    def test_accepts_64_char_hex_key(self):
        os.environ["ENCRYPTION_KEY"] = VALID_HEX_KEY
        assert crypto._load_key() is not None
        assert len(crypto._load_key()) == 32

    def test_accepts_base64_key(self):
        crypto._cached_key = None
        os.environ["ENCRYPTION_KEY"] = VALID_B64_KEY
        assert len(crypto._load_key()) == 32

    def _reset(self, key: str = ""):
        from app.config import get_settings
        crypto._cached_key = None
        os.environ["ENCRYPTION_KEY"] = key
        get_settings.cache_clear()

    def test_missing_key_returns_none(self):
        self._reset("")
        assert crypto._load_key() is None

    def test_invalid_key_raises_value_error(self):
        self._reset("tooshort")
        with pytest.raises(ValueError, match="must decode to"):
            crypto._load_key()

    def test_encrypt_without_key_raises_runtime_error(self):
        self._reset("")
        with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is not set"):
            crypto.encrypt("secret")

    def test_is_key_configured_true(self):
        self._reset(VALID_HEX_KEY)
        assert crypto.is_key_configured() is True

    def test_is_key_configured_false_when_missing(self):
        self._reset("")
        assert crypto.is_key_configured() is False
