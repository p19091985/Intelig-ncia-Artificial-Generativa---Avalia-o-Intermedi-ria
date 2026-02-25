"""
test_ai_concreto.py — Tests for the LangChain-based AI concrete dosage module.
Uses unittest.mock to avoid real API calls during testing.
"""
import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.limites_normativos import consultar_limites_normativos
from components.ai_concreto import (
    sugerir_traco,
    otimizar_traco,
    TracoOutput,
    OtimizacaoOutput,
    MaterialDetalhe,
    MateriaisDict,
)


# ---------------------------------------------------------------------------
# 1. Tool tests — these run locally, no API needed
# ---------------------------------------------------------------------------
class TestConsultarLimitesNormativos:
    """Tests for the @tool consultar_limites_normativos."""

    def test_fck_10_returns_class_I(self):
        result = json.loads(consultar_limites_normativos.invoke({"fck": 10.0}))
        assert result["relacao_ac_maxima"] == 0.65
        assert result["consumo_minimo_cimento_kg"] == 260
        assert result["classe_agressividade"] == "I (Fraca)"

    def test_fck_25_returns_class_II(self):
        result = json.loads(consultar_limites_normativos.invoke({"fck": 25.0}))
        assert result["relacao_ac_maxima"] == 0.55
        assert result["consumo_minimo_cimento_kg"] == 280
        assert result["classe_agressividade"] == "II (Moderada)"

    def test_fck_35_returns_class_III(self):
        result = json.loads(consultar_limites_normativos.invoke({"fck": 35.0}))
        assert result["relacao_ac_maxima"] == 0.45
        assert result["consumo_minimo_cimento_kg"] == 320
        assert result["classe_agressividade"] == "III (Forte)"

    def test_fck_50_returns_class_IV(self):
        result = json.loads(consultar_limites_normativos.invoke({"fck": 50.0}))
        assert result["relacao_ac_maxima"] == 0.40
        assert result["consumo_minimo_cimento_kg"] == 360
        assert result["classe_agressividade"] == "IV (Muito Forte)"

    def test_boundary_fck_20(self):
        """FCK exactly 20 should be Class I (<=20)."""
        result = json.loads(consultar_limites_normativos.invoke({"fck": 20.0}))
        assert result["relacao_ac_maxima"] == 0.65

    def test_boundary_fck_30(self):
        """FCK exactly 30 should be Class II (<=30)."""
        result = json.loads(consultar_limites_normativos.invoke({"fck": 30.0}))
        assert result["relacao_ac_maxima"] == 0.55

    def test_boundary_fck_40(self):
        """FCK exactly 40 should be Class III (<=40)."""
        result = json.loads(consultar_limites_normativos.invoke({"fck": 40.0}))
        assert result["relacao_ac_maxima"] == 0.45

    def test_returns_valid_json(self):
        """Output must be a valid JSON string for all ranges."""
        for fck in [5, 15, 20, 25, 30, 35, 40, 45, 50, 60]:
            raw = consultar_limites_normativos.invoke({"fck": float(fck)})
            data = json.loads(raw)
            assert "relacao_ac_maxima" in data
            assert "consumo_minimo_cimento_kg" in data
            assert "classe_agressividade" in data


# ---------------------------------------------------------------------------
# 2. Pydantic model validation tests — no API needed
# ---------------------------------------------------------------------------
class TestPydanticModels:
    """Tests that Pydantic models accept valid data and reject invalid data."""

    def _make_materiais(self):
        return MateriaisDict(
            Cimento=MaterialDetalhe(tipo="CP-IV", kg=350, custo_kg=0.70),
            Areia=MaterialDetalhe(tipo="Fina", kg=700, custo_kg=0.05),
            Brita=MaterialDetalhe(tipo="Brita 1", kg=1050, custo_kg=0.06),
            **{"Água": MaterialDetalhe(tipo="Potável", kg=175, custo_kg=0.01)},
            Aditivo=MaterialDetalhe(tipo="Superplastificante", kg=2.8, custo_kg=8.50),
        )

    def test_traco_output_valid(self):
        """A fully populated TracoOutput should validate without errors."""
        mat = self._make_materiais()
        t = TracoOutput(
            raciocinio_cot="Step 1: chose CP-IV. Step 2: checked limits.",
            traco_sugerido="1 : 2.0 : 3.0 : 0.50 a/c",
            cimento_tipo="CP-IV",
            fck_alvo=30.0,
            slump_alvo=100.0,
            agregado_max="Brita 1",
            relacao_ac=0.50,
            consumo_cimento_m3=350.0,
            justificativa="Technical analysis",
            custo_estimado=320.50,
            materiais_m3=mat,
        )
        assert t.raciocinio_cot.startswith("Step 1")
        assert t.fck_alvo == 30.0

    def test_traco_output_raciocinio_cot_is_first_field(self):
        """raciocinio_cot must be the first field in the schema for CoT."""
        fields = list(TracoOutput.model_fields.keys())
        assert fields[0] == "raciocinio_cot"

    def test_otimizacao_output_valid(self):
        o = OtimizacaoOutput(
            nome_otimizado="T-30 Otimizado",
            traco_original="1:2:3:0.5",
            traco_otimizado="1:2.1:3.1:0.48",
            consumo_original=350.0,
            consumo_otimizado=322.0,
            aditivo_kg=2.6,
            economia_liquida_m3=15.40,
            justificativa="Reduced cement by 8%",
        )
        assert o.consumo_otimizado < o.consumo_original


