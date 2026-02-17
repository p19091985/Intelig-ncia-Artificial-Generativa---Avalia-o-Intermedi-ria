import pandas as pd
from sqlalchemy import text, exc, Connection
import logging
import config
from typing import Optional, Any
log = logging.getLogger(__name__)

class BaseRepository:

    def __init__(self, connection: Connection):
        if connection is None:
            raise ValueError('A conexão não pode ser nula para o repositório.')
        self.conn = connection

    def _execute_query_to_dataframe(self, query: str, params: dict=None) -> pd.DataFrame:
        if not config.DATABASE_ENABLED:
            return pd.DataFrame()
        try:
            safe_params = params if params else {}
            df = pd.read_sql_query(text(query), self.conn, params=safe_params)
            df.columns = [str(col).lower() for col in df.columns]
            return df
        except exc.SQLAlchemyError as e:
            log.error(f'Erro query DF: {e}')
            raise

    def _execute_raw_sql(self, query: str, params: dict=None) -> Optional[int]:
        if not config.DATABASE_ENABLED:
            return None
        try:
            sql_query = text(query) if isinstance(query, str) else query
            result = self.conn.execute(sql_query, params)
            return result.rowcount
        except exc.SQLAlchemyError as e:
            log.error(f'Erro SQL Raw: {e}')
            raise

    def _execute_scalar(self, query: str, params: dict=None) -> Any:
        if not config.DATABASE_ENABLED:
            return None
        try:
            sql_query = text(query) if isinstance(query, str) else query
            result = self.conn.execute(sql_query, params)
            return result.scalar()
        except exc.SQLAlchemyError as e:
            log.error(f'Erro Scalar: {e}')
            raise

    def _write_dataframe_to_table(self, df: pd.DataFrame, table_name: str):
        if not config.DATABASE_ENABLED:
            return
        try:
            df_to_write = df.copy()
            df_to_write.columns = [str(col).lower() for col in df_to_write.columns]
            df_to_write.to_sql(table_name, con=self.conn, if_exists='append', index=False)
        except exc.SQLAlchemyError as e:
            log.error(f"Erro ao escrever na tabela '{table_name}'. Erro: {e}")
            raise

    def _update_table(self, table_name: str, update_values: dict, where_conditions: dict):
        if not config.DATABASE_ENABLED:
            return
        try:
            
            
            set_clauses = []
            params = {}
            
            for key, val in update_values.items():
                param_name = f"val_{key}"
                set_clauses.append(f"{key} = :{param_name}")
                params[param_name] = val
                
            where_clauses = []
            for key, val in where_conditions.items():
                param_name = f"wh_{key}"
                where_clauses.append(f"{key} = :{param_name}")
                params[param_name] = val
                
            set_str = ", ".join(set_clauses)
            where_str = " AND ".join(where_clauses)
            
            query = f"UPDATE {table_name} SET {set_str} WHERE {where_str}"
            self._execute_raw_sql(query, params)
        except Exception as e:
            log.error(f'Erro Update Table {table_name}: {e}')
            raise

    def _delete_from_table(self, table_name: str, where_conditions: dict):
        if not config.DATABASE_ENABLED:
            return
        try:
            where_clauses = []
            params = {}
            for key, val in where_conditions.items():
                where_clauses.append(f"{key} = :{key}")
                params[key] = val
            
            where_str = " AND ".join(where_clauses)
            query = f"DELETE FROM {table_name} WHERE {where_str}"
            self._execute_raw_sql(query, params)
        except Exception as e:
            log.error(f'Erro Delete Table {table_name}: {e}')
            raise