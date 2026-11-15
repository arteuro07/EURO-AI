import json
import os
import unittest
from unittest.mock import patch

from core.cloudflare import (
    CloudflareConfigError,
    CloudflareReadOnlyClient,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class EuroCloudTests(unittest.TestCase):
    def setUp(self):
        self.client = CloudflareReadOnlyClient(
            token="test-token",
            account_id="a" * 32,
        )

    @patch("core.cloudflare.urlopen")
    def test_lists_workers_with_get(self, mocked):
        mocked.return_value = FakeResponse({
            "success": True,
            "result": [{"id": "euro-ai", "created_on": "2026-01-01"}],
        })
        self.assertEqual(self.client.list_workers()[0]["id"], "euro-ai")
        request = mocked.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("/workers/scripts", request.full_url)

    @patch("core.cloudflare.urlopen")
    def test_lists_d1_databases(self, mocked):
        mocked.return_value = FakeResponse({
            "success": True,
            "result": [{"name": "euro-ai-db"}],
            "result_info": {"total_pages": 1},
        })
        self.assertEqual(self.client.list_d1_databases()[0]["name"], "euro-ai-db")

    def test_rejects_invalid_account_id(self):
        with self.assertRaises(CloudflareConfigError):
            CloudflareReadOnlyClient(token="x", account_id="not-an-account-id")

    def test_rejects_unapproved_endpoint(self):
        with self.assertRaises(CloudflareConfigError):
            self.client._get(f"/accounts/{self.client.account_id}/workers/scripts/worker/delete")

    def test_missing_environment_is_reported(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CloudflareConfigError):
                CloudflareReadOnlyClient()


if __name__ == "__main__":
    unittest.main()
