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


class TestBulkApprovalOperations(unittest.TestCase):
    def test_parse_exact_filter(self) -> None:
        self.assertEqual(
            approve.parse_filter_expression(
                "library=CONTEMPORARY"
            ),
            ("library", "eq", "CONTEMPORARY"),
        )

    def test_parse_contains_filter(self) -> None:
        self.assertEqual(
            approve.parse_filter_expression(
                "folder~Beatles"
            ),
            ("folder", "contains", "Beatles"),
        )

    def test_parse_filter_preserves_equals_in_value(self) -> None:
        self.assertEqual(
            approve.parse_filter_expression(
                "reason=value=example"
            ),
            ("reason", "eq", "value=example"),
        )

    def test_parse_filter_rejects_missing_operator(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Invalid filter expression",
        ):
            approve.parse_filter_expression("library")

    def test_parse_filter_rejects_empty_value(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "must not be empty",
        ):
            approve.parse_filter_expression("library=")

    def test_bulk_decision_requires_filter(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "at least one filter",
        ):
            approve.set_bulk_decision([], "APPROVED")

    def test_bulk_decision_rejects_invalid_decision(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported approval decision",
        ):
            approve.set_bulk_decision(
                [("library", "eq", "CLASSICAL")],
                "INVALID",
            )

    def test_bulk_decision_updates_all_matches_once(self) -> None:
        audit_patcher = unittest.mock.patch.object(
            approve,
            "append_audit_events",
        )
        audit_patcher.start()
        self.addCleanup(audit_patcher.stop)
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CONTEMPORARY",
                    "approval": "PENDING",
                    "decision_at": None,
                },
                {
                    "id": "ACT-2",
                    "library": "CONTEMPORARY",
                    "approval": "PENDING",
                    "decision_at": None,
                },
                {
                    "id": "ACT-3",
                    "library": "CLASSICAL",
                    "approval": "PENDING",
                    "decision_at": None,
                },
            ],
        }

        with unittest.mock.patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), unittest.mock.patch.object(
            approve,
            "save_plan",
        ) as save_plan, unittest.mock.patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T12:00:00Z",
        ):
            approve.set_bulk_decision(
                [
                    (
                        "library",
                        "eq",
                        "CONTEMPORARY",
                    )
                ],
                "APPROVED",
            )

        self.assertEqual(
            plan["actions"][0]["approval"],
            "APPROVED",
        )
        self.assertEqual(
            plan["actions"][1]["approval"],
            "APPROVED",
        )
        self.assertEqual(
            plan["actions"][2]["approval"],
            "PENDING",
        )
        self.assertEqual(
            plan["actions"][0]["decision_at"],
            "2026-07-17T12:00:00Z",
        )
        self.assertEqual(save_plan.call_count, 1)

    def test_bulk_decision_is_idempotent(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CLASSICAL",
                    "approval": "APPROVED",
                    "decision_at": "2026-07-15T12:00:32Z",
                }
            ],
        }

        with unittest.mock.patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), unittest.mock.patch.object(
            approve,
            "save_plan",
        ) as save_plan:
            approve.set_bulk_decision(
                [("library", "eq", "CLASSICAL")],
                "APPROVED",
            )

        save_plan.assert_not_called()
        self.assertEqual(
            plan["actions"][0]["decision_at"],
            "2026-07-15T12:00:32Z",
        )

    def test_bulk_reset_clears_decision_timestamp(self) -> None:
        audit_patcher = unittest.mock.patch.object(
            approve,
            "append_audit_events",
        )
        audit_patcher.start()
        self.addCleanup(audit_patcher.stop)
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CLASSICAL",
                    "approval": "APPROVED",
                    "decision_at": "2026-07-15T12:00:32Z",
                }
            ],
        }

        with unittest.mock.patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), unittest.mock.patch.object(
            approve,
            "save_plan",
        ):
            approve.set_bulk_decision(
                [("library", "eq", "CLASSICAL")],
                "PENDING",
            )

        self.assertEqual(
            plan["actions"][0]["approval"],
            "PENDING",
        )
        self.assertIsNone(
            plan["actions"][0]["decision_at"]
        )

    def test_bulk_decision_rejects_zero_matches(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CLASSICAL",
                    "approval": "PENDING",
                }
            ],
        }

        with unittest.mock.patch.object(
            approve,
            "read_json",
            return_value=plan,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "No actions matched",
            ):
                approve.set_bulk_decision(
                    [
                        (
                            "library",
                            "eq",
                            "CONTEMPORARY",
                        )
                    ],
                    "APPROVED",
                )


