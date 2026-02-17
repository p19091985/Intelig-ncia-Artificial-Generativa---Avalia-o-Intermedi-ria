
import streamlit as st
import logging
import config
log = logging.getLogger(__name__)

def st_check_session():
    log.debug('Executando st_check_session()...')
    if 'user_info' not in st.session_state or st.session_state.user_info is None:
        log.warning(f"Falha na verificação de sessão: 'user_info' não encontrado.")
        log.debug('Chamando st.rerun() para forçar recarregamento e exibir login...')
        st.warning('Acesso negado. Por favor, faça o login.')
        st.rerun()
        st.stop()
    log.debug(f'Sessão válida encontrada para: {st.session_state.user_info.get('name', 'N/A')}')
    log.debug(f'Sessão válida encontrada para: {st.session_state.user_info.get("name", "N/A")}')
    st.sidebar.title('Painel de Controle')
    st.sidebar.markdown(f'**Usuário:** `{st.session_state.user_info["name"]}`')
    st.sidebar.markdown(f'**Perfil:** `{st.session_state.user_info["access_level"]}`')
    if st.sidebar.button('🚪 Sair', width='stretch', type='primary'):
        username = st.session_state.user_info.get('username', 'desconhecido')
        log.info(f"Botão 'Sair' clicado. Iniciando logout do usuário: '{username}'.")
        keys_to_clear = list(st.session_state.keys())
        log.debug(f'Limpando {len(keys_to_clear)} chaves da sessão: {keys_to_clear}')
        for key in keys_to_clear:
            del st.session_state[key]
        log.info('Sessão limpa.')
        log.debug('Chamando st.rerun() para recarregar Home.py e mostrar login...')
        st.rerun()
        st.stop()

def check_access(allowed_roles: list):
    log.debug(f'Executando check_access(). Perfis permitidos para esta página: {allowed_roles}')
    if not allowed_roles:
        log.debug("Acesso permitido: 'allowed_roles' está vazia (página pública para logados).")
        return True
    try:
        user_access_level = st.session_state.user_info.get('access_level')
        log.debug(f"Perfil do usuário atual (da sessão): '{user_access_level}'.")
        if user_access_level not in allowed_roles:
            log.warning(f"ACESSO NEGADO. Usuário '{st.session_state.user_info.get('username')}' (Perfil: '{user_access_level}') não está na lista de perfis permitidos: {allowed_roles}.")
            st.error('Você não tem permissão para acessar esta página.')
            st.image('https://http.cat/401', use_container_width=True)
            st.stop()
        log.debug(f"Acesso PERMITIDO. Perfil '{user_access_level}' está na lista.")
        return True
    except AttributeError:
        log.error(f'Falha em check_access: st.session_state.user_info não é um dicionário ou é None. {st.session_state.user_info}')
        st.error("Erro na verificação de permissão. 'user_info' inválido.")
        st.stop()
    except Exception as e:
        log.error(f'Erro inesperado em check_access: {e}', exc_info=True)
        st.error(f'Erro inesperado na verificação de permissão: {e}')
        st.stop()