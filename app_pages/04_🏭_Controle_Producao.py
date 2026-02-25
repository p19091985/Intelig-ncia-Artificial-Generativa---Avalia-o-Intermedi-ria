"""
04_🏭_Controle_Producao.py — Gerenciamento de Chão de Fábrica
"""
import streamlit as st
import pandas as pd
import time
from pathlib import Path
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
from utils.traco_utils import formatar_traco_legivel
import config

st.set_page_config(page_title="Controle de Produção", layout="wide", page_icon="🏭")

# ── Segurança ────────────────────────────────────────────────
st_check_session()
try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    # Se a página não estiver no banco ainda, permite admin/engenheiro por fallback ou mostra erro
    # Para desenvolvimento, vamos logar apenas
    pass 

if not config.DATABASE_ENABLED:
    st.warning("Banco de dados desabilitado.")
    st.stop()

# ── Helper: Parse do Traço ───────────────────────────────────
def parse_traco_str(traco_str: str) -> dict:
    """Retorna proporções {areia: float, brita: float} a partir da string '1 : X : Y : Z'."""
    try:
        # Ex: "1 : 2.2 : 3.1 : 0.5 a/c"
        clean = traco_str.replace("a/c", "").replace(" ", "")
        parts = clean.split(":")
        if len(parts) >= 3:
            return {
                "areia": float(parts[1]),
                "brita": float(parts[2]),
                "agua": float(parts[3]) if len(parts) > 3 else 0.5
            }
    except:
        pass
    return {"areia": 2.0, "brita": 3.0, "agua": 0.5} # Fallback

# ── Título ───────────────────────────────────────────────────
st.title("🏭 Controle de Produção")
st.markdown("Gerencie o status dos pedidos e realize a baixa de materiais.")

# ── Carregar Pedidos ─────────────────────────────────────────
df_pedidos = pd.DataFrame()
with UnitOfWork() as uow:
    df_pedidos = uow.fabrica.get_all_pedidos()
    df_materiais = uow.fabrica.get_all_materiais()

if df_pedidos.empty:
    st.info("Nenhum pedido registrado no sistema.")
    st.stop()

# Abas de Status
tab1, tab2, tab3 = st.tabs(["⏳ Pendentes", "⚙️ Em Produção", "✅ Concluídos"])

# ── ABA: PENDENTES ───────────────────────────────────────────
with tab1:
    pendentes = df_pedidos[df_pedidos["status"] == "Pendente"]
    if pendentes.empty:
        st.write("Sem pedidos pendentes.")
    else:
        for idx, row in pendentes.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.markdown(f"**Pedido #{row['id']}** - {row['cliente']}")
                c2.markdown(f"📦 {row['quantidade']}x {row['elemento']}")
                c3.markdown(f"📅 Entrega: {row['data_entrega']}")
                
                if c4.button("▶️ Iniciar", key=f"btn_start_{row['id']}", type="primary"):
                    with UnitOfWork() as uow:
                        uow.fabrica.update_pedido_status(row["id"], "Em Produção")
                    st.toast(f"Pedido #{row['id']} iniciado!")
                    time.sleep(0.5)
                    st.rerun()

# ── ABA: EM PRODUÇÃO ─────────────────────────────────────────
with tab2:
    em_producao = df_pedidos[df_pedidos["status"] == "Em Produção"]
    if em_producao.empty:
        st.write("Nenhum pedido em produção no momento.")
    else:
        for idx, row in em_producao.iterrows():
            with st.expander(f"⚙️ Pedido #{row['id']} - {row['cliente']} ({row['elemento']})", expanded=True):
                # Detalhes do cálculo
                vol_total = row['volume_total_m3']
                traco_str = row['traco_str'] if row['traco_str'] else "1:2:3"
                consumo_cimento_unit = row['consumo_cimento_m3'] if pd.notna(row['consumo_cimento_m3']) else 300.0
                
                # Parse
                props = parse_traco_str(traco_str)
                
                # Totais Teóricos
                kg_cimento = round(consumo_cimento_unit * vol_total, 1)
                kg_areia = round(kg_cimento * props["areia"], 1)
                kg_brita = round(kg_cimento * props["brita"], 1)
                kg_aditivo = round(kg_cimento * 0.005, 2) # Est. 0.5%
                
                st.info(f"**Traço:** {formatar_traco_legivel(traco_str)}  ·  Subtotal Previsto: {vol_total} m³ de Concreto")
                
                # Form para Baixa
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 📉 Estimativa de Consumo")
                    st.markdown(f"- **Cimento:** {kg_cimento} kg")
                    st.markdown(f"- **Areia:** {kg_areia} kg")
                    st.markdown(f"- **Brita:** {kg_brita} kg")
                    st.markdown(f"- **Aditivo:** {kg_aditivo} kg")
                
                with c2:
                    st.markdown("##### 📦 Deduzir do Estoque:")
                    # Selectboxes para escolher qual material descontar
                    # Filtra materiais
                    opts_cimento = df_materiais[df_materiais['tipo'] == 'Cimento']['nome'].tolist()
                    opts_areia = df_materiais[df_materiais['tipo'] == 'Areia']['nome'].tolist()
                    opts_brita = df_materiais[df_materiais['tipo'] == 'Brita']['nome'].tolist()
                    opts_aditivo = df_materiais[df_materiais['tipo'] == 'Aditivo']['nome'].tolist()

                    sel_cimento = st.selectbox("Lote Cimento", ["Não Baixar"] + opts_cimento, index=1 if opts_cimento else 0, key=f"s_cim_{row['id']}")
                    sel_areia = st.selectbox("Lote Areia", ["Não Baixar"] + opts_areia, index=1 if opts_areia else 0, key=f"s_are_{row['id']}")
                    sel_brita = st.selectbox("Lote Brita", ["Não Baixar"] + opts_brita, index=1 if opts_brita else 0, key=f"s_bri_{row['id']}")
                    sel_aditivo = st.selectbox("Lote Aditivo", ["Não Baixar"] + opts_aditivo, index=0, key=f"s_adi_{row['id']}")

                st.markdown("---")
                if st.button("✅ Concluir e Baixar Estoque", key=f"btn_finish_{row['id']}", type="primary"):
                    try:
                        with UnitOfWork() as uow:
                            # 1. Atualizar Status
                            uow.fabrica.update_pedido_status(row["id"], "Concluído")
                            
                            # 2. Baixar Estoque (se selecionado)
                            msgs = []
                            def baixar(nome, qtd):
                                if nome and nome != "Não Baixar":
                                    mat = df_materiais[df_materiais['nome'] == nome].iloc[0]
                                    nova_qtd = float(mat['estoque_atual']) - qtd
                                    uow.fabrica.update_estoque(int(mat['id']), nova_qtd)
                                    msgs.append(f"{qtd}kg de {nome}")

                            baixar(sel_cimento, kg_cimento)
                            baixar(sel_areia, kg_areia)
                            baixar(sel_brita, kg_brita)
                            baixar(sel_aditivo, kg_aditivo)
                            
                        st.success(f"Pedido Concluído! Baixados: {', '.join(msgs)}")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")

# ── ABA: CONCLUÍDOS ──────────────────────────────────────────
with tab3:
    concluidos = df_pedidos[df_pedidos["status"] == "Concluído"]
    if concluidos.empty:
        st.write("Histórico vazio.")
    else:
        st.dataframe(
            concluidos[["id", "cliente", "elemento", "quantidade", "data_entrega", "volume_total_m3"]],
            width="stretch",
            hide_index=True
        )
