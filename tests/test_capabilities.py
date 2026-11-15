import json
import tempfile
import unittest
from pathlib import Path

from core.capabilities import capability_context, load_capabilities, render_capabilities


class EuroCapabilitiesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "registry.json"
        self.path.write_text(json.dumps({
            "version": "test",
            "modules": [
                {"id": "brain", "name": "EURO BRAIN", "availability": "operational", "current_state": "Local model active."},
                {"id": "cloud", "name": "EURO CLOUD", "availability": "partial", "current_state": "Worker exists; integration pending."},
                {"id": "scout", "name": "SCOUT", "availability": "planned", "current_state": "Not connected."}
            ]
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_registry_states_are_loaded(self):
        data = load_capabilities(self.path)
        self.assertEqual([m["availability"] for m in data["modules"]], ["operational", "partial", "planned"])

    def test_unknown_state_defaults_to_planned(self):
        self.path.write_text(json.dumps({"modules": [{"id": "x", "availability": "unknown"}]}), encoding="utf-8")
        self.assertEqual(load_capabilities(self.path)["modules"][0]["availability"], "planned")

    def test_context_warns_against_overclaiming(self):
        context = capability_context(load_capabilities(self.path))
        self.assertIn("PARTIEL", context)
        self.assertIn("À CONSTRUIRE", context)
        self.assertIn("Ne prétends jamais", context)

    def test_report_groups_capabilities(self):
        report = render_capabilities(load_capabilities(self.path))
        self.assertIn("OPÉRATIONNEL", report)
        self.assertIn("PARTIEL", report)
        self.assertIn("À CONSTRUIRE", report)


if __name__ == "__main__":
    unittest.main()
