import logging
from typing import List
from persistencia.unit_of_work import UnitOfWork
log = logging.getLogger(__name__)

def get_allowed_roles_for_page(page_filename: str) -> List[str]:
    log.info(f'Serviço Gerenciador: Verificando permissões para: {page_filename}')
    try:
        with UnitOfWork() as uow:
            df = uow.paginas.get_allowed_roles_for_page(page_filename)
        if df.empty:
            return ['Administrador Global']
        role_list = df['nome_perfil'].tolist()
        if 'Administrador Global' not in role_list:
            role_list.append('Administrador Global')
        return role_list
    except Exception as e:
        log.error(f"Erro ao buscar perfis para página '{page_filename}': {e}", exc_info=True)
        return ['Administrador Global']