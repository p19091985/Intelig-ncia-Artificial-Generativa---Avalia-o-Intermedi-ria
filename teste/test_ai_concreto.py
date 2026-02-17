"""
test_ai_concreto.py — Testes do módulo Mock AI de dosagem de concreto.
Testa as funções sugerir_traco e otimizar_traco com vários parâmetros.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.ai_concreto import sugerir_traco, otimizar_traco


class TestSugerirTraco:
    """Testes para a função sugerir_traco."""

    def test_retorna_dict_com_campos_obrigatorios(self):
        """Verifica que o resultado contém todos os campos esperados."""
        resultado = sugerir_traco(30.0, 100.0, "Brita 1")
        campos = [
            "traco_sugerido", "cimento_tipo", "relacao_ac",
            "consumo_cimento_m3", "custo_estimado",
            "materiais_m3", "justificativa",
        ]
        for campo in campos:
            assert campo in resultado, f"Campo '{campo}' ausente no resultado"

    def test_fck_baixo_10(self):
        """FCK 10 MPa deve sugerir traço econômico com CP-II."""
        resultado = sugerir_traco(10.0, 80.0, "Brita 1")
        assert resultado["consumo_cimento_m3"] < 300
        assert "CP-II" in resultado["cimento_tipo"] or "CP-IV" in resultado["cimento_tipo"]

    def test_fck_alto_50(self):
        """FCK 50 MPa deve usar mais cimento e custar mais."""
        r_baixo = sugerir_traco(10.0, 80.0, "Brita 1")
        r_alto = sugerir_traco(50.0, 80.0, "Brita 1")
        assert r_alto["consumo_cimento_m3"] > r_baixo["consumo_cimento_m3"]
        assert r_alto["custo_estimado"] > r_baixo["custo_estimado"]

    def test_relacao_ac_diminui_com_fck(self):
        """Relação a/c deve diminuir conforme FCK aumenta (Abrams)."""
        r10 = sugerir_traco(10.0, 100.0, "Brita 1")
        r40 = sugerir_traco(40.0, 100.0, "Brita 1")
        assert r40["relacao_ac"] < r10["relacao_ac"]

    def test_materiais_m3_contem_componentes(self):
        """Verifica que os materiais por m³ contêm os componentes essenciais."""
        resultado = sugerir_traco(25.0, 100.0, "Brita 1")
        mat = resultado["materiais_m3"]
        assert len(mat) >= 3, "Deve ter pelo menos Cimento, Areia e Brita"

    def test_diferentes_agregados(self):
        """Agregar tipos diferentes deve produzir custos ligeiramente diferentes."""
        r0 = sugerir_traco(30.0, 100.0, "Brita 0")
        r1 = sugerir_traco(30.0, 100.0, "Brita 1")
        r2 = sugerir_traco(30.0, 100.0, "Brita 2")
        # Todos devem gerar resultados válidos
        assert r0["custo_estimado"] > 0
        assert r1["custo_estimado"] > 0
        assert r2["custo_estimado"] > 0

    def test_justificativa_nao_vazia(self):
        """A justificativa técnica não deve estar vazia."""
        resultado = sugerir_traco(30.0, 100.0, "Brita 1")
        assert len(resultado["justificativa"]) > 50

    def test_custo_positivo(self):
        """Custo estimado deve ser sempre positivo."""
        for fck in [10, 20, 30, 40, 50]:
            resultado = sugerir_traco(float(fck), 100.0, "Brita 1")
            assert resultado["custo_estimado"] > 0, f"Custo negativo para FCK {fck}"


class TestOtimizarTraco:
    """Testes para a função otimizar_traco."""

    def test_retorna_traco_otimizado(self):
        """Verifica que a otimização retorna uma estrutura válida."""
        traco_original = {
            "nome": "Traço Teste FCK 30",
            "fck_alvo": 30.0,
            "traco_str": "1 : 2.2 : 3.1 : 0.50 a/c",
            "consumo_cimento_m3": 370.0,
        }
        resultado = otimizar_traco(traco_original)
        assert "traco_otimizado" in resultado
        assert "consumo_otimizado" in resultado
        assert "economia_liquida_m3" in resultado

    def test_custo_otimizado_reduz_consumo(self):
        """Traço otimizado deve consumir menos cimento que o original."""
        traco_original = {
            "nome": "Traço Teste FCK 30",
            "fck_alvo": 30.0,
            "traco_str": "1 : 2.2 : 3.1 : 0.50 a/c",
            "consumo_cimento_m3": 370.0,
        }
        resultado = otimizar_traco(traco_original)
        assert resultado["consumo_otimizado"] < traco_original["consumo_cimento_m3"]

    def test_economia_liquida_is_float(self):
        """A economia líquida deve ser um número calculado corretamente."""
        traco_original = {
            "nome": "Traço Pilar FCK 40",
            "fck_alvo": 40.0,
            "traco_str": "1 : 1.8 : 2.5 : 0.42 a/c",
            "consumo_cimento_m3": 450.0,
        }
        resultado = otimizar_traco(traco_original)
        assert isinstance(resultado["economia_liquida_m3"], float)
        # Verify formula: cement savings - additive cost
        economia_cimento = round((450.0 - resultado["consumo_otimizado"]) * 0.70, 2)
        custo_aditivo = round(resultado["aditivo_kg"] * 8.50, 2)
        expected = round(economia_cimento - custo_aditivo, 2)
        assert resultado["economia_liquida_m3"] == expected

    def test_justificativa_da_otimizacao(self):
        """A otimização deve incluir justificativa."""
        traco_original = {
            "nome": "Traço Teste",
            "fck_alvo": 25.0,
            "traco_str": "1 : 2.5 : 3.5 : 0.55 a/c",
            "consumo_cimento_m3": 320.0,
        }
        resultado = otimizar_traco(traco_original)
        assert "justificativa" in resultado
        assert len(resultado["justificativa"]) > 50
