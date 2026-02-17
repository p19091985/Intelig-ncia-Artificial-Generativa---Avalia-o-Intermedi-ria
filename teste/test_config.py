"""
test_config.py — Testes do módulo de configuração.
Verifica carregamento de settings e valores padrão.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


class TestConfig:
    """Testes para o módulo config.py."""

    def test_database_enabled_is_bool(self):
        """DATABASE_ENABLED deve ser um booleano."""
        assert isinstance(config.DATABASE_ENABLED, bool)

    def test_initialize_database_is_bool(self):
        """INITIALIZE_DATABASE_ON_STARTUP deve ser um booleano."""
        assert isinstance(config.INITIALIZE_DATABASE_ON_STARTUP, bool)

    def test_max_login_attempts_positive(self):
        """MAX_LOGIN_ATTEMPTS deve ser um inteiro positivo."""
        assert isinstance(config.MAX_LOGIN_ATTEMPTS, int)
        assert config.MAX_LOGIN_ATTEMPTS > 0

    def test_app_title_not_empty(self):
        """APP_TITLE deve estar definido e não vazio."""
        assert hasattr(config, 'APP_TITLE')
        assert len(config.APP_TITLE) > 0

    def test_app_header_not_empty(self):
        """APP_HEADER deve estar definido e não vazio."""
        assert hasattr(config, 'APP_HEADER')
        assert len(config.APP_HEADER) > 0

    def test_app_title_contains_brand(self):
        """APP_TITLE deve conter o nome da empresa."""
        assert 'Garantia Eterna' in config.APP_TITLE

    def test_database_url_defined(self):
        """DATABASE_URL deve estar definida."""
        assert hasattr(config, 'DATABASE_URL')
