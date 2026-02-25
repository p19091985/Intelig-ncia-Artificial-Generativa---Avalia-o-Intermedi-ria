"""
03_📝_Novo_Pedido.py — Formulário para criação de novos pedidos
Selecionar cliente, elemento, quantidade e data de entrega.
"""
import streamlit as st
import pandas as pd
import logging
import time
from pathlib import Path
from datetime import date, timedelta
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components.ai_concreto import sugerir_traco
from components import servicos_gerenciador as servico
from utils.traco_utils import formatar_traco_legivel, formatar_traco_detalhado
import config

log = logging.getLogger(__name__)

st.set_page_config(page_title="Novo Pedido", layout="wide", page_icon="📝")

# ── Segurança ────────────────────────────────────────────────
st_check_session()
try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    st.error(f"Erro ao verificar permissões: {e}")
    st.stop()

if not config.DATABASE_ENABLED:
    st.warning("Banco de dados desabilitado.")
    st.stop()

# ── Título ───────────────────────────────────────────────────
st.title("📝 Novo Pedido de Produção")

# ── Feedback ─────────────────────────────────────────────────
if "pedido_feedback" in st.session_state:
    fb = st.session_state.pop("pedido_feedback")
    {"sucesso": st.success, "erro": st.error}.get(fb["tipo"], st.info)(fb["texto"])

# ── Carregar Dados ───────────────────────────────────────────
with UnitOfWork() as uow:
    df_clientes = uow.fabrica.get_all_clientes()
    df_elementos = uow.fabrica.get_catalogo_elementos()
    df_tracos = uow.fabrica.get_tracos_padrao()

if df_clientes.empty or df_elementos.empty or df_tracos.empty:
    st.warning("Cadastre clientes, elementos e traços antes de criar pedidos.")
    st.stop()

