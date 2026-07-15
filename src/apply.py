#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from common import PROJECT_ROOT, utc_timestamp

APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"
APPLY_DIR = PROJECT_ROOT / "runtime" / "apply"

INPUT = APPROVAL_DIR / "approved-actions.json"

REPORT = APPLY_DIR / "apply-report.json"


def write_json(path: Path, payload: dict) -> None:
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


def main() -> int:

    with INPUT.open(
        "r",
        encoding="utf-8",
    ) as handle:
        plan = json.load(handle)

    report = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "mode": "DRY_RUN",
        "transaction_count": plan["action_count"],
        "successful": plan["action_count"],
        "failed": 0,
        "transactions": [],
    }

    for action in plan["actions"]:

        report["transactions"].append(
            {
                "id": action["id"],
                "operation": action["action"],
                "status": "SIMULATED",
                "target": action["folder"],
                "value": action["proposed_value"],
            }
        )

    write_json(
        REPORT,
        report,
    )

    print("KINTYRE Apply Engine")
    print(f"Transactions: {plan['action_count']}")
    print("Mode: DRY_RUN")
    print(f"Created: {REPORT}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
