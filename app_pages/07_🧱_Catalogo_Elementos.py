"""
16_🧱_Catalogo_Elementos.py — CRUD de Elementos Pré-Moldados
Gerenciar catálogo de blocos, tubos, vigas, pilares e outros elementos.
"""
import streamlit as st
import pandas as pd
import logging
import time
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
from utils.traco_utils import formatar_traco_legivel
import config

st.set_page_config(page_title="Catálogo de Elementos", layout="wide", page_icon="🧱")
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
if "elem_show_form" not in st.session_state:
    st.session_state.elem_show_form = False
if "elem_editing" not in st.session_state:
    st.session_state.elem_editing = None
if "elem_feedback" not in st.session_state:
    st.session_state.elem_feedback = None

def mostrar_feedback():
    if st.session_state.elem_feedback:
        fb = st.session_state.elem_feedback
        if fb["tipo"] == "sucesso":
            st.success(fb["texto"], icon="✅")
        elif fb["tipo"] == "erro":
            st.error(fb["texto"], icon="❌")

# ── Título ───────────────────────────────────────────────────
st.title("🧱 Catálogo de Elementos Pré-Moldados")
st.markdown("Gerencie os elementos fabricados: Blocos, Tubos, Vigas, Pilares e mais.")
st.markdown("---")

# ── Carregar dados ───────────────────────────────────────────
def get_elementos():
    try:
        with UnitOfWork() as uow:
            return uow.fabrica.get_catalogo_elementos()
    except Exception as e:
        log.error(f"Erro ao carregar elementos: {e}")
        return pd.DataFrame()

def get_tracos():
    try:
        with UnitOfWork() as uow:
            return uow.fabrica.get_tracos_padrao()
    except Exception as e:
        log.error(f"Erro ao carregar traços: {e}")
        return pd.DataFrame()

# ── Botão novo + filtro ──────────────────────────────────────
c1, c2 = st.columns([4, 1])
c1.caption("Clique em uma linha para editar.")
if c2.button("➕ Novo Elemento", width="stretch"):
    st.session_state.elem_show_form = True
    st.session_state.elem_editing = None
    st.session_state.elem_feedback = None
    st.rerun()

df_elem = get_elementos()
df_tracos = get_tracos()

# ── Formulário (Criar / Editar) ──────────────────────────────
if st.session_state.elem_show_form:
    item = st.session_state.elem_editing
    with st.container(border=True):
        st.markdown(f"### 📝 {'Editar' if item else 'Novo'} Elemento")
        mostrar_feedback()

        with st.form("form_elemento"):
            ca, cb = st.columns(2)
            nome = ca.text_input("Nome", value=item["nome"] if item else "")
            tipo = cb.selectbox(
                "Tipo",
                options=["Bloco", "Tubo", "Viga", "Pilar", "Laje", "Poste", "Piso", "Outro"],
                index=(
                    ["Bloco", "Tubo", "Viga", "Pilar", "Laje", "Poste", "Piso", "Outro"]
                    .index(item["tipo"]) if item and item["tipo"] in
                    ["Bloco", "Tubo", "Viga", "Pilar", "Laje", "Poste", "Piso", "Outro"] else 0
                ),
            )
            cc, cd = st.columns(2)
            volume = cc.number_input(
                "Volume (m³)",
                min_value=0.0001,
                value=float(item["volume_m3"]) if item else 0.01,
                step=0.001,
                format="%.4f",
            )
            fck = cd.number_input(
                "FCK Necessário (MPa)",
                min_value=1.0,
                value=float(item["fck_necessario"]) if item else 25.0,
                step=5.0,
            )

            # ── Traço Padrão Sugerido ────────────────────────
            traco_opcoes = {"(Nenhum)": None}
            if not df_tracos.empty:
                for _, tr in df_tracos.iterrows():
                    label = f"{tr['nome']} ({formatar_traco_legivel(tr['traco_str'])})"
                    traco_opcoes[label] = int(tr["id"])

            # Determinar índice inicial
            traco_index = 0
            if item and item.get("traco_id") and not pd.isna(item["traco_id"]):
                current_traco_id = int(item["traco_id"])
                for i, (_, tid) in enumerate(traco_opcoes.items()):
                    if tid == current_traco_id:
                        traco_index = i
                        break

            traco_label = st.selectbox(
                "🧪 Traço Padrão Sugerido",
                options=list(traco_opcoes.keys()),
                index=traco_index,
                help="Traço recomendado para este elemento. Será sugerido automaticamente ao criar pedidos.",
            )
            traco_id_selecionado = traco_opcoes[traco_label]

            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                if not nome.strip():
                    st.session_state.elem_feedback = {"tipo": "erro", "texto": "O nome é obrigatório."}
                    st.rerun()
                else:
                    try:
                        data = {
                            "nome": nome.strip(),
                            "tipo": tipo,
                            "volume_m3": volume,
                            "fck_necessario": fck,
                            "traco_id": traco_id_selecionado,
                        }
                        with UnitOfWork() as uow:
                            elem_id = int(item["id"]) if item else None
                            uow.fabrica.save_elemento(data, elem_id)
                        st.balloons()
                        st.toast("Elemento salvo com sucesso!", icon="✅")
                        st.session_state.elem_show_form = False
                        st.session_state.elem_feedback = None
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        msg = (
                            "Erro: Já existe um elemento com este nome."
                            if "unique" in str(e).lower()
                            else f"Erro técnico: {e}"
                        )
                        st.session_state.elem_feedback = {"tipo": "erro", "texto": msg}
                        st.rerun()

            if item and b2.form_submit_button("🗑️ Excluir", type="secondary", width="stretch"):
                try:
                    with UnitOfWork() as uow:
                        uow.fabrica.delete_elemento(int(item["id"]))
                    st.toast("Elemento excluído com sucesso!", icon="🗑️")
                    st.session_state.elem_show_form = False
                    st.session_state.elem_feedback = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.session_state.elem_feedback = {"tipo": "erro", "texto": f"Erro ao excluir: {e}"}
                    st.rerun()
            elif not item and b2.form_submit_button("Cancelar"):
                st.session_state.elem_show_form = False
                st.session_state.elem_feedback = None
                st.rerun()

# ── Tabela de Elementos ──────────────────────────────────────
if not df_elem.empty:
    st.subheader("📋 Elementos Cadastrados")

    # Filtro por tipo
    tipos_disponiveis = ["Todos"] + sorted(df_elem["tipo"].unique().tolist())
    tipo_filtro = st.selectbox("Filtrar por tipo:", tipos_disponiveis)
    if tipo_filtro != "Todos":
        df_exibir = df_elem[df_elem["tipo"] == tipo_filtro]
    else:
        df_exibir = df_elem

    event = st.dataframe(
        df_exibir,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "id": None,
            "traco_id": None,
            "traco_str_display": None,
            "nome": "Nome do Elemento",
            "tipo": "Tipo",
            "volume_m3": st.column_config.NumberColumn("Volume (m³)", format="%.4f"),
            "fck_necessario": st.column_config.NumberColumn("FCK (MPa)", format="%.0f"),
            "traco_nome": "Traço Padrão",
        },
    )

    if event.selection.rows:
        idx = event.selection.rows[0]
        selected = df_exibir.iloc[idx].to_dict()
        current_id = st.session_state.elem_editing["id"] if st.session_state.elem_editing else None
        if current_id != selected["id"]:
            st.session_state.elem_editing = selected
            st.session_state.elem_show_form = True
            st.session_state.elem_feedback = None
            st.rerun()
elif not st.session_state.elem_show_form:
    st.info('Nenhum elemento cadastrado. Clique em "➕ Novo Elemento" para começar.')
