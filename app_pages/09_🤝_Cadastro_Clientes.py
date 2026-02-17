"""
09_🤝_Cadastro_Clientes.py — CRUD de Clientes
Gerenciar cadastro de clientes da fábrica de pré-moldados.
"""
import streamlit as st
import pandas as pd
import logging
import time
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
import config

st.set_page_config(page_title="Cadastro de Clientes", layout="wide", page_icon="🤝")
log = logging.getLogger(__name__)

# ── Segurança ────────────────────────────────────────────────
st_check_session()
try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    st.error(f"Erro ao verificar permissões: {e}")
    st.stop()

if not config.DATABASE_ENABLED:
    st.warning("Funcionalidade indisponível: banco de dados desabilitado.")
    st.stop()

# ── Session State ────────────────────────────────────────────
if "cli_show_form" not in st.session_state:
    st.session_state.cli_show_form = False
if "cli_editing" not in st.session_state:
    st.session_state.cli_editing = None
if "cli_feedback" not in st.session_state:
    st.session_state.cli_feedback = None

def mostrar_feedback():
    if st.session_state.cli_feedback:
        fb = st.session_state.cli_feedback
        if fb["tipo"] == "sucesso":
            st.success(fb["texto"], icon="✅")
        elif fb["tipo"] == "erro":
            st.error(fb["texto"], icon="❌")

# ── Título ───────────────────────────────────────────────────
st.title("🤝 Cadastro de Clientes")
st.markdown("Gerencie os clientes da fábrica: construtoras, engenharias e empreiteiras.")
st.markdown("---")

# ── Carregar dados ───────────────────────────────────────────
def get_clientes():
    try:
        with UnitOfWork() as uow:
            return uow.fabrica.get_all_clientes()
    except Exception as e:
        log.error(f"Erro ao carregar clientes: {e}")
        return pd.DataFrame()

# ── Botão novo ───────────────────────────────────────────────
c1, c2 = st.columns([4, 1])
c1.caption("Clique em uma linha para editar.")
if c2.button("➕ Novo Cliente", width="stretch"):
    st.session_state.cli_show_form = True
    st.session_state.cli_editing = None
    st.session_state.cli_feedback = None
    st.rerun()

df_cli = get_clientes()

# ── Formulário (Criar / Editar) ──────────────────────────────
if st.session_state.cli_show_form:
    item = st.session_state.cli_editing
    with st.container(border=True):
        st.markdown(f"### 📝 {'Editar' if item else 'Novo'} Cliente")
        mostrar_feedback()

        with st.form("form_cliente"):
            nome = st.text_input(
                "Nome / Razão Social",
                value=item["nome"] if item else "",
                placeholder="Ex: Construtora Horizonte Ltda",
            )
            ca, cb = st.columns(2)
            documento = ca.text_input(
                "CNPJ / CPF",
                value=item["documento"] if item else "",
                placeholder="Ex: 12.345.678/0001-90",
            )
            endereco = cb.text_input(
                "Endereço",
                value=item["endereco"] if item else "",
                placeholder="Ex: Rua das Palmeiras, 120 - São Paulo/SP",
            )

            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                if not nome.strip():
                    st.session_state.cli_feedback = {"tipo": "erro", "texto": "O nome é obrigatório."}
                    st.rerun()
                elif not documento.strip():
                    st.session_state.cli_feedback = {"tipo": "erro", "texto": "O CNPJ/CPF é obrigatório."}
                    st.rerun()
                else:
                    try:
                        data = {
                            "nome": nome.strip(),
                            "documento": documento.strip(),
                            "endereco": endereco.strip() if endereco else None,
                        }
                        with UnitOfWork() as uow:
                            cli_id = int(item["id"]) if item else None
                            uow.fabrica.save_cliente(data, cli_id)
                        st.balloons()
                        st.toast("Cliente salvo com sucesso!", icon="✅")
                        st.session_state.cli_show_form = False
                        st.session_state.cli_feedback = None
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        msg = (
                            "Erro: Já existe um cliente com este CNPJ/CPF."
                            if "unique" in str(e).lower()
                            else f"Erro técnico: {e}"
                        )
                        st.session_state.cli_feedback = {"tipo": "erro", "texto": msg}
                        st.rerun()

            if item and b2.form_submit_button("🗑️ Excluir", type="secondary", width="stretch"):
                try:
                    with UnitOfWork() as uow:
                        uow.fabrica.delete_cliente(int(item["id"]))
                    st.toast("Cliente excluído com sucesso!", icon="🗑️")
                    st.session_state.cli_show_form = False
                    st.session_state.cli_feedback = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    if "foreign" in str(e).lower() or "constraint" in str(e).lower():
                        msg = "Não é possível excluir: este cliente possui pedidos vinculados."
                    else:
                        msg = f"Erro ao excluir: {e}"
                    st.session_state.cli_feedback = {"tipo": "erro", "texto": msg}
                    st.rerun()
            elif not item and b2.form_submit_button("Cancelar"):
                st.session_state.cli_show_form = False
                st.session_state.cli_feedback = None
                st.rerun()

# ── Tabela de Clientes ───────────────────────────────────────
if not df_cli.empty:
    st.subheader("📋 Clientes Cadastrados")

    # Filtro por nome
    filtro_nome = st.text_input("🔍 Buscar por nome:", placeholder="Digite para filtrar...")
    if filtro_nome:
        df_exibir = df_cli[df_cli["nome"].str.contains(filtro_nome, case=False, na=False)]
    else:
        df_exibir = df_cli

    # Métricas
    st.metric("Total de Clientes", len(df_exibir))

    event = st.dataframe(
        df_exibir,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "id": None,
            "nome": "Nome / Razão Social",
            "documento": "CNPJ / CPF",
            "endereco": "Endereço",
        },
    )

    if event.selection.rows:
        idx = event.selection.rows[0]
        selected = df_exibir.iloc[idx].to_dict()
        current_id = st.session_state.cli_editing["id"] if st.session_state.cli_editing else None
        if current_id != selected["id"]:
            st.session_state.cli_editing = selected
            st.session_state.cli_show_form = True
            st.session_state.cli_feedback = None
            st.rerun()
elif not st.session_state.cli_show_form:
    st.info('Nenhum cliente cadastrado. Clique em "➕ Novo Cliente" para começar.')
