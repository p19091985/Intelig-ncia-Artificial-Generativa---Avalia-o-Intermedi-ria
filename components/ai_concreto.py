"""
Serviço de Mock AI — Inteligência de Concreto.
Simula uma resposta de LLM para cálculo de traço (dosagem) de concreto,
usando regras determinísticas baseadas em normas técnicas brasileiras.
"""
import random
import math
from datetime import datetime


def sugerir_traco(
    fck: float,
    slump: float = 100.0,
    agregado_max: str = "Brita 1",
    materiais_selecionados: dict = None,
) -> dict:
    """
    Gera uma sugestão de traço de concreto (Mock AI) com base nos parâmetros de entrada.

    Args:
        fck: Resistência característica desejada (MPa).
        slump: Abatimento do tronco de cone desejado (mm).
        agregado_max: Tamanho máximo do agregado graúdo.
        materiais_selecionados: Dict opcional com objetos dos materiais escolhidos pelo usuário.
                                Ex: {'Cimento': {...}, 'Areia': {...}, 'Brita': {...}, 'Aditivo': {...}}

    Returns:
        Dicionário com traço sugerido, justificativa técnica, custo estimado e materiais por m³.
    """
    # Defaults se nada for selecionado
    if materiais_selecionados is None:
        materiais_selecionados = {}

    sel_cimento = materiais_selecionados.get("Cimento")
    sel_areia = materiais_selecionados.get("Areia")
    sel_brita = materiais_selecionados.get("Brita")
    sel_aditivo = materiais_selecionados.get("Aditivo")

    # ── Seleção de cimento ───────────────────────────────────
    # Se o usuário selecionou, usa o dele. Se não, usa a lógica da IA.
    if sel_cimento:
        cimento_tipo = sel_cimento["nome"]
        cimento_custo_kg = float(sel_cimento["custo_kg"])
        
        # Ajusta relação a/c baseada no tipo se possível, ou mantém lógica por FCK
        # Aqui mantemos a lógica por FCK para garantir segurança técnica
        if fck > 40:
             relacao_ac = round(0.30 + random.uniform(0, 0.05), 2)
        elif fck < 20:
             relacao_ac = round(0.62 + random.uniform(0, 0.08), 2)
        else:
             relacao_ac = round(0.42 + (40 - fck) * 0.01, 2)

        cimento_justif = (
            f"Utilizando o cimento selecionado **{cimento_tipo}**. "
            f"Para FCK {fck} MPa, a relação água/cimento foi calculada em **{relacao_ac}** "
            f"para garantir a resistência alvo."
        )
    else:
        # Lógica original da IA
        if fck > 40:
            cimento_tipo = "CP-V ARI"
            cimento_custo_kg = 0.85
            relacao_ac = round(0.30 + random.uniform(0, 0.05), 2)
            cimento_justif = (
                f"Para FCK {fck} MPa (alta resistência), recomenda-se o cimento **CP-V ARI**..."
            )
        elif fck < 20:
            cimento_tipo = "CP-II F-32"
            cimento_custo_kg = 0.65
            relacao_ac = round(0.62 + random.uniform(0, 0.08), 2)
            cimento_justif = (
                f"Para FCK {fck} MPa (baixa resistência), o cimento **CP-II F-32** é adequado..."
            )
        else:
            cimento_tipo = "CP-IV-32"
            cimento_custo_kg = 0.68
            relacao_ac = round(0.42 + (40 - fck) * 0.01, 2)
            cimento_justif = (
                f"Para FCK {fck} MPa (resistência moderada), o cimento **CP-IV-32**..."
            )

    # ── Cálculo do consumo de cimento (Lei de Abrams simplificada) ──
    consumo_cimento = round(fck * 8.5 + 100 + random.uniform(-10, 10), 1)
    consumo_cimento = max(200, min(650, consumo_cimento))

    # ── Fatores de agregado ──────────────────────────────────
    brita_map = {
        "Brita 0": {"fator_areia": 2.0, "fator_brita": 2.5, "dmax": 9.5},
        "Brita 1": {"fator_areia": 2.2, "fator_brita": 3.1, "dmax": 19.0},
        "Brita 2": {"fator_areia": 2.5, "fator_brita": 3.8, "dmax": 25.0},
    }
    # Tenta mapear pelo nome selecionado ou usa o parametro
    agreg_nome = sel_brita["nome"] if sel_brita else agregado_max
    # Simplificação: tenta achar "Brita 0", "Brita 1" no nome, senão default Brita 1
    if "Brita 0" in agreg_nome or "Pedrisco" in agreg_nome:
        key_brita = "Brita 0"
    elif "Brita 2" in agreg_nome:
        key_brita = "Brita 2"
    else:
        key_brita = "Brita 1"
        
    agreg = brita_map[key_brita]

    # Ajuste pela relação a/c
    fator_cimento = 1.0
    fator_areia = round(agreg["fator_areia"] * (1 + relacao_ac * 0.1), 1)
    fator_brita = round(agreg["fator_brita"] * (1 - relacao_ac * 0.05), 1)

    traco_str = f"1 : {fator_areia} : {fator_brita} : {relacao_ac} a/c"

    # ── Quantidades por m³ ───────────────────────────────────
    consumo_areia = round(consumo_cimento * fator_areia, 1)
    consumo_brita = round(consumo_cimento * fator_brita, 1)
    consumo_agua = round(consumo_cimento * relacao_ac, 1)

    # Definição de custos unitários via seleção ou default
    custo_areia = float(sel_areia["custo_kg"]) if sel_areia else 0.08
    nome_areia = sel_areia["nome"] if sel_areia else "Areia Média Lavada"
    
    custo_brita = float(sel_brita["custo_kg"]) if sel_brita else 0.10
    nome_brita = sel_brita["nome"] if sel_brita else agregado_max

    # Aditivo
    if sel_aditivo:
        # Se selecionou, usa
        aditivo_nome = sel_aditivo["nome"]
        aditivo_custo_kg = float(sel_aditivo["custo_kg"])
        # Dosagem estimada típica se não especificada (0.5%)
        pct_aditivo = 0.005 
        consumo_aditivo = round(consumo_cimento * pct_aditivo, 2)
    else:
        # Lógica original automática
        if fck > 30:
            pct_aditivo = round(0.005 + (fck - 30) * 0.0003, 4)
            consumo_aditivo = round(consumo_cimento * pct_aditivo, 2)
            aditivo_nome = "Superplastificante (Auto)"
            aditivo_custo_kg = 8.50
        else:
            pct_aditivo = 0.003
            consumo_aditivo = round(consumo_cimento * pct_aditivo, 2)
            aditivo_nome = "Plastificante (Auto)"
            aditivo_custo_kg = 5.20

    materiais_m3 = {
        "Cimento": {"tipo": cimento_tipo, "kg": consumo_cimento, "custo_kg": cimento_custo_kg},
        "Areia":   {"tipo": nome_areia, "kg": consumo_areia, "custo_kg": custo_areia},
        "Brita":   {"tipo": nome_brita, "kg": consumo_brita, "custo_kg": custo_brita},
        "Água":    {"tipo": "Água Industrial", "litros": consumo_agua, "custo_kg": 0.005},
        "Aditivo": {"tipo": aditivo_nome, "kg": consumo_aditivo, "custo_kg": aditivo_custo_kg},
    }

    # ── Custo estimado por m³ ────────────────────────────────
    custo_total = round(
        consumo_cimento * cimento_custo_kg
        + consumo_areia * custo_areia
        + consumo_brita * custo_brita
        + consumo_agua * 0.005
        + consumo_aditivo * aditivo_custo_kg,
        2,
    )

    # ── Justificativa completa ───────────────────────────────
    justificativa = (
        f"## Análise Técnica — Dosagem de Concreto\n\n"
        f"**Data da análise:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"### 1. Cimento\n"
        f"{cimento_justif}\n\n"
        f"### 2. Dosagem dos Agregados\n"
        f"Considerando **{nome_brita}** e **{nome_areia}**.\n"
        f"Abatimento alvo de **{slump} mm**.\n\n"
        f"- **{nome_areia}:** {consumo_areia} kg/m³\n"
        f"- **{nome_brita}:** {consumo_brita} kg/m³\n\n"
        f"### 3. Relação Água/Cimento\n"
        f"Relação a/c calculada: **{relacao_ac}** ({consumo_agua} L/m³).\n\n"
        f"### 4. Aditivo\n"
        f"**{aditivo_nome}**: {consumo_aditivo} kg/m³.\n\n"
        f"### 5. Custo Estimado (Preços Cadastrados)\n"
        f"Custo total por m³: **R$ {custo_total:.2f}**.\n"
    )

    return {
        "traco_sugerido": traco_str,
        "cimento_tipo": cimento_tipo,
        "fck_alvo": fck,
        "slump_alvo": slump,
        "agregado_max": nome_brita,
        "relacao_ac": relacao_ac,
        "consumo_cimento_m3": consumo_cimento,
        "justificativa": justificativa,
        "custo_estimado": custo_total,
        "materiais_m3": materiais_m3,
    }


