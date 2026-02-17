
import sys
import os
import streamlit as st
import config
from persistencia import auth, database, logger
from persistencia.unit_of_work import UnitOfWork
from sqlalchemy import text
import logging

def validar_configuracoes():

    if config.INITIALIZE_DATABASE_ON_STARTUP and (not config.DATABASE_ENABLED):
        st.set_page_config(page_title='Erro de Configuração', layout='centered')
        st.title('❌ Erro de Configuração Inválida')
        st.error('A aplicação não pode iniciar devido a uma configuração inconsistente.')
        st.warning('\n            **Problema Detectado:**\n            - `INITIALIZE_DATABASE_ON_STARTUP` está definido como `True`.\n            - `DATABASE_ENABLED` está definido como `False`.\n\n            **Motivo:** O sistema não pode criar as tabelas do banco de dados (schema)\n            se o acesso ao banco de dados como um todo está desativado.\n            ')
        st.info('**Solução:** Altere seu arquivo `config.py` para uma das opções abaixo e reinicie o servidor:\n1. Habilite o banco de dados: `DATABASE_ENABLED = True`\n2. Desabilite a inicialização automática: `INITIALIZE_DATABASE_ON_STARTUP = False`')
        st.stop()
validar_configuracoes()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
st.set_page_config(page_title='Pré-Moldados Garantia Eterna', layout='wide')
if 'logger_setup' not in st.session_state:
    logger.setup_loggers()
    st.session_state.logger_setup = True
if 'db_initialized' not in st.session_state and config.DATABASE_ENABLED:
    if config.INITIALIZE_DATABASE_ON_STARTUP:
        try:
            database.DatabaseManager.initialize_database()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f'Falha crítica na inicialização do banco de dados: {e}')
            st.stop()
    else:
        st.session_state.db_initialized = True
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0

@st.dialog('Autenticação Necessária', dismissible=False)
def login_dialog():
    st.markdown('### Por favor, faça o login para continuar')
    if st.session_state.login_attempts >= config.MAX_LOGIN_ATTEMPTS:
        st.error('Acesso bloqueado. Número máximo de tentativas de login excedido.')
        if st.button('OK'):
            st.stop()
        return
    show_password = st.checkbox('Mostrar senha', key='show_password_dialog')
    password_type = 'default' if show_password else 'password'
    with st.form('login_form_dialog'):
        username = st.text_input('Usuário', key='username_input_dialog')
        password = st.text_input('Senha', type=password_type, key='password_input_dialog')
        submitted = st.form_submit_button('Entrar', type='primary')
        if submitted:
            if not config.DATABASE_ENABLED:
                st.error('O sistema de login está desabilitado pois o banco de dados não está ativo.')
                return
            user_data = auth.verify_user_credentials(username, password)
            if user_data == 'connection_error':
                st.error('Falha na conexão com o banco de dados.')
            elif user_data:
                st.session_state.user_info = user_data
                st.session_state.login_attempts = 0
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error('Usuário ou senha inválidos.')
                remaining = config.MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
                if remaining > 0:
                    st.warning(f'Você tem {remaining} tentativa(s) restante(s).')
                else:
                    st.error('Acesso bloqueado!')

def get_allowed_pages_for_user(profile_name: str) -> list:
    try:
        with UnitOfWork() as uow:
            df = uow.paginas.get_allowed_pages_for_profile(profile_name)
    except Exception as e:
        logging.error(f'Erro ao carregar páginas permitidas: {e}')
        return []
    page_list = []
    is_first_page = True
    for _, row in df.iterrows():
        try:
            filename = row['nome_arquivo']
            friendly_name = row['nome_amigavel']
            parts = filename.split('_')
            icon = parts[1] if len(parts) > 1 else '📄'
            page_list.append(st.Page(f'app_pages/{filename}', title=friendly_name, icon=icon, default=is_first_page))
            is_first_page = False
        except Exception as e:
            logging.error(f'Erro ao processar página {filename}: {e}')
    return page_list
if st.session_state.user_info is None:
    st.title(config.APP_TITLE)
    st.header(config.APP_HEADER)
    st.markdown('---')
    st.info('Aguardando autenticação do usuário...')
    login_dialog()
else:
    user_profile = st.session_state.user_info['access_level']
    allowed_pages = get_allowed_pages_for_user(user_profile)
    if not allowed_pages:
        st.error('Erro: Seu perfil não tem permissão para ver nenhuma página.')
        st.stop()
    navigation = st.navigation(allowed_pages)
    navigation.run()