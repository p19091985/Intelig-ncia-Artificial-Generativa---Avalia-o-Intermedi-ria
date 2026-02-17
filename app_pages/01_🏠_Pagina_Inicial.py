
import streamlit as st
from utils.st_utils import st_check_session, check_access
from pathlib import Path
from components import servicos_gerenciador as servico
from persistencia.unit_of_work import UnitOfWork
import config

st.set_page_config(page_title='Página Inicial', layout='wide', page_icon='🏠')
st_check_session()

try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    st.error(f'Erro ao verificar permissões: {e}')
    st.stop()

user_info = st.session_state.get('user_info', {})
user_name = user_info.get('name', 'Usuário')
user_profile = user_info.get('access_level', '')

# ── Header ───────────────────────────────────────────────────
st.title(f'👷 Bem-vindo, {user_name}!')
st.markdown(f'**Perfil:** `{user_profile}` — Fábrica de Pré-Moldados de Concreto')
st.markdown('---')

# ── KPIs Resumidos ───────────────────────────────────────────
if config.DATABASE_ENABLED:
    try:
        with UnitOfWork() as uow:
            resumo = uow.fabrica.get_resumo_pedidos()
            df_estoque_baixo = uow.fabrica.get_estoque_baixo(limite=1000.0)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric('📦 Pedidos Ativos', resumo['total'] - resumo['concluidos'])
        k2.metric('🔨 Em Produção', resumo['em_producao'])
        k3.metric('📐 Volume Programado', f"{resumo['volume_programado_m3']:.1f} m³")
        alertas = len(df_estoque_baixo) if not df_estoque_baixo.empty else 0
        k4.metric('🚨 Alertas de Estoque', alertas, delta='Materiais abaixo de 1.000 kg' if alertas > 0 else None, delta_color='inverse')
    except Exception:
        pass

st.markdown('---')

# ── Navegação Rápida ─────────────────────────────────────────
st.subheader('🧭 Navegação Rápida')
st.caption('Acesse diretamente os módulos do sistema clicando nos cards abaixo.')

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown('### 🏭 Dashboard')
        st.markdown('Visão geral da produção, KPIs e alertas de estoque.')
        st.caption('📊 Gráficos · 🚨 Alertas · 📈 Tendências')

    with st.container(border=True):
        st.markdown('### 📝 Novo Pedido')
        st.markdown('Registre pedidos de elementos pré-moldados.')
        st.caption('👤 Cliente · 🧱 Elemento · 📅 Entrega')

with col2:
    with st.container(border=True):
        st.markdown('### 🧠 IA de Concreto')
        st.markdown('Dosagem inteligente de traços via **Mock AI**.')
        st.caption('🔬 Granulometria · 📐 Abrams · 💰 Custo')

    with st.container(border=True):
        st.markdown('### 🧪 Banco de Traços')
        st.markdown('Consulte e otimize traços padrão com IA.')
        st.caption('⚡ Otimização · 📋 Filtros · 🤖 AI')

with col3:
    with st.container(border=True):
        st.markdown('### 🧱 Catálogo')
        st.markdown('CRUD completo de elementos pré-moldados.')
        st.caption('📏 Volume · 🏗️ Tipo · ✏️ Editar')

    with st.container(border=True):
        st.markdown('### 🧮 Calculadora')
        st.markdown('Explosão BOM e comparação com estoque.')
        st.caption('📦 Materiais · ❌ Faltas · 💲 Custos')

st.markdown('---')

# ── Rodapé ───────────────────────────────────────────────────
st.markdown('')
with st.container(border=True):
    st.markdown(
        '**🏭 Pré-Moldados Garantia Eterna — Sistema de Gestão Integrada**  \n'
        'Tecnologias: Python · Streamlit · SQLite · Pandas · SQLAlchemy  \n'
        'Inteligência: Algoritmos de Mock AI para dosagem de concreto (a/c, Abrams, NBR)'
    )