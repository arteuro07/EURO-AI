import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_json(path, default):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default

def answer(message: str) -> str:
    config = load_json("config.json", {"name": "EURO AI"})
    rules = load_json("rules/rules.json", {})
    text = message.strip()
    if not text:
        return "Écris une demande pour EURO AI."
    blocked = [str(x).lower() for x in rules.get("blocked_categories", [])]
    # Initial safe foundation: custom rules are displayed and applied as policy
    # constraints in later model-backed releases. No shell execution is allowed.
    for term in blocked:
        if term and term in text.lower():
            return "Cette demande correspond à une catégorie bloquée par les règles du propriétaire."
    return (
        f"{config.get('name', 'EURO AI')} — moteur de base actif.\n"
        "La demande a été reçue. Le cerveau de langage sera ajouté après validation "
        "du pipeline GitHub.\n\n"
        f"Message : {text[:2000]}"
    )

if __name__ == "__main__":
    import sys
    print(answer(" ".join(sys.argv[1:])))
