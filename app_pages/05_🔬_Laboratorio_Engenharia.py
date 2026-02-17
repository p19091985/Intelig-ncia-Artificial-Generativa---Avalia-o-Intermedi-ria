"""
14_🧠_AI_Recomendacao_Traco.py — Recomendação de Traço com IA (Mock)
Interface de chat conversacional para dosagem de concreto via IA simulada.
Usa st.chat_message para simular uma interação com LLM.
"""
import streamlit as st
import pandas as pd
import time
from pathlib import Path
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico
from components.ai_concreto import sugerir_traco
from persistencia.unit_of_work import UnitOfWork
import config

st.set_page_config(page_title="AI Recomendação de Traço", layout="wide", page_icon="🧠")

# ── Segurança ────────────────────────────────────────────────
st_check_session()
try:
    allowed_roles = servico.get_allowed_roles_for_page(Path(__file__).name)
    check_access(allowed_roles)
except Exception as e:
    st.error(f"Erro ao verificar permissões: {e}")
    st.stop()

# ── Título ───────────────────────────────────────────────────
st.title("🧠 Inteligência Artificial para Dosagem de Concreto")
st.markdown(
    "Converse com a IA para obter traços otimizados. O sistema analisa "
    "granulometria, curvas de Abrams e normas técnicas (NBR 6118/12655)."
)
st.markdown("---")

# ── Session State para histórico de chat ─────────────────────
if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = [
        {
            "role": "assistant",
            "content": (
                "🤖 **Olá! Sou o assistente de dosagem de concreto.**\n\n"
                "Posso analisar parâmetros e recomendar o traço ideal para sua aplicação. "
                "Configure os parâmetros no painel à esquerda e clique em **Gerar Traço** "
                "para iniciar a análise.\n\n"
                "Exemplos de aplicações que posso ajudar:\n"
                "- Pilar de edifício (FCK 40 MPa)\n"
                "- Bloco estrutural (FCK 10 MPa)\n"
                "- Viga de ponte (FCK 50 MPa)\n"
                "- Piso industrial (FCK 35 MPa)"
            ),
        }
    ]

# ── Layout: Sidebar de parâmetros + Chat principal ───────────
# ── Carregar Materiais do Banco ──────────────────────────────
df_materiais = pd.DataFrame()
if config.DATABASE_ENABLED:
    try:
        with UnitOfWork() as uow:
            df_materiais = uow.fabrica.get_all_materiais()
    except Exception as e:
        st.error(f"Erro ao carregar materiais: {e}")

# ── Layout: Sidebar de parâmetros + Chat principal ───────────
col_params, col_chat = st.columns([1, 2])

with col_params:
    with st.container(border=True):
        st.subheader("⚙️ Parâmetros")
        
        # Seleção de Materiais (Novo)
        st.markdown("**(Opcional) Selecione Materiais Específicos:**")
        
        selected_mats = {}
        
        if not df_materiais.empty:
            # Helper para criar selectbox
            def criar_selectbox(label, tipo, key_suffix):
                opcoes = df_materiais[df_materiais['tipo'] == tipo].to_dict('records')
                # Adiciona opção "Automático" (None)
                opcoes_display = ["🤖 Automático (IA decide)"] + [f"{m['nome']} (R$ {m['custo_kg']:.2f}/kg)" for m in opcoes]
                
                escolha = st.selectbox(label, options=opcoes_display, index=0, key=f"sel_{key_suffix}")
                
                if escolha and "🤖" not in escolha:
                    # Encontrar o objeto original pelo nome (simplificado)
                    nome_escolhido = escolha.split(" (R$")[0]
                    return next((m for m in opcoes if m['nome'] == nome_escolhido), None)
                return None

            selected_mats['Cimento'] = criar_selectbox("🧱 Cimento", "Cimento", "cimento")
            selected_mats['Areia'] = criar_selectbox("🏖️ Areia", "Areia", "areia")
            selected_mats['Brita'] = criar_selectbox("🪨 Brita", "Brita", "brita")
            selected_mats['Aditivo'] = criar_selectbox("💧 Aditivo", "Aditivo", "aditivo")
        else:
            st.warning("Sem materiais cadastrados no banco.")

        st.markdown("---")
        st.caption("Parâmetros do Concreto:")

        fck = st.number_input(
            "🎯 FCK Desejado (MPa)",
            min_value=5.0,
            max_value=80.0,
            value=30.0,
            step=5.0,
            help="Resistência característica à compressão",
        )
        slump = st.number_input(
            "📏 Slump / Abatimento (mm)",
            min_value=20.0,
            max_value=250.0,
            value=100.0,
            step=10.0,
            help="Medida de trabalhabilidade do concreto",
        )
        # Agregado Graúdo (Legacy / Fallback se não selecionou brita específica)
        if not selected_mats.get('Brita'):
            agregado_legacy = st.selectbox(
                "🪨 Tamanho Agregado (Estimado)",
                options=["Brita 0", "Brita 1", "Brita 2"],
                index=1,
            )
        else:
            agregado_legacy = selected_mats['Brita']['nome']

        aplicacao = st.text_input(
            "🏗️ Aplicação (opcional)",
            placeholder="Ex: Pilar 30x30, Bloco estrutural...",
        )

        st.markdown("")
        gerar = st.button(
            "🚀 Gerar Traço com IA",
            type="primary",
            width="stretch",
        )

        st.markdown("")
        if st.button("🗑️ Limpar Conversa", width="stretch"):
            st.session_state.ai_chat_history = [
                st.session_state.ai_chat_history[0]
            ]
            st.rerun()

