"""
Serviço de AI Generativa — Inteligência de Concreto.
Refatorado para utilizar LangChain e Pydantic (Structured Outputs),
conforme ensinado na Aula 05.
"""
import json
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

import config

log = logging.getLogger(__name__)

from tools.limites_normativos import consultar_limites_normativos

# --- 2. Modelos Pydantic para Structured Output (Aula 05 - Slide 29) ---
class MaterialDetalhe(BaseModel):
    tipo: str = Field(description="Nome ou tipo do material")
    kg: float = Field(description="Quantidade em kg (ou litros para água)")
    custo_kg: float = Field(description="Custo unitário")

class MateriaisDict(BaseModel):
    Cimento: MaterialDetalhe
    Areia: MaterialDetalhe
    Brita: MaterialDetalhe
    Agua: MaterialDetalhe = Field(alias="Água")
    Aditivo: MaterialDetalhe

class TracoOutput(BaseModel):
    raciocinio_cot: str = Field(description="Chain of Thought: Seu processo de raciocínio lógico, passo a passo, detalhando todas as restrições da norma ANTES de preencher o restante dos campos.", alias="raciocinio_cot")
    traco_sugerido: str = Field(description="Proporção do traço no formato 'Cimento : Areia : Brita : a/c', ex: 1 : 2.2 : 3.1 : 0.5 a/c")
    cimento_tipo: str
    fck_alvo: float
    slump_alvo: float
    agregado_max: str
    relacao_ac: float
    consumo_cimento_m3: float
    justificativa: str = Field(description="Texto longo em Markdown com a análise técnica")
    custo_estimado: float = Field(description="Custo total estimado em R$/m³. OBRIGATÓRIO calcular: somar (kg × custo_kg) de CADA material (Cimento, Areia, Brita, Água, Aditivo). Se custos não forem informados nos materiais_selecionados, usar referência: Cimento R$0.65/kg, Areia R$0.08/kg, Brita R$0.10/kg, Água R$0.005/L, Aditivo R$5.20/kg. Este valor NUNCA pode ser 0.00.")
    materiais_m3: MateriaisDict

class OtimizacaoOutput(BaseModel):
    nome_otimizado: str
    traco_original: str
    traco_otimizado: str
    consumo_original: float
    consumo_otimizado: float
    aditivo_kg: float
    economia_liquida_m3: float
    justificativa: str = Field(description="Relatório Markdown de engenharia")


# --- 3. Helper: Escapar cifrão para Streamlit Markdown ---

def _escapar_cifrao(obj):
    """
    Recursively escapes '$' → '\\$' in all string values of a dict/list.
    Prevents Streamlit from interpreting 'R$' as LaTeX math delimiters.
    """
    if isinstance(obj, str):
        return obj.replace("R$", "R\\$")
    elif isinstance(obj, dict):
        return {k: _escapar_cifrao(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_escapar_cifrao(item) for item in obj]
    return obj


# --- 4. Lógica Principal com LangChain ---

def sugerir_traco(
    fck: float,
    slump: float = 100.0,
    agregado_max: str = "Brita 1",
    materiais_selecionados: dict = None,
) -> dict:

    if materiais_selecionados is None:
        materiais_selecionados = {}

    # Instancia o modelo via LangChain
    llm = ChatOpenAI(
        api_key=config.OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0.2
    )

    # Associa a ferramenta (Tool Calling) ao modelo
    llm_com_tools = llm.bind_tools([consultar_limites_normativos])

    materiais_str = json.dumps(materiais_selecionados, ensure_ascii=False)

    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_path = os.path.join(BASE_DIR, "prompts", "sugerir_traco_system.txt")

    # Carrega o System Prompt do arquivo externo refatorado
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt_template = f.read()

    system_prompt = f"{system_prompt_template}\n\nMateriais selecionados no estoque: {materiais_str}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Calcule o traço para FCK={fck} MPa, Slump={slump} mm, Agregado={agregado_max}.")
    ]

    try:
        # Passo 1: O modelo raciocina e decide usar a ferramenta
        resposta_inicial = llm_com_tools.invoke(messages)
        messages.append(resposta_inicial)

        # Se o LLM solicitou a ferramenta, nós executamos
        if resposta_inicial.tool_calls:
            for tool_call in resposta_inicial.tool_calls:
                if tool_call["name"] == "consultar_limites_normativos":
                    resultado_tool = consultar_limites_normativos.invoke(tool_call["args"])

                    messages.append(ToolMessage(
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"],
                        content=str(resultado_tool)
                    ))

        # Passo 2: Exige a formatação de saída como JSON Estruturado (Structured Output)
        llm_estruturado = llm.with_structured_output(TracoOutput)
        resposta_final = llm_estruturado.invoke(messages)

        # Converte o Pydantic BaseModel de volta para um dicionário para o Streamlit renderizar
        resultado = resposta_final.model_dump(by_alias=True)

        # Passo 3: Recalcular custo_estimado no Python (IA é imprecisa em aritmética)
        # Somar (kg × custo_kg) de cada material retornado em materiais_m3
        custo_calculado = 0.0
        if resultado.get("materiais_m3") and isinstance(resultado["materiais_m3"], dict):
            for nome_mat, info_mat in resultado["materiais_m3"].items():
                if isinstance(info_mat, dict):
                    kg = info_mat.get("kg", 0.0)
                    custo_kg = info_mat.get("custo_kg", 0.0)
                    custo_calculado += kg * custo_kg

        # Usar o valor calculado se for maior que 0, senão manter o da IA como fallback
        if custo_calculado > 0:
            resultado["custo_estimado"] = round(custo_calculado, 2)

        # Escapar '$' para evitar renderização LaTeX no Streamlit (R$0.70 → R\$0.70)
        return _escapar_cifrao(resultado)

    except Exception as e:
        log.error(f"Erro ao processar LLM sugerir_traco: {e}")
        return {
            "raciocinio_cot": "Falha na geração do modelo.",
            "traco_sugerido": "Erro na IA",
            "cimento_tipo": "Desconhecido",
            "fck_alvo": fck,
            "slump_alvo": slump,
            "agregado_max": agregado_max,
            "relacao_ac": 0.0,
            "consumo_cimento_m3": 0.0,
            "justificativa": f"### Erro na comunicação com LangChain\n`{str(e)}`",
            "custo_estimado": 0.0,
            "materiais_m3": {}
        }


def otimizar_traco(traco_dict: dict) -> dict:
    traco_json = json.dumps(traco_dict, ensure_ascii=False)

    llm = ChatOpenAI(
        api_key=config.OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0.3
    )

    # Aplicação direta do output estruturado
    llm_estruturado = llm.with_structured_output(OtimizacaoOutput)

    system_prompt = f"""Você é um Engenheiro Civil Sênior especialista em redução de custos.
Sua missão é otimizar o consumo de cimento deste traço usando aditivos superplastificantes.

Dados originais do traço:
{traco_json}

Regras:
1. Reduza o consumo de cimento entre 5% e 10%.
2. Compense com um Aditivo Superplastificante (0.5% a 1.0% do peso do novo cimento).
3. Calcule o novo custo e a economia gerada. Custo base do cimento: R$0.70/kg. Custo base do superplastificante: R$8.50/kg."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="Otimize este traço agora mesmo com foco em custo-benefício.")
    ]

    try:
        resposta = llm_estruturado.invoke(messages)
        # Escapar '$' para evitar renderização LaTeX no Streamlit (R$0.70 → R\$0.70)
        return _escapar_cifrao(resposta.model_dump())

    except Exception as e:
        log.error(f"Erro ao processar LLM otimizar_traco: {e}")
        return {
            "nome_otimizado": "Erro de Otimização IA",
            "traco_original": traco_dict.get("traco_str", ""),
            "traco_otimizado": "N/A",
            "consumo_original": float(traco_dict.get("consumo_cimento_m3", 0)),
            "consumo_otimizado": 0.0,
            "aditivo_kg": 0.0,
            "economia_liquida_m3": 0.0,
            "justificativa": f"Falha na Otimização: `{str(e)}`",
        }