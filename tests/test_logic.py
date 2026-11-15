import unittest

from core.logic import analyze


class EuroLogicTests(unittest.TestCase):
    def test_simple_question_gets_small_budget(self):
        result = analyze("Dis bonjour.")
        self.assertEqual(result.complexity, "simple")
        self.assertLessEqual(result.max_tokens, 120)

    def test_development_request_is_classified(self):
        result = analyze("Corrige ce bug Python dans mon application.")
        self.assertEqual(result.intent, "développement")
        self.assertIn("tester le résultat", result.steps)

    def test_build_request_is_proactive(self):
        result = analyze("Construis un système complet et automatise le projet.")
        self.assertEqual(result.intent, "construction")
        self.assertTrue(result.initiative)

    def test_destructive_action_is_flagged(self):
        result = analyze("Supprime ce dépôt.")
        self.assertTrue(result.confirmation_recommended)

    def test_privacy_note_is_always_present(self):
        self.assertIn("Confidentialité", analyze("Bonjour").privacy_note)


if __name__ == "__main__":
    unittest.main()
