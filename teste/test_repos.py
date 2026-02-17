import pytest
from persistencia.unit_of_work import UnitOfWork
from sqlalchemy import text


def test_fabrica_catalogo_elementos():
    """Test CRUD on fab_catalogo_elementos via the fabrica repository."""
    # Create
    with UnitOfWork() as uow:
        data = {'nome': 'Tubo D400', 'tipo': 'Tubo', 'volume_m3': 0.125, 'fck_necessario': 25.0}
        uow.fabrica.save_elemento(data)

    # Read
    with UnitOfWork() as uow:
        df = uow.fabrica.get_catalogo_elementos()
        assert len(df) >= 1
        tubo = df[df['nome'] == 'Tubo D400']
        assert len(tubo) == 1
        assert tubo.iloc[0]['tipo'] == 'Tubo'
        elem_id = int(tubo.iloc[0]['id'])

    # Update
    with UnitOfWork() as uow:
        data_update = {'nome': 'Tubo D400 Reforçado', 'tipo': 'Tubo', 'volume_m3': 0.130, 'fck_necessario': 30.0}
        uow.fabrica.save_elemento(data_update, elem_id)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_catalogo_elementos()
        tubo = df[df['id'] == elem_id]
        assert tubo.iloc[0]['nome'] == 'Tubo D400 Reforçado'
        assert float(tubo.iloc[0]['fck_necessario']) == 30.0

    # Delete
    with UnitOfWork() as uow:
        uow.fabrica.delete_elemento(elem_id)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_catalogo_elementos()
        assert len(df[df['id'] == elem_id]) == 0


def test_fabrica_clientes_crud():
    """Test full CRUD on fab_clientes via the fabrica repository."""
    # Read seeded
    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_clientes()
        assert len(df) >= 1

    # Create
    with UnitOfWork() as uow:
        data = {'nome': 'Engenharia Teste S.A.', 'documento': '99.999.999/0001-99', 'endereco': 'Rua Teste, 1'}
        uow.fabrica.save_cliente(data)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_clientes()
        novo = df[df['documento'] == '99.999.999/0001-99']
        assert len(novo) == 1
        assert novo.iloc[0]['nome'] == 'Engenharia Teste S.A.'
        cli_id = int(novo.iloc[0]['id'])

    # Update
    with UnitOfWork() as uow:
        data_update = {'nome': 'Engenharia Teste Atualizada', 'documento': '99.999.999/0001-99', 'endereco': 'Av. Nova, 200'}
        uow.fabrica.save_cliente(data_update, cli_id)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_clientes()
        atualizado = df[df['id'] == cli_id]
        assert atualizado.iloc[0]['nome'] == 'Engenharia Teste Atualizada'

    # Delete
    with UnitOfWork() as uow:
        uow.fabrica.delete_cliente(cli_id)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_clientes()
        assert len(df[df['id'] == cli_id]) == 0


def test_fabrica_materiais():
    """Test reading seeded materials."""
    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_materiais()
        assert len(df) >= 1


def test_fabrica_tracos():
    """Test reading seeded tracos."""
    with UnitOfWork() as uow:
        df = uow.fabrica.get_tracos_padrao()
        assert len(df) >= 1


def test_fabrica_pedidos_and_status():
    """Test creating a pedido and updating its status."""
    with UnitOfWork() as uow:
        pedido = {
            'cliente_id': 1,
            'elemento_id': 1,
            'quantidade': 500,
            'data_entrega': '2026-03-01',
            'status': 'Pendente',
            'traco_usado_id': 1,
        }
        uow.fabrica.save_pedido(pedido)

    with UnitOfWork() as uow:
        df = uow.fabrica.get_all_pedidos()
        assert len(df) >= 1
        pedido_id = int(df.iloc[0]['id'])

    # Update status
    with UnitOfWork() as uow:
        uow.fabrica.update_pedido_status(pedido_id, 'Em Produção')

    with UnitOfWork() as uow:
        resumo = uow.fabrica.get_resumo_pedidos()
        assert resumo['em_producao'] >= 1


def test_pagina_repository_permissions(engine):
    with engine.connect() as conn:
        try:
            conn.execute(text("INSERT INTO pagina (nome_arquivo, nome_amigavel) VALUES ('01_Test.py', 'Test Page')"))
            conn.commit()
        except Exception:
            pass

    with UnitOfWork() as uow:
        roles = uow.paginas.get_allowed_roles_for_page('01_Test.py')
        assert roles is not None
