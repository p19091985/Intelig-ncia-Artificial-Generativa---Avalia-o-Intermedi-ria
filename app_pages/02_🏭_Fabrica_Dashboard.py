"""
12_🏭_Fabrica_Dashboard.py — Dashboard da Fábrica de Pré-Moldados
Visão geral: KPIs, alertas de estoque e gráfico de pedidos por status.
"""
import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
import config

st.set_page_config(page_title="Fábrica Dashboard", layout="wide", page_icon="🏭")
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
st.title("🏭 Dashboard da Fábrica de Pré-Moldados")
st.markdown("Visão geral da produção, estoque e pedidos em andamento.")
st.markdown("---")

# ── Carregar dados ───────────────────────────────────────────
try:
    with UnitOfWork() as uow:
        resumo = uow.fabrica.get_resumo_pedidos()
        df_estoque_baixo = uow.fabrica.get_estoque_baixo(limite=1000.0)
        df_por_status = uow.fabrica.get_pedidos_por_status()
except Exception as e:
    st.error(f"Erro ao carregar dados do dashboard: {e}")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Total de Pedidos", resumo["total"])
col2.metric("⏳ Pendentes", resumo["pendentes"])
col3.metric("🔨 Em Produção", resumo["em_producao"])
col4.metric("📐 Volume Programado", f"{resumo['volume_programado_m3']:.1f} m³")

st.markdown("---")

# ── Gráfico de Pedidos por Status ────────────────────────────
col_chart, col_alerts = st.columns([3, 2])

with col_chart:
    st.subheader("📊 Pedidos por Status")
    if not df_por_status.empty:
        import plotly.express as px

        color_map = {
            "Pendente": "#FFA726",
            "Em Produção": "#42A5F5",
            "Concluído": "#66BB6A",
            "Cancelado": "#EF5350",
        }
        fig = px.bar(
            df_por_status,
            x="status",
            y="quantidade",
            color="status",
            color_discrete_map=color_map,
            text="quantidade",
            labels={"status": "Status", "quantidade": "Quantidade"},
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum pedido registrado ainda.")

# ── Alertas de Estoque Baixo ────────────────────────────────
with col_alerts:
    st.subheader("🚨 Alertas de Estoque Baixo")
    if not df_estoque_baixo.empty:
        for _, row in df_estoque_baixo.iterrows():
            severity = "🔴" if row["estoque_atual"] < 300 else "🟡"
            st.warning(
                f"{severity} **{row['nome']}** ({row['tipo']}): "
                f"apenas **{row['estoque_atual']:.0f} kg** em estoque"
            )
    else:
        st.success("✅ Todos os materiais com estoque adequado (> 1.000 kg).")

# ── Gráfico de Volume de Produção ao Longo do Tempo ─────────
st.markdown("---")
st.subheader("📈 Tendência de Produção")

try:
    with UnitOfWork() as uow:
        df_timeline = uow.fabrica.get_all_pedidos()

    if not df_timeline.empty and "data_pedido" in df_timeline.columns:
        df_timeline["data_pedido"] = pd.to_datetime(df_timeline["data_pedido"], errors="coerce")
        df_timeline = df_timeline.dropna(subset=["data_pedido"])

        if not df_timeline.empty:
            df_timeline["semana"] = df_timeline["data_pedido"].dt.to_period("W").apply(lambda r: r.start_time)
            df_semanal = df_timeline.groupby("semana").agg(
                pedidos=("id", "count"),
                volume=("volume_total_m3", "sum"),
            ).reset_index()
            df_semanal["semana"] = pd.to_datetime(df_semanal["semana"])

            import plotly.graph_objects as go
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_semanal["semana"],
                y=df_semanal["volume"],
                mode="lines+markers",
                name="Volume (m³)",
                line=dict(color="#42A5F5", width=3),
                fill="tozeroy",
                fillcolor="rgba(66, 165, 245, 0.1)",
            ))
            fig2.add_trace(go.Bar(
                x=df_semanal["semana"],
                y=df_semanal["pedidos"],
                name="Pedidos",
                marker_color="rgba(255, 167, 38, 0.6)",
                yaxis="y2",
            ))
            fig2.update_layout(
                xaxis_title="Semana",
                yaxis_title="Volume (m³)",
                yaxis2=dict(title="Nº Pedidos", overlaying="y", side="right"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=30, b=20),
                height=350,
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados suficientes para gráfico de tendência.")
    else:
        st.info("Sem pedidos para exibir tendência.")
except Exception as e:
    st.caption(f"Gráfico de tendência indisponível: {e}")

# ── Resumo de Pedidos Concluídos ─────────────────────────────
st.markdown("---")
st.subheader("✅ Produção Concluída")
st.metric("Pedidos Concluídos", resumo["concluidos"])

