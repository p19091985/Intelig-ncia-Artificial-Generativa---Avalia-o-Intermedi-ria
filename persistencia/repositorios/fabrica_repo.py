"""
Repositório para o módulo Fábrica de Pré-Moldados.
Encapsula todas as operações de banco de dados das tabelas fab_*.
"""
from persistencia.repositorios.base import BaseRepository
import pandas as pd
import logging
log = logging.getLogger(__name__)


class FabricaRepository(BaseRepository):
    """Acesso a dados do módulo de fábrica de pré-moldados."""

    # ── Clientes ─────────────────────────────────────────────
    def get_all_clientes(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_clientes ORDER BY nome"
        )

    def get_cliente_by_id(self, cliente_id: int) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_clientes WHERE id = :id", {"id": cliente_id}
        )

    def save_cliente(self, data: dict, cliente_id: int = None):
        if cliente_id:
            self._update_table("fab_clientes", data, {"id": cliente_id})
        else:
            self._write_dataframe_to_table(
                pd.DataFrame([data]), "fab_clientes"
            )

    def delete_cliente(self, cliente_id: int):
        self._delete_from_table("fab_clientes", {"id": cliente_id})

    # ── Materiais ────────────────────────────────────────────
    def get_all_materiais(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_materiais ORDER BY tipo, nome"
        )

    def get_materiais_by_tipo(self, tipo: str) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_materiais WHERE tipo = :tipo ORDER BY nome",
            {"tipo": tipo},
        )

    def get_estoque_baixo(self, limite: float = 1000.0) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_materiais WHERE estoque_atual < :limite ORDER BY estoque_atual",
            {"limite": limite},
        )

    def update_estoque(self, material_id: int, nova_quantidade: float):
        self._update_table(
            "fab_materiais",
            {"estoque_atual": nova_quantidade},
            {"id": material_id},
        )

    def save_material(self, data: dict, material_id: int = None):
        """Salva ou atualiza um material no banco de dados."""
        if material_id:
            self._update_table("fab_materiais", data, {"id": material_id})
        else:
            self._write_dataframe_to_table(
                pd.DataFrame([data]), "fab_materiais"
            )

    def delete_material(self, material_id: int):
        """Exclui um material do banco de dados."""
        self._delete_from_table("fab_materiais", {"id": material_id})

    # ── Catálogo de Elementos ────────────────────────────────
    def get_catalogo_elementos(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe("""
            SELECT e.*, t.nome AS traco_nome, t.traco_str AS traco_str_display
            FROM fab_catalogo_elementos e
            LEFT JOIN fab_tracos_padrao t ON e.traco_id = t.id
            ORDER BY e.tipo, e.nome
        """)

    def get_elemento_by_id(self, elemento_id: int) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_catalogo_elementos WHERE id = :id",
            {"id": elemento_id},
        )

    def save_elemento(self, data: dict, elemento_id: int = None):
        if elemento_id:
            self._update_table("fab_catalogo_elementos", data, {"id": elemento_id})
        else:
            self._write_dataframe_to_table(
                pd.DataFrame([data]), "fab_catalogo_elementos"
            )

    def delete_elemento(self, elemento_id: int):
        self._delete_from_table("fab_catalogo_elementos", {"id": elemento_id})

    # ── Traços Padrão ────────────────────────────────────────
    def get_tracos_padrao(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_tracos_padrao ORDER BY fck_alvo"
        )

    def get_traco_by_id(self, traco_id: int) -> pd.DataFrame:
        return self._execute_query_to_dataframe(
            "SELECT * FROM fab_tracos_padrao WHERE id = :id", {"id": traco_id}
        )

    def save_traco(self, data: dict, traco_id: int = None):
        """Salva ou atualiza um traço padrão no banco de dados."""
        if traco_id:
            self._update_table("fab_tracos_padrao", data, {"id": traco_id})
        else:
            self._write_dataframe_to_table(
                pd.DataFrame([data]), "fab_tracos_padrao"
            )

    # ── Pedidos ──────────────────────────────────────────────
    def get_all_pedidos(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe("""
            SELECT p.id, c.nome AS cliente, e.nome AS elemento,
                   p.quantidade, e.volume_m3,
                   ROUND(p.quantidade * e.volume_m3, 2) AS volume_total_m3,
                   p.data_pedido, p.data_entrega, p.status,
                   t.nome AS traco_nome, t.traco_str, t.consumo_cimento_m3,
                   p.cliente_id, p.elemento_id, p.traco_usado_id
            FROM fab_pedidos p
            JOIN fab_clientes c ON p.cliente_id = c.id
            JOIN fab_catalogo_elementos e ON p.elemento_id = e.id
            LEFT JOIN fab_tracos_padrao t ON p.traco_usado_id = t.id
            ORDER BY p.data_pedido DESC
        """)

    def get_pedido_by_id(self, pedido_id: int) -> pd.DataFrame:
        return self._execute_query_to_dataframe("""
            SELECT p.*, c.nome AS cliente, e.nome AS elemento,
                   e.volume_m3, e.fck_necessario,
                   t.nome AS traco_nome, t.traco_str, t.consumo_cimento_m3
            FROM fab_pedidos p
            JOIN fab_clientes c ON p.cliente_id = c.id
            JOIN fab_catalogo_elementos e ON p.elemento_id = e.id
            LEFT JOIN fab_tracos_padrao t ON p.traco_usado_id = t.id
            WHERE p.id = :id
        """, {"id": pedido_id})

    def save_pedido(self, data: dict):
        self._write_dataframe_to_table(pd.DataFrame([data]), "fab_pedidos")

    def update_pedido_status(self, pedido_id: int, status: str):
        self._update_table("fab_pedidos", {"status": status}, {"id": pedido_id})

    # ── Estatísticas / Dashboard ─────────────────────────────
    def get_resumo_pedidos(self) -> dict:
        total = self._execute_scalar("SELECT COUNT(*) FROM fab_pedidos")
        pendentes = self._execute_scalar(
            "SELECT COUNT(*) FROM fab_pedidos WHERE status = 'Pendente'"
        )
        em_producao = self._execute_scalar(
            "SELECT COUNT(*) FROM fab_pedidos WHERE status = 'Em Produção'"
        )
        concluidos = self._execute_scalar(
            "SELECT COUNT(*) FROM fab_pedidos WHERE status = 'Concluído'"
        )
        volume = self._execute_scalar("""
            SELECT COALESCE(ROUND(SUM(p.quantidade * e.volume_m3), 2), 0)
            FROM fab_pedidos p
            JOIN fab_catalogo_elementos e ON p.elemento_id = e.id
            WHERE p.status IN ('Pendente', 'Em Produção')
        """)
        return {
            "total": total or 0,
            "pendentes": pendentes or 0,
            "em_producao": em_producao or 0,
            "concluidos": concluidos or 0,
            "volume_programado_m3": volume or 0.0,
        }

    def get_pedidos_por_status(self) -> pd.DataFrame:
        return self._execute_query_to_dataframe("""
            SELECT status, COUNT(*) AS quantidade
            FROM fab_pedidos
            GROUP BY status
            ORDER BY status
        """)
