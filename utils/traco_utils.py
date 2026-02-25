"""
traco_utils.py — Utility functions for formatting concrete mix trace strings.

Converts raw trace proportions like "1 : 2.2 : 3.1 : 0.5 a/c" into
human-readable, labeled versions for display throughout the system.
"""


def formatar_traco_legivel(traco_str: str) -> str:
    """
    Converts a raw trace string into a labeled, readable version.

    Input:  "1 : 2.2 : 3.1 : 0.5 a/c"
    Output: "1 (Cimento) : 2.2 (Areia) : 3.1 (Brita) : 0.5 (a/c)"

    If the string cannot be parsed, returns the original unchanged.
    """
    if not traco_str or not isinstance(traco_str, str):
        return traco_str or ""

    labels = ["Cimento", "Areia", "Brita", "a/c"]

    try:
        # Remove "a/c" suffix and extra whitespace
        clean = traco_str.replace("a/c", "").strip()
        parts = [p.strip() for p in clean.split(":")]

        if len(parts) < 3:
            return traco_str  # Cannot parse, return original

        result_parts = []
        for i, part in enumerate(parts):
            if i < len(labels):
                result_parts.append(f"{part} ({labels[i]})")
            else:
                result_parts.append(part)

        return " : ".join(result_parts)
    except Exception:
        return traco_str


def formatar_traco_detalhado(traco_str: str) -> str:
    """
    Returns a multi-line Markdown breakdown of each trace component.

    Input:  "1 : 2.2 : 3.1 : 0.5 a/c"
    Output:
        "**Cimento:** 1 | **Areia:** 2.2 | **Brita:** 3.1 | **a/c:** 0.5"
    """
    if not traco_str or not isinstance(traco_str, str):
        return traco_str or ""

    labels = ["Cimento", "Areia", "Brita", "a/c"]
    icons = ["🧱", "🏖️", "🪨", "💧"]

    try:
        clean = traco_str.replace("a/c", "").strip()
        parts = [p.strip() for p in clean.split(":")]

        if len(parts) < 3:
            return traco_str

        items = []
        for i, part in enumerate(parts):
            if i < len(labels):
                items.append(f"{icons[i]} **{labels[i]}:** {part}")
            else:
                items.append(part)

        return " &nbsp;|&nbsp; ".join(items)
    except Exception:
        return traco_str
