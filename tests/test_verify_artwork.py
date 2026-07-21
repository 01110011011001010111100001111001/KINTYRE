from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from commission_artwork import CommissionTarget, MusicAssistantError
from verify_artwork import run_verification, verify_target


class FakeClient:
    def __init__(self, detail):
        self.detail = detail
        self.calls = []

    def command(self, command, args=None):
        self.calls.append((command, args or {}))
        if command.endswith("library_items"):
            if (args or {}).get("offset", 0):
                return []
            return [{"item_id": "1", "provider": "library", "name": "Album"}]
        if isinstance(self.detail, Exception):
            raise self.detail
        return self.detail


class TestArtworkVerification(unittest.TestCase):
    def setUp(self):
        self.target = CommissionTarget("albums", "1", "library", "Album")

    def test_missing_when_images_are_null(self):
        client = FakeClient({"metadata": {"images": None}})
        record = verify_target(client, self.target)
        self.assertEqual(record.status, "MISSING")
        self.assertEqual(record.artwork_count, 0)
        command, args = client.calls[-1]
        self.assertEqual(command, "music/albums/get_album")
        self.assertEqual(args["provider_instance_id_or_domain"], "library")
        self.assertFalse(args["add_to_library"])

    def test_present_when_thumb_exists(self):
        client = FakeClient(
            {
                "metadata": {
                    "images": [
                        {
                            "type": "thumb",
                            "path": "album/file.mp3",
                            "provider": "filesystem_local--abc",
                            "proxy_id": "123",
                        },
                        {
                            "type": "discart",
                            "path": "https://example.invalid/disc.png",
                            "provider": "theaudiodb",
                        },
                    ]
                }
            }
        )
        record = verify_target(client, self.target)
        self.assertEqual(record.status, "PRESENT")
        self.assertEqual(record.artwork_count, 2)
        self.assertEqual(record.thumb_count, 1)
        self.assertEqual(record.image_types, ("discart", "thumb"))

    def test_non_primary_only_when_images_have_no_thumb(self):
        client = FakeClient(
            {"metadata": {"images": [{"type": "discart", "provider": "theaudiodb"}]}}
        )
        record = verify_target(client, self.target)
        self.assertEqual(record.status, "NON_PRIMARY_ONLY")

    def test_api_failure_is_recorded(self):
        client = FakeClient(MusicAssistantError("failed"))
        record = verify_target(client, self.target)
        self.assertEqual(record.status, "ERROR")
        self.assertEqual(record.reason, "failed")

    def test_report_states_evidence_boundary(self):
        client = FakeClient({"metadata": {"images": None}})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            report = run_verification(
                client,
                media_types=("albums",),
                page_size=250,
                limit=1,
                report_path=path,
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["counts"], {"MISSING": 1})
            self.assertEqual(saved["evidence_boundary"]["retrievability"], "NOT_TESTED")
            self.assertEqual(saved["evidence_boundary"]["image_validity"], "NOT_TESTED")


if __name__ == "__main__":
    unittest.main()