# ---------------------------------------------------------------------------
# 3. System prompt file tests — no API needed
# ---------------------------------------------------------------------------
class TestSystemPromptFile:
    """Tests that the system prompt file exists and contains required elements."""

    @pytest.fixture(autouse=True)
    def _set_base_dir(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.prompt_path = os.path.join(self.base_dir, "prompts", "sugerir_traco_system.txt")

    def test_prompt_file_exists(self):
        assert os.path.isfile(self.prompt_path), "prompts/sugerir_traco_system.txt not found"

    def test_prompt_contains_xml_tags(self):
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        for tag in ["<role>", "</role>", "<context>", "</context>", "<rules>", "</rules>"]:
            assert tag in content, f"XML tag '{tag}' missing from system prompt"

    def test_prompt_contains_cot_instructions(self):
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<thought_process_instructions>" in content
        assert "raciocinio_cot" in content

    def test_prompt_contains_few_shot(self):
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<few_shot_example>" in content
        assert "<user_input>" in content
        assert "<expected_output>" in content

    def test_prompt_mentions_tool(self):
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "consultar_limites_normativos" in content


# ---------------------------------------------------------------------------
# 4. Integration tests with mocked LLM — no real API calls
# ---------------------------------------------------------------------------
class TestSugerirTracoMocked:
    """Tests sugerir_traco with a fully mocked LangChain pipeline."""

    def _build_mock_traco_output(self):
        """Returns a TracoOutput that the mocked LLM will return."""
        mat = MateriaisDict(
            Cimento=MaterialDetalhe(tipo="CP-IV", kg=350, custo_kg=0.70),
            Areia=MaterialDetalhe(tipo="Fina", kg=700, custo_kg=0.05),
            Brita=MaterialDetalhe(tipo="Brita 1", kg=1050, custo_kg=0.06),
            **{"Água": MaterialDetalhe(tipo="Potável", kg=175, custo_kg=0.01)},
            Aditivo=MaterialDetalhe(tipo="Superplastificante", kg=2.8, custo_kg=8.50),
        )
        return TracoOutput(
            raciocinio_cot="CoT: FCK 30 → CP-IV. Tool returned a/c max 0.55. Adopted 0.50.",
            traco_sugerido="1 : 2.0 : 3.0 : 0.50 a/c",
            cimento_tipo="CP-IV",
            fck_alvo=30.0,
            slump_alvo=100.0,
            agregado_max="Brita 1",
            relacao_ac=0.50,
            consumo_cimento_m3=350.0,
            justificativa="Detailed technical analysis in Markdown",
            custo_estimado=320.50,
            materiais_m3=mat,
        )

    @patch("components.ai_concreto.ChatOpenAI")
    def test_sugerir_traco_returns_all_fields(self, MockChatOpenAI):
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm

        # Mock .bind_tools().invoke() — first call returns tool_calls
        mock_initial_response = MagicMock()
        mock_initial_response.tool_calls = [
            {"name": "consultar_limites_normativos", "args": {"fck": 30.0}, "id": "call_123"}
        ]
        mock_llm.bind_tools.return_value.invoke.return_value = mock_initial_response

        # Mock .with_structured_output().invoke() — second call returns Pydantic
        mock_traco = self._build_mock_traco_output()
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_traco

        result = sugerir_traco(30.0, 100.0, "Brita 1")

        expected_fields = [
            "raciocinio_cot", "traco_sugerido", "cimento_tipo", "fck_alvo",
            "slump_alvo", "agregado_max", "relacao_ac", "consumo_cimento_m3",
            "justificativa", "custo_estimado", "materiais_m3",
        ]
        for field in expected_fields:
            assert field in result, f"Field '{field}' missing from sugerir_traco result"

    @patch("components.ai_concreto.ChatOpenAI")
    def test_sugerir_traco_uses_temperature_02(self, MockChatOpenAI):
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm

        mock_initial_response = MagicMock()
        mock_initial_response.tool_calls = []
        mock_llm.bind_tools.return_value.invoke.return_value = mock_initial_response

        mock_traco = self._build_mock_traco_output()
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_traco

        sugerir_traco(30.0)

        MockChatOpenAI.assert_called_once()
        call_kwargs = MockChatOpenAI.call_args
        assert call_kwargs.kwargs.get("temperature") == 0.2 or call_kwargs[1].get("temperature") == 0.2

    @patch("components.ai_concreto.ChatOpenAI")
    def test_sugerir_traco_error_fallback(self, MockChatOpenAI):
        """When the LLM raises an exception, the function returns a graceful fallback."""
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm
        mock_llm.bind_tools.return_value.invoke.side_effect = Exception("API Error")

        result = sugerir_traco(30.0)

        assert result["traco_sugerido"] == "Erro na IA"
        assert result["raciocinio_cot"] == "Falha na geração do modelo."
        assert result["fck_alvo"] == 30.0

    @patch("components.ai_concreto.ChatOpenAI")
    def test_sugerir_traco_binds_tool(self, MockChatOpenAI):
        """Verifies that .bind_tools() is called with consultar_limites_normativos."""
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm

        mock_initial_response = MagicMock()
        mock_initial_response.tool_calls = []
        mock_llm.bind_tools.return_value.invoke.return_value = mock_initial_response

        mock_traco = self._build_mock_traco_output()
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_traco

        sugerir_traco(25.0)

        mock_llm.bind_tools.assert_called_once()
        tools_arg = mock_llm.bind_tools.call_args[0][0]
        assert len(tools_arg) == 1
        assert tools_arg[0] == consultar_limites_normativos


class TestOtimizarTracoMocked:
    """Tests otimizar_traco with a mocked LangChain pipeline."""

    @patch("components.ai_concreto.ChatOpenAI")
    def test_otimizar_traco_returns_all_fields(self, MockChatOpenAI):
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm

        mock_output = OtimizacaoOutput(
            nome_otimizado="T-30 Otimizado",
            traco_original="1:2:3:0.5",
            traco_otimizado="1:2.1:3.1:0.48",
            consumo_original=350.0,
            consumo_otimizado=322.0,
            aditivo_kg=2.6,
            economia_liquida_m3=15.40,
            justificativa="Reduced cement by 8%, compensated with superplasticizer",
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_output

        traco_input = {"nome": "T-30", "fck_alvo": 30.0, "traco_str": "1:2:3:0.5", "consumo_cimento_m3": 350.0}
        result = otimizar_traco(traco_input)

        assert result["consumo_otimizado"] == 322.0
        assert result["economia_liquida_m3"] == 15.40
        assert "justificativa" in result

    @patch("components.ai_concreto.ChatOpenAI")
    def test_otimizar_traco_uses_temperature_03(self, MockChatOpenAI):
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm

        mock_output = MagicMock()
        mock_output.model_dump.return_value = {"nome_otimizado": "T", "justificativa": "ok"}
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_output

        otimizar_traco({"consumo_cimento_m3": 350})

        call_kwargs = MockChatOpenAI.call_args
        assert call_kwargs.kwargs.get("temperature") == 0.3 or call_kwargs[1].get("temperature") == 0.3

    @patch("components.ai_concreto.ChatOpenAI")
    def test_otimizar_traco_error_fallback(self, MockChatOpenAI):
        mock_llm = MagicMock()
        MockChatOpenAI.return_value = mock_llm
        mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Timeout")

        result = otimizar_traco({"traco_str": "1:2:3", "consumo_cimento_m3": 300})

        assert result["nome_otimizado"] == "Erro de Otimização IA"
        assert "Timeout" in result["justificativa"]
