import configparser
from pathlib import Path
import logging
import sys
from typing import Dict, Tuple
import os
_config_path = Path(__file__).parent / 'config_settings.ini'
_parser = configparser.ConfigParser()
if not _config_path.is_file():
    print(f"Aviso: '{_config_path.name}' não encontrado. Criando arquivo padrão.", file=sys.stderr)
    default_ini_content = '[Settings]\ndatabase_enabled = True\ninitialize_database_on_startup = True\nredirect_console_to_log = False\nenable_theme_menu = True\nlog_level = DEBUG\nlog_format = [%(asctime)s] [%(name)s] [%(levelname)-8s] - %(message)s\n'
    try:
        with open(_config_path, 'w', encoding='utf-8') as f:
            f.write(default_ini_content)
    except Exception as e:
        print(f"Erro crítico: Não foi possível criar '{_config_path}': {e}", file=sys.stderr)
        sys.exit(1)
try:
    _parser.read(_config_path, encoding='utf-8')
    if 'Settings' not in _parser:
        print('Aviso: Seção [Settings] não encontrada. Usando padrões.', file=sys.stderr)
        _parser['Settings'] = {}
except Exception as e:
    print(f'Erro ao ler .ini: {e}. Usando padrões.', file=sys.stderr)
    _parser['Settings'] = {}

def _get_boolean_setting(key, default=False):
    try:
        return _parser.getboolean('Settings', key, fallback=default)
    except (configparser.Error, ValueError):
        return default

def _get_string_setting(key, default=''):
    try:
        return _parser.get('Settings', key, fallback=default)
    except (configparser.Error, ValueError):
        return default
DATABASE_ENABLED = _get_boolean_setting('database_enabled', default=True)
INITIALIZE_DATABASE_ON_STARTUP = _get_boolean_setting('initialize_database_on_startup', default=True)
REDIRECT_CONSOLE_TO_LOG = _get_boolean_setting('redirect_console_to_log', default=False)
ENABLE_THEME_MENU = _get_boolean_setting('enable_theme_menu', default=True)
MAX_LOGIN_ATTEMPTS = 3
APP_TITLE = _get_string_setting('app_title', default='🚀 Painel de Controle Moderno')
APP_HEADER = _get_string_setting('app_header', default='Sistema de Demonstração')
LOG_LEVEL_STR = _get_string_setting('log_level', default='INFO').upper()
LOG_FORMAT = _get_string_setting('log_format', default='[%(asctime)s] [%(name)s] [%(levelname)-8s] - %(message)s')
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)