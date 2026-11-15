"""EURO CLOUD: client Cloudflare REST strictement en lecture seule (première version)."""

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.cloudflare.com/client/v4"
ACCOUNT_ID_RE = re.compile(r"^[a-f0-9]{32}$", re.I)


class CloudflareConfigError(RuntimeError):
    pass


class CloudflareAPIError(RuntimeError):
    pass


class CloudflareReadOnlyClient:
    """Expose uniquement des opérations GET explicitement autorisées."""

    def __init__(self, token=None, account_id=None, timeout=20):
        self.token = token or os.environ.get("CLOUDFLARE_API_TOKEN")
        self.account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        self.timeout = timeout
        if not self.token:
            raise CloudflareConfigError("Variable CLOUDFLARE_API_TOKEN absente.")
        if not self.account_id or not ACCOUNT_ID_RE.fullmatch(self.account_id):
            raise CloudflareConfigError("CLOUDFLARE_ACCOUNT_ID absent ou invalide (32 caractères hexadécimaux).")

    def _get(self, path, params=None):
        # Allowlist stricte : aucune méthode d'écriture n'existe dans ce client.
        allowed = {
            f"/accounts/{self.account_id}/workers/scripts",
            f"/accounts/{self.account_id}/d1/database",
        }
        if path not in allowed:
            raise CloudflareConfigError("Endpoint non autorisé par le client en lecture seule.")
        query = "?" + urlencode(params) if params else ""
        request = Request(
            API_BASE + path + query,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/json",
                "User-Agent": "EURO-AI-Cloud-ReadOnly/0.1",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise CloudflareAPIError(f"Cloudflare a répondu HTTP {exc.code}. Vérifie le token et ses permissions.") from None
        except URLError:
            raise CloudflareAPIError("Connexion Cloudflare impossible. Vérifie Internet et réessaie.") from None
        except (TimeoutError, OSError):
            raise CloudflareAPIError("Délai dépassé ou erreur réseau pendant l'accès à Cloudflare.") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise CloudflareAPIError("Réponse Cloudflare illisible.") from None
        if not isinstance(payload, dict) or not payload.get("success"):
            errors = payload.get("errors", []) if isinstance(payload, dict) else []
            message = errors[0].get("message", "Erreur API inconnue") if errors and isinstance(errors[0], dict) else "Erreur API inconnue"
            raise CloudflareAPIError("Échec API Cloudflare : " + str(message)[:240])
        return payload

    def list_workers(self):
        path = f"/accounts/{self.account_id}/workers/scripts"
        payload = self._get(path)
        return payload.get("result", [])

    def list_d1_databases(self):
        path = f"/accounts/{self.account_id}/d1/database"
        items = []
        page = 1
        while True:
            payload = self._get(path, {"page": page, "per_page": 100})
            items.extend(payload.get("result", []))
            info = payload.get("result_info", {})
            total_pages = info.get("total_pages", page)
            if page >= total_pages:
                break
            page += 1
        return items


def _print_items(title, items, name_key):
    print(f"{title} ({len(items)})")
    for item in items:
        name = item.get(name_key, "nom inconnu")
        print("- " + str(name))


def run_readonly_command(command):
    """Retourne le résultat texte d'une commande EURO CLOUD autorisée."""
    if command == "status":
        return (
            "EURO CLOUD : client lecture seule installé.\n"
            f"Token : {'présent' if os.environ.get('CLOUDFLARE_API_TOKEN') else 'absent'}\n"
            f"Account ID : {'présent' if os.environ.get('CLOUDFLARE_ACCOUNT_ID') else 'absent'}\n"
            "Aucune requête réseau effectuée."
        )
    if command not in ("workers", "d1"):
        return "Commande EURO CLOUD inconnue. Commandes : status, workers, d1."
    try:
        client = CloudflareReadOnlyClient()
        if command == "workers":
            items = client.list_workers()
            lines = [f"Workers Cloudflare ({len(items)})"]
            lines.extend("- " + str(item.get("id", "nom inconnu")) for item in items)
        else:
            items = client.list_d1_databases()
            lines = [f"Bases D1 Cloudflare ({len(items)})"]
            lines.extend("- " + str(item.get("name", "nom inconnu")) for item in items)
        return "\n".join(lines)
    except (CloudflareConfigError, CloudflareAPIError) as exc:
        return "EURO CLOUD : " + str(exc)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "help"
    if command == "help":
        print("EURO CLOUD — lecture seule")
        print("Commandes : status | workers | d1")
        print("Configuration : CLOUDFLARE_API_TOKEN et CLOUDFLARE_ACCOUNT_ID")
        return 0
    if command == "status":
        print("EURO CLOUD : client lecture seule installé.")
        print("Token :", "présent" if os.environ.get("CLOUDFLARE_API_TOKEN") else "absent")
        print("Account ID :", "présent" if os.environ.get("CLOUDFLARE_ACCOUNT_ID") else "absent")
        print("Aucune requête réseau effectuée.")
        return 0
    if command not in ("workers", "d1"):
        print("Commande inconnue. Utilise : python -m core.cloudflare help")
        return 2
    try:
        client = CloudflareReadOnlyClient()
        if command == "workers":
            _print_items("Workers Cloudflare", client.list_workers(), "id")
        else:
            _print_items("Bases D1 Cloudflare", client.list_d1_databases(), "name")
        return 0
    except (CloudflareConfigError, CloudflareAPIError) as exc:
        print("EURO CLOUD :", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
