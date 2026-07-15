#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from common import PROJECT_ROOT, utc_timestamp

PREVIEW_DIR = PROJECT_ROOT / "runtime" / "preview"
APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"

INPUT_PLAN = PREVIEW_DIR / "apply-plan.json"

APPROVAL_PLAN = APPROVAL_DIR / "approval-plan.json"
APPROVAL_SUMMARY = APPROVAL_DIR / "approval-summary.json"


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def main() -> int:

    APPROVAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with INPUT_PLAN.open(
        "r",
        encoding="utf-8",
    ) as handle:
        preview = json.load(handle)

    approval_plan = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "source_generated_at": preview["generated_at"],
        "mode": "READ_ONLY",
        "action_count": preview["action_count"],
        "actions": preview["actions"],
    }

    approval_summary = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "mode": "READ_ONLY",
        "action_count": preview["action_count"],
        "approval_state": "INITIAL",
    }

    write_json(APPROVAL_PLAN, approval_plan)
    write_json(APPROVAL_SUMMARY, approval_summary)

    print("KINTYRE Approval Engine")
    print(f"Actions: {preview['action_count']}")
    print(f"Created: {APPROVAL_PLAN}")
    print(f"Created: {APPROVAL_SUMMARY}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
