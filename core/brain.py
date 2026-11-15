"""Client minimal pour le serveur local llama.cpp compatible OpenAI."""

import json
import os
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def chat_completion(system_prompt: str, user_message: str) -> str:
    base_url = os.environ.get("EURO_AI_LOCAL_API", "http://127.0.0.1:8080/v1").rstrip("/")
    payload = {
        "model": "EURO-AI-local",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.35,
        "top_p": 0.85,
        "max_tokens": 450,
        "stream": False,
        "reasoning_effort": "none",
        "chat_template_kwargs": {"enable_thinking": False}
    }
    request = Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urlopen(request, timeout=240) as response:
            data = json.loads(response.read().decode("utf-8"))
        message = data["choices"][0]["message"]
        answer = (message.get("content") or "").strip()
        if not answer:
            raise RuntimeError(
                "Réponse vide du modèle. "
                f"finish_reason={data['choices'][0].get('finish_reason')!r}; "
                f"reasoning_content_present={bool(message.get('reasoning_content'))}. "
                "Vérifie que le serveur a été redémarré avec --reasoning off."
            )
        return answer
    except (URLError, HTTPError, TimeoutError, KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(
            "Impossible de joindre le cerveau local. Vérifie que le serveur tourne "
            "avec bash scripts/start-local-brain.sh.\n"
            f"Détail technique : {exc}"
        ) from exc
