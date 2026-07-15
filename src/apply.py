#!/usr/bin/env python3
from __future__ import annotations

import argparse
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



def execute_transaction(
    transaction: dict[str, Any],
    *,
    execute: bool,
) -> dict[str, Any]:
    if transaction["validation"] != "PASS":
        return transaction

    if transaction["operation"] not in SUPPORTED_OPERATIONS:
        return {
            **transaction,
            "status": "BLOCKED",
            "validation": "FAIL",
            "reason": "Unsupported operation.",
        }

    if execute:
        return {
            **transaction,
            "status": "BLOCKED",
            "validation": "FAIL",
            "reason": "Live writer not implemented yet.",
        }

    return transaction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate or execute approved metadata transactions."
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable live metadata writes.",
    )

    parser.add_argument(
        "--confirm",
        default="",
        help=(
            "Required confirmation phrase for live execution: "
            "I_APPROVE_KINTYRE_APPLY"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.execute and args.confirm != "I_APPROVE_KINTYRE_APPLY":
        raise RuntimeError(
            "Live execution refused. Supply both --execute and "
            "--confirm I_APPROVE_KINTYRE_APPLY."
        )

    mode = "EXECUTE" if args.execute else "DRY_RUN"

    with INPUT.open(
        "r",
        encoding="utf-8",
    ) as handle:
        plan = json.load(handle)

    validated = [
        validate_action(action)
        for action in plan["actions"]
    ]

    transactions = [
        execute_transaction(
            transaction,
            execute=args.execute,
        )
        for transaction in validated
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
        "mode": mode,
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
    print(f"Mode: {mode}")
    print(f"Created: {REPORT}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
