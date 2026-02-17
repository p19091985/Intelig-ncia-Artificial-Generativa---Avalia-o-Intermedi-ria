from sqlalchemy import text
from persistencia.database import DatabaseManager

def test_database_connection_fixture(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

def test_database_manager_singleton():
    engine1 = DatabaseManager.get_engine()
    engine2 = DatabaseManager.get_engine()
    assert engine1 is engine2
    assert engine1 is not None
