import sys
import os
import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import StaticPool


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from persistencia.database import DatabaseManager
from persistencia.unit_of_work import UnitOfWork


config.DATABASE_URL = 'sqlite:///:memory:'
config.DATABASE_ENABLED = True

@pytest.fixture(scope='session')
def engine():
    
    db_engine = create_engine(
        config.DATABASE_URL, 
        connect_args={'check_same_thread': False}, 
        poolclass=StaticPool
    )
    
    
    with db_engine.connect() as conn:
        statements = [
            "CREATE TABLE IF NOT EXISTS perfil_acesso (perfil_id INTEGER PRIMARY KEY AUTOINCREMENT, nome_perfil TEXT NOT NULL UNIQUE)",
            "CREATE TABLE IF NOT EXISTS usuarios (usuario_id INTEGER PRIMARY KEY AUTOINCREMENT, login_usuario TEXT NOT NULL UNIQUE, senha_criptografada TEXT NOT NULL, nome_completo TEXT NOT NULL, perfil_id INTEGER NOT NULL, FOREIGN KEY (perfil_id) REFERENCES perfil_acesso(perfil_id))",
            "CREATE TABLE IF NOT EXISTS pagina (pagina_id INTEGER PRIMARY KEY AUTOINCREMENT, nome_arquivo TEXT NOT NULL UNIQUE, nome_amigavel TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS perfil_pagina_permissao (permissao_id INTEGER PRIMARY KEY AUTOINCREMENT, perfil_id INTEGER NOT NULL, pagina_id INTEGER NOT NULL, FOREIGN KEY (perfil_id) REFERENCES perfil_acesso(perfil_id) ON DELETE CASCADE, FOREIGN KEY (pagina_id) REFERENCES pagina(pagina_id) ON DELETE CASCADE, UNIQUE(perfil_id, pagina_id))",
            # ── Tabelas da Fábrica ────────────────────────────
            "CREATE TABLE IF NOT EXISTS fab_clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, documento TEXT, endereco TEXT)",
            "CREATE TABLE IF NOT EXISTS fab_materiais (id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL CHECK(tipo IN ('Cimento', 'Areia', 'Brita', 'Aditivo', 'Água', 'Adição', 'Pigmento', 'Fibra')), nome TEXT NOT NULL, custo_kg REAL NOT NULL DEFAULT 0.0, estoque_atual REAL NOT NULL DEFAULT 0.0)",
            "CREATE TABLE IF NOT EXISTS fab_catalogo_elementos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, tipo TEXT NOT NULL, volume_m3 REAL NOT NULL, fck_necessario REAL NOT NULL DEFAULT 25.0, traco_id INTEGER, FOREIGN KEY (traco_id) REFERENCES fab_tracos_padrao(id))",
            "CREATE TABLE IF NOT EXISTS fab_tracos_padrao (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, fck_alvo REAL NOT NULL, traco_str TEXT NOT NULL, consumo_cimento_m3 REAL NOT NULL DEFAULT 350.0)",
            "CREATE TABLE IF NOT EXISTS fab_pedidos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, elemento_id INTEGER NOT NULL, quantidade INTEGER NOT NULL DEFAULT 1, data_pedido TEXT NOT NULL DEFAULT (DATE('now')), data_entrega TEXT, status TEXT NOT NULL DEFAULT 'Pendente', traco_usado_id INTEGER, FOREIGN KEY (cliente_id) REFERENCES fab_clientes(id), FOREIGN KEY (elemento_id) REFERENCES fab_catalogo_elementos(id), FOREIGN KEY (traco_usado_id) REFERENCES fab_tracos_padrao(id))",
            # ── Seed data ────────────────────────────────────
            "INSERT OR IGNORE INTO fab_clientes (id, nome, documento) VALUES (1, 'Construtora Teste', '12345678000100')",
            "INSERT OR IGNORE INTO fab_materiais (id, tipo, nome, custo_kg, estoque_atual) VALUES (1, 'Cimento', 'CP-IV-32', 0.68, 5000.0)",
            "INSERT OR IGNORE INTO fab_tracos_padrao (id, nome, fck_alvo, traco_str, consumo_cimento_m3) VALUES (1, 'FCK 10 Econômico', 10, '1:3.5:4.5:0.68 a/c', 250)",
            "INSERT OR IGNORE INTO fab_catalogo_elementos (id, nome, tipo, volume_m3, fck_necessario, traco_id) VALUES (1, 'Bloco 14x19x39', 'Bloco', 0.0106, 10, 1)",
        ]
        
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    
    DatabaseManager._engine = db_engine
    return db_engine

@pytest.fixture(autouse=True)
def version_reset(engine):
    
    pass

@pytest.fixture
def uow(engine):
    
    
    return UnitOfWork()
