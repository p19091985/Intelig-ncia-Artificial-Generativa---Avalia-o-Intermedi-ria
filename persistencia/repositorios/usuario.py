from typing import Optional
from .base import BaseRepository

class UsuarioRepository(BaseRepository):

    def get_user_id_by_login(self, login: str) -> Optional[int]:
        query = 'SELECT usuario_id FROM usuarios WHERE login_usuario = :login LIMIT 1'
        return self._execute_scalar(query, {'login': login})

    def get_all_users_detailed(self):
        query = '\n            SELECT u.usuario_id, u.login_usuario, u.nome_completo, p.nome_perfil, u.perfil_id\n            FROM usuarios u\n            LEFT JOIN perfil_acesso p ON u.perfil_id = p.perfil_id\n            ORDER BY u.nome_completo\n        '
        return self._execute_query_to_dataframe(query)

    def get_all_perfis(self):
        return self._execute_query_to_dataframe('SELECT * FROM perfil_acesso ORDER BY nome_perfil')

    def salvar_usuario(self, data: dict, user_id: int=None):
        if user_id:
            fields = ', '.join([f'{k}=:{k}' for k in data.keys()])
            data['id'] = user_id
            self._execute_raw_sql(f'UPDATE usuarios SET {fields} WHERE usuario_id=:id', data)
        else:
            cols = ', '.join(data.keys())
            params = ', '.join([f':{k}' for k in data.keys()])
            self._execute_raw_sql(f'INSERT INTO usuarios ({cols}) VALUES ({params})', data)

    def excluir_usuario(self, user_id: int):
        self._execute_raw_sql('DELETE FROM usuarios WHERE usuario_id=:id', {'id': user_id})

    def salvar_perfil(self, data: dict, perfil_id: int=None):
        if perfil_id:
            self._execute_raw_sql('UPDATE perfil_acesso SET nome_perfil=:nome WHERE perfil_id=:id', {'nome': data['nome_perfil'], 'id': perfil_id})
        else:
            self._execute_raw_sql('INSERT INTO perfil_acesso (nome_perfil) VALUES (:nome)', {'nome': data['nome_perfil']})

    def excluir_perfil(self, perfil_id: int):
        self._execute_raw_sql('DELETE FROM perfil_acesso WHERE perfil_id=:id', {'id': perfil_id})