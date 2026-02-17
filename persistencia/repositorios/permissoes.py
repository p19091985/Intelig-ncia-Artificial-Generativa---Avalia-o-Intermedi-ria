import pandas as pd
from .base import BaseRepository

class PermissaoRepository(BaseRepository):

    def get_all_pages(self):
        return self._execute_query_to_dataframe('SELECT * FROM pagina ORDER BY pagina_id')

    def get_all_profiles(self):
        return self._execute_query_to_dataframe("SELECT * FROM perfil_acesso WHERE nome_perfil != 'Administrador Global' ORDER BY nome_perfil")

    def get_permissions_map(self):
        df = self._execute_query_to_dataframe('SELECT * FROM perfil_pagina_permissao')
        if df.empty:
            return {}
        return df.groupby('pagina_id')['perfil_id'].apply(list).to_dict()

    def salvar_matriz_permissoes(self, df_permissoes: pd.DataFrame):
        self._execute_raw_sql('DELETE FROM perfil_pagina_permissao WHERE perfil_id != 1')
        if not df_permissoes.empty:
            self._write_dataframe_to_table(df_permissoes, 'perfil_pagina_permissao')