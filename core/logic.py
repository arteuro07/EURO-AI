"""EURO LOGIC: analyseur local déterministe pour orienter EURO AI.

Ce module ne remplace pas le modèle linguistique : il prépare une lecture structurée
de la demande, estime l'effort nécessaire et aide l'agent à être proactif.
"""
from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class Analysis:
    intent: str
    complexity: str
    score: int
    max_tokens: int
    steps: tuple[str, ...]
    initiative: str
    confirmation_recommended: bool
    privacy_note: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["steps"] = list(self.steps)
        return data

    def prompt_context(self) -> str:
        lines = [
            f"Intention détectée : {self.intent}.",
            f"Complexité estimée : {self.complexity} (score {self.score}/10).",
            f"Budget de réponse : environ {self.max_tokens} tokens.",
        ]
        if self.steps:
            lines.append("Approche conseillée : " + " ; ".join(self.steps) + ".")
        if self.initiative:
            lines.append("Initiative utile : " + self.initiative)
        if self.confirmation_recommended:
            lines.append(
                "L'action semble externe, destructive ou engageante : prépare une "
                "proposition claire et attends l'accord du propriétaire avant son exécution."
            )
        if self.privacy_note:
            lines.append(self.privacy_note)
        return "\n".join(lines)


def analyze(message: str) -> Analysis:
    text = message.strip()
    lower = text.lower()
    words = re.findall(r"\w+", lower, flags=re.UNICODE)
    score = 1
    if len(words) > 18:
        score += 1
    if len(words) > 45:
        score += 1
    if re.search(r"\b(code|python|javascript|sql|bug|erreur|compiler|débog|architecture|api)\b", lower):
        score += 2
    if re.search(r"\b(crée|construis|développe|automatise|analyse|compare|planifie|intègre|corrige)\b", lower):
        score += 2
    if re.search(r"\b(étape|ensuite|puis|plusieurs|workflow|projet|système|complet)\b", lower):
        score += 1
    if lower.count("?") > 1 or re.search(r"\b(et aussi|en plus|à la fois|plusieurs)\b", lower):
        score += 1
    score = min(score, 10)

    if re.search(r"\b(supprime|efface|détruis|déploie|publie|envoie|achète|paie|transfère|modifie dns)\b", lower):
        intent = "action"
    elif re.search(r"\b(code|python|javascript|programme|bug|erreur|compiler|débog|api|application)\b", lower):
        intent = "développement"
    elif re.search(r"\b(plan|projet|organise|construis|crée|automatise|architecture)\b", lower):
        intent = "construction"
    elif re.search(r"\b(compare|recherche|trouve|opportunité|marché|vérifie)\b", lower):
        intent = "recherche"
    elif re.search(r"\b(explique|comment|pourquoi|définis|c'est quoi)\b", lower):
        intent = "explication"
    else:
        intent = "conversation"

    complexity = "simple" if score <= 2 else "intermédiaire" if score <= 5 else "complexe"
    max_tokens = 120 if complexity == "simple" else 220 if complexity == "intermédiaire" else 360

    if intent == "développement":
        steps = ("comprendre le résultat attendu", "examiner le code et les dépendances", "proposer une modification", "tester le résultat")
        initiative = "signaler un défaut connexe ou une amélioration concrète si elle est utile."
    elif intent == "construction":
        steps = ("clarifier l'objectif", "concevoir les composants", "construire par étapes", "valider chaque étape")
        initiative = "identifier spontanément la prochaine étape qui débloque le projet."
    elif intent == "recherche":
        steps = ("définir les critères", "collecter les informations", "recouper les éléments", "présenter les conclusions")
        initiative = "proposer la suite la plus utile à partir des résultats."
    elif intent == "action":
        steps = ("identifier précisément l'action", "évaluer ses effets", "présenter la proposition", "exécuter après accord si nécessaire")
        initiative = "préparer une action concrète et expliquer son résultat attendu."
    else:
        steps = ("comprendre l'intention", "répondre directement", "ajouter une précision utile si nécessaire")
        initiative = ""

    confirmation = intent == "action"
    privacy_note = (
        "Confidentialité : privilégie le traitement local ; ne révèle jamais les secrets, "
        "jetons ou données privées et ne les transmets pas à un service externe sans accord."
    )
    return Analysis(
        intent=intent,
        complexity=complexity,
        score=score,
        max_tokens=max_tokens,
        steps=steps,
        initiative=initiative,
        confirmation_recommended=confirmation,
        privacy_note=privacy_note,
    )
