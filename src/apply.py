#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import PROJECT_ROOT, utc_timestamp

APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"
APPLY_DIR = PROJECT_ROOT / "runtime" / "apply"

INPUT = APPROVAL_DIR / "approved-actions.json"
REPORT = APPLY_DIR / "apply-report.json"

SUPPORTED_OPERATIONS = {
    "ADD_ALBUMARTIST",
}


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def validate_action(
    action: dict[str, Any],
) -> dict[str, Any]:
    target = Path(str(action.get("folder", "")))
    operation = str(action.get("action", ""))
    value = action.get("proposed_value")

    checks = {
        "folder_exists": target.is_dir(),
        "supported_operation":
            operation in SUPPORTED_OPERATIONS,
        "value_present":
            isinstance(value, str)
            and bool(value.strip()),
        "approval_confirmed":
            action.get("approval") == "APPROVED",
    }

    passed = all(checks.values())

    return {
        "id": action.get("id"),
        "operation": operation,
        "status":
            "SIMULATED"
            if passed
            else "BLOCKED",
        "validation":
            "PASS"
            if passed
            else "FAIL",
        "target": str(target),
        "value": value,
        "checks": checks,
    }


def main() -> int:
    with INPUT.open(
        "r",
        encoding="utf-8",
    ) as handle:
        plan = json.load(handle)

    transactions = [
        validate_action(action)
        for action in plan["actions"]
    ]

    successful = sum(
        1
        for transaction in transactions
        if transaction["validation"] == "PASS"
    )

    failed = len(transactions) - successful

    report = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "mode": "DRY_RUN",
        "transaction_count": len(transactions),
        "successful": successful,
        "failed": failed,
        "transactions": transactions,
    }

    write_json(
        REPORT,
        report,
    )

    print("KINTYRE Apply Engine")
    print(f"Transactions: {len(transactions)}")
    print(f"Validated: {successful}")
    print(f"Blocked: {failed}")
    print("Mode: DRY_RUN")
    print(f"Created: {REPORT}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
