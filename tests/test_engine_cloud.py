import unittest
from unittest.mock import patch

from core.engine import build_prompt_and_message


class EuroCloudCommandTests(unittest.TestCase):
    def test_cloudflare_status_is_local_and_does_not_call_model(self):
        prompt, answer = build_prompt_and_message("cloudflare status")
        self.assertIsNone(prompt)
        self.assertIn("lecture seule installé", answer)
        self.assertIn("Aucune requête réseau", answer)

    @patch("core.engine.run_readonly_command", return_value="Workers Cloudflare (1)\n- euro-ai")
    def test_cloudflare_workers_routes_to_readonly_client(self, mocked):
        prompt, answer = build_prompt_and_message("cloudflare workers")
        self.assertIsNone(prompt)
        self.assertIn("euro-ai", answer)
        mocked.assert_called_once_with("workers")


if __name__ == "__main__":
    unittest.main()
