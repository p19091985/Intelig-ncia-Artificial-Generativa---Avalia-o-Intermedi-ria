
import streamlit as st
from utils.st_utils import st_check_session, check_access
from pathlib import Path
from components import servicos_gerenciador as servico

st.set_page_config(page_title='Sobre o Sistema', layout='wide', page_icon='ℹ️')
st_check_session()

try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    st.error(f'Acesso Negado: {e}')
    st.stop()

st.title('🏭 Pré-Moldados Garantia Eterna — Sistema de Gestão Integrada')
st.markdown('---')

st.subheader('Visão Geral')
st.caption('Plataforma inteligente para gestão de fábricas de pré-moldados de concreto.')

with st.expander('🎯 Propósito e Escopo', expanded=True):
    c1, c2 = st.columns([1, 5])
    with c1:
        st.write('<div style="font-size: 4rem; text-align: center;">🏗️</div>', unsafe_allow_html=True)
    with c2:
        st.info("""
        **Sistema de Gestão Integrada para Fábrica de Pré-Moldados**

        Plataforma desenvolvida para digitalizar e otimizar a gestão completa de fábricas
        de pré-moldados de concreto, desde a dosagem inteligente de traços até o controle
        de produção e estoque de materiais.

        O sistema utiliza **Algoritmos Avançados de Mock AI** para auxiliar na dosagem de
        concreto, sugerindo traços otimizados com base na resistência desejada (fck),
        abatimento (slump) e tipo de agregado, reduzindo custos e desperdícios.
        """)
        st.markdown("""
        ### Principais Capacidades:
        * **Dosagem Inteligente (Mock AI):** Sugestão e otimização de traços de concreto via algoritmos avançados.
        * **Gestão de Pedidos:** Ciclo completo do pedido: criação, acompanhamento e histórico de produção.
        * **Catálogo de Elementos:** CRUD completo de peças pré-moldadas com volume e fck necessário.
        * **Cadastro de Clientes:** CRUD completo de clientes (nome, CNPJ/CPF, endereço).
        * **Controle de Estoque:** Visão em tempo real dos materiais (cimento, areia, brita, aditivos).
        * **Dashboard Operacional:** KPIs de produção, gráficos de status e alertas de estoque baixo.
        * **Calculadora de Materiais:** Estimativa de consumo por pedido com custos detalhados.
        * **Controle de Acesso (RBAC):** Permissões granulares por perfil (Engenharia, Produção, Comercial).
        """)

with st.expander('🛠️ Arquitetura e Tecnologias', expanded=True):
    c1, c2 = st.columns([1, 5])
    with c1:
        st.write('<div style="font-size: 4rem; text-align: center;">⚙️</div>', unsafe_allow_html=True)
    with c2:
        st.subheader('Stack Tecnológica')
        st.markdown("""
        O sistema foi construído sobre padrões modernos de engenharia de software,
        garantindo manutenibilidade, segurança e desempenho.

        | Camada | Tecnologia | Função |
        | :--- | :--- | :--- |
        | **Apresentação** | Streamlit | UI Reativa, Dashboards Interativos, Formulários. |
        | **Inteligência** | Python (Mock AI) | Dosagem de Concreto via Algoritmos Determinísticos. |
        | **Dados** | SQLite + Pandas | Armazenamento local, manipulação eficiente de DataFrames. |
        | **Acesso a Dados** | SQLAlchemy | Abstração ORM/Core, Padrão Repository + Unit of Work. |
        | **Segurança** | Bcrypt + Fernet | Hashing de Senha, Criptografia de Credenciais. |
        """)
        st.divider()
        st.subheader('Padrões de Projeto')
        st.markdown("""
        * **`Unit of Work`**: Gerencia o escopo de transações, garantindo consistência de dados.
        * **`Repository Pattern`**: Encapsula toda a lógica SQL (`FabricaRepository`), mantendo as páginas limpas.
        * **`RBAC (Role-Based Access Control)`**: Controle de acesso por perfil, com 4 perfis especializados.
        * **`Mock AI Service`**: Serviço de inteligência desacoplado (`ai_concreto.py`), pronto para substituição por LLM real.
        """)

with st.expander('👥 Perfis de Acesso', expanded=False):
    st.markdown("""
    O sistema possui **4 perfis de acesso** com permissões diferenciadas:

    | Perfil | Foco Principal | Páginas com Acesso |
    | :--- | :--- | :--- |
    | **Administrador** | Acesso total | Todas as 14 páginas do sistema |
    | **Engenharia** | Traços e Mock AI | Home, Sobre, AI Traço, Banco de Traços, Catálogo, Calculadora |
    | **Produção** | Estoque e Histórico | Home, Sobre, Dashboard, Calculadora, Histórico |
    | **Comercial** | Pedidos e Clientes | Home, Sobre, Dashboard, Novo Pedido, Catálogo, Clientes |

    > **Senha padrão para todos os usuários:** `123`
    """)

with st.expander('🔄 Fluxo de Dados', expanded=False):
    st.markdown("""
    1. **Ação do Usuário:** Interação no Streamlit (Clique em Botão, Envio de Formulário).
    2. **Chamada de Serviço:** A página chama o Repositório via `UnitOfWork`.
    3. **Transação:** `UnitOfWork` abre um contexto de transação atômica.
    4. **Execução:** `FabricaRepository` executa consultas SQL com segurança.
    5. **Commit/Rollback:** `UnitOfWork` garante commit atômico no sucesso ou rollback no erro.
    6. **Exibição:** Dados retornados como `pandas.DataFrame` para visualização no Streamlit.
    """)

st.markdown('---')
st.caption('Pré-Moldados Garantia Eterna — Sistema de Gestão Integrada — Avaliação Intermediária — 2026')