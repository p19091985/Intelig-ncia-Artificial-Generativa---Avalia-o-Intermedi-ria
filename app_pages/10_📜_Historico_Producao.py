"""
18_📜_Historico_Producao.py — Histórico de Produção
Relatório filtrável de todos os pedidos passados e atuais.
"""
import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
import config

st.set_page_config(page_title="Histórico de Produção", layout="wide", page_icon="📜")
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
st.title("📜 Histórico de Produção")
st.markdown("Consulte o registro completo de todos os pedidos de produção da fábrica.")
st.markdown("---")

# ── Carregar dados ───────────────────────────────────────────
try:
    with UnitOfWork() as uow:
        df_pedidos = uow.fabrica.get_all_pedidos()
except Exception as e:
    st.error(f"Erro ao carregar histórico: {e}")
    st.stop()

if df_pedidos.empty:
    st.info("Nenhum pedido registrado no sistema.")
    st.stop()

# ── Filtros ──────────────────────────────────────────────────
st.subheader("🔍 Filtros")
col_f1, col_f2, col_f3 = st.columns(3)

# Filtro por cliente
clientes = ["Todos"] + sorted(df_pedidos["cliente"].unique().tolist())
filtro_cliente = col_f1.selectbox("👤 Cliente", options=clientes)

# Filtro por status
statuses = ["Todos"] + sorted(df_pedidos["status"].unique().tolist())
filtro_status = col_f2.selectbox("📊 Status", options=statuses)

# Filtro por data
df_pedidos["data_pedido"] = pd.to_datetime(df_pedidos["data_pedido"], errors="coerce")
data_min = df_pedidos["data_pedido"].min()
data_max = df_pedidos["data_pedido"].max()

if pd.notna(data_min) and pd.notna(data_max):
    filtro_data = col_f3.date_input(
        "📅 Período",
        value=(data_min.date(), data_max.date()),
        min_value=data_min.date(),
        max_value=data_max.date(),
    )
else:
    filtro_data = None

# ── Aplicar filtros ──────────────────────────────────────────
df_filtrado = df_pedidos.copy()

if filtro_cliente != "Todos":
    df_filtrado = df_filtrado[df_filtrado["cliente"] == filtro_cliente]

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == filtro_status]

if filtro_data and len(filtro_data) == 2:
    dt_ini = pd.Timestamp(filtro_data[0])
    dt_fim = pd.Timestamp(filtro_data[1])
    df_filtrado = df_filtrado[
        (df_filtrado["data_pedido"] >= dt_ini) & (df_filtrado["data_pedido"] <= dt_fim)
    ]

# ── KPIs ─────────────────────────────────────────────────────
st.markdown("---")
k1, k2, k3, k4 = st.columns(4)
k1.metric("📦 Pedidos encontrados", len(df_filtrado))
k2.metric(
    "📐 Volume Total (m³)",
    f"{df_filtrado['volume_total_m3'].sum():.2f}" if "volume_total_m3" in df_filtrado.columns else "N/A",
)
k3.metric("🔨 Em Produção", len(df_filtrado[df_filtrado["status"] == "Em Produção"]))
k4.metric("✅ Concluídos", len(df_filtrado[df_filtrado["status"] == "Concluído"]))

# ── Tabela ───────────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 Registro de Pedidos ({len(df_filtrado)} resultados)")

# Formatar data para exibição
df_display = df_filtrado.copy()
df_display["data_pedido"] = df_display["data_pedido"].dt.strftime("%d/%m/%Y")
if "data_entrega" in df_display.columns:
    df_display["data_entrega"] = pd.to_datetime(df_display["data_entrega"], errors="coerce")
    df_display["data_entrega"] = df_display["data_entrega"].dt.strftime("%d/%m/%Y")

# Colunas de exibição
colunas_exibir = [
    "id", "cliente", "elemento", "quantidade", "volume_total_m3",
    "data_pedido", "data_entrega", "status", "traco_nome",
]
colunas_existentes = [c for c in colunas_exibir if c in df_display.columns]

st.dataframe(
    df_display[colunas_existentes],
    width="stretch",
    hide_index=True,
    column_config={
        "id": "Pedido #",
        "cliente": "Cliente",
        "elemento": "Elemento",
        "quantidade": st.column_config.NumberColumn("Qtd.", format="%d"),
        "volume_total_m3": st.column_config.NumberColumn("Volume (m³)", format="%.2f"),
        "data_pedido": "Data Pedido",
        "data_entrega": "Data Entrega",
        "status": "Status",
        "traco_nome": "Traço Utilizado",
    },
)

# ── Atualizar Status ─────────────────────────────────────────
st.markdown("---")
st.subheader("🔄 Atualizar Status de Pedido")

# Filtrar pedidos que podem mudar de status
pedidos_atualizaveis = df_filtrado[df_filtrado["status"].isin(["Pendente", "Em Produção"])]

if not pedidos_atualizaveis.empty:
    opcoes_pedido = {
        f"#{row['id']} — {row['cliente']} — {row['elemento']} ({row['status']})": row["id"]
        for _, row in pedidos_atualizaveis.iterrows()
    }
    pedido_selecionado = st.selectbox(
        "Selecione o pedido:",
        options=list(opcoes_pedido.keys()),
        key="hist_pedido_select",
    )
    pedido_id = opcoes_pedido[pedido_selecionado]
    pedido_status_atual = pedidos_atualizaveis[pedidos_atualizaveis["id"] == pedido_id].iloc[0]["status"]

    col_a, col_b, col_c = st.columns(3)

    if pedido_status_atual == "Pendente":
        if col_a.button("🔨 Marcar como Em Produção", type="primary", width="stretch"):
            try:
                with UnitOfWork() as uow:
                    uow.fabrica.update_pedido_status(pedido_id, "Em Produção")
                st.toast("Status atualizado para 'Em Produção'!", icon="🔨")
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

    if pedido_status_atual in ("Pendente", "Em Produção"):
        if col_b.button("✅ Marcar como Concluído", width="stretch"):
            try:
                with UnitOfWork() as uow:
                    uow.fabrica.update_pedido_status(pedido_id, "Concluído")
                st.toast("Status atualizado para 'Concluído'!", icon="✅")
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")

    if col_c.button("❌ Cancelar Pedido", width="stretch"):
        try:
            with UnitOfWork() as uow:
                uow.fabrica.update_pedido_status(pedido_id, "Cancelado")
            st.toast("Pedido cancelado.", icon="❌")
            import time
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao cancelar: {e}")
else:
    st.info("Não há pedidos com status atualizável (Pendente ou Em Produção).")

# ── Exportar CSV ─────────────────────────────────────────────
st.markdown("---")
csv_data = df_display[colunas_existentes].to_csv(index=False, sep=";", encoding="utf-8-sig")
st.download_button(
    label="📥 Exportar para CSV",
    data=csv_data,
    file_name="historico_producao.csv",
    mime="text/csv",
    width="stretch",
)

