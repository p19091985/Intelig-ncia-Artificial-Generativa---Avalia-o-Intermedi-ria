-- ============================================================
-- DML: Dados iniciais do módulo Fábrica de Pré-Moldados
-- ============================================================

-- 1. Clientes
INSERT OR IGNORE INTO fab_clientes (id, nome, documento, endereco) VALUES
    (1, 'Construtora Horizonte Ltda',   '12.345.678/0001-90', 'Rua das Palmeiras, 120 - São Paulo/SP'),
    (2, 'Engenharia Nova Era S.A.',     '98.765.432/0001-10', 'Av. Brasil, 3500 - Curitiba/PR'),
    (3, 'MRV Engenharia',              '08.343.492/0001-20', 'Av. Presidente Juscelino, 1455 - BH/MG'),
    (4, 'Concretiza Obras',            '45.123.789/0001-55', 'Rua dos Engenheiros, 88 - Campinas/SP'),
    (5, 'Fundações Brasil',            '33.222.111/0001-44', 'Rod. Castelo Branco, km 72 - Sorocaba/SP');

-- 2. Materiais
INSERT OR IGNORE INTO fab_materiais (id, tipo, nome, custo_kg, estoque_atual) VALUES
    -- Cimentos
    (1, 'Cimento', 'CP-I-32 (Comum)', 0.60, 5000.0),
    (2, 'Cimento', 'CP-I-40 (Comum)', 0.65, 5000.0),
    (3, 'Cimento', 'CP-II-E-32 (Composto Escória)', 0.62, 8000.0),
    (4, 'Cimento', 'CP-II-E-40 (Composto Escória)', 0.68, 4000.0),
    (5, 'Cimento', 'CP-II-Z-32 (Composto Pozolana)', 0.63, 6000.0),
    (6, 'Cimento', 'CP-II-F-32 (Composto Filler)', 0.65, 12000.0),
    (7, 'Cimento', 'CP-II-F-40 (Composto Filler)', 0.70, 5000.0),
    (8, 'Cimento', 'CP-III-32 (Alto Forno)', 0.58, 7000.0),
    (9, 'Cimento', 'CP-III-40 (Alto Forno)', 0.64, 4000.0),
    (10, 'Cimento', 'CP-IV-32 (Pozolânico)', 0.68, 5000.0),
    (11, 'Cimento', 'CP-V-ARI (Alta Resistência Inicial)', 0.85, 6000.0),
    (12, 'Cimento', 'Cimento Branco Estrutural', 1.20, 1000.0),

    -- Agregados Miúdos (Areia)
    (13, 'Areia', 'Areia Fina (Módulo < 2.0)', 0.07, 30000.0),
    (14, 'Areia', 'Areia Média Lavada (Rio)', 0.08, 50000.0),
    (15, 'Areia', 'Areia Grossa (Módulo > 3.0)', 0.09, 20000.0),
    (16, 'Areia', 'Areia Artificial (Pó de Pedra)', 0.05, 15000.0),
    (17, 'Areia', 'Areia de Quartzo', 0.12, 5000.0),

    -- Agregados Graúdos (Brita)
    (18, 'Brita', 'Pedrisco (Brita 0)', 0.09, 25000.0),
    (19, 'Brita', 'Brita 1 (9.5mm - 19mm)', 0.10, 40000.0),
    (20, 'Brita', 'Brita 2 (19mm - 25mm)', 0.11, 15000.0),
    (21, 'Brita', 'Brita 3 (25mm - 50mm)', 0.10, 5000.0),
    (22, 'Brita', 'Brita 4 (50mm - 76mm)', 0.09, 2000.0),
    (23, 'Brita', 'Rachão (Pedra de Mão)', 0.08, 3000.0),
    (24, 'Brita', 'Seixo Rolado Lavado', 0.15, 2000.0),

    -- Aditivos
    (25, 'Aditivo', 'Plastificante Padrão', 5.20, 500.0),
    (26, 'Aditivo', 'Superplastificante (Alta Eficiência)', 8.50, 300.0),
    (27, 'Aditivo', 'Incorporador de Ar', 7.00, 100.0),
    (28, 'Aditivo', 'Acelerador de Pega (C/ Cloreto)', 4.50, 200.0),
    (29, 'Aditivo', 'Acelerador de Pega (S/ Cloreto)', 6.50, 150.0),
    (30, 'Aditivo', 'Retardador de Pega', 6.00, 100.0),
    (31, 'Aditivo', 'Hidrofugante de Massa', 9.00, 200.0),
    (32, 'Aditivo', 'Curador Químico', 5.50, 100.0),

    -- Adições Minerais
    (33, 'Adição', 'Sílica Ativa', 2.50, 1000.0),
    (34, 'Adição', 'Metacaulim', 1.80, 1000.0),
    (35, 'Adição', 'Cinza Volante', 0.50, 2000.0),

    -- Pigmentos
    (36, 'Pigmento', 'Óxido de Ferro Vermelho', 12.00, 100.0),
    (37, 'Pigmento', 'Óxido de Ferro Amarelo', 12.00, 100.0),
    (38, 'Pigmento', 'Óxido de Ferro Preto', 11.00, 100.0),
    (39, 'Pigmento', 'Óxido de Cromo Verde', 25.00, 50.0),
    (40, 'Pigmento', 'Azul Ftalocianina', 30.00, 20.0),

    -- Fibras
    (41, 'Fibra', 'Polipropileno (Micro)', 15.00, 200.0),
    (42, 'Fibra', 'Polipropileno (Macro)', 18.00, 200.0),
    (43, 'Fibra', 'Fibra de Aço', 8.00, 500.0),
    (44, 'Fibra', 'Fibra de Vidro (AR)', 22.00, 100.0),

    -- Água
    (45, 'Água', 'Água Industrial', 0.005, 999999.0);

