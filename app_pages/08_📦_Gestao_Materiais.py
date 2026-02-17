"""
08_📦_Gestao_Materiais.py — Cadastro e Controle de Estoque de Materiais
CRUD completo para materiais: Cimento, Areia, Brita, Aditvos, Água.
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

st.set_page_config(page_title="Gestão de Materiais", layout="wide", page_icon="📦")
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
if "mat_show_form" not in st.session_state:
    st.session_state.mat_show_form = False
if "mat_editing" not in st.session_state:
    st.session_state.mat_editing = None
if "mat_feedback" not in st.session_state:
    st.session_state.mat_feedback = None


def mostrar_feedback():
    if st.session_state.mat_feedback:
        fb = st.session_state.mat_feedback
        if fb["tipo"] == "sucesso":
            st.success(fb["texto"], icon="✅")
        elif fb["tipo"] == "erro":
            st.error(fb["texto"], icon="❌")


# ── Título ───────────────────────────────────────────────────
st.title("📦 Gestão de Materiais e Estoque")
st.markdown(
    "Cadastre, edite e controle o estoque de matérias-primas: "
    "Cimento, Areia, Brita, Aditivos e Água."
)
st.markdown("---")


# ── Carregar dados ───────────────────────────────────────────
def get_materiais():
    try:
        with UnitOfWork() as uow:
            return uow.fabrica.get_all_materiais()
    except Exception as e:
        log.error(f"Erro ao carregar materiais: {e}")
        return pd.DataFrame()


# ── Botão novo ───────────────────────────────────────────────
c1, c2 = st.columns([4, 1])
c1.caption("Clique em uma linha para editar.")
if c2.button("➕ Novo Material", width="stretch"):
    st.session_state.mat_show_form = True
    st.session_state.mat_editing = None
    st.session_state.mat_feedback = None
    st.rerun()

df_mat = get_materiais()

# ── Formulário (Criar / Editar) ──────────────────────────────
TIPOS_MATERIAL = ["Cimento", "Areia", "Brita", "Aditivo", "Água"]

if st.session_state.mat_show_form:
    item = st.session_state.mat_editing
    with st.container(border=True):
        st.markdown(f"### 📝 {'Editar' if item else 'Novo'} Material")
        mostrar_feedback()

        with st.form("form_material"):
            ca, cb = st.columns(2)
            nome = ca.text_input("Nome do Material", value=item["nome"] if item else "")
            tipo_idx = 0
            if item and item.get("tipo") in TIPOS_MATERIAL:
                tipo_idx = TIPOS_MATERIAL.index(item["tipo"])
            tipo = cb.selectbox("Tipo", options=TIPOS_MATERIAL, index=tipo_idx)

            cc, cd = st.columns(2)
            custo_kg = cc.number_input(
                "Custo por kg (R$)",
                min_value=0.0,
                value=float(item["custo_kg"]) if item else 0.0,
                step=0.01,
                format="%.3f",
            )
            estoque_atual = cd.number_input(
                "Estoque Atual (kg)",
                min_value=0.0,
                value=float(item["estoque_atual"]) if item else 0.0,
                step=100.0,
                format="%.1f",
            )

            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                if not nome.strip():
                    st.session_state.mat_feedback = {
                        "tipo": "erro",
                        "texto": "O nome é obrigatório.",
                    }
                    st.rerun()
                else:
                    try:
                        data = {
                            "nome": nome.strip(),
                            "tipo": tipo,
                            "custo_kg": custo_kg,
                            "estoque_atual": estoque_atual,
                        }
                        with UnitOfWork() as uow:
                            mat_id = int(item["id"]) if item else None
                            uow.fabrica.save_material(data, mat_id)
                        st.balloons()
                        st.toast("Material salvo com sucesso!", icon="✅")
                        st.session_state.mat_show_form = False
                        st.session_state.mat_feedback = None
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        msg = (
                            "Erro: Já existe um material com este nome."
                            if "unique" in str(e).lower()
                            else f"Erro técnico: {e}"
                        )
                        st.session_state.mat_feedback = {"tipo": "erro", "texto": msg}
                        st.rerun()

            if item and b2.form_submit_button(
                "🗑️ Excluir", type="secondary", width="stretch"
            ):
                try:
                    with UnitOfWork() as uow:
                        uow.fabrica.delete_material(int(item["id"]))
                    st.toast("Material excluído com sucesso!", icon="🗑️")
                    st.session_state.mat_show_form = False
                    st.session_state.mat_feedback = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.session_state.mat_feedback = {
                        "tipo": "erro",
                        "texto": f"Erro ao excluir: {e}",
                    }
                    st.rerun()
            elif not item and b2.form_submit_button("Cancelar"):
                st.session_state.mat_show_form = False
                st.session_state.mat_feedback = None
                st.rerun()

# ── Tabela de Materiais ──────────────────────────────────────
if not df_mat.empty:
    st.subheader("📋 Materiais Cadastrados")

    # Filtro por tipo
    tipos_disponiveis = ["Todos"] + sorted(df_mat["tipo"].unique().tolist())
    tipo_filtro = st.selectbox("Filtrar por tipo:", tipos_disponiveis)
    if tipo_filtro != "Todos":
        df_exibir = df_mat[df_mat["tipo"] == tipo_filtro]
    else:
        df_exibir = df_mat

    # KPIs de estoque
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📦 Total de Materiais", len(df_mat))
    k2.metric(
        "⚠️ Estoque Baixo (<1000 kg)",
        len(df_mat[df_mat["estoque_atual"] < 1000]),
    )
    estoque_valor = (df_mat["estoque_atual"] * df_mat["custo_kg"]).sum()
    k3.metric("💰 Valor em Estoque", f"R$ {estoque_valor:,.2f}")
    k4.metric("📊 Tipos", df_mat["tipo"].nunique())
    st.markdown("---")

    event = st.dataframe(
        df_exibir,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "id": None,
            "nome": "Nome",
            "tipo": "Tipo",
            "custo_kg": st.column_config.NumberColumn("Custo/kg (R$)", format="R$ %.3f"),
            "estoque_atual": st.column_config.NumberColumn(
                "Estoque (kg)", format="%.1f"
            ),
        },
    )

    if event.selection.rows:
        idx = event.selection.rows[0]
        selected = df_exibir.iloc[idx].to_dict()
        current_id = (
            st.session_state.mat_editing["id"]
            if st.session_state.mat_editing
            else None
        )
        if current_id != selected["id"]:
            st.session_state.mat_editing = selected
            st.session_state.mat_show_form = True
            st.session_state.mat_feedback = None
            st.rerun()

    # ── Alertas de Estoque Baixo ─────────────────────────────
    baixo = df_mat[df_mat["estoque_atual"] < 1000]
    if not baixo.empty:
        st.markdown("---")
        st.warning(f"⚠️ **{len(baixo)} material(is) com estoque abaixo de 1.000 kg:**")
        for _, row in baixo.iterrows():
            st.caption(
                f"🔴 **{row['nome']}** ({row['tipo']}): "
                f"apenas **{row['estoque_atual']:.0f} kg** em estoque"
            )

elif not st.session_state.mat_show_form:
    st.info('Nenhum material cadastrado. Clique em "➕ Novo Material" para começar.')
