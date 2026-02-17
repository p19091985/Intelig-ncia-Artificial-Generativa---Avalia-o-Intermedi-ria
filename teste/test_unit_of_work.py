import pytest
from persistencia.unit_of_work import UnitOfWork

def test_uow_context_manager():
    with UnitOfWork() as uow:
        assert uow.connection is not None
        assert uow.transaction is not None
        assert uow.usuarios is not None
        assert uow.paginas is not None

def test_uow_repositories_initialization():
    with UnitOfWork() as uow:
        assert hasattr(uow, 'fabrica')
        assert hasattr(uow, 'permissoes')
        assert hasattr(uow, 'paginas')
