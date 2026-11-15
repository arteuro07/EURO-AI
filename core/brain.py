"""Client streaming pour le serveur local llama.cpp compatible OpenAI."""

import json
import os
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def chat_completion_stream(system_prompt: str, user_message: str, max_tokens: int = 220):
    base_url = os.environ.get("EURO_AI_LOCAL_API", "http://127.0.0.1:8080/v1").rstrip("/")
    payload = {
        "model": "EURO-AI-local",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.35,
        "top_p": 0.85,
        "max_tokens": max(32, min(int(max_tokens), 600)),
        "stream": True,
        "reasoning_effort": "none",
        "chat_template_kwargs": {"enable_thinking": False}
    }
    request = Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST"
    )
    received_text = False
    try:
        with urlopen(request, timeout=240) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_text = line[5:].strip()
                if data_text == "[DONE]":
                    break
                try:
                    data = json.loads(data_text)
                except json.JSONDecodeError:
                    continue
                choices = data.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                chunk = delta.get("content")
                if isinstance(chunk, str) and chunk:
                    received_text = True
                    yield chunk
        if not received_text:
            raise RuntimeError(
                "Réponse vide du modèle. Vérifie que le serveur a été redémarré "
                "avec --reasoning off."
            )
    except (URLError, HTTPError, TimeoutError, KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(
            "Impossible de joindre le cerveau local. Vérifie que le serveur tourne "
            "avec bash scripts/start-local-brain.sh.\n"
            f"Détail technique : {exc}"
        ) from exc


def chat_completion(system_prompt: str, user_message: str) -> str:
    return "".join(chat_completion_stream(system_prompt, user_message))
