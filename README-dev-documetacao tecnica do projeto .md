# 🏭 Pré-Moldados Garantia Eterna — Sistema de Gestão Integrada

> **Avaliação Intermediária — Inteligência Artificial Generativa (2026)**
>
> Sistema web para gestão integrada de fábrica de pré-moldados de concreto,
> com dosagem inteligente de traços via **GPT-4o-mini** (LangChain + Tool Calling + Structured Output).

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#%EF%B8%8F-arquitetura)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [Perfis de Acesso](#-perfis-de-acesso)
- [Estrutura de Diretórios](#-estrutura-de-diretórios)
- [Testes](#-testes)
- [Mock AI — Dosagem de Concreto](#-mock-ai--dosagem-de-concreto)
- [Banco de Dados](#-banco-de-dados)
- [Sobre o Uso de IA Generativa](#-sobre-o-uso-de-ia-generativa)

---

## 🎯 Visão Geral

O **Pré-Moldados Garantia Eterna** é uma plataforma web construída com **Streamlit** para digitalizar
a gestão completa de uma fábrica de pré-moldados de concreto. O sistema cobre:

- **Dosagem inteligente** de traços de concreto (via IA real — GPT-4o-mini com LangChain)
- **Gestão de pedidos** com ciclo completo (Pendente → Em Produção → Concluído)
- **Controle de estoque** de materiais (cimento, areia, brita, aditivos, adições, fibras, água)
- **Catálogo de elementos** pré-moldados com CRUD completo
- **Dashboard operacional** com KPIs, gráficos e alertas
- **Controle de acesso** por perfis (RBAC) com 4 níveis

### Problema Resolvido

Fábricas de pré-moldados frequentemente gerenciam pedidos, traços e estoque em planilhas
desconectadas. Este sistema centraliza todas as operações numa interface web única, adicionando
inteligência artificial real (GPT-4o-mini) para dosagem e otimização de custos de concreto.

---

## ✨ Funcionalidades

| # | Página | Descrição |
|---|--------|-----------|
| 01 | 🏠 Página Inicial | Dashboard resumido com KPIs e navegação rápida |
| 02 | 🏭 Fábrica Dashboard | KPIs de produção, gráficos, tendência semanal, alertas |
| 03 | 📝 Novo Pedido | Formulário de pedidos + geração de traço com IA integrada |
| 04 | 🏭 Controle de Produção | Chão de fábrica: status de pedidos + baixa automática de estoque |
| 05 | 🔬 Laboratório de Engenharia | P&D de traços via Mock AI (chat e otimização) |
| 06 | 🧪 Banco de Traços | Consulta e otimização de traços padrão |
| 07 | 🧱 Catálogo Elementos | CRUD de peças (blocos, tubos, vigas, pilares) |
| 08 | 📦 Gestão de Materiais | Estoque, custos, alertas de estoque baixo |
| 09 | 🤝 Cadastro Clientes | CRUD de clientes (nome, CNPJ/CPF, endereço) |
| 10 | 📜 Histórico Produção | Relatório filtrado com exportação CSV |
| 11 | ⚙️ Configurações | Admin unificado: Usuários, Permissões, Páginas, Tema |
| 12 | ℹ️ Sobre | Documentação técnica do sistema |

---

## 🏗️ Arquitetura

O sistema segue uma arquitetura em camadas com padrões de projeto bem definidos:

```
┌──────────────────────────────────────────────┐
│              Streamlit UI (13 páginas)        │
├──────────────────────────────────────────────┤
│          AI Service (ai_concreto.py + GPT-4o-mini)  │
├──────────────────────────────────────────────┤
│     Unit of Work + Repository Pattern         │
│  ┌────────────┐  ┌────────────────────────┐  │
│  │ UnitOfWork  │→│ FabricaRepository      │  │
│  │             │→│ UsuarioRepository      │  │
│  │             │→│ PaginaRepository       │  │
│  │             │→│ PermissaoRepository    │  │
│  └────────────┘  └────────────────────────┘  │
├──────────────────────────────────────────────┤
│      SQLAlchemy Core + SQLite                 │
└──────────────────────────────────────────────┘
```

### Padrões de Projeto Utilizados

| Padrão | Implementação | Benefício |
|--------|---------------|-----------|
| **Unit of Work** | `persistencia/unit_of_work.py` | Transações atômicas com commit/rollback automático |
| **Repository** | `persistencia/repositorios/` | Separação entre lógica de negócio e acesso a dados |
| **RBAC** | `perfil_acesso` + `perfil_pagina_permissao` | Controle de acesso granular por perfil |
| **AI Service** | `components/ai_concreto.py` | Pipeline LangChain (GPT-4o-mini) com Tool Calling e Structured Output |

---

## 🔧 Tecnologias

| Tecnologia | Versão | Função |
|------------|--------|--------|
| Python | 3.10+ | Linguagem principal |
| Streamlit | 1.30+ | Framework web / UI |
| SQLite | 3 | Banco de dados local |
| SQLAlchemy | 2.0+ | Abstração de banco de dados |
| Pandas | 2.0+ | Manipulação de DataFrames |
| Plotly | 5.0+ | Gráficos interativos |
| LangChain | 0.3+ | Framework de orquestração de LLM |
| OpenAI API | gpt-4o-mini | Modelo de IA generativa |
| Bcrypt | 4.0+ | Hash de senhas |
| Fernet | — | Criptografia de credenciais |

---

## 📦 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes)

### Passo a Passo

```bash
# 1. Clonar o repositório
git clone https://github.com/seu-usuario/Intelig-ncia-Artificial-Generativa---Avalia-o-Intermedi-ria.git
cd Intelig-ncia-Artificial-Generativa---Avalia-o-Intermedi-ria

# 2. Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Iniciar a aplicação
streamlit run Home.py
```

> **Nota:** O banco de dados SQLite será criado automaticamente na primeira execução
> quando `initialize_database_on_startup = True` em `config_settings.ini`.

---

## 🚀 Uso

### Login

Ao acessar o sistema, uma tela de autenticação será exibida.

| Usuário | Senha | Perfil |
|---------|-------|--------|
| `admin` | `123` | Administrador (acesso total) |
| `eng.patrik` | `123` | Engenharia |
| `prod.francis` | `123` | Produção |
| `vend.calos` | `123` | Comercial |

### Fluxo Típico de Uso

1. **Login** → Acessar com credenciais
2. **Dashboard** → Verificar KPIs e alertas de estoque
3. **Novo Pedido** → Registrar pedido de cliente
4. **AI Traço** → Gerar dosagem inteligente para o concreto
5. **Calculadora** → Verificar materiais necessários
6. **Histórico** → Atualizar status do pedido conforme produção avança

---

## 👥 Perfis de Acesso

| Perfil | Páginas com Acesso |
|--------|-------------------|
| **Administrador** | Todas (12 páginas) |
| **Engenharia** | Home, Sobre, Lab, Traços, Catálogo, Materiais, Produção |
| **Produção** | Home, Sobre, Dashboard, Controle Produção, Materiais, Histórico |
| **Comercial** | Home, Sobre, Dashboard, Novo Pedido, Catálogo, Clientes |

---

## 📂 Estrutura de Diretórios

```
├── Home.py                          # Ponto de entrada (login + navegação)
├── config.py                        # Configurações da aplicação
├── config_settings.ini              # Parâmetros configuráveis
├── banco.ini                        # Configuração de banco de dados
├── requirements.txt                 # Dependências Python
│
├── app_pages/                       # 12 Páginas Streamlit (Pipeline)
│   ├── 01_🏠_Pagina_Inicial.py      # Home
│   ├── 02_🏭_Fabrica_Dashboard.py   # KPIs e visão geral
│   ├── 03_📝_Novo_Pedido.py         # Vendas (+ IA integrada)
│   ├── 04_🏭_Controle_Producao.py   # Chão de fábrica + Baixa de Estoque
│   ├── 05_🔬_Laboratorio_Engenharia.py # P&D de traços
│   ├── 06_🧪_Banco_de_Tracos.py     # Receitas de concreto
│   ├── 07_🧱_Catalogo_Elementos.py  # Produtos pré-moldados
│   ├── 08_📦_Gestao_Materiais.py    # Estoque e custos
│   ├── 09_🤝_Cadastro_Clientes.py   # CRM
│   ├── 10_📜_Historico_Producao.py   # Relatórios
│   ├── 11_⚙️_Configuracoes.py       # Admin (Usuários+Permissões+Páginas+Tema)
│   └── 12_ℹ️_Sobre.py               # Documentação técnica
│
├── components/                      # Lógica de negócio
│   ├── ai_concreto.py               # Pipeline IA (LangChain + GPT-4o-mini: sugerir_traco, otimizar_traco)
│   └── servicos_gerenciador.py      # Serviço de permissões
│
├── persistencia/                    # Camada de dados
│   ├── database.py                  # DatabaseManager (singleton)
│   ├── unit_of_work.py              # Padrão Unit of Work
│   ├── auth.py                      # Autenticação de usuários
│   ├── sql_schema_SQLLite.sql       # DDL + DML completo
│   └── repositorios/
│       ├── base.py                  # BaseRepository (abstração SQL)
│       ├── fabrica_repo.py          # FabricaRepository (fab_*)
│       ├── usuario.py               # UsuarioRepository
│       ├── paginas.py               # PaginaRepository
│       └── permissoes.py            # PermissaoRepository
│
├── teste/                           # Suite de testes
│   ├── conftest.py                  # Fixtures (DB in-memory)
│   ├── test_db_connection.py        # Conexão e singleton
│   ├── test_unit_of_work.py         # Context manager + repos
│   ├── test_repos.py                # CRUD de fábrica + permissões
│   ├── test_ai_concreto.py          # Mock AI (sugerir + otimizar)
│   └── test_config.py               # Configurações
│
├── utils/                           # Utilitários Streamlit
│   ├── st_utils.py                  # Sessão, acesso, navegação
│   └── traco_utils.py               # Formatação de traço com rótulos (Cimento:Areia:Brita:a/c)
│
└── instalacao/                      # Ferramentas de instalação
    ├── config_gui.py                # Configurador visual
    ├── gerador_credenciais_gui.py   # Gerador de hashes/chaves
    └── sql_fabrica_*.sql            # SQL separado da fábrica
```

---

## 🧪 Testes

O projeto utiliza **pytest** com banco in-memory (SQLite `:memory:`).

```bash
# Rodar todos os testes
python3 -m pytest teste/ -v

# Rodar um arquivo específico
python3 -m pytest teste/test_ai_concreto.py -v
```

### Cobertura de Testes

| Arquivo | Testes | Descrição |
|---------|--------|-----------|
| `test_db_connection.py` | 2 | Conexão ao banco, singleton do DatabaseManager |
| `test_unit_of_work.py` | 2 | Context manager, inicialização dos repositórios |
| `test_repos.py` | 5 | CRUD de elementos, clientes, materiais, traços, pedidos + status |
| `test_ai_concreto.py` | 6 | Sugestão de traço, otimização, limites, custos |
| `test_config.py` | 3 | Carregamento de configurações, defaults |

---

## 🧠 IA Real — Dosagem de Concreto via GPT-4o-mini

O módulo `components/ai_concreto.py` implementa um pipeline de IA generativa para dosagem de concreto
utilizando **GPT-4o-mini** via **LangChain** com:

- **Tool Calling** → Consulta automática de limites normativos ABNT (NBR 6118 / NBR 12655)
- **Structured Output (Pydantic)** → Resposta validada com schema tipado (`TracoOutput`)
- **Chain-of-Thought** → Raciocínio explícito antes do cálculo final
- **Recálculo de Custo** → Custo por m³ recalculado em Python (IA é imprecisa em aritmética)
- **Escape de Cifrão** → `R$` escapado para renderização correta no Streamlit Markdown

### Funções Disponíveis

| Função | Entrada | Saída |
|--------|---------|-------|
| `sugerir_traco(fck, slump, agregado, materiais_selecionados)` | FCK (MPa), Slump (mm), Tipo de brita, Materiais do estoque | Traço, materiais/m³, custo, justificativa técnica |
| `otimizar_traco(traco_dict)` | Dicionário de traço existente | Traço otimizado com redução de custo via aditivos |

### Exemplo de Interface

A página **05_🔬_Laboratório_Engenharia** implementa uma interface conversacional (`st.chat_message`)
com interação com o GPT-4o-mini:

1. Usuário configura parâmetros (FCK, Slump, Agregado, Materiais do estoque)
2. Clica em "Gerar Traço com IA"
3. Sistema chama a API OpenAI, executa Tool Calling e retorna traço validado
4. Histórico de conversa é mantido para comparar múltiplas dosagens

---

## 🗄️ Banco de Dados

O sistema utiliza **SQLite** com o seguinte esquema:

### Tabelas do Sistema

| Tabela | Função |
|--------|--------|
| `perfil_acesso` | 4 perfis (Admin, Engenharia, Produção, Comercial) |
| `usuarios` | Dados de login com senha hash (bcrypt) |
| `pagina` | 14 páginas registradas |
| `perfil_pagina_permissao` | Matriz de permissões perfil × página |

### Tabelas da Fábrica

| Tabela | Registros | Função |
|--------|-----------|--------|
| `fab_clientes` | 5 | Clientes da fábrica |
| `fab_materiais` | 44 | Cimento, areia, brita, aditivos, adições, fibras, água |
| `fab_catalogo_elementos` | 12 | Blocos, tubos, vigas, pilares, lajes |
| `fab_tracos_padrao` | 6 | Traços de referência (FCK 10 a 50) |
| `fab_pedidos` | 10 | Pedidos com status e rastreabilidade |

---

## 🤖 Sobre o Uso de IA Generativa

Este projeto foi desenvolvido com auxílio intensivo de assistentes de IA generativa (Gemini/Claude)
para geração de código, debugging, e documentação.

### Pontos Fortes da IA

- **Geração de boilerplate**: Criação rápida de páginas Streamlit com padrão consistente
- **Padrões de projeto**: Implementação do Repository Pattern e Unit of Work
- **SQL Schema**: Geração de DDL/DML com dados realistas para demonstração
- **Testes**: Geração de fixtures e testes automatizados
- **Documentação**: Criação de README e docstrings

### Limitações Observadas

- **Contexto limitado**: Em projetos grandes, a IA pode perder referências de código anteriores
- **Nomes e referências**: Código legado nem sempre é identificado automaticamente (ex: referências a "gatos" persistiram após remoção da tabela)
- **Testes de UI**: A IA não consegue testar visualmente interfaces Streamlit — verificação manual necessária
- **Decisões de design**: A IA sugere soluções, mas decisões arquiteturais devem ser validadas pelo desenvolvedor

### Fluxo de Trabalho com IA

1. Planejamento → IA cria implementation_plan.md
2. Revisão → Desenvolvedor aprova/ajusta o plano
3. Execução → IA implementa as mudanças
4. Verificação → Testes automatizados + revisão manual
5. Iteração → Correções baseadas em feedback

---

## 📄 Licença

Este projeto foi desenvolvido como trabalho acadêmico para a disciplina de
**Inteligência Artificial Generativa** — Avaliação Intermediária (2026).

---

*Pré-Moldados Garantia Eterna — Construindo o futuro com inteligência.*