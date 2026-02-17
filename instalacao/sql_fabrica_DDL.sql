-- ============================================================
-- DDL: Tabelas do módulo Fábrica de Pré-Moldados
-- Prefixo: fab_
-- ============================================================
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS fab_clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE,
    endereco TEXT
);

CREATE TABLE IF NOT EXISTS fab_materiais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('Cimento', 'Areia', 'Brita', 'Aditivo', 'Água', 'Adição', 'Pigmento', 'Fibra')),
    nome TEXT NOT NULL UNIQUE,
    custo_kg REAL NOT NULL DEFAULT 0.0,
    estoque_atual REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS fab_catalogo_elementos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    tipo TEXT NOT NULL,
    volume_m3 REAL NOT NULL,
    fck_necessario REAL NOT NULL,
    traco_id INTEGER,
    FOREIGN KEY (traco_id) REFERENCES fab_tracos_padrao(id)
);

CREATE TABLE IF NOT EXISTS fab_tracos_padrao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    fck_alvo REAL NOT NULL,
    traco_str TEXT NOT NULL,
    consumo_cimento_m3 REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fab_pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    elemento_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    data_pedido TEXT NOT NULL DEFAULT (date('now')),
    data_entrega TEXT,
    status TEXT NOT NULL DEFAULT 'Pendente' CHECK(status IN ('Pendente', 'Em Produção', 'Concluído', 'Cancelado')),
    traco_usado_id INTEGER,
    FOREIGN KEY (cliente_id)  REFERENCES fab_clientes(id),
    FOREIGN KEY (elemento_id) REFERENCES fab_catalogo_elementos(id),
    FOREIGN KEY (traco_usado_id) REFERENCES fab_tracos_padrao(id)
);