# ── Formulário ───────────────────────────────────────────────
with st.container(border=True):
    st.subheader("🛒 Dados do Pedido")

    col1, col2 = st.columns(2)

    # Cliente
    clientes_opcoes = dict(zip(df_clientes["nome"], df_clientes["id"]))
    cliente_nome = col1.selectbox("👤 Cliente", options=list(clientes_opcoes.keys()))
    cliente_id = clientes_opcoes[cliente_nome]

    # Elemento
    elementos_opcoes = {
        f"{row['nome']} (FCK {row['fck_necessario']:.0f} MPa)": row["id"]
        for _, row in df_elementos.iterrows()
    }
    elemento_label = col2.selectbox("🧱 Elemento Pré-Moldado", options=list(elementos_opcoes.keys()))
    elemento_id = elementos_opcoes[elemento_label]

    # Detalhes do elemento selecionado
    elem_selecionado = df_elementos[df_elementos["id"] == elemento_id].iloc[0]

    col3, col4, col5 = st.columns(3)
    quantidade = col3.number_input("📦 Quantidade", min_value=1, value=100, step=10)
    data_entrega = col4.date_input(
        "📅 Data de Entrega",
        value=date.today() + timedelta(days=15),
        min_value=date.today(),
    )

    # Traço
    tracos_opcoes = {
        f"{row['nome']} ({formatar_traco_legivel(row['traco_str'])})": row["id"]
        for _, row in df_tracos.iterrows()
    }
    tracos_labels = list(tracos_opcoes.keys())
    tracos_ids = list(tracos_opcoes.values())

    # Auto-selecionar traço vinculado ao elemento (Regra Padrão)
    # Se acabamos de criar um traço novo via IA, ele deve ter preferência
    traco_index = 0
    if "novo_traco_id" in st.session_state:
        # Tenta selecionar o ID recém-criado
        new_id = st.session_state.novo_traco_id
        if new_id in tracos_ids:
            traco_index = tracos_ids.index(new_id)
            st.toast("Traço criado via IA selecionado automaticamente!", icon="✨")
        del st.session_state.novo_traco_id # Limpa após usar
    else:
        # Lógica padrão (vinculo do elemento)
        elem_traco_id = elem_selecionado.get("traco_id")
        if elem_traco_id and not pd.isna(elem_traco_id):
            elem_traco_id = int(elem_traco_id)
            if elem_traco_id in tracos_ids:
                traco_index = tracos_ids.index(elem_traco_id)

    traco_label = col5.selectbox(
        "🧪 Traço a Utilizar",
        options=tracos_labels,
        index=traco_index,
        help="Traço sugerido automaticamente pelo elemento selecionado.",
    )
    traco_id = tracos_opcoes[traco_label]

    # ── ✨ INTEGRAÇÃO IA (NOVO) ──────────────────────────────
    with st.expander("✨ Criar Traço Personalizado com IA (Opcional)"):
        st.caption("Se nenhum dos traços acima servir, gere um novo agora mesmo. "
                   "Selecione os materiais do seu estoque e a IA calculará a dosagem ideal.")

        # Load all materials from the database once
        df_mats = pd.DataFrame()
        try:
            with UnitOfWork() as uow:
                df_mats = uow.fabrica.get_all_materiais()
        except Exception:
            pass

        # ── Row 1: Main Parameters ───────────────────────────
        st.markdown("##### 📐 Parâmetros Principais")
        c_ia1, c_ia2, c_ia3 = st.columns(3)
        ia_fck = c_ia1.number_input(
            "FCK (MPa)", value=float(elem_selecionado['fck_necessario']),
            min_value=5.0, max_value=100.0, step=5.0, key="ia_fck",
            help="Resistência característica à compressão do concreto."
        )
        ia_slump = c_ia2.number_input(
            "Slump (mm)", value=100.0,
            min_value=0.0, max_value=250.0, step=10.0, key="ia_slump",
            help="Abatimento do tronco de cone — indica a trabalhabilidade."
        )
        agressividade_opcoes = [
            "I — Fraca (Rural)",
            "II — Moderada (Urbana)",
            "III — Forte (Marinha/Industrial)",
            "IV — Muito Forte (Respingos de Maré)",
        ]
        ia_agressividade = c_ia3.selectbox(
            "Classe de Agressividade (ABNT 6118)",
            options=agressividade_opcoes, index=1, key="ia_agress",
            help="Influencia a relação água/cimento máxima e o cobrimento."
        )

        # ── Row 2: Base Materials (from DB) ──────────────────
        st.markdown("##### 🧱 Materiais Base")
        sel_mats = {}
        ia_brita = "Brita 1"

        if not df_mats.empty:
            c_m1, c_m2, c_m3 = st.columns(3)

            # Cement selector
            cimentos = df_mats[df_mats['tipo'] == 'Cimento']
            cimento_nomes = cimentos['nome'].tolist()
            # Default: CP-II-F-32 (general purpose, index 5 in seed data)
            cimento_default = 0
            for i, name in enumerate(cimento_nomes):
                if "CP-II-F-32" in name:
                    cimento_default = i
                    break
            ia_cimento_nome = c_m1.selectbox(
                "🏗️ Tipo de Cimento", options=cimento_nomes,
                index=cimento_default, key="ia_cimento_sel",
                help="Selecione o cimento disponível no estoque."
            )
            cimento_row = cimentos[cimentos['nome'] == ia_cimento_nome].iloc[0]
            sel_mats['Cimento'] = {
                "tipo": ia_cimento_nome, "custo_kg": float(cimento_row['custo_kg'])
            }
            c_m1.caption(f"📦 Estoque: {cimento_row['estoque_atual']:,.0f} kg  •  R$ {cimento_row['custo_kg']:.2f}/kg")

            # Sand selector
            areias = df_mats[df_mats['tipo'] == 'Areia']
            areia_nomes = areias['nome'].tolist()
            areia_default = 0
            for i, name in enumerate(areia_nomes):
                if "Média" in name:
                    areia_default = i
                    break
            ia_areia_nome = c_m2.selectbox(
                "🏖️ Agregado Miúdo (Areia)", options=areia_nomes,
                index=areia_default, key="ia_areia_sel",
                help="Selecione a areia disponível no estoque."
            )
            areia_row = areias[areias['nome'] == ia_areia_nome].iloc[0]
            sel_mats['Areia'] = {
                "tipo": ia_areia_nome, "custo_kg": float(areia_row['custo_kg'])
            }
            c_m2.caption(f"📦 Estoque: {areia_row['estoque_atual']:,.0f} kg  •  R$ {areia_row['custo_kg']:.2f}/kg")

            # Gravel selector
            britas = df_mats[df_mats['tipo'] == 'Brita']
            brita_nomes = britas['nome'].tolist()
            brita_default = 0
            for i, name in enumerate(brita_nomes):
                if "Brita 1" in name:
                    brita_default = i
                    break
            ia_brita_nome = c_m3.selectbox(
                "🪨 Agregado Graúdo (Brita)", options=brita_nomes,
                index=brita_default, key="ia_brita_sel",
                help="Selecione a brita disponível no estoque."
            )
            brita_row = britas[britas['nome'] == ia_brita_nome].iloc[0]
            ia_brita = ia_brita_nome
            sel_mats['Brita'] = {
                "tipo": ia_brita_nome, "custo_kg": float(brita_row['custo_kg'])
            }
            c_m3.caption(f"📦 Estoque: {brita_row['estoque_atual']:,.0f} kg  •  R$ {brita_row['custo_kg']:.2f}/kg")

            # Water (auto-selected, always present)
            agua = df_mats[df_mats['tipo'] == 'Água']
            if not agua.empty:
                agua_row = agua.iloc[0]
                sel_mats['Água'] = {
                    "tipo": agua_row['nome'], "custo_kg": float(agua_row['custo_kg'])
                }

            # ── Row 3: Optional Advanced Inputs ──────────────
            with st.expander("⚙️ Opções Avançadas (Aditivos, Adições, Fibras)", expanded=False):
                c_a1, c_a2, c_a3 = st.columns(3)

                # Additive selector
                aditivos = df_mats[df_mats['tipo'] == 'Aditivo']
                aditivo_nomes = ["Nenhum"] + aditivos['nome'].tolist()
                ia_aditivo_nome = c_a1.selectbox(
                    "🧪 Aditivo", options=aditivo_nomes,
                    index=0, key="ia_aditivo_sel",
                    help="Aditivos químicos para melhorar propriedades do concreto."
                )
                if ia_aditivo_nome != "Nenhum":
                    aditivo_row = aditivos[aditivos['nome'] == ia_aditivo_nome].iloc[0]
                    sel_mats['Aditivo'] = {
                        "tipo": ia_aditivo_nome, "custo_kg": float(aditivo_row['custo_kg'])
                    }
                    c_a1.caption(f"📦 Estoque: {aditivo_row['estoque_atual']:,.0f} kg  •  R$ {aditivo_row['custo_kg']:.2f}/kg")

                # Mineral addition selector
                adicoes = df_mats[df_mats['tipo'] == 'Adição']
                adicao_nomes = ["Nenhuma"] + adicoes['nome'].tolist()
                ia_adicao_nome = c_a2.selectbox(
                    "🔬 Adição Mineral", options=adicao_nomes,
                    index=0, key="ia_adicao_sel",
                    help="Adições minerais (Sílica Ativa, Metacaulim, Cinza Volante)."
                )
                if ia_adicao_nome != "Nenhuma":
                    adicao_row = adicoes[adicoes['nome'] == ia_adicao_nome].iloc[0]
                    sel_mats['Adição'] = {
                        "tipo": ia_adicao_nome, "custo_kg": float(adicao_row['custo_kg'])
                    }
                    c_a2.caption(f"📦 Estoque: {adicao_row['estoque_atual']:,.0f} kg  •  R$ {adicao_row['custo_kg']:.2f}/kg")

                # Fiber selector
                fibras = df_mats[df_mats['tipo'] == 'Fibra']
                fibra_nomes = ["Nenhuma"] + fibras['nome'].tolist()
                ia_fibra_nome = c_a3.selectbox(
                    "🧵 Fibra", options=fibra_nomes,
                    index=0, key="ia_fibra_sel",
                    help="Fibras para reforço estrutural e controle de fissuras."
                )
                if ia_fibra_nome != "Nenhuma":
                    fibra_row = fibras[fibras['nome'] == ia_fibra_nome].iloc[0]
                    sel_mats['Fibra'] = {
                        "tipo": ia_fibra_nome, "custo_kg": float(fibra_row['custo_kg'])
                    }
                    c_a3.caption(f"📦 Estoque: {fibra_row['estoque_atual']:,.0f} kg  •  R$ {fibra_row['custo_kg']:.2f}/kg")

        else:
            st.warning("⚠️ Não foi possível carregar os materiais do banco. "
                       "Verifique se há materiais cadastrados na Gestão de Materiais.")

        # ── Generate Button ──────────────────────────────────
        st.markdown("---")
        if st.button("🚀 Gerar Sugestão", key="btn_gerar_ia", type="primary", use_container_width=True):
            with st.spinner("🤖 IA calculando dosagem com base nos materiais selecionados..."):
                time.sleep(1)
                res = sugerir_traco(
                    ia_fck, ia_slump, ia_brita,
                    materiais_selecionados=sel_mats
                )
                st.session_state.ia_resultado_temp = res

        if "ia_resultado_temp" in st.session_state:
            res = st.session_state.ia_resultado_temp
            st.markdown(f"💡 **Sugestão IA:** {formatar_traco_detalhado(res['traco_sugerido'])}")
            st.metric("💰 Custo Estimado", f"R$ {res['custo_estimado']:.2f}/m³")

            col_save1, col_save2 = st.columns([3, 1])
            from datetime import datetime
            ts = datetime.now().strftime("%H%M%S")
            nome_sug = col_save1.text_input("Nome do Traço", value=f"IA FCK {ia_fck:.0f} — {ts}", key="ia_nome_traco")

            if col_save2.button("💾 Salvar e Usar", type="primary", key="btn_save_ia"):
                try:
                    t_data = {
                        "nome": nome_sug,
                        "fck_alvo": float(ia_fck),
                        "traco_str": res["traco_sugerido"],
                        "consumo_cimento_m3": float(res["consumo_cimento_m3"]),
                    }
                    with UnitOfWork() as uow:
                        uow.fabrica.save_traco(t_data)
                        # Recuperar ID do traço recém salvo
                        from sqlalchemy import text
                        new_traco = uow.connection.execute(
                            text("SELECT id FROM fab_tracos_padrao WHERE nome = :nome"), {"nome": nome_sug}
                        ).fetchone()
                        if new_traco:
                            st.session_state.novo_traco_id = new_traco[0]

                    st.success("Traço salvo! Recarregando...")
                    del st.session_state.ia_resultado_temp
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ── Cálculo automático de volume ─────────────────────────
    st.markdown("---")
    volume_unitario = elem_selecionado["volume_m3"]
    volume_total = round(quantidade * volume_unitario, 4)

    m1, m2, m3 = st.columns(3)
    m1.metric("Volume unitário", f"{volume_unitario:.4f} m³")
    m2.metric("Quantidade", f"{quantidade:,}")
    m3.metric("📐 Volume Total", f"{volume_total:.2f} m³", help="Quantidade × Volume unitário")

    # ── Botão Salvar ─────────────────────────────────────────
    st.markdown("")
    if st.button("💾 Salvar Pedido", type="primary", width="stretch"):
        try:
            pedido_data = {
                "cliente_id": int(cliente_id),
                "elemento_id": int(elemento_id),
                "quantidade": int(quantidade),
                "data_entrega": str(data_entrega),
                "status": "Pendente",
                "traco_usado_id": int(traco_id),
            }
            with UnitOfWork() as uow:
                uow.fabrica.save_pedido(pedido_data)
            st.balloons()
            st.session_state.pedido_feedback = {
                "tipo": "sucesso",
                "texto": f"Pedido registrado com sucesso! {quantidade}x {elem_selecionado['nome']} "
                         f"para {cliente_nome} (Volume: {volume_total:.2f} m³).",
            }
            time.sleep(1)
            st.rerun()
        except Exception as e:
            log.error(f"Erro ao salvar pedido: {e}", exc_info=True)
            st.session_state.pedido_feedback = {
                "tipo": "erro",
                "texto": f"Erro ao salvar pedido: {e}",
            }
            st.rerun()
