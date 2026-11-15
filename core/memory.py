"""Mémoire persistante locale EURO AI (SQLite, sans transfert réseau)."""
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(os.environ.get(
    "EURO_AI_MEMORY_DB",
    str(Path.home() / ".local" / "share" / "euro-ai" / "memory.sqlite3")
))
KINDS = {"episodic", "semantic", "procedural", "project", "preference"}


def _connect(db_path=None):
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL NOT NULL DEFAULT 1.0,
            tags_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status, kind)")
    return conn


def remember(content, kind="semantic", key=None, source="owner", confidence=1.0, tags=None, db_path=None):
    content = str(content).strip()
    if not content:
        raise ValueError("Le contenu de la mémoire est vide.")
    if kind not in KINDS:
        raise ValueError("Type mémoire invalide: " + ", ".join(sorted(KINDS)))
    if not 0 <= float(confidence) <= 1:
        raise ValueError("La confiance doit être comprise entre 0 et 1.")
    key = (key or content[:100]).strip()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    try:
        with conn:
            conn.execute(
                "UPDATE memories SET status='superseded', updated_at=? "
                "WHERE kind=? AND memory_key=? AND status='active'",
                (now, kind, key)
            )
            conn.execute(
                "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (str(uuid.uuid4()), kind, key, content, source, float(confidence),
                 json.dumps(tags or [], ensure_ascii=False), now, now)
            )
    finally:
        conn.close()
    return {"status": "saved", "kind": kind, "key": key}


def retrieve(query, limit=6, db_path=None):
    words = set(re.findall(r"[a-zA-ZÀ-ÿ0-9_]{3,}", query.lower()))
    if not words:
        return []
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM memories WHERE status='active' ORDER BY updated_at DESC"
        ).fetchall()
    finally:
        conn.close()
    ranked = []
    for row in rows:
        haystack = (row["memory_key"] + " " + row["content"] + " " +
                    " ".join(json.loads(row["tags_json"]))).lower()
        terms = set(re.findall(r"[a-zA-ZÀ-ÿ0-9_]{3,}", haystack))
        overlap = len(words & terms)
        if overlap:
            ranked.append((overlap / max(1, len(words)), row))
    ranked.sort(key=lambda item: (item[0], item[1]["updated_at"]), reverse=True)
    return [{
        "id": row["id"], "kind": row["kind"], "key": row["memory_key"],
        "content": row["content"], "confidence": row["confidence"],
        "updated_at": row["updated_at"]
    } for score, row in ranked[:max(1, min(int(limit), 20))]]


def forget(query, db_path=None):
    terms = set(re.findall(r"[a-zA-ZÀ-ÿ0-9_]{3,}", query.lower()))
    if not terms:
        return 0
    conn = _connect(db_path)
    try:
        rows = conn.execute("SELECT id, memory_key, content FROM memories WHERE status='active'").fetchall()
        ids = []
        for row in rows:
            haystack = (row["memory_key"] + " " + row["content"]).lower()
            if all(term in haystack for term in terms):
                ids.append(row["id"])
        with conn:
            conn.executemany("DELETE FROM memories WHERE id=?", [(item,) for item in ids])
        return len(ids)
    finally:
        conn.close()


def format_memories(items):
    if not items:
        return ""
    lines = ["MÉMOIRE PERSISTANTE PERTINENTE (faits enregistrés, à utiliser si utiles) :"]
    for item in items:
        lines.append(f"- [{item['kind']}] {item['content']}")
    return "\n".join(lines)