-- 3. Catálogo de Elementos Pré-Moldados
INSERT OR IGNORE INTO fab_tracos_padrao (id, nome, fck_alvo, traco_str, consumo_cimento_m3) VALUES
    (1, 'Traço Bloco Estrutural FCK 10',  10.0, '1 : 4.0 : 6.0 : 0.70 a/c', 180.0),
    (2, 'Traço Tubo FCK 25',              25.0, '1 : 2.5 : 3.5 : 0.55 a/c', 320.0),
    (3, 'Traço Viga FCK 30',              30.0, '1 : 2.2 : 3.1 : 0.50 a/c', 370.0),
    (4, 'Traço Pilar FCK 40',             40.0, '1 : 1.8 : 2.5 : 0.42 a/c', 450.0),
    (5, 'Traço Alta Resist. FCK 50',      50.0, '1 : 1.5 : 2.0 : 0.35 a/c', 520.0),
    (6, 'Traço Paver FCK 35',             35.0, '1 : 2.0 : 2.8 : 0.45 a/c', 400.0);

INSERT OR IGNORE INTO fab_catalogo_elementos (id, nome, tipo, volume_m3, fck_necessario, traco_id) VALUES
    (1, 'Bloco 14x19x39',        'Bloco',    0.0105,  10.0, 1),
    (2, 'Bloco 19x19x39',        'Bloco',    0.0141,  10.0, 1),
    (3, 'Bloco Canaleta 14x19x39','Bloco',   0.0090,  10.0, 1),
    (4, 'Meio-Bloco 14x19x19',   'Bloco',    0.0050,  10.0, 1),
    (5, 'Tubo Ø 400mm x 1m',     'Tubo',     0.0800,  25.0, 2),
    (6, 'Tubo Ø 600mm x 1m',     'Tubo',     0.1400,  25.0, 2),
    (7, 'Viga Baldrame 20x30 1m', 'Viga',     0.0600,  30.0, 3),
    (8, 'Viga T 40x60 6m',       'Viga',     0.1440,  35.0, 6),
    (9, 'Pilar 30x30 3m',        'Pilar',    0.2700,  40.0, 4),
    (10,'Laje Treliçada 12cm 1m²','Laje',     0.0720,  25.0, 2),
    (11,'Poste 9m DAN 300',      'Poste',    0.1500,  35.0, 6),
    (12,'Paver Intertravado 8cm', 'Piso',     0.0032,  35.0, 6);

-- 4. Traços Padrão


-- 5. Pedidos de exemplo
INSERT OR IGNORE INTO fab_pedidos (id, cliente_id, elemento_id, quantidade, data_pedido, data_entrega, status, traco_usado_id) VALUES
    (1, 1, 1, 5000,  '2026-02-01', '2026-02-20', 'Em Produção', 1),
    (2, 1, 2, 3000,  '2026-02-03', '2026-02-25', 'Pendente',    1),
    (3, 2, 5,  200,  '2026-02-05', '2026-03-01', 'Em Produção', 2),
    (4, 2, 7,  150,  '2026-02-06', '2026-03-05', 'Pendente',    3),
    (5, 3, 9,   50,  '2026-02-08', '2026-03-10', 'Pendente',    4),
    (6, 3, 12, 10000,'2026-02-10', '2026-03-15', 'Pendente',    6),
    (7, 4, 8,   80,  '2026-01-15', '2026-02-10', 'Concluído',   4),
    (8, 5, 10,  500, '2026-01-20', '2026-02-15', 'Concluído',   2),
    (9, 4, 11,   30, '2026-02-12', '2026-03-20', 'Pendente',    5),
    (10,1, 3,  2000, '2026-02-14', '2026-03-01', 'Em Produção', 1);

-- ============================================================
-- 6. Páginas do módulo Fábrica (Pipeline 12 páginas)
-- ============================================================
INSERT OR IGNORE INTO pagina (pagina_id, nome_arquivo, nome_amigavel) VALUES
    (2,  '02_🏭_Fabrica_Dashboard.py',              'Fábrica Dashboard'),
    (3,  '03_📝_Novo_Pedido.py',                     'Novo Pedido'),
    (4,  '04_🏭_Controle_Producao.py',               'Controle de Produção'),
    (5,  '05_🔬_Laboratorio_Engenharia.py',          'Laboratório de Engenharia'),
    (6,  '06_🧪_Banco_de_Tracos_Inteligente.py',     'Banco de Traços'),
    (7,  '07_🧱_Catalogo_Elementos.py',              'Catálogo Elementos'),
    (8,  '08_📦_Gestao_Materiais.py',                'Gestão de Materiais'),
    (9,  '09_🤝_Cadastro_Clientes.py',              'Cadastro de Clientes'),
    (10, '10_📜_Historico_Producao.py',              'Histórico Produção'),
    (11, '11_⚙️_Configuracoes.py',                   'Configurações'),
    (12, '12_ℹ️_Sobre.py',                           'Sobre');

-- 7. Permissões para Admin (perfil 1) — acesso total
INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id)
SELECT 1, pagina_id FROM pagina WHERE pagina_id BETWEEN 2 AND 12;

-- 8. Permissões: perfis específicos
-- Dashboard (2) para todos
INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id)
SELECT p.perfil_id, 2
FROM perfil_acesso p WHERE p.perfil_id IN (2, 3, 4);

-- Engenharia (2): Lab(5), Traços(6), Catálogo(7), Materiais(8), Produção(4)
INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id)
SELECT 2, pagina_id FROM pagina WHERE pagina_id IN (4, 5, 6, 7, 8);

-- Produção (3): Controle(4), Histórico(10), Materiais(8)
INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id)
SELECT 3, pagina_id FROM pagina WHERE pagina_id IN (4, 8, 10);

-- Comercial (4): Novo Pedido(3), Clientes(9), Catálogo(7)
INSERT OR IGNORE INTO perfil_pagina_permissao (perfil_id, pagina_id)
SELECT 4, pagina_id FROM pagina WHERE pagina_id IN (3, 7, 9);