# ── Área de Chat ─────────────────────────────────────────────
with col_chat:
    # Exibir histórico de mensagens
    for msg in st.session_state.ai_chat_history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👷"):
            st.markdown(msg["content"])

    # Processar nova geração
    if gerar:
        # Mensagem do "usuário"
        app_text = f" para **{aplicacao}**" if aplicacao.strip() else ""
        
        # Monta descrição dos materiais escolhidos
        mats_desc = []
        if selected_mats.get('Cimento'): mats_desc.append(f"Cimento: {selected_mats['Cimento']['nome']}")
        if selected_mats.get('Areia'): mats_desc.append(f"Areia: {selected_mats['Areia']['nome']}")
        if selected_mats.get('Brita'): mats_desc.append(f"Brita: {selected_mats['Brita']['nome']}")
        if selected_mats.get('Aditivo'): mats_desc.append(f"Aditivo: {selected_mats['Aditivo']['nome']}")
        
        mats_str = "\n- ".join(mats_desc) if mats_desc else "Automático (IA decide)"
        
        user_msg = (
            f"Preciso de um traço de concreto{app_text} com as seguintes especificações:\n\n"
            f"- **FCK:** {fck} MPa\n"
            f"- **Slump:** {slump} mm\n"
            f"- **Materiais:**\n- {mats_str}"
        )
        st.session_state.ai_chat_history.append({"role": "user", "content": user_msg})

        with st.chat_message("user", avatar="👷"):
            st.markdown(user_msg)

        # Resposta da "IA"
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔬 Analisando granulometria e curvas de Abrams..."):
                time.sleep(2)
                resultado = sugerir_traco(
                    fck=fck, 
                    slump=slump, 
                    agregado_max=agregado_legacy,
                    materiais_selecionados=selected_mats
                )

            st.success("✅ Análise concluída!")

            # KPIs do resultado
            r1, r2, r3 = st.columns(3)
            r1.metric("Traço", resultado["traco_sugerido"])
            r2.metric("Cimento", resultado["cimento_tipo"])
            r3.metric("💰 Custo/m³", f"R$ {resultado['custo_estimado']:.2f}")

            # Materiais por m³
            st.markdown("**📦 Materiais para 1 m³:**")
            mat = resultado["materiais_m3"]
            mat_cols = st.columns(len(mat))
            for i, (nome, info) in enumerate(mat.items()):
                with mat_cols[i]:
                    qtd_key = "litros" if "litros" in info else "kg"
                    qtd = info[qtd_key]
                    custo_total = round(qtd * info["custo_kg"], 2)
                    st.metric(
                        nome,
                        f"{qtd} {qtd_key}",
                        delta=f"R$ {custo_total:.2f}",
                        delta_color="off",
                    )

            # Justificativa
            with st.expander("📖 Justificativa Técnica Completa", expanded=False):
                st.markdown(resultado["justificativa"])

            # Montar resposta resumida para o histórico
            ai_response = (
                f"✅ **Traço gerado com sucesso!**\n\n"
                f"| Parâmetro | Valor |\n|---|---|\n"
                f"| Traço | {resultado['traco_sugerido']} |\n"
                f"| Cimento | {resultado['cimento_tipo']} |\n"
                f"| Relação a/c | {resultado['relacao_ac']} |\n"
                f"| Custo/m³ | R$ {resultado['custo_estimado']:.2f} |\n"
                f"| Consumo Cimento | {resultado['consumo_cimento_m3']} kg/m³ |\n\n"
                f"_Clique em 'Gerar Traço' com novos parâmetros para comparar._"
            )
            st.session_state.ai_chat_history.append(
                {"role": "assistant", "content": ai_response}
            )

        # Guardar último resultado
        st.session_state["ultimo_traco_ai"] = resultado

    # ── Botão Salvar Traço no Banco ──────────────────────────
    if st.session_state.get("ultimo_traco_ai") and config.DATABASE_ENABLED:
        st.markdown("---")
        res = st.session_state["ultimo_traco_ai"]
        st.info(
            f"📌 Último traço gerado: **{res['traco_sugerido']}** "
            f"(FCK {res['fck_alvo']} MPa)"
        )
        from datetime import datetime
        ts = datetime.now().strftime("%H%M%S")
        if aplicacao.strip():
            nome_default = f"{aplicacao.strip()} — {ts}"
        else:
            nome_default = f"IA — FCK {res['fck_alvo']:.0f} ({res['agregado_max']}) — {ts}"
        nome_traco = st.text_input(
            "📝 Nome para o traço",
            value=nome_default,
            help="Dê um nome descritivo para identificar este traço no banco.",
        )
        if st.button(
            "💾 Salvar no Banco de Traços",
            type="primary",
            width="stretch",
        ):
            try:
                traco_data = {
                    "nome": nome_traco,
                    "fck_alvo": float(res["fck_alvo"]),
                    "traco_str": res["traco_sugerido"],
                    "consumo_cimento_m3": float(res["consumo_cimento_m3"]),
                }
                with UnitOfWork() as uow:
                    uow.fabrica.save_traco(traco_data)
                st.success(
                    f"✅ Traço **{nome_traco}** salvo com sucesso! "
                    f"Agora ele está disponível em **Novo Pedido** e **Banco de Traços**."
                )
                st.balloons()
            except Exception as e:
                st.error(f"❌ Erro ao salvar traço: {e}")
