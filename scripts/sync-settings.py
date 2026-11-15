"""Synchronise les réglages du propriétaire depuis EURO AI Cloudflare vers Termux."""

import getpass
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://euro-ai.arteuro07.workers.dev/api/settings"
EMAIL = "arteuro07@gmail.com"


def main():
    token = getpass.getpass("Code secret EURO AI (saisie masquée) : ").strip()
    if not token:
        raise SystemExit("Aucun code secret fourni.")
    request = Request(
        API,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "X-Owner-Email": EMAIL,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(f"Synchronisation impossible : {exc}") from exc

    settings = payload.get("settings")
    if not isinstance(settings, dict):
        raise SystemExit("Réponse invalide : réglages absents.")
    destination = Path.home() / ".config" / "euro-ai" / "owner-settings.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    print(f"Réglages synchronisés : {destination}")
    print("Le code secret n'a pas été enregistré.")


if __name__ == "__main__":
    main()