class TestApprovalAuditLogging(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.audit_path = (
            Path(self.temporary_directory.name)
            / "approval-audit.json"
        )
        self.audit_patcher = patch.object(
            approve,
            "APPROVAL_AUDIT",
            self.audit_path,
        )
        self.audit_patcher.start()
        self.addCleanup(self.audit_patcher.stop)
        self.addCleanup(self.temporary_directory.cleanup)

    def read_audit(self) -> dict:
        return json.loads(
            self.audit_path.read_text(encoding="utf-8")
        )

    def test_append_audit_events_creates_document(self) -> None:
        with patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T15:00:00Z",
        ):
            approve.append_audit_events(
                [
                    {
                        "recorded_at": "2026-07-17T15:00:00Z",
                        "operation": "single",
                        "action_id": "ACT-1",
                        "previous_state": "PENDING",
                        "new_state": "APPROVED",
                    }
                ]
            )

        audit = self.read_audit()

        self.assertEqual(audit["schema_version"], "1.0")
        self.assertEqual(audit["event_count"], 1)
        self.assertEqual(
            audit["events"][0]["action_id"],
            "ACT-1",
        )

    def test_append_audit_events_preserves_history(self) -> None:
        with patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T15:00:00Z",
        ):
            approve.append_audit_events(
                [
                    {
                        "recorded_at": "2026-07-17T15:00:00Z",
                        "operation": "single",
                        "action_id": "ACT-1",
                        "previous_state": "PENDING",
                        "new_state": "APPROVED",
                    }
                ]
            )
            approve.append_audit_events(
                [
                    {
                        "recorded_at": "2026-07-17T15:05:00Z",
                        "operation": "single",
                        "action_id": "ACT-2",
                        "previous_state": "PENDING",
                        "new_state": "REJECTED",
                    }
                ]
            )

        audit = self.read_audit()

        self.assertEqual(audit["event_count"], 2)
        self.assertEqual(
            [
                event["action_id"]
                for event in audit["events"]
            ],
            ["ACT-1", "ACT-2"],
        )

    def test_single_decision_writes_audit_event(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "approval": "PENDING",
                    "decision_at": None,
                }
            ],
        }

        with patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), patch.object(
            approve,
            "save_plan",
        ), patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T15:10:00Z",
        ):
            approve.set_decision(
                "ACT-1",
                "APPROVED",
            )

        audit = self.read_audit()
        event = audit["events"][0]

        self.assertEqual(event["operation"], "single")
        self.assertEqual(event["action_id"], "ACT-1")
        self.assertEqual(
            event["previous_state"],
            "PENDING",
        )
        self.assertEqual(
            event["new_state"],
            "APPROVED",
        )

    def test_idempotent_single_decision_is_not_logged(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "approval": "APPROVED",
                    "decision_at": "2026-07-17T15:10:00Z",
                }
            ],
        }

        with patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), patch.object(
            approve,
            "save_plan",
        ):
            approve.set_decision(
                "ACT-1",
                "APPROVED",
            )

        self.assertFalse(self.audit_path.exists())

    def test_bulk_decision_logs_only_changed_actions(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CLASSICAL",
                    "approval": "PENDING",
                    "decision_at": None,
                },
                {
                    "id": "ACT-2",
                    "library": "CLASSICAL",
                    "approval": "APPROVED",
                    "decision_at": "2026-07-17T14:00:00Z",
                },
            ],
        }

        filters = [
            ("library", "eq", "CLASSICAL")
        ]

        with patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), patch.object(
            approve,
            "save_plan",
        ), patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T15:20:00Z",
        ):
            approve.set_bulk_decision(
                filters,
                "APPROVED",
            )

        audit = self.read_audit()

        self.assertEqual(audit["event_count"], 1)
        event = audit["events"][0]
        self.assertEqual(event["operation"], "bulk")
        self.assertEqual(event["action_id"], "ACT-1")
        self.assertEqual(
            event["filters"],
            [
                {
                    "field": "library",
                    "operator": "eq",
                    "value": "CLASSICAL",
                }
            ],
        )

    def test_bulk_reset_is_audited(self) -> None:
        plan = {
            "schema_version": "1.0",
            "actions": [
                {
                    "id": "ACT-1",
                    "library": "CLASSICAL",
                    "approval": "DEFERRED",
                    "decision_at": "2026-07-17T14:00:00Z",
                }
            ],
        }

        with patch.object(
            approve,
            "read_json",
            return_value=plan,
        ), patch.object(
            approve,
            "save_plan",
        ), patch.object(
            approve,
            "utc_timestamp",
            return_value="2026-07-17T15:30:00Z",
        ):
            approve.set_bulk_decision(
                [("library", "eq", "CLASSICAL")],
                "PENDING",
            )

        audit = self.read_audit()
        event = audit["events"][0]

        self.assertEqual(
            event["previous_state"],
            "DEFERRED",
        )
        self.assertEqual(
            event["new_state"],
            "PENDING",
        )
        self.assertIsNone(
            plan["actions"][0]["decision_at"]
        )


if __name__ == "__main__":
    unittest.main()

class TestApproveAllCLI(unittest.TestCase):
    def test_approve_all_selects_every_action(self) -> None:
        with unittest.mock.patch.object(
            sys,
            "argv",
            ["approve.py", "approve", "--all"],
        ), unittest.mock.patch.object(
            approve,
            "set_bulk_decision",
        ) as bulk:
            result = approve.main()
        self.assertEqual(result, 0)
        bulk.assert_called_once_with(
            [],
            "APPROVED",
            select_all=True,
        )
