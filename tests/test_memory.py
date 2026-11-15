import tempfile
import unittest
from pathlib import Path

from core.memory import forget, remember, retrieve


class EuroMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "memory.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_store_and_retrieve(self):
        remember("Le projet EURO AI utilise Termux et GitHub.", db_path=self.db)
        found = retrieve("Comment fonctionne le projet EURO AI ?", db_path=self.db)
        self.assertEqual(len(found), 1)
        self.assertIn("Termux", found[0]["content"])

    def test_update_preserves_old_version_as_superseded(self):
        remember("Le modèle est Qwen petit.", key="modèle", db_path=self.db)
        remember("Le modèle est Qwen amélioré.", key="modèle", db_path=self.db)
        found = retrieve("modèle Qwen", db_path=self.db)
        self.assertEqual(len(found), 1)
        self.assertIn("amélioré", found[0]["content"])

    def test_forget_removes_matching_memory(self):
        remember("Le projet secret alpha utilise SQLite.", db_path=self.db)
        self.assertEqual(forget("secret alpha", db_path=self.db), 1)
        self.assertEqual(retrieve("secret alpha", db_path=self.db), [])

    def test_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            remember("Test", kind="unknown", db_path=self.db)


if __name__ == "__main__":
    unittest.main()
