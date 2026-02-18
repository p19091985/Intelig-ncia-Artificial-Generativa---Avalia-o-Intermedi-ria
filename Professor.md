---
title: "Arquitetura de Simulação — O Desenvolvimento do SystemConcreto"
author: Patrik
date: 2026-02-18
context: "Avaliação Intermediária — IA Generativa"
agentes: "Claude 4.6 Opus · Gemini 1.5 Pro · IDE Antigravity"
---

# Arquitetura de Simulação — O Desenvolvimento do SystemConcreto

> **Documento de Processo:** Este documento descreve, em detalhe, como o **SystemConcreto** foi concebido, projetado e construído. Ele percorre cada decisão técnica, cada interação com os agentes de IA e cada problema encontrado durante o desenvolvimento — incluindo o que funcionou, o que falhou e o que exigiu intervenção humana.

---

## Sumário

1. [Contexto e Objetivo](#1-contexto-e-objetivo)
2. [Fase 0 — A Herança Técnica (NexlifyStreamlit)](#2-fase-0--a-herança-técnica-nexlifystreamlit)
3. [Fase 1 — Migração Arquitetural: De Script para Enterprise](#3-fase-1--migração-arquitetural-de-script-para-enterprise)
4. [Fase 2 — Pivô de Domínio: De CRUD Genérico para Engenharia Civil](#4-fase-2--pivô-de-domínio-de-crud-genérico-para-engenharia-civil)
5. [Fase 3 — O Motor de Inferência Simulada (Mock AI)](#5-fase-3--o-motor-de-inferência-simulada-mock-ai)
6. [Fase 4 — Frontend e Gestão de Estado (Streamlit)](#6-fase-4--frontend-e-gestão-de-estado-streamlit)
7. [Fase 5 — Segurança, Testes e Polimento para Entrega](#7-fase-5--segurança-testes-e-polimento-para-entrega)
8. [O Que Funcionou — Experiência Positiva com os Agentes](#8-o-que-funcionou--experiência-positiva-com-os-agentes)
9. [O Que Não Funcionou — Falhas, Alucinações e Intervenção Humana](#9-o-que-não-funcionou--falhas-alucinações-e-intervenção-humana)
10. [Conclusão Técnica e Arquitetura Final](#10-conclusão-técnica-e-arquitetura-final)

---

## 1. Contexto e Objetivo

A avaliação exigia um sistema que:

| Requisito | Resposta do Projeto |
|---|---|
| Resolver um **problema real e desafiador** | Gestão completa de uma Fábrica de Pré-Moldados de Concreto |
| Ser construído **inteiramente por agentes de IA** | Desenvolvido com **Claude 4.6 Opus** e **Gemini 1.5 Pro**, operando na IDE **Antigravity** |
| **Não integrar LLMs** na execução — usar _Mock AI_ | Criado `ai_concreto.py` com lógica determinística + ruído estocástico |
| Publicar um **endpoint funcional** | Streamlit com sistema de autenticação completo |
| Manter um **repositório GitHub organizado** | Commits incrementais documentando cada fase de desenvolvimento |

> [!IMPORTANT]
> A premissa do projeto era **enganosamente simples**: usar IA para construir uma aplicação, mas sem que a aplicação final use IA real. A complexidade emergiu na arquitetura necessária para simular comportamentos inteligentes de forma convincente.

---

## 2. Fase 0 — A Herança Técnica (NexlifyStreamlit)

### O Ponto de Partida

O projeto **não partiu do zero**. A base foi o **NexlifyStreamlit** (`easyToUseWeb`), um boilerplate Streamlit desenvolvido previamente com suporte a autenticação, logs e configurações via banco de dados.

### O Problema Identificado

Uma análise técnica inicial revelou que a arquitetura do Nexlify era **insuficiente** para a complexidade de uma planta industrial:

```
┌─────────────────────────────────────────────────────┐
│                 ARQUITETURA LEGADA                   │
│                                                     │
│  GenericRepository (@staticmethod)                  │
│  ├── Conexão aberta/fechada a CADA query            │
│  ├── Sem controle transacional (ACID)               │
│  ├── Sem rollback automático                        │
│  └── Queries misturadas com lógica de conexão       │
│                                                     │
│  Problema: Para um CRUD de gatos, bastava.          │
│  Para uma fábrica de concreto? RISCO INACEITÁVEL.   │
└─────────────────────────────────────────────────────┘
```

**Cenário de risco concreto:** Um pedido de venda dispara baixas em múltiplos estoques (cimento, areia, brita) e gera ordens de produção. Se o cimento fosse baixado mas a brita falhasse, o estado do banco ficaria **inconsistente** — sem mecanismo de rollback.

> [!CAUTION]
> **Decisão crítica tomada aqui:** Antes de adicionar qualquer funcionalidade de negócio, era necessário **reconstruir a camada de persistência inteira**. Sem ACID, o sistema seria um castelo de cartas.

---

## 3. Fase 1 — Migração Arquitetural: De Script para Enterprise

> **Migração:** `NexlifyStreamlit-easyToUseWeb` → `easyToUseWebWithDatabase`

Esta foi a **maior mudança técnica** do projeto. Instruí os agentes Claude e Gemini a realizar uma refatoração completa em quatro frentes simultâneas.

### 3.1. Evolução da Camada de Persistência

#### Como era (Antigo)

```python
# Padrão monolítico com @staticmethod
# Cada chamada abre e fecha uma conexão independente
resultado = GenericRepository.execute_query_to_dataframe(sql, params)
```

*   **Problema 1:** Controle transacional manual ou inexistente.
*   **Problema 2:** Se uma operação falhasse no meio de um processo, não havia rollback seguro.
*   **Problema 3:** Código misturava regras de conexão com execução de queries.

#### Como ficou (Novo) — Unit of Work + Repository Pattern

**Decisão:** Implementar o padrão **Unit of Work (UoW)** combinado com **Repository Pattern**, garantindo atomicidade transacional.

> [!NOTE]
> **Ref:** [`persistencia/unit_of_work.py`](persistencia/unit_of_work.py)

A classe `UnitOfWork` foi desenhada como um **Context Manager** (`__enter__`, `__exit__`):

```python
with UnitOfWork() as uow:
    # Todas as operações compartilham a mesma conexão e transação
    uow.pedidos.criar(...)
    uow.estoque.baixar(...)
    # Se ocorrer QUALQUER erro → __exit__ chama self.transaction.rollback()
    # Se TUDO der certo         → __exit__ chama self.transaction.commit()
```

**Componentes criados:**

| Arquivo | Função |
|---|---|
| [`unit_of_work.py`](persistencia/unit_of_work.py) | Context Manager que gerencia transações atômicas |
| [`repositorios/base.py`](persistencia/repositorios/base.py) | Classe base `BaseRepository` com lógica SQL reutilizável |
| [`repositorios/usuario.py`](persistencia/repositorios/usuario.py) | CRUD de usuários |
| [`repositorios/permissoes.py`](persistencia/repositorios/permissoes.py) | Gestão de perfis de acesso |
| [`repositorios/paginas.py`](persistencia/repositorios/paginas.py) | Mapeamento de páginas e permissões |
| [`repositorios/fabrica_repo.py`](persistencia/repositorios/fabrica_repo.py) | Repositório especializado do domínio Fábrica |

**Tratamento sofisticado de exceções no `__exit__`:**

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type == StopException:
        # st.stop() do Streamlit NÃO é um erro de banco — COMMIT
        self.transaction.commit()
    elif exc_type == SimulationRollback:
        # Simulação da IA finalizou — ROLLBACK preventivo
        self.transaction.rollback()
    elif exc_type:
        # Erro real — ROLLBACK
        self.transaction.rollback()
    else:
        # Sucesso — COMMIT
        self.transaction.commit()
```

> [!TIP]
> **Detalhe técnico:** O `UnitOfWork` trata o `StopException` do Streamlit (gerado por `st.stop()`) como um encerramento normal e faz **commit** em vez de rollback. Sem essa lógica, toda interrupção de fluxo perderia os dados já processados.

### 3.2. Reestruturação de Pastas e Organização

A estrutura de arquivos foi reorganizada para separar responsabilidades:

| Antes (Legado) | Depois (Enterprise) | Motivo |
|---|---|---|
| `pages/` | `app_pages/` | Evitar conflitos com o roteamento automático do Streamlit |
| `2_📋_Painel_Modelo.py` | `05_📋_Painel_Modelo.py` | Padronização de ordem com prefixo numérico de 2 dígitos |
| Lógica de negócio nas páginas | `components/servicos_gerenciador.py` | Separação de responsabilidades (Service Layer) |
| Sem testes | `teste/` com `conftest.py`, `test_*.py` | Adoção de **pytest** para testes automatizados |

### 3.3. Padronização e Qualidade de Código

| Aspecto | Antes | Depois |
|---|---|---|
| **Logging** | `logging.basicConfig()` global | `logging.getLogger(__name__)` por módulo — rastreamento granular |
| **Tipagem** | Ausente | Type Hints em todo lugar: `connection: Connection`, `-> pd.DataFrame` |
| **Exceções** | Genéricas | Específicas: `SimulationRollback`, tratamento de `StopException` |

> **Prompt usado (Claude):** *"Refatore a camada de persistência do NexlifyStreamlit implementando o padrão Unit of Work com SQLAlchemy. O UoW deve ser um context manager que garanta atomicidade ACID. Crie uma BaseRepository que receba a conexão por injeção de dependência."*
>
> **Resultado:** O Claude gerou a estrutura completa em uma única iteração, incluindo o tratamento de `StopException` — algo que eu não havia solicitado explicitamente, mas que demonstrou compreensão profunda do ecossistema Streamlit.

---

## 4. Fase 2 — Pivô de Domínio: De CRUD Genérico para Engenharia Civil

> **Migração:** `easyToUseWebWithDatabase` → `SystemConcreto` (Avaliação Intermediária)

O sistema original era um esqueleto com autenticação e um exemplo de cadastro de gatos. O pivô reorientou **completamente** o propósito do software para gestão de uma **Fábrica de Pré-Moldados de Concreto**.

### 4.1. Modelagem de Dados — A Fábrica em SQL

Utilizando a IDE Antigravity, instruí os agentes a gerar um esquema DDL robusto. A modelagem resultou no arquivo [`sql_fabrica_DDL.sql`](instalacao/sql_fabrica_DDL.sql), estruturado em cinco entidades com prefixo `fab_` para isolamento de namespace:

> [!NOTE]
> **Ref:** [`instalacao/sql_fabrica_DDL.sql`](instalacao/sql_fabrica_DDL.sql)

```sql
-- 1. Clientes da fábrica
CREATE TABLE IF NOT EXISTS fab_clientes (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome     TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE,
    endereco TEXT
);

-- 2. Estoque de insumos com tipo validado
CREATE TABLE IF NOT EXISTS fab_materiais (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT NOT NULL CHECK(tipo IN
                  ('Cimento','Areia','Brita','Aditivo','Água','Adição','Pigmento','Fibra')),
    nome          TEXT NOT NULL UNIQUE,
    custo_kg      REAL NOT NULL DEFAULT 0.0,
    estoque_atual REAL NOT NULL DEFAULT 0.0
);

-- 3. "Receita" do concreto com resistência alvo
CREATE TABLE IF NOT EXISTS fab_tracos_padrao (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nome              TEXT NOT NULL UNIQUE,
    fck_alvo          REAL NOT NULL,
    traco_str         TEXT NOT NULL,
    consumo_cimento_m3 REAL NOT NULL
);

-- 4. Catálogo de produtos finais com FK para traço
CREATE TABLE IF NOT EXISTS fab_catalogo_elementos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT NOT NULL UNIQUE,
    tipo           TEXT NOT NULL,
    volume_m3      REAL NOT NULL,
    fck_necessario REAL NOT NULL,
    traco_id       INTEGER,
    FOREIGN KEY (traco_id) REFERENCES fab_tracos_padrao(id)
);

-- 5. Tabela transacional central com FKs múltiplas
CREATE TABLE IF NOT EXISTS fab_pedidos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id     INTEGER NOT NULL,
    elemento_id    INTEGER NOT NULL,
    quantidade     INTEGER NOT NULL,
    data_pedido    TEXT NOT NULL DEFAULT (date('now')),
    data_entrega   TEXT,
    status         TEXT NOT NULL DEFAULT 'Pendente'
                   CHECK(status IN ('Pendente','Em Produção','Concluído','Cancelado')),
    traco_usado_id INTEGER,
    FOREIGN KEY (cliente_id)     REFERENCES fab_clientes(id),
    FOREIGN KEY (elemento_id)    REFERENCES fab_catalogo_elementos(id),
    FOREIGN KEY (traco_usado_id) REFERENCES fab_tracos_padrao(id)
);
```

**Decisões de design tomadas:**

1.  **`CHECK` constraints** no banco, não no código Python — garante integridade independente da UI.
2.  **Normalização via `traco_id` como Foreign Key** — um elemento de catálogo aponta para uma receita, evitando duplicação de dados químicos.
3.  **Prefixo `fab_`** — isola o namespace das tabelas industriais das tabelas administrativas (usuários, permissões), permitindo convivência no mesmo banco SQLite.

### 4.2. Integração no Unit of Work

O arquivo `unit_of_work.py` foi modificado para incluir o novo domínio:

```python
# ANTES: Só carregava repositórios administrativos
self.usuarios   = UsuarioRepository(self.connection)
self.permissoes = PermissaoRepository(self.connection)
self.paginas    = PaginaRepository(self.connection)

# DEPOIS: Adicionado o repositório da fábrica na mesma transação
self.fabrica = FabricaRepository(self.connection)
```

> **Impacto:** Todas as operações da fábrica (criar pedido, baixar estoque, gerar traço) agora participam da **mesma transação atômica** — se a baixa de cimento falhar, o pedido inteiro é revertido.

### 4.3. Repositório Especializado — Queries Complexas

> [!NOTE]
> **Ref:** [`persistencia/repositorios/fabrica_repo.py`](persistencia/repositorios/fabrica_repo.py)

O `FabricaRepository` contém queries de alta complexidade. O método `get_all_pedidos()` realiza **quatro JOINs simultâneos** para montar a visão do dashboard:

```sql
SELECT p.id, c.nome AS cliente, e.nome AS elemento,
       e.volume_m3, t.consumo_cimento_m3, p.status, p.data_pedido
FROM   fab_pedidos p
JOIN   fab_clientes c            ON p.cliente_id     = c.id
JOIN   fab_catalogo_elementos e  ON p.elemento_id    = e.id
LEFT JOIN fab_tracos_padrao t    ON p.traco_usado_id  = t.id
```

> **Prompt usado (Claude):** *"Crie um FabricaRepository estendendo BaseRepository, com métodos CRUD para todas as 5 tabelas fab_. O get_all_pedidos deve retornar dados denormalizados com JOINs para exibição direta no dashboard."*
>
> **Resultado:** O Claude gerou o repositório com **todas as queries corretas** na primeira iteração, incluindo o `LEFT JOIN` para pedidos sem traço definido — um detalhe sutil que evitaria erros em pedidos pendentes.

---

## 5. Fase 3 — O Motor de Inferência Simulada (Mock AI)

> **Desafio central:** Como simular uma IA sem usar uma IA?

A solução técnica reside no arquivo [`components/ai_concreto.py`](components/ai_concreto.py) — 265 linhas de lógica determinística que simulam o comportamento de um modelo generativo.

### 5.1. Abordagem: Modelagem Estocástica Determinística

Em vez de usar uma rede neural caixa-preta, codificamos as **regras da Engenharia Civil** (especificamente a **Lei de Abrams** para relação água/cimento), mas injetamos **ruído controlado** para simular a variação de um modelo generativo.

### 5.2. Função `sugerir_traco()` — Análise Detalhada

> [!TIP]
> **Ref:** [`components/ai_concreto.py`](components/ai_concreto.py) — linhas 11–193

**Parâmetros de entrada:**

```python
def sugerir_traco(
    fck: float,                        # Resistência desejada (MPa)
    slump: float = 100.0,              # Abatimento do tronce de cone (mm)
    agregado_max: str = "Brita 1",     # Tipo de agregado
    materiais_selecionados: dict = None # Materiais disponíveis em estoque
) -> dict:
```

**Passo 1 — Seleção de Cimento (Lógica Fuzzy):**

O sistema decide o tipo de cimento baseado no FCK, simulando o "raciocínio" de um engenheiro:

| FCK (MPa) | Cimento Selecionado | Justificativa |
|---|---|---|
| > 40 | CP-V ARI (Alta Resistência Inicial) | Necessário para concretos de alta performance |
| 20–40 | CP-IV (Pozolânico) | Equilíbrio entre resistência e custo |
| < 20 | CP-II (Composto) | Suficiente para aplicações de baixa solicitação |

**Passo 2 — Cálculo da Relação Água/Cimento (a/c):**

```python
relacao_ac = round(0.42 + (40 - fck) * 0.01, 2)
# Adição de "jitter" para simular a "temperatura" de um LLM:
relacao_ac += random.uniform(0, 0.05)
```

> **Por que o jitter?** Cada "geração" da IA é **ligeiramente única** — se o usuário pedir o mesmo traço duas vezes, receberá valores sutilmente diferentes, mimetizando a temperatura de um modelo generativo. Isso torna a simulação **realista e convincente**.

**Passo 3 — Cálculo de Agregados (Algoritmo de Empacotamento Simplificado):**

Implementamos um dicionário `brita_map` que define fatores de proporção para Brita 0 e Brita 1. O algoritmo ajusta a quantidade de areia **inversamente proporcional** à quantidade de cimento para manter o volume de 1m³.

**Passo 4 — Geração de Justificativa Técnica:**

A função retorna um dicionário completo com `materiais_por_m3`, `custo_estimado` e uma `justificativa` textual detalhada — simulando o output narrativo que um LLM produziria.

### 5.3. Função `otimizar_traco()` — Simulação de Agente Econômico

> [!NOTE]
> **Ref:** [`components/ai_concreto.py`](components/ai_concreto.py) — linhas 196–264

A função simula um **agente especialista em redução de custos**:

1.  **Reduz** o consumo de cimento em 8% (`consumo * 0.92`)
2.  **Compensa** a perda de trabalhabilidade adicionando superplastificante (0.8%)
3.  **Recalcula** o custo total e retorna a "Economia Líquida" gerada

```python
# Estratégia de otimização codificada
cimento_otimizado = consumo_original * 0.92          # -8% de cimento
aditivo_compensacao = consumo_original * 0.008       # +0.8% de superplastificante
economia = custo_original - custo_otimizado          # Economia real em R$
```

> **Prompt usado (Gemini):** *"Crie um módulo ai_concreto.py que simule uma IA de engenharia de concreto. A função sugerir_traco deve receber FCK e Slump e retornar um traço completo com justificativa técnica. Use algoritmos determinísticos com fatores de aleatoriedade para simular variação de um LLM."*
>
> **Resultado:** O Gemini gerou a estrutura base corretamente, mas a fórmula da Lei de Abrams teve que ser **ajustada manualmente** para ficar dentro de faixas técnicas realistas. A justificativa textual gerada foi de excelente qualidade.

---

## 6. Fase 4 — Frontend e Gestão de Estado (Streamlit)

A escolha do Streamlit trouxe velocidade de desenvolvimento, mas impôs um desafio técnico severo: **o ciclo de vida da aplicação**. O Streamlit é fundamentalmente *stateless* — o script inteiro roda novamente a cada interação do usuário.

### 6.1. O Problema da "Amnésia da IA"

Quando o usuário clicava em **"Gerar Traço com IA"**, o backend `ai_concreto.py` retornava os dados. Porém, ao clicar em **"Salvar no Banco"**, a página **recarregava**, as variáveis locais eram limpas e o traço gerado se **perdia** antes de ser persistido.

### 6.2. A Solução — Persistência de Sessão (`st.session_state`)

> [!NOTE]
> **Ref:** [`app_pages/06_🧪_Banco_de_Tracos_Inteligente.py`](app_pages/06_🧪_Banco_de_Tracos_Inteligente.py)

Implementamos um padrão de retenção de dados temporários:

```
┌─────────────────────────────────────────────────────────────┐
│  Fluxo de Dados com Session State                           │
│                                                             │
│  1. Botão "Gerar" → Chama sugerir_traco()                  │
│     └── Grava resultado em st.session_state['traco_gerado'] │
│                                                             │
│  2. Recarregamento da página (automático do Streamlit)      │
│     └── Verifica: 'traco_gerado' in st.session_state?       │
│                                                             │
│  3. Se SIM → Exibe resultado e habilita botão "Salvar"      │
│                                                             │
│  4. Botão "Salvar" → Lê do session_state                    │
│     └── Persiste via UoW → Limpa o estado                   │
└─────────────────────────────────────────────────────────────┘
```

### 6.3. Páginas Desenvolvidas

A pasta `app_pages/` foi preenchida com **12 páginas** especializadas, substituindo os exemplos genéricos:

| Página | Arquivo | Descrição |
|---|---|---|
| 🏠 Página Inicial | `01_🏠_Pagina_Inicial.py` | Landing page com overview do sistema |
| 🏭 Dashboard Executivo | `02_🏭_Fabrica_Dashboard.py` | KPIs de produção, alertas de estoque, gráficos Plotly |
| 📝 Novo Pedido | `03_📝_Novo_Pedido.py` | Formulário de entrada de vendas com validação |
| 🏭 Controle de Produção | `04_🏭_Controle_Producao.py` | Gestão do fluxo produtivo |
| 🔬 Laboratório | `05_🔬_Laboratorio_Engenharia.py` | Área técnica de engenharia |
| 🧪 Traços Inteligentes | `06_🧪_Banco_de_Tracos_Inteligente.py` | Interface do Mock AI |
| 🧱 Catálogo de Elementos | `07_🧱_Catalogo_Elementos.py` | CRUD de produtos finais (Pilares, Vigas) |
| 📦 Gestão de Materiais | `08_📦_Gestao_Materiais.py` | Controle de estoque de insumos |
| 🤝 Cadastro de Clientes | `09_🤝_Cadastro_Clientes.py` | CRUD completo de clientes |
| 📜 Histórico de Produção | `10_📜_Historico_Producao.py` | Log de pedidos e produção |
| ⚙️ Configurações | `11_⚙️_Configuracoes.py` | Admin: permissões, perfis, páginas |
| ℹ️ Sobre | `12_ℹ️_Sobre.py` | Informações do sistema |

### 6.4. Dashboard e Visualização de Dados

Para o painel executivo (`02_🏭_Fabrica_Dashboard.py`), utilizamos a biblioteca **Plotly Express**. A integração exigiu que o retorno do banco (SQLAlchemy Row objects) fosse convertido para DataFrames do Pandas.

O método `GenericRepository.execute_query_to_dataframe` foi modificado para normalizar nomes de colunas para minúsculas, garantindo compatibilidade com o Plotly.

---

## 7. Fase 5 — Segurança, Testes e Polimento para Entrega

### 7.1. Controle de Acesso (RBAC) Dinâmico

> [!NOTE]
> **Ref:** [`components/servicos_gerenciador.py`](components/servicos_gerenciador.py)

O sistema de controle de acesso migrou de verificações manuais (`check_access([])`) para um sistema **dinâmico baseado em banco de dados**:

```python
def get_allowed_roles_for_page(page_filename: str) -> List[str]:
    with UnitOfWork() as uow:
        df = uow.paginas.get_allowed_roles_for_page(page_filename)
    if df.empty:
        return ['Administrador Global']  # Fallback seguro
    role_list = df['nome_perfil'].tolist()
    if 'Administrador Global' not in role_list:
        role_list.append('Administrador Global')
    return role_list
```

**Técnica:** O middleware intercepta o carregamento da página, captura o nome do arquivo (`Path(__file__).name`), consulta a tabela `permissoes` e, se o usuário não tiver a *role* necessária, invoca `st.stop()` — impedindo acesso mesmo por URL direta.

### 7.2. Suíte de Testes Automatizados

A adoção de **pytest** foi uma evolução significativa em relação à versão legada (sem testes):

| Arquivo de Teste | Cobertura |
|---|---|
| [`conftest.py`](teste/conftest.py) | Fixtures compartilhadas e setup de banco de teste |
| [`test_db_connection.py`](teste/test_db_connection.py) | Validação de conectividade com o banco |
| [`test_unit_of_work.py`](teste/test_unit_of_work.py) | Testes de atomicidade e rollback do UoW |
| [`test_ai_concreto.py`](teste/test_ai_concreto.py) | Validação das funções `sugerir_traco` e `otimizar_traco` |
| [`test_repos.py`](teste/test_repos.py) | Testes CRUD dos repositórios |
| [`test_config.py`](teste/test_config.py) | Validação de configurações |

### 7.3. Ferramentas de Instalação

A pasta `instalacao/` contém **ferramentas GUI** criadas com Tkinter para facilitar o setup do projeto em qualquer máquina:

| Ferramenta | Descrição |
|---|---|
| `config_banco_gui.py` | Interface para configurar conexão com o banco |
| `gerador_credenciais_gui.py` | Gerador seguro de credenciais de admin |
| `gerador_schema_gui.py` | Executor visual de scripts DDL |
| `limpeza_dev.py` | Reset de ambiente de desenvolvimento |
| `reset_database_template.py` | Template para reinicialização do banco |

---

## 8. O Que Funcionou — Experiência Positiva com os Agentes

### Claude 4.6 Opus — Pontos Fortes

| Área | Resultado | Exemplo |
|---|---|---|
| **Arquitetura** | ⭐ Excelente | Gerou o `UnitOfWork` completo com tratamento de `StopException` sem ser instruído |
| **SQL complexo** | ⭐ Excelente | Queries com 4 JOINs geradas corretamente na primeira iteração |
| **Refatoração** | ⭐ Excelente | Migração de `GenericRepository` para Repository Pattern com mínima intervenção |
| **Compreensão contextual** | ⭐ Excelente | Entendeu a semântica do Streamlit (stateless) e sugeriu padrões de sessão adequados |

### Gemini 1.5 Pro — Pontos Fortes

| Área | Resultado | Exemplo |
|---|---|---|
| **Geração de UI** | ⭐ Excelente | Páginas Streamlit com Plotly e formulários complexos |
| **Mock AI** | ✅ Bom | Estrutura do `ai_concreto.py` gerada corretamente |
| **Documentação** | ✅ Bom | Docstrings e comentários de boa qualidade |

### Prompts Que Funcionaram Bem

> **Prompt efetivo 1:** *"Crie uma página Streamlit para gestão de pedidos de concreto. O formulário deve ter selects dinâmicos que busquem clientes, elementos e traços do banco via UnitOfWork. Ao salvar, valide campos obrigatórios e exiba toast de sucesso."*
>
> **Prompt efetivo 2:** *"Implemente o padrão RBAC baseado em banco de dados. O middleware deve capturar Path(__file__).name, consultar a tabela de permissões e fazer st.stop() se o perfil não tiver acesso."*

---

## 9. O Que Não Funcionou — Falhas, Alucinações e Intervenção Humana

### 9.1. Alucinação de Dependências (Gemini)

Ao solicitar o cálculo de volume de cilindros de concreto, o agente **Gemini tentou importar** uma biblioteca chamada `concrete_engineering` — **que não existe** no ecossistema Python.

> [!WARNING]
> **Lição aprendida:** Código gerado por IA deve ser **auditado linha a linha** antes de integração. Bibliotecas inexistentes podem parecer totalmente plausíveis.

**Correção aplicada:** Refatoração manual para utilizar a biblioteca nativa `math`:

```python
# ANTES (Alucinação do Gemini):
from concrete_engineering import calculate_volume  # NÃO EXISTE!

# DEPOIS (Correção humana):
import math
volume = math.pi * (raio ** 2) * altura  # V = π * r² * h
```

### 9.2. Fórmulas Técnicas Imprecisas

A Lei de Abrams gerada pelo agente produzia valores fora das faixas técnicas aceitas pela ABNT. Os coeficientes tiveram que ser **calibrados manualmente** com base em tabelas de dosagem reais.

### 9.3. Inconsistências de Estado no Streamlit

Os agentes inicialmente geraram código onde variáveis eram declaradas fora do `session_state`, causando perda de dados entre recarregamentos. Foi necessário **intervenção humana** para padronizar o padrão de sessão em todas as 12 páginas.

### 9.4. O Que Seria Feito Diferente

1.  **Prompts mais específicos para fórmulas de engenharia** — incluir referências de normas técnicas (ABNT NBR) diretamente no prompt.
2.  **Validação incremental** — testar a saída de cada função gerada antes de pedir a próxima, em vez de gerar módulos inteiros de uma vez.
3.  **Usar o Claude para toda a lógica de negócio** — o Claude demonstrou melhor compreensão contextual do domínio, enquanto o Gemini foi mais adequado para UI.

---

## 10. Conclusão Técnica e Arquitetura Final

O **SystemConcreto** atende aos requisitos da avaliação através de uma arquitetura em camadas bem definida, resultado de duas migrações incrementais documentadas:

```
┌────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA FINAL                               │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PRESENTATION LAYER                                          │  │
│  │  Streamlit (12 páginas) + Plotly Express                     │  │
│  │  Gestão de estado via st.session_state                       │  │
│  └──────────────────┬───────────────────────────────────────────┘  │
│                     │                                              │
│  ┌──────────────────▼───────────────────────────────────────────┐  │
│  │  BUSINESS LAYER                                              │  │
│  │  ai_concreto.py (Mock AI — Lógica Estocástica)               │  │
│  │  servicos_gerenciador.py (RBAC Middleware)                   │  │
│  └──────────────────┬───────────────────────────────────────────┘  │
│                     │                                              │
│  ┌──────────────────▼───────────────────────────────────────────┐  │
│  │  PERSISTENCE LAYER                                           │  │
│  │  Unit of Work (Transações ACID)                              │  │
│  │  Repository Pattern (BaseRepo + FabricaRepo + UsuarioRepo)  │  │
│  └──────────────────┬───────────────────────────────────────────┘  │
│                     │                                              │
│  ┌──────────────────▼───────────────────────────────────────────┐  │
│  │  DATA LAYER                                                  │  │
│  │  SQLite + CHECK Constraints + Foreign Keys                   │  │
│  │  DDL/DML scripts com ferramentas GUI de instalação           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  AGENTES UTILIZADOS: Claude 4.6 Opus · Gemini 1.5 Pro            │
│  IDE: Antigravity                                                  │
│  TESTES: pytest (6 módulos de teste)                              │
└────────────────────────────────────────────────────────────────────┘
```

### Resumo das Migrações

| Fase | De → Para | Foco |
|---|---|---|
| **Fase 0** | Zero → NexlifyStreamlit | Boilerplate com autenticação e CRUD básico |
| **Fase 1** | `easyToUseWeb` → `easyToUseWebWithDatabase` | Refatoração arquitetural: UoW, Repository, RBAC, Testes |
| **Fase 2** | `easyToUseWebWithDatabase` → **SystemConcreto** | Pivô de domínio: Fábrica de Concreto, Mock AI, 12 páginas |

> A migração provou que a estrutura base (autenticação, logs, config) poderia ser reaproveitada, mas o domínio do problema exigiu uma **reescrita completa** da camada de dados e lógica de negócios. O resultado é um sistema **funcional, seguro e capaz de simular decisões de engenharia complexas** — construído inteiramente com supervisão de agentes de IA.