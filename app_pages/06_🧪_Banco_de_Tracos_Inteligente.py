"""
15_🧪_Banco_de_Tracos_Inteligente.py — Banco de Traços Padrão com Otimização IA
Tabela filtrável de traços e funcionalidade de otimização de custo via Mock AI.
"""
import streamlit as st
import pandas as pd
import logging
import time
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
from components.ai_concreto import otimizar_traco
import config

st.set_page_config(page_title="Banco de Traços", layout="wide", page_icon="🧪")
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

# ── Título ───────────────────────────────────────────────────
st.title("🧪 Banco de Traços Inteligente")
st.markdown("Consulte os traços padrão da fábrica e utilize a IA para otimizar custos.")
st.markdown("---")

# ── Carregar traços ──────────────────────────────────────────
try:
    with UnitOfWork() as uow:
        df_tracos = uow.fabrica.get_tracos_padrao()
except Exception as e:
    st.error(f"Erro ao carregar traços: {e}")
    st.stop()

if df_tracos.empty:
    st.info("Nenhum traço padrão cadastrado.")
    st.stop()

# ── Filtro ───────────────────────────────────────────────────
col_filtro1, col_filtro2 = st.columns(2)
fck_min = col_filtro1.number_input("FCK mínimo (MPa)", min_value=0.0, value=0.0, step=5.0)
fck_max = col_filtro2.number_input("FCK máximo (MPa)", min_value=0.0, value=100.0, step=5.0)

df_filtrado = df_tracos[
    (df_tracos["fck_alvo"] >= fck_min) & (df_tracos["fck_alvo"] <= fck_max)
]

# ── Tabela ───────────────────────────────────────────────────
st.subheader(f"📋 Traços Disponíveis ({len(df_filtrado)})")
event = st.dataframe(
    df_filtrado,
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "id": None,
        "nome": "Nome do Traço",
        "fck_alvo": st.column_config.NumberColumn("FCK Alvo (MPa)", format="%.0f"),
        "traco_str": "Traço (proporção)",
        "consumo_cimento_m3": st.column_config.NumberColumn("Cimento (kg/m³)", format="%.0f"),
    },
)

# ── Otimização IA ────────────────────────────────────────────
st.markdown("---")
st.subheader("🤖 Otimização de Custo com IA")

if event.selection.rows:
    idx = event.selection.rows[0]
    selected_row = df_filtrado.iloc[idx].to_dict()

    st.info(f"📌 Traço selecionado: **{selected_row['nome']}** — {selected_row['traco_str']}")

    if st.button("⚡ Otimizar Custo com AI", type="primary", width="stretch"):
        with st.spinner("🤖 IA analisando composição granulométrica e custos de materiais..."):
            time.sleep(1.5)
            resultado = otimizar_traco(selected_row)

        # Persistir resultado e FCK do traço original no session_state
        st.session_state["traco_otimizado"] = resultado
        st.session_state["traco_otimizado_fck"] = float(selected_row["fck_alvo"])

    # Exibir resultado persistido (sobrevive a reruns)
    if st.session_state.get("traco_otimizado"):
        resultado = st.session_state["traco_otimizado"]

        st.success("✅ Otimização concluída!")

        col_orig, col_otim = st.columns(2)
        with col_orig:
            st.metric("Traço Original", resultado["traco_original"])
            st.metric("Consumo Cimento", f"{resultado['consumo_original']} kg/m³")
        with col_otim:
            st.metric("Traço Otimizado", resultado["traco_otimizado"])
            st.metric(
                "Consumo Cimento",
                f"{resultado['consumo_otimizado']} kg/m³",
                delta=f"-{resultado['consumo_original'] - resultado['consumo_otimizado']:.1f} kg",
            )

        st.metric(
            "💰 Economia Líquida por m³",
            f"R$ {resultado['economia_liquida_m3']:.2f}",
            delta=f"Aditivo: {resultado['aditivo_kg']} kg/m³",
            delta_color="off",
        )

        with st.expander("📖 Justificativa Técnica da Otimização", expanded=True):
            st.markdown(resultado["justificativa"])

        # ── Salvar Traço Otimizado ───────────────────────────
        if config.DATABASE_ENABLED:
            st.markdown("---")
            st.subheader("💾 Salvar Traço Otimizado no Banco")
            nome_otimizado = st.text_input(
                "📝 Nome para o traço otimizado",
                value=resultado.get("nome_otimizado", "Traço Otimizado"),
                help="Escolha um nome descritivo. O traço será salvo como um novo registro.",
            )
            if st.button("💾 Salvar no Banco de Traços", type="primary", width="stretch"):
                try:
                    traco_data = {
                        "nome": nome_otimizado,
                        "fck_alvo": st.session_state["traco_otimizado_fck"],
                        "traco_str": resultado["traco_otimizado"],
                        "consumo_cimento_m3": float(resultado["consumo_otimizado"]),
                    }
                    with UnitOfWork() as uow:
                        uow.fabrica.save_traco(traco_data)
                    st.success(
                        f"✅ Traço **{nome_otimizado}** salvo com sucesso! "
                        f"Agora ele está disponível em **Novo Pedido** e **Catálogo de Elementos**."
                    )
                    st.balloons()
                    st.session_state.pop("traco_otimizado", None)
                    st.session_state.pop("traco_otimizado_fck", None)
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    msg = (
                        "Erro: Já existe um traço com este nome."
                        if "unique" in str(e).lower()
                        else f"Erro técnico: {e}"
                    )
                    st.error(f"❌ {msg}")
else:
    st.caption("👆 Selecione um traço na tabela acima para otimizar.")
    st.session_state.pop("traco_otimizado", None)
    st.session_state.pop("traco_otimizado_fck", None)