def otimizar_traco(traco_dict: dict) -> dict:
    """
    Recebe um traço padrão e retorna uma versão otimizada para custo (Mock AI).
    Estratégia: reduz cimento em ~8% e compensa com aditivo plastificante.

    Args:
        traco_dict: Dicionário do traço original (da tabela fab_tracos_padrao).

    Returns:
        Dicionário com traço otimizado, economia e justificativa.
    """
    nome_original = traco_dict.get("nome", "Traço Desconhecido")
    fck_alvo = float(traco_dict.get("fck_alvo", 25))
    traco_str_original = traco_dict.get("traco_str", "1:2:3:0.5 a/c")
    consumo_original = float(traco_dict.get("consumo_cimento_m3", 350))

    # Redução de 8% no cimento
    reducao_pct = 0.08
    novo_consumo = round(consumo_original * (1 - reducao_pct), 1)

    # Adiciona superplastificante para compensar
    aditivo_kg = round(novo_consumo * 0.008, 2)

    # Calcula economia
    economia_cimento = round((consumo_original - novo_consumo) * 0.70, 2)
    custo_aditivo = round(aditivo_kg * 8.50, 2)
    economia_liquida = round(economia_cimento - custo_aditivo, 2)

    # Ajusta traço string
    partes = traco_str_original.replace("a/c", "").strip().split(":")
    if len(partes) >= 4:
        p = [p.strip() for p in partes]
        import re
        ac_match = re.match(r"[\d.]+", p[3])
        ac_val = float(ac_match.group()) if ac_match else 0.5
        nova_ac = round(ac_val - 0.03, 2)
        novo_traco = f"{p[0]} : {p[1]} : {p[2]} : {nova_ac} a/c + Superplast."
    else:
        novo_traco = traco_str_original + " + Superplast."

    justificativa = (
        f"## Otimização de Custo — {nome_original}\n\n"
        f"**Estratégia IA:** Redução de cimento com compensação via superplastificante.\n\n"
        f"### Alterações Realizadas\n"
        f"| Parâmetro | Original | Otimizado |\n"
        f"|---|---|---|\n"
        f"| Consumo Cimento | {consumo_original} kg/m³ | {novo_consumo} kg/m³ |\n"
        f"| Aditivo | Nenhum | Superplast. {aditivo_kg} kg/m³ |\n"
        f"| Relação a/c | Original | Reduzida em 0.03 |\n\n"
        f"### Análise Econômica\n"
        f"- Economia em cimento: **R$ {economia_cimento:.2f}/m³**\n"
        f"- Custo do aditivo: **R$ {custo_aditivo:.2f}/m³**\n"
        f"- **Economia líquida: R$ {economia_liquida:.2f}/m³**\n\n"
        f"### Observação Técnica\n"
        f"A adição de superplastificante permite manter o abatimento (slump) "
        f"e a resistência FCK {fck_alvo} MPa mesmo com menor consumo de cimento, "
        f"pois o aditivo melhora a dispersão das partículas e reduz a necessidade de água."
    )

    return {
        "nome_otimizado": f"{nome_original} (Otimizado)",
        "traco_original": traco_str_original,
        "traco_otimizado": novo_traco,
        "consumo_original": consumo_original,
        "consumo_otimizado": novo_consumo,
        "aditivo_kg": aditivo_kg,
        "economia_liquida_m3": economia_liquida,
        "justificativa": justificativa,
    }
