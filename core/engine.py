import json
from pathlib import Path

from core.brain import chat_completion, chat_completion_stream

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


def build_prompt_and_message(message: str):
    text = message.strip()
    if not text:
        return None, "Écris une demande pour EURO AI."

    config = load_json("config.json", {"name": "EURO AI"})
    settings = load_owner_settings()
    blocked = [str(x).strip().lower() for x in settings.get("blocked_categories", [])]
    for term in blocked:
        if term and term in text.lower():
            return None, "Cette demande correspond à une catégorie bloquée dans tes réglages."

    instructions = settings.get("owner_instructions", [])
    custom_rules = settings.get("custom_rules", [])
    language = settings.get("language", config.get("language", "fr"))
    system_prompt = (
        f"Tu es {config.get('name', 'EURO AI')}, un assistant personnel polyvalent.\\n"
        f"Langue préférée : {language}.\\n"
        "Réponds de manière utile, précise et honnête. Pour une demande simple, "
        "privilégie une réponse courte de 3 à 6 phrases. "
        "N'invente jamais l'exécution d'une action ou l'accès à un service. "
        "Tu peux expliquer et écrire du code, mais ne prétends pas avoir exécuté du code "
        "ou modifié un dépôt sans résultat vérifiable d'un outil.\\n"
        "Instructions du propriétaire :\\n- " + "\\n- ".join(map(str, instructions)) +
        "\\nRègles personnalisées du propriétaire :\\n- " + "\\n- ".join(map(str, custom_rules))
    )
    return system_prompt, text


def answer_stream(message: str):
    system_prompt, text = build_prompt_and_message(message)
    if system_prompt is None:
        yield text
        return
    yield from chat_completion_stream(system_prompt, text)


def answer(message: str) -> str:
    return "".join(answer_stream(message))


if __name__ == "__main__":
    import sys
    try:
        print("EURO AI : ", end="", flush=True)
        for chunk in answer_stream(" ".join(sys.argv[1:])):
            print(chunk, end="", flush=True)
        print()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
