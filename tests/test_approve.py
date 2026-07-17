from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import approve


class TestApprovalStateModel(unittest.TestCase):
    def test_legacy_action_defaults_to_pending(self) -> None:
        action = {"id": "action-001"}

        self.assertEqual(
            approve.approval_state(action),
            "PENDING",
        )

    def test_state_is_normalized_to_uppercase(self) -> None:
        action = {
            "id": "action-001",
            "approval": "approved",
        }

        self.assertEqual(
            approve.approval_state(action),
            "APPROVED",
        )

    def test_invalid_state_is_rejected(self) -> None:
        action = {
            "id": "action-001",
            "approval": "UNKNOWN",
        }

        with self.assertRaisesRegex(
            ValueError,
            "Invalid approval state",
        ):
            approve.approval_state(action)

    def test_normalize_plan_preserves_existing_decision(self) -> None:
        plan = {
            "actions": [
                {
                    "id": "action-001",
                    "approval": "REJECTED",
                    "decision_at": "2026-07-17T10:00:00Z",
                },
                {
                    "id": "action-002",
                },
            ]
        }

        normalized = approve.normalize_plan(plan)

        self.assertEqual(
            normalized["actions"][0]["approval"],
            "REJECTED",
        )
        self.assertEqual(
            normalized["actions"][0]["decision_at"],
            "2026-07-17T10:00:00Z",
        )
        self.assertEqual(
            normalized["actions"][1]["approval"],
            "PENDING",
        )
        self.assertIsNone(
            normalized["actions"][1]["decision_at"],
        )

    def test_normalize_plan_rejects_missing_actions_list(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "no valid actions list",
        ):
            approve.normalize_plan({})


class TestApprovalPersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)

        self.approval_plan = root / "approval-plan.json"
        self.approval_summary = root / "approval-summary.json"
        self.approved_actions = root / "approved-actions.json"

        self.path_patchers = [
            patch.object(
                approve,
                "APPROVAL_PLAN",
                self.approval_plan,
            ),
            patch.object(
                approve,
                "APPROVAL_SUMMARY",
                self.approval_summary,
            ),
            patch.object(
                approve,
                "APPROVED_ACTIONS",
                self.approved_actions,
            ),
        ]

        for patcher in self.path_patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.addCleanup(self.temporary_directory.cleanup)

    def write_plan(self, actions: list[dict]) -> None:
        payload = {
            "schema_version": "1.0",
            "generated_at": "2026-07-17T10:00:00Z",
            "actions": actions,
        }

        self.approval_plan.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def read_json(self, path: Path) -> dict:
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def test_approve_exports_only_approved_actions(self) -> None:
        self.write_plan(
            [
                {"id": "action-001"},
                {"id": "action-002"},
            ]
        )

        approve.set_decision(
            "action-001",
            "APPROVED",
        )

        plan = self.read_json(self.approval_plan)
        exported = self.read_json(self.approved_actions)

        states = {
            action["id"]: action["approval"]
            for action in plan["actions"]
        }

        self.assertEqual(
            states,
            {
                "action-001": "APPROVED",
                "action-002": "PENDING",
            },
        )
        self.assertEqual(
            exported["action_count"],
            1,
        )
        self.assertEqual(
            exported["actions"][0]["id"],
            "action-001",
        )

    def test_reset_returns_action_to_pending(self) -> None:
        self.write_plan(
            [
                {
                    "id": "action-001",
                    "approval": "APPROVED",
                    "decision_at": "2026-07-17T10:00:00Z",
                }
            ]
        )

        approve.set_decision(
            "action-001",
            "PENDING",
        )

        plan = self.read_json(self.approval_plan)
        action = plan["actions"][0]

        self.assertEqual(
            action["approval"],
            "PENDING",
        )
        self.assertIsNone(
            action["decision_at"],
        )

    def test_repeated_decision_is_idempotent(self) -> None:
        original_timestamp = "2026-07-17T10:00:00Z"

        self.write_plan(
            [
                {
                    "id": "action-001",
                    "approval": "APPROVED",
                    "decision_at": original_timestamp,
                }
            ]
        )

        approve.set_decision(
            "action-001",
            "APPROVED",
        )

        plan = self.read_json(self.approval_plan)
        action = plan["actions"][0]

        self.assertEqual(
            action["approval"],
            "APPROVED",
        )
        self.assertEqual(
            action["decision_at"],
            original_timestamp,
        )

    def test_summary_contains_all_four_states(self) -> None:
        plan = {
            "actions": [
                {"id": "1", "approval": "PENDING"},
                {"id": "2", "approval": "APPROVED"},
                {"id": "3", "approval": "REJECTED"},
                {"id": "4", "approval": "DEFERRED"},
            ]
        }

        summary = approve.build_summary(plan)

        self.assertEqual(
            summary["approval_counts"],
            {
                "PENDING": 1,
                "APPROVED": 1,
                "REJECTED": 1,
                "DEFERRED": 1,
            },
        )


class TestApprovalFilters(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = [
            {
                "id": "ACT-000001",
                "action": "ADD_ALBUMARTIST",
                "album_id": "ALB-F73342DA",
                "approval": "APPROVED",
                "confidence": "HIGH",
                "folder": "/data/Music/CLASSICAL/Holst",
                "library": "CLASSICAL",
                "proposed_value": "Andrew Davis",
                "reason": "Missing AlbumArtist",
                "risk": "LOW",
            },
            {
                "id": "ACT-000002",
                "action": "ADD_ALBUMARTIST",
                "album_id": "ALB-3967DE3F",
                "approval": "PENDING",
                "confidence": "HIGH",
                "folder": "/data/Music/CONTEMPORARY/A-Ha/1985",
                "library": "CONTEMPORARY",
                "proposed_value": "A-Ha",
                "reason": "Missing AlbumArtist",
                "risk": "LOW",
            },
            {
                "id": "ACT-000003",
                "action": "ADD_ALBUMARTIST",
                "album_id": "ALB-00000003",
                "approval": "DEFERRED",
                "confidence": "HIGH",
                "folder": "/data/Music/CONTEMPORARY/The Beatles",
                "library": "CONTEMPORARY",
                "proposed_value": "The Beatles",
                "reason": "Missing AlbumArtist",
                "risk": "LOW",
            },
        ]

    def test_exact_filter_is_case_insensitive(self) -> None:
        matches = approve.filter_actions(
            self.actions,
            [("library", "eq", "classical")],
        )
        self.assertEqual(
            [action["id"] for action in matches],
            ["ACT-000001"],
        )

    def test_contains_filter_is_case_insensitive(self) -> None:
        matches = approve.filter_actions(
            self.actions,
            [("folder", "contains", "beatles")],
        )
        self.assertEqual(
            [action["id"] for action in matches],
            ["ACT-000003"],
        )

    def test_multiple_filters_use_logical_and(self) -> None:
        matches = approve.filter_actions(
            self.actions,
            [
                ("library", "eq", "CONTEMPORARY"),
                ("approval", "eq", "PENDING"),
            ],
        )
        self.assertEqual(
            [action["id"] for action in matches],
            ["ACT-000002"],
        )

    def test_empty_filters_preserve_order(self) -> None:
        matches = approve.filter_actions(self.actions, [])
        self.assertEqual(
            [action["id"] for action in matches],
            ["ACT-000001", "ACT-000002", "ACT-000003"],
        )

    def test_no_match_returns_empty_list(self) -> None:
        matches = approve.filter_actions(
            self.actions,
            [("library", "eq", "UNKNOWN")],
        )
        self.assertEqual(matches, [])

    def test_invalid_field_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported filter field",
        ):
            approve.filter_actions(
                self.actions,
                [("artist", "eq", "A-Ha")],
            )

    def test_invalid_operator_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported filter operator",
        ):
            approve.filter_actions(
                self.actions,
                [("library", "regex", "CLASSICAL")],
            )

    def test_legacy_action_matches_pending(self) -> None:
        actions = [
            {
                "id": "ACT-LEGACY",
                "library": "CONTEMPORARY",
            }
        ]
        matches = approve.filter_actions(
            actions,
            [("approval", "eq", "PENDING")],
        )
        self.assertEqual(
            [action["id"] for action in matches],
            ["ACT-LEGACY"],
        )


if __name__ == "__main__":
    unittest.main()
