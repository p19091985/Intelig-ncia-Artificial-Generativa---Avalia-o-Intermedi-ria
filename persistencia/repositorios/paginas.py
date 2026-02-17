from typing import List
import pandas as pd
from .base import BaseRepository

class PaginaRepository(BaseRepository):

    def get_all_paginas(self) -> pd.DataFrame:
        query = 'SELECT * FROM pagina ORDER BY nome_amigavel'
        return self._execute_query_to_dataframe(query)

    def salvar_pagina(self, data: dict, pagina_id: int=None):
        if pagina_id:
            self._execute_raw_sql('UPDATE pagina SET nome_arquivo=:arq, nome_amigavel=:nome WHERE pagina_id=:id', {'arq': data['nome_arquivo'], 'nome': data['nome_amigavel'], 'id': pagina_id})
        else:
            self._execute_raw_sql('INSERT INTO pagina (nome_arquivo, nome_amigavel) VALUES (:arq, :nome)', {'arq': data['nome_arquivo'], 'nome': data['nome_amigavel']})

    def excluir_pagina(self, pagina_id: int):
        self._execute_raw_sql('DELETE FROM pagina WHERE pagina_id=:id', {'id': pagina_id})

    def get_allowed_pages_for_profile(self, profile_name: str) -> pd.DataFrame:
        if profile_name == 'Administrador Global':
            query = 'SELECT nome_arquivo, nome_amigavel FROM pagina ORDER BY nome_arquivo'
            return self._execute_query_to_dataframe(query)
        else:
            query = '\n                SELECT p.nome_arquivo, p.nome_amigavel\n                FROM pagina p\n                JOIN perfil_pagina_permissao ppp ON p.pagina_id = ppp.pagina_id\n                JOIN perfil_acesso pa ON ppp.perfil_id = pa.perfil_id\n                WHERE pa.nome_perfil = :profile_name\n                ORDER BY p.nome_arquivo\n            '
            return self._execute_query_to_dataframe(query, params={'profile_name': profile_name})

    def get_allowed_roles_for_page(self, filename: str) -> pd.DataFrame:
        query = '\n            SELECT pa.nome_perfil\n            FROM perfil_pagina_permissao ppp\n            JOIN pagina p ON ppp.pagina_id = p.pagina_id\n            JOIN perfil_acesso pa ON ppp.perfil_id = pa.perfil_id\n            WHERE p.nome_arquivo = :filename\n        '
        return self._execute_query_to_dataframe(query, params={'filename': filename})