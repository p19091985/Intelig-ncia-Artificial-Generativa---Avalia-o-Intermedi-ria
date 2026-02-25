import json

from langchain_core.tools import tool

@tool
def consultar_limites_normativos(fck: float) -> str:
    """
    Obtém os limites normativos de relação água/cimento máxima e consumo mínimo de cimento com base no FCK alvo.
    """
    # Lógica de engenharia baseada na norma
    if fck <= 20:
        data = {"relacao_ac_maxima": 0.65, "consumo_minimo_cimento_kg": 260, "classe_agressividade": "I (Fraca)"}
    elif fck <= 30:
        data = {"relacao_ac_maxima": 0.55, "consumo_minimo_cimento_kg": 280, "classe_agressividade": "II (Moderada)"}
    elif fck <= 40:
        data = {"relacao_ac_maxima": 0.45, "consumo_minimo_cimento_kg": 320, "classe_agressividade": "III (Forte)"}
    else:
        data = {"relacao_ac_maxima": 0.40, "consumo_minimo_cimento_kg": 360, "classe_agressividade": "IV (Muito Forte)"}

    return json.dumps(data)
