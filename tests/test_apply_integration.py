from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import apply


class TestApplyAuditIntegration(unittest.TestCase):
    def test_dry_run_records_apply_audit_event(self) -> None:
        action = {
            "id": "ACT-1",
            "folder": "/tmp/test-album",
            "action": "ADD_ALBUMARTIST",
            "proposed_value": "Artist",
            "approval": "APPROVED",
        }

        transaction = {
            "id": "ACT-1",
            "status": "SIMULATED",
            "validation": "PASS",
        }

        with TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "approved-actions.json"
            report_path = root / "apply-report.json"

            input_path.write_text(
                json.dumps({"actions": [action]}),
                encoding="utf-8",
            )

            with mock.patch.object(apply, "INPUT", input_path), \
                 mock.patch.object(apply, "REPORT", report_path), \
                 mock.patch.object(apply, "parse_args") as parse_args, \
                 mock.patch.object(
                     apply,
                     "validate_action",
                     return_value=transaction,
                 ), \
                 mock.patch.object(
                     apply,
                     "execute_transaction",
                     return_value=transaction,
                 ), \
                 mock.patch.object(
                     apply,
                     "utc_timestamp",
                     return_value="2026-07-17T17:00:00Z",
                 ), \
                 mock.patch.object(
                     apply,
                     "append_audit_events",
                 ) as append_audit_events:
                parse_args.return_value = mock.Mock(
                    execute=False,
                    confirm="",
                )

                result = apply.main()

        self.assertEqual(result, 0)
        append_audit_events.assert_called_once_with(
            [
                {
                    "recorded_at": "2026-07-17T17:00:00Z",
                    "operation": "apply",
                    "action_id": "ACT-1",
                    "apply_mode": "DRY_RUN",
                    "apply_status": "SIMULATED",
                    "validation": "PASS",
                }
            ]
        )


if __name__ == "__main__":
    unittest.main()
