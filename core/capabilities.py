"""Registre dynamique des capacités déclarées par EURO AI."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "operational": "OPÉRATIONNEL",
    "partial": "PARTIEL",
    "planned": "À CONSTRUIRE",
}


def load_capabilities(path=None):
    registry_path = Path(path) if path else ROOT / "skills" / "registry.json"
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "inconnue", "modules": []}
    modules = data.get("modules", [])
    if not isinstance(modules, list):
        modules = []
    normalized = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        item = dict(module)
        state = item.get("availability", "planned")
        if state not in LABELS:
            state = "planned"
        item["availability"] = state
        item["availability_label"] = LABELS[state]
        normalized.append(item)
    return {"version": data.get("version", "inconnue"), "modules": normalized}


def capability_context(registry=None):
    data = registry or load_capabilities()
    lines = ["ÉTAT RÉEL DES CAPACITÉS EURO AI :"]
    for module in data["modules"]:
        lines.append(
            f"- {module.get('name', module.get('id', 'Module'))} : "
            f"{module['availability_label']}. "
            f"{module.get('current_state', module.get('description', 'État non détaillé'))}"
        )
    lines.append(
        "Règle : une capacité PARTIELLE n'est utilisable que dans les limites décrites ; "
        "une capacité À CONSTRUIRE n'est pas disponible. Ne prétends jamais avoir exécuté "
        "une action sans résultat vérifiable."
    )
    return "\n".join(lines)


def render_capabilities(registry=None):
    data = registry or load_capabilities()
    groups = {"operational": [], "partial": [], "planned": []}
    for module in data["modules"]:
        groups[module["availability"]].append(module)
    lines = [f"EURO AI — Registre des capacités (version {data['version']})"]
    for state in ("operational", "partial", "planned"):
        if not groups[state]:
            continue
        lines.append(f"\n{LABELS[state]} :")
        for module in groups[state]:
            lines.append(f"- {module.get('name', module.get('id', 'Module'))} — {module.get('current_state', module.get('description', ''))}")
    return "\n".join(lines)
