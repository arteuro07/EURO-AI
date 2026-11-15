import json
from pathlib import Path

from core.brain import chat_completion

ROOT = Path(__file__).resolve().parents[1]


def load_json(path, default):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def load_owner_settings():
    settings = load_json("rules/rules.json", {})
    external = Path.home() / ".config" / "euro-ai" / "owner-settings.json"
    try:
        saved = json.loads(external.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            settings.update(saved)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return settings


def answer(message: str) -> str:
    text = message.strip()
    if not text:
        return "Écris une demande pour EURO AI."

    config = load_json("config.json", {"name": "EURO AI"})
    settings = load_owner_settings()
    blocked = [str(x).strip().lower() for x in settings.get("blocked_categories", [])]
    for term in blocked:
        if term and term in text.lower():
            return "Cette demande correspond à une catégorie bloquée dans tes réglages."

    instructions = settings.get("owner_instructions", [])
    custom_rules = settings.get("custom_rules", [])
    language = settings.get("language", config.get("language", "fr"))
    system_prompt = (
        f"Tu es {config.get('name', 'EURO AI')}, un assistant personnel polyvalent.\n"
        f"Langue préférée : {language}.\n"
        "Réponds de manière utile, précise et honnête. Si tu ne sais pas, dis-le. "
        "N'invente jamais l'exécution d'une action ou l'accès à un service. "
        "Tu peux expliquer et écrire du code, mais ne prétends pas avoir exécuté du code "
        "ou modifié un dépôt sans résultat vérifiable d'un outil.\n"
        "Instructions du propriétaire :\n- " + "\n- ".join(map(str, instructions)) +
        "\nRègles personnalisées du propriétaire :\n- " + "\n- ".join(map(str, custom_rules))
    )
    return chat_completion(system_prompt, text)


if __name__ == "__main__":
    import sys
    try:
        print(answer(" ".join(sys.argv[1:])))
    except RuntimeError as exc:
        raise SystemExit(str(exc))
