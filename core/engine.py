import json
from pathlib import Path

from core.brain import chat_completion_stream
from core.capabilities import capability_context, render_capabilities
from core.logic import analyze
from core.memory import format_memories, forget, remember, retrieve

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

    lower = text.lower()
    if lower in ("capacités", "capacites", "mes capacités", "mes capacites", "que sais-tu faire", "quelles sont tes capacités", "quelles sont tes capacites"):
        return None, render_capabilities()
    if lower.startswith(("mémorise :", "memorise :", "souviens-toi :")):
        content = text.split(":", 1)[1].strip()
        if not content:
            return None, "Indique ce que tu veux que je mémorise."
        result = remember(content, source="owner")
        return None, f"Mémoire enregistrée ✓ ({result['kind']})"
    if lower.startswith(("oublie :", "supprime de ma mémoire :")):
        query = text.split(":", 1)[1].strip()
        count = forget(query)
        return None, f"{count} mémoire(s) supprimée(s)."

    config = load_json("config.json", {"name": "EURO AI"})
    settings = load_owner_settings()
    blocked = [str(x).strip().lower() for x in settings.get("blocked_categories", [])]
    for term in blocked:
        if term and term in text.lower():
            return None, "Cette demande correspond à une catégorie bloquée dans tes réglages."

    analysis = analyze(text)
    memories = format_memories(retrieve(text))
    instructions = settings.get("owner_instructions", [])
    custom_rules = settings.get("custom_rules", [])
    language = settings.get("language", config.get("language", "fr"))
    brain = config.get("brain", {})
    identity_context = (
        "Faits vérifiés sur ta propre architecture (source : config.json du dépôt) :\n"
        f"- Ton cerveau IA local tourne sur le téléphone Android du propriétaire, dans Termux, via llama.cpp.\n"
        f"- Modèle local configuré : {brain.get('model', 'non renseigné')} ({brain.get('size', 'taille inconnue')}, {brain.get('quantization', 'quantification inconnue')}).\n"
        f"- Adresse API locale : {brain.get('local_api', 'non renseignée')}.\n"
        f"- Les calculs et tâches lourdes sont prévus sur : {brain.get('heavy_compute', 'non renseigné')}.\n"
        "Le panneau Cloudflare sert de passerelle/interface ; il n'héberge pas le modèle local.\n"
        "Utilise ces faits pour répondre aux questions sur EURO AI. Ne dis pas que tu ignores ta configuration lorsqu'elle est indiquée ici.\n\n"
    )
    system_prompt = (
        f"Tu es {config.get('name', 'EURO AI')}, un agent IA personnel, proactif et polyvalent.\n"
        f"Langue préférée : {language}.\n"
        + identity_context +
        capability_context() + "\\n\\n" +
        "Comprends l'objectif réel, raisonne avec méthode et prends des initiatives utiles. "
        "Pour une tâche importante, organise le travail en étapes et indique la prochaine action concrète. "
        "Signale les risques, améliorations et opportunités pertinentes. Ne pose une question que si "
        "une information manquante empêche réellement d'avancer. Sois direct pour les demandes simples. "
        "Ne prétends jamais avoir exécuté une action ou utilisé un outil sans résultat vérifiable. "
        "Les outils non connectés ne sont pas disponibles : propose une méthode réalisable au lieu de simuler leur usage.\n\n"
        "Confidentialité : traite localement par défaut. Ne révèle pas de secrets, clés ou jetons. "
        "N'envoie pas de données privées à un service externe sans accord. Respecte les choix du propriétaire.\n\n"
        + analysis.prompt_context() + "\n\n" + memories +
        "\n\nInstructions du propriétaire :\n- " + "\n- ".join(map(str, instructions)) +
        "\nRègles personnalisées :\n- " + "\n- ".join(map(str, custom_rules))
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
