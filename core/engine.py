import json
from pathlib import Path

from core.brain import chat_completion_stream
from core.logic import analyze

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

    analysis = analyze(text)
    instructions = settings.get("owner_instructions", [])
    custom_rules = settings.get("custom_rules", [])
    language = settings.get("language", config.get("language", "fr"))
    system_prompt = (
        f"Tu es {config.get('name', 'EURO AI')}, un agent IA personnel, proactif et polyvalent.\n"
        f"Langue préférée : {language}.\n"
        "Tu dois comprendre l'objectif réel, raisonner avec méthode et prendre des initiatives utiles. "
        "Pour une tâche importante, organise ton travail en étapes et indique la prochaine action concrète. "
        "N'attends pas que le propriétaire découvre lui-même les problèmes : signale les risques, "
        "améliorations et opportunités pertinentes. Ne pose une question que si une information "
        "manquante empêche réellement d'avancer. Sois direct pour les demandes simples. "
        "Ne prétends jamais avoir exécuté une action ou utilisé un outil sans résultat vérifiable. "
        "Les outils et intégrations non connectés ne sont pas disponibles : propose leur activation "
        "ou une méthode réalisable au lieu de simuler leur usage.\n\n"
        "Confidentialité : traite localement par défaut. Ne révèle pas de secrets, clés, jetons "
        "ou données privées. N'envoie pas de données privées à un service externe sans accord. "
        "Respecte les choix et règles personnelles du propriétaire.\n\n"
        "ANALYSE EURO LOGIC :\n" + analysis.prompt_context() +
        "\n\nInstructions du propriétaire :\n- " + "\n- ".join(map(str, instructions)) +
        "\nRègles personnalisées du propriétaire :\n- " + "\n- ".join(map(str, custom_rules))
    )
    return system_prompt, text, analysis


def answer_stream(message: str):
    prepared = build_prompt_and_message(message)
    if len(prepared) == 2:
        system_prompt, text = prepared
        if system_prompt is None:
            yield text
            return
        analysis = analyze(text)
    else:
        system_prompt, text, analysis = prepared
    yield from chat_completion_stream(system_prompt, text, max_tokens=analysis.max_tokens)


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
