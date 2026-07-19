from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.commission_artwork import (
    CommissionTarget,
    MusicAssistantClient,
    iter_library_targets,
    run_commissioning,
    touch_target,
)


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def command(self, command, args=None):
        self.calls.append((command, args or {}))
        if command.endswith("library_items"):
            offset = (args or {}).get("offset", 0)
            if offset == 0:
                return [
                    {"item_id": "2", "provider": "library", "name": "Beta"},
                    {"item_id": "1", "provider": "library", "name": "Alpha"},
                ]
            return []
        return {"item_id": (args or {}).get("item_id")}


class TestArtworkCommissioning(unittest.TestCase):
    def test_library_targets_are_paginated_and_deduplicated(self):
        client = FakeClient()
        targets = list(iter_library_targets(client, "albums", page_size=2))
        self.assertEqual([target.item_id for target in targets], ["2", "1"])
        self.assertEqual(client.calls[1][1]["offset"], 2)

    def test_touch_uses_read_only_detail_command(self):
        client = FakeClient()
        touch_target(client, CommissionTarget("artists", "7", "library", "Artist"))
        command, args = client.calls[-1]
        self.assertEqual(command, "music/artists/get_artist")
        self.assertFalse(args["add_to_library"])

    def test_dry_run_writes_plan_without_touching_entities(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = run_commissioning(
                client,
                execute=False,
                media_types=("albums",),
                page_size=2,
                delay=0,
                report_path=root / "report.json",
                state_path=root / "state.json",
            )
            self.assertEqual(report["counts"], {"PLANNED": 2})
            self.assertFalse((root / "state.json").exists())
            self.assertEqual(len([call for call in client.calls if "get_album" in call[0]]), 0)

    def test_execute_persists_resume_state(self):
        client = FakeClient()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kwargs = dict(
                media_types=("albums",),
                page_size=2,
                delay=0,
                report_path=root / "report.json",
                state_path=root / "state.json",
            )
            first = run_commissioning(client, execute=True, **kwargs)
            second = run_commissioning(client, execute=True, **kwargs)
            self.assertEqual(first["counts"], {"TOUCHED": 2})
            self.assertEqual(second["counts"], {"SKIPPED_COMPLETED": 2})
            state = json.loads((root / "state.json").read_text())
            self.assertEqual(len(state["completed"]), 2)

    def test_http_client_sends_bearer_json_rpc(self):
        response = Mock()
        response.read.return_value = b'{"result":{"ok":true}}'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock(return_value=response)
        client = MusicAssistantClient("http://ma:8095", "secret", opener=opener)
        self.assertEqual(client.command("test/ping"), {"ok": True})
        request = opener.call_args.args[0]
        self.assertEqual(request.full_url, "http://ma:8095/api")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")


if __name__ == "__main__":
    unittest.main()
