import unittest

from core.engine import build_prompt_and_message


class EuroEngineCapabilityAnswerTests(unittest.TestCase):
    def test_cloudflare_access_question_gets_accurate_status(self):
        prompt, answer = build_prompt_and_message(
            "Peux-tu gérer directement mon Cloudflare et modifier mes Workers ?"
        )
        self.assertIsNone(prompt)
        self.assertIn("euro-ai.arteuro07.workers.dev", answer)
        self.assertIn("euro-ai-db", answer)
        self.assertIn("client EURO CLOUD en lecture seule", answer)
        self.assertIn("pas encore authentifié", answer)
        self.assertIn("token API", answer)
        self.assertIn("Account ID", answer)
        self.assertIn("ne peux donc pas modifier ou déployer", answer)


if __name__ == "__main__":
    unittest.main()