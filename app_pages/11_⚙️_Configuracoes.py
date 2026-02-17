"""
11_⚙️_Configuracoes.py — Painel Administrativo Unificado
Unifica: Gestão de Usuários, Permissões, Páginas e Tema.
"""
import streamlit as st
import pandas as pd
import numpy as np
import toml
import config
import logging
import time
from pathlib import Path
from persistencia.auth import hash_password
from persistencia.unit_of_work import UnitOfWork
from utils.st_utils import st_check_session, check_access
from components import servicos_gerenciador as servico

st.set_page_config(page_title="Configurações do Sistema", layout="wide", page_icon="⚙️")
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
    st.warning("Banco de dados desabilitado.")
    st.stop()

# ── Session State ────────────────────────────────────────────
for key, default in {
    "user_show_form": False, "user_editing": None,
    "perfil_show_form": False, "perfil_editing": None,
    "pag_show_form": False, "pag_editing": None,
    "feedback_msg": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def mostrar_feedback():
    if st.session_state.feedback_msg:
        fb = st.session_state.feedback_msg
        {"sucesso": st.success, "erro": st.error, "aviso": st.warning}.get(
            fb["tipo"], st.info
        )(fb["texto"])

# ── Título ───────────────────────────────────────────────────
st.title("⚙️ Configurações do Sistema")

tab_users, tab_perms, tab_pages, tab_theme = st.tabs([
    "👤 Usuários", "🔒 Permissões", "📄 Páginas", "🎨 Tema"
])

# ═══════════════════════════════════════════════════════════════
# ABA 1: GESTÃO DE USUÁRIOS
# ═══════════════════════════════════════════════════════════════
with tab_users:
    from streamlit_option_menu import option_menu
    selected_sub = option_menu(
        None, options=["Gerenciar Usuários", "Gerenciar Perfis de Acesso"],
        icons=["person-fill-gear", "shield-lock-fill"], orientation="horizontal"
    )

    if selected_sub == "Gerenciar Usuários":
        c1, c2 = st.columns([4, 1])
        c1.caption("Clique em uma linha para editar.")
        if c2.button("➕ Novo Usuário", width="stretch"):
            st.session_state.user_show_form = True
            st.session_state.user_editing = None
            st.session_state.feedback_msg = None
            st.rerun()

        with UnitOfWork() as uow:
            df_users = uow.usuarios.get_all_users_detailed()
            df_perfis_ref = uow.usuarios.get_all_perfis()
        perfis_map = dict(zip(df_perfis_ref["perfil_id"], df_perfis_ref["nome_perfil"]))

        if st.session_state.user_show_form:
            item = st.session_state.user_editing
            with st.container(border=True):
                st.markdown(f"### 📝 {'Editar' if item else 'Novo'} Usuário")
                mostrar_feedback()
                with st.form("form_user"):
                    c_a, c_b = st.columns(2)
                    login = c_a.text_input("Login", value=item["login_usuario"] if item else "")
                    nome = c_b.text_input("Nome", value=item["nome_completo"] if item else "")
                    c_c, c_d = st.columns(2)
                    idx_perfil = 0
                    if item and item["perfil_id"] in perfis_map:
                        try:
                            idx_perfil = list(perfis_map.keys()).index(item["perfil_id"])
                        except ValueError:
                            idx_perfil = 0
                    perfil_id = c_c.selectbox("Perfil", options=list(perfis_map.keys()),
                                              format_func=lambda x: perfis_map[x], index=idx_perfil)
                    senha = c_d.text_input("Senha", type="password",
                                           placeholder="Vazio para manter atual" if item else "Obrigatória")
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                        try:
                            data = {"login_usuario": login, "nome_completo": nome, "perfil_id": perfil_id}
                            if senha:
                                data["senha_criptografada"] = hash_password(senha)
                            elif not item:
                                st.session_state.feedback_msg = {"tipo": "erro", "texto": "Senha obrigatória."}
                                st.rerun()
                            with UnitOfWork() as uow:
                                uow.usuarios.salvar_usuario(data, item["usuario_id"] if item else None)
                            st.toast("Usuário salvo!", icon="✅")
                            st.session_state.user_show_form = False
                            st.session_state.feedback_msg = None
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            msg = "Login já existe." if "unique" in str(e).lower() else f"Erro: {e}"
                            st.session_state.feedback_msg = {"tipo": "erro", "texto": msg}
                            st.rerun()
                    if item and b2.form_submit_button("🗑️ Excluir", type="secondary", width="stretch"):
                        try:
                            with UnitOfWork() as uow:
                                uow.usuarios.excluir_usuario(item["usuario_id"])
                            st.toast("Excluído!", icon="🗑️")
                            st.session_state.user_show_form = False
                            st.session_state.feedback_msg = None
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            erro = str(e).lower()
                            if any(k in erro for k in ["constraint", "foreign key"]):
                                st.session_state.feedback_msg = {"tipo": "aviso", "texto": "Registros vinculados."}
                            else:
                                st.session_state.feedback_msg = {"tipo": "erro", "texto": f"Erro: {e}"}
                            st.rerun()
                    elif not item and b2.form_submit_button("Cancelar"):
                        st.session_state.user_show_form = False
                        st.session_state.feedback_msg = None
                        st.rerun()

        event = st.dataframe(df_users, width="stretch", hide_index=True,
                             on_select="rerun", selection_mode="single-row",
                             column_config={"usuario_id": None, "perfil_id": None,
                                            "login_usuario": "Login", "nome_completo": "Nome",
                                            "nome_perfil": "Perfil"})
        if event.selection.rows:
            idx = event.selection.rows[0]
            row = df_users.iloc[idx].to_dict()
            cur = st.session_state.user_editing
            if not cur or cur.get("usuario_id") != row["usuario_id"]:
                st.session_state.user_editing = row
                st.session_state.user_show_form = True
                st.session_state.feedback_msg = None
                st.rerun()

    elif selected_sub == "Gerenciar Perfis de Acesso":
        c1, c2 = st.columns([4, 1])
        c1.caption("Gestão de Perfis")
        if c2.button("➕ Novo Perfil", width="stretch"):
            st.session_state.perfil_show_form = True
            st.session_state.perfil_editing = None
            st.session_state.feedback_msg = None
            st.rerun()
        with UnitOfWork() as uow:
            df_perfis = uow.usuarios.get_all_perfis()
        if st.session_state.perfil_show_form:
            item = st.session_state.perfil_editing
            with st.container(border=True):
                mostrar_feedback()
                with st.form("form_perfil"):
                    nome_perfil = st.text_input("Nome do Perfil", value=item["nome_perfil"] if item else "")
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                        try:
                            with UnitOfWork() as uow:
                                uow.usuarios.salvar_perfil({"nome_perfil": nome_perfil},
                                                           item["perfil_id"] if item else None)
                            st.toast("Perfil salvo!", icon="✅")
                            st.session_state.perfil_show_form = False
                            st.session_state.feedback_msg = None
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            st.session_state.feedback_msg = {"tipo": "erro", "texto": f"Erro: {e}"}
                            st.rerun()
                    if item and b2.form_submit_button("🗑️ Excluir", type="secondary", width="stretch"):
                        try:
                            with UnitOfWork() as uow:
                                uow.usuarios.excluir_perfil(item["perfil_id"])
                            st.toast("Excluído!", icon="🗑️")
                            st.session_state.perfil_show_form = False
                            st.session_state.feedback_msg = None
                            time.sleep(0.8)
                            st.rerun()
                        except Exception as e:
                            erro = str(e).lower()
                            if any(k in erro for k in ["constraint", "foreign key"]):
                                st.session_state.feedback_msg = {"tipo": "aviso", "texto": "Usuários vinculados."}
                            else:
                                st.session_state.feedback_msg = {"tipo": "erro", "texto": f"Erro: {e}"}
                            st.rerun()
                    elif not item and b2.form_submit_button("Cancelar"):
                        st.session_state.perfil_show_form = False
                        st.session_state.feedback_msg = None
                        st.rerun()
        event = st.dataframe(df_perfis, width="stretch", hide_index=True,
                             on_select="rerun", selection_mode="single-row",
                             column_config={"perfil_id": None})
        if event.selection.rows:
            idx = event.selection.rows[0]
            row = df_perfis.iloc[idx].to_dict()
            cur = st.session_state.perfil_editing
            if not cur or cur.get("perfil_id") != row["perfil_id"]:
                st.session_state.perfil_editing = row
                st.session_state.perfil_show_form = True
                st.session_state.feedback_msg = None
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# ABA 2: PERMISSÕES
# ═══════════════════════════════════════════════════════════════
with tab_perms:
    def load_perm_data():
        with UnitOfWork() as uow:
            df_p = uow.permissoes.get_all_pages()
            df_pr = uow.permissoes.get_all_profiles()
            mapa = uow.permissoes.get_permissions_map()
        return df_p, df_pr, mapa

    def build_matrix(df_pag, df_perf, mapa):
        m = df_pag[["pagina_id", "nome_amigavel"]].copy()
        m = m.rename(columns={"nome_amigavel": "Página"})
        for _, p in df_perf.iterrows():
            m[p["nome_perfil"]] = m["pagina_id"].apply(lambda pid: p["perfil_id"] in mapa.get(pid, []))
        return m

    df_pags, df_perfs, mapa_perms = load_perm_data()
    if df_pags.empty:
        st.error("Tabela de páginas vazia.")
    else:
        matrix = build_matrix(df_pags, df_perfs, mapa_perms)
        st.info("O perfil **Administrador Global** sempre tem acesso a tudo.", icon="ℹ️")
        with st.form("matrix_form"):
            st.markdown("Marque as caixas para conceder permissão.")
            col_cfg = {"pagina_id": None, "Página": st.column_config.TextColumn(label="Página", disabled=True, width="large")}
            for pn in df_perfs["nome_perfil"]:
                col_cfg[pn] = st.column_config.CheckboxColumn(label=pn, width="medium")
            edited = st.data_editor(matrix, column_config=col_cfg, hide_index=True, key="perm_matrix")
            if st.form_submit_button("💾 Salvar Todas as Alterações", type="primary", width="stretch"):
                try:
                    lookup = dict(zip(df_perfs["nome_perfil"], df_perfs["perfil_id"]))
                    id_vars = ["pagina_id", "Página"]
                    val_vars = [c for c in edited.columns if c not in id_vars]
                    melted = edited.melt(id_vars=id_vars, value_vars=val_vars, var_name="nome_perfil", value_name="tem")
                    granted = melted[melted["tem"] == True].copy()
                    granted["perfil_id"] = granted["nome_perfil"].map(lookup)
                    final = granted[["pagina_id", "perfil_id"]].dropna().astype(int)
                    with UnitOfWork() as uow:
                        uow.permissoes.salvar_matriz_permissoes(final)
                    st.balloons()
                    st.toast("Permissões salvas!", icon="✅")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    log.error(f"Erro permissões: {e}")
                    st.error(f"Erro: {e}")

# ═══════════════════════════════════════════════════════════════
# ABA 3: PÁGINAS
# ═══════════════════════════════════════════════════════════════
with tab_pages:
    st.markdown("Cadastre os arquivos `.py` que compõem o sistema.")
    c1, c2 = st.columns([4, 1])
    c1.subheader("Lista de Páginas Cadastradas")
    if c2.button("➕ Nova Página", width="stretch"):
        st.session_state.pag_show_form = True
        st.session_state.pag_editing = None
        st.rerun()
    with UnitOfWork() as uow:
        df_pag_list = uow.paginas.get_all_paginas()
    if st.session_state.pag_show_form:
        item = st.session_state.pag_editing
        with st.container(border=True):
            st.markdown(f"### 📝 {'Editar' if item else 'Nova'} Página")
            with st.form("form_pag"):
                ca, cb = st.columns(2)
                nome_arq = ca.text_input("Nome do Arquivo", value=item["nome_arquivo"] if item else "")
                nome_ami = cb.text_input("Nome Amigável", value=item["nome_amigavel"] if item else "")
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 Salvar", type="primary", width="stretch"):
                    if not nome_arq or not nome_ami:
                        st.error("Todos os campos são obrigatórios.")
                    else:
                        try:
                            with UnitOfWork() as uow:
                                uow.paginas.salvar_pagina(
                                    {"nome_arquivo": nome_arq, "nome_amigavel": nome_ami},
                                    item["pagina_id"] if item else None
                                )
                            st.toast("Salvo!", icon="✅")
                            st.session_state.pag_show_form = False
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE" in str(e).upper():
                                st.error("Página já cadastrada.")
                            else:
                                st.error(f"Erro: {e}")
                if item:
                    if b2.form_submit_button("🗑️ Excluir", type="secondary", width="stretch"):
                        try:
                            with UnitOfWork() as uow:
                                uow.paginas.excluir_pagina(item["pagina_id"])
                            st.toast("Excluído!", icon="🗑️")
                            st.session_state.pag_show_form = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro (permissões vinculadas?): {e}")
                elif b2.form_submit_button("Cancelar", width="stretch"):
                    st.session_state.pag_show_form = False
                    st.rerun()
    if df_pag_list.empty:
        st.info("Nenhuma página cadastrada.")
    else:
        ev = st.dataframe(df_pag_list, width="stretch", hide_index=True,
                          on_select="rerun", selection_mode="single-row",
                          column_config={"pagina_id": st.column_config.NumberColumn("ID", width="small"),
                                         "nome_arquivo": "Arquivo", "nome_amigavel": "Nome no Menu"},
                          column_order=["pagina_id", "nome_amigavel", "nome_arquivo"])
        if ev.selection.rows:
            row = df_pag_list.iloc[ev.selection.rows[0]].to_dict()
            if not st.session_state.pag_show_form or st.session_state.pag_editing != row:
                st.session_state.pag_editing = row
                st.session_state.pag_show_form = True
                st.rerun()

# ═══════════════════════════════════════════════════════════════
# ABA 4: TEMA
# ═══════════════════════════════════════════════════════════════
with tab_theme:
    CONFIG_PATH = Path(".streamlit/config.toml")
    PRESET_THEMES = {
        "☀️ Claros": {
            "Padrão Streamlit": {"primaryColor": "#FF4B4B", "backgroundColor": "#FFFFFF", "secondaryBackgroundColor": "#F0F2F6", "textColor": "#31333F", "font": "sans serif"},
            "Menta Suave": {"primaryColor": "#1FAB89", "backgroundColor": "#D7FBE8", "secondaryBackgroundColor": "#9DF3C4", "textColor": "#042F1A", "font": "sans serif"},
            "Areia e Céu": {"primaryColor": "#3C8DAD", "backgroundColor": "#F0EBE3", "secondaryBackgroundColor": "#D4C7B0", "textColor": "#1E3C4A", "font": "sans serif"},
        },
        "🌙 Escuros": {
            "Drácula": {"primaryColor": "#bd93f9", "backgroundColor": "#282a36", "secondaryBackgroundColor": "#44475a", "textColor": "#f8f8f2", "font": "sans serif"},
            "Nord": {"primaryColor": "#88C0D0", "backgroundColor": "#2E3440", "secondaryBackgroundColor": "#3B4252", "textColor": "#ECEFF4", "font": "sans serif"},
            "One Dark Pro": {"primaryColor": "#61AFEF", "backgroundColor": "#282C34", "secondaryBackgroundColor": "#31353F", "textColor": "#ABB2BF", "font": "monospace"},
            "Café Expresso": {"primaryColor": "#A1887F", "backgroundColor": "#211F1F", "secondaryBackgroundColor": "#3E2723", "textColor": "#D7CCC8", "font": "serif"},
        },
        "💼 Corporativos": {
            "Azul Executivo": {"primaryColor": "#005A9E", "backgroundColor": "#F5F5F5", "secondaryBackgroundColor": "#E1EBF5", "textColor": "#212121", "font": "sans serif"},
            "Verde Confiança": {"primaryColor": "#007A5E", "backgroundColor": "#F7F9F9", "secondaryBackgroundColor": "#E6F2F0", "textColor": "#1D1C1D", "font": "sans serif"},
            "Ouro e Petróleo": {"primaryColor": "#B8860B", "backgroundColor": "#121212", "secondaryBackgroundColor": "#282828", "textColor": "#E5E5E5", "font": "serif"},
        },
    }

    def load_theme():
        if not CONFIG_PATH.is_file():
            return PRESET_THEMES["☀️ Claros"]["Padrão Streamlit"]
        try:
            return toml.load(CONFIG_PATH).get("theme", PRESET_THEMES["☀️ Claros"]["Padrão Streamlit"])
        except Exception:
            return PRESET_THEMES["☀️ Claros"]["Padrão Streamlit"]

    def save_theme(settings):
        try:
            CONFIG_PATH.parent.mkdir(exist_ok=True)
            full = toml.load(CONFIG_PATH) if CONFIG_PATH.is_file() else {}
            full["theme"] = settings
            with open(CONFIG_PATH, "w") as f:
                toml.dump(full, f)
            st.toast("Tema salvo!", icon="✅")
            st.success("Recarregue a página (pressione 'R') para aplicar.")
            st.balloons()
        except Exception as e:
            st.error(f"Erro: {e}")

    if "current_theme" not in st.session_state:
        st.session_state.current_theme = load_theme()

    def update_tv(tk, wk):
        if wk in st.session_state:
            st.session_state.current_theme[tk] = st.session_state[wk]

    cols = st.columns([1, 1.4])
    with cols[0]:
        st.subheader("🎨 Galeria de Temas")
        cat = st.selectbox("Categoria", options=PRESET_THEMES.keys())
        tn = st.selectbox("Tema", options=PRESET_THEMES[cat].keys())
        if st.button("Aplicar Tema", width="stretch"):
            st.session_state.current_theme = PRESET_THEMES[cat][tn].copy()
            st.rerun()

        st.subheader("Ajuste Fino")
        st.color_picker("Cor Primária", value=st.session_state.current_theme.get("primaryColor", "#FF4B4B"),
                         key="pk_pc", on_change=update_tv, kwargs={"tk": "primaryColor", "wk": "pk_pc"})
        st.color_picker("Fundo", value=st.session_state.current_theme.get("backgroundColor", "#FFFFFF"),
                         key="pk_bg", on_change=update_tv, kwargs={"tk": "backgroundColor", "wk": "pk_bg"})
        st.color_picker("Fundo 2º", value=st.session_state.current_theme.get("secondaryBackgroundColor", "#F0F2F6"),
                         key="pk_sb", on_change=update_tv, kwargs={"tk": "secondaryBackgroundColor", "wk": "pk_sb"})
        st.color_picker("Texto", value=st.session_state.current_theme.get("textColor", "#31333F"),
                         key="pk_tc", on_change=update_tv, kwargs={"tk": "textColor", "wk": "pk_tc"})

        st.divider()
        ac = st.columns(2)
        if ac[0].button("💾 Salvar Tema", type="primary", width="stretch"):
            save_theme(st.session_state.current_theme)
        if ac[1].button("🗑️ Restaurar Padrão", width="stretch"):
            try:
                if CONFIG_PATH.is_file():
                    full = toml.load(CONFIG_PATH)
                    if "theme" in full:
                        del full["theme"]
                        with open(CONFIG_PATH, "w") as f:
                            toml.dump(full, f)
                        st.toast("Padrão restaurado!", icon="✅")
            except Exception as e:
                st.error(f"Erro: {e}")

    with cols[1]:
        st.subheader("👁️ Pré-visualização")
        t = st.session_state.current_theme
        css = f"""<style>.pv{{border:2px solid {t.get('secondaryBackgroundColor','#F0F2F6')};
        background:{t.get('backgroundColor','#FFF')};color:{t.get('textColor','#333')};
        border-radius:0.75rem;padding:20px}}.pv *,.pv h3,.pv p{{color:{t.get('textColor','#333')}!important}}</style>"""
        st.markdown(css, unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="pv">', unsafe_allow_html=True)
            st.info("Mensagem de informação")
            st.success("Operação concluída")
            chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["A", "B", "C"])
            st.line_chart(chart_data)
            st.progress(75, text="Progresso")
            st.slider("Slider", 0, 100, 50)
            st.markdown("</div>", unsafe_allow_html=True)
