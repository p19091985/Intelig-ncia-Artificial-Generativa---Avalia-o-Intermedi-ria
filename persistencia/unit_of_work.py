
import logging
from sqlalchemy.engine import Engine
from persistencia.database import DatabaseManager
from streamlit.runtime.scriptrunner.script_runner import StopException
from persistencia.repositorios import UsuarioRepository, PermissaoRepository, PaginaRepository

from persistencia.repositorios.fabrica_repo import FabricaRepository
log = logging.getLogger(__name__)

class SimulationRollback(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(message)

class UnitOfWork:

    def __enter__(self):
        try:
            self.engine: Engine = DatabaseManager.get_engine()
            if self.engine is None:
                raise ConnectionError('A engine do banco de dados não está disponível.')
            self.connection = self.engine.connect()
            self.transaction = self.connection.begin()
            log.debug('UoW: Transação iniciada.')
            self.usuarios = UsuarioRepository(self.connection)
            self.permissoes = PermissaoRepository(self.connection)
            self.paginas = PaginaRepository(self.connection)

            self.fabrica = FabricaRepository(self.connection)
            return self
        except Exception as e:
            log.error(f'UoW: Falha ao iniciar a transação: {e}', exc_info=True)
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                if exc_type == StopException:
                    log.debug('UoW: Interrupção do Streamlit (st.stop) detectada. Commitando transação.')
                    self.transaction.commit()
                    return False
                if exc_type == SimulationRollback:
                    log.info(f'UoW: Simulação finalizada. Executando ROLLBACK preventivo.')
                    self.transaction.rollback()
                    return False
                log.warning(f'UoW: Erro detectado. Executando ROLLBACK. Erro: {exc_val}', exc_info=True)
                self.transaction.rollback()
            else:
                log.debug('UoW: Sucesso. Executando COMMIT.')
                self.transaction.commit()
        except Exception as e:
            log.error(f'UoW: Erro crítico durante o __exit__ (commit/rollback): {e}', exc_info=True)
            try:
                self.transaction.rollback()
            except:
                pass
        finally:
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
            log.debug('UoW: Conexão fechada.')