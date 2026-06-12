"""
Unit tests for app.config

Verifies Settings reads env vars correctly, applies defaults,
and the is_sqlite property works for both DB drivers.
"""

import os
import pytest
from functools import lru_cache


def _fresh_settings(**overrides):
    """Return a Settings instance with a clean lru_cache, applying overrides via env."""
    from app.config import Settings
    for k, v in overrides.items():
        os.environ[k.upper()] = v
    s = Settings()
    for k in overrides:
        os.environ.pop(k.upper(), None)
    return s


class TestSettingsDefaults:
    def test_app_name_default(self):
        from app.config import get_settings
        assert get_settings().app_name == "Nexus Oracle"

    def test_debug_default_false(self):
        from app.config import get_settings
        assert get_settings().debug is False

    def test_log_level_default(self):
        from app.config import get_settings
        assert get_settings().log_level == "info"

    def test_jwt_algorithm_default(self):
        from app.config import get_settings
        assert get_settings().jwt_algorithm == "HS256"

    def test_oracle_port_default(self):
        from app.config import get_settings
        assert get_settings().oracle_port == 8000


class TestIsSqlite:
    def test_sqlite_url_detected(self):
        s = _fresh_settings(database_url="sqlite+aiosqlite:///./dev.db")
        assert s.is_sqlite is True

    def test_postgres_url_not_sqlite(self):
        s = _fresh_settings(database_url="postgresql+asyncpg://user:pass@localhost/nexus")
        assert s.is_sqlite is False

    def test_test_db_url_is_sqlite(self):
        s = _fresh_settings(database_url="sqlite+aiosqlite:///./test.db")
        assert s.is_sqlite is True


class TestSettingsFromEnv:
    def test_reads_jwt_secret_from_env(self):
        s = _fresh_settings(jwt_secret="my-test-secret")
        assert s.jwt_secret == "my-test-secret"

    def test_reads_log_level_from_env(self):
        s = _fresh_settings(log_level="debug")
        assert s.log_level == "debug"

    def test_reads_oracle_port_from_env(self):
        s = _fresh_settings(oracle_port="9000")
        assert s.oracle_port == 9000
