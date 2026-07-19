#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from common import PROJECT_ROOT, utc_timestamp

PREVIEW_DIR = PROJECT_ROOT / "runtime" / "preview"
APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"

INPUT_PLAN = PREVIEW_DIR / "apply-plan.json"
APPROVAL_PLAN = APPROVAL_DIR / "approval-plan.json"
APPROVAL_SUMMARY = APPROVAL_DIR / "approval-summary.json"
APPROVED_ACTIONS = APPROVAL_DIR / "approved-actions.json"
APPROVAL_AUDIT = APPROVAL_DIR / "approval-audit.json"

APPROVAL_STATES = (
    "PENDING",
    "APPROVED",
    "REJECTED",
    "DEFERRED",
)

DECISIONS = {
    "approve": "APPROVED",
    "reject": "REJECTED",
    "defer": "DEFERRED",
    "reset": "PENDING",
}

FILTERABLE_FIELDS = (
    "id",
    "action",
    "album_id",
    "approval",
    "confidence",
    "folder",
    "library",
    "proposed_value",
    "reason",
    "risk",
)

FILTER_OPERATORS = (
    "eq",
    "contains",
)


def validate_filter(field: str, operator: str) -> None:
    """Validate a transaction filter definition."""
    if field not in FILTERABLE_FIELDS:
        raise ValueError(
            f"Unsupported filter field {field!r}. "
            f"Allowed fields: {', '.join(FILTERABLE_FIELDS)}"
        )

    if operator not in FILTER_OPERATORS:
        raise ValueError(
            f"Unsupported filter operator {operator!r}. "
            f"Allowed operators: {', '.join(FILTER_OPERATORS)}"
        )


def action_matches_filter(
    action: dict[str, Any],
    *,
    field: str,
    operator: str,
    value: str,
) -> bool:
    """Return whether one action matches one filter predicate."""
    validate_filter(field, operator)

    actual = (
        approval_state(action)
        if field == "approval"
        else action.get(field)
    )

    if actual is None:
        return False

    actual_text = str(actual).casefold()
    expected_text = str(value).casefold()

    if operator == "eq":
        return actual_text == expected_text

    if operator == "contains":
        return expected_text in actual_text

    raise AssertionError(
        f"Unhandled filter operator: {operator}"
    )


def filter_actions(
    actions: list[dict[str, Any]],
    filters: list[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    """Return actions matching all supplied predicates."""
    for field, operator, _value in filters:
        validate_filter(field, operator)

    return [
        action
        for action in actions
        if all(
            action_matches_filter(
                action,
                field=field,
                operator=operator,
                value=value,
            )
            for field, operator, value in filters
        )
    ]


def approval_state(action: dict[str, Any]) -> str:
    """Return and validate an action's approval state.

    Legacy actions without an approval field are treated as PENDING.
    """
    state = str(action.get("approval", "PENDING")).upper()

    if state not in APPROVAL_STATES:
        raise ValueError(
            f"Invalid approval state {state!r} "
            f"for action {action.get('id', '<unknown>')}."
        )

    return state


def normalize_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy approval plans without losing decisions."""
    actions = plan.get("actions")

    if not isinstance(actions, list):
        raise ValueError("Approval plan has no valid actions list.")

    for action in actions:
        if not isinstance(action, dict):
            raise ValueError(
                "Every approval action must be an object."
            )

        action["approval"] = approval_state(action)
        action.setdefault("decision_at", None)

    return plan


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(temporary_name, 0o644)
        os.replace(temporary_name, path)

    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")

    return payload


def read_audit() -> dict[str, Any]:
    """Read or initialize the approval audit document."""
    if not APPROVAL_AUDIT.exists():
        generated_at = utc_timestamp()
        return {
            "schema_version": "1.0",
            "generated_at": generated_at,
            "updated_at": generated_at,
            "event_count": 0,
            "events": [],
        }

    audit = read_json(APPROVAL_AUDIT)
    events = audit.get("events")

    if not isinstance(events, list):
        raise ValueError(
            f"Invalid events list in {APPROVAL_AUDIT}"
        )

    audit.setdefault("schema_version", "1.0")
    audit.setdefault("generated_at", utc_timestamp())
    audit["event_count"] = len(events)
    return audit


def append_audit_events(
    events: list[dict[str, Any]],
) -> None:
    """Append decision events using one atomic audit write."""
    if not events:
        return

    for event in events:
        if not isinstance(event, dict):
            raise ValueError(
                "Every approval audit event must be an object."
            )

    audit = read_audit()
    stored_events = audit["events"]
    stored_events.extend(
        dict(event)
        for event in events
    )
    audit["updated_at"] = utc_timestamp()
    audit["event_count"] = len(stored_events)

    atomic_write_json(
        APPROVAL_AUDIT,
        audit,
    )


def build_summary(plan: dict[str, Any]) -> dict[str, Any]:
    actions = plan.get("actions", [])

    counts = Counter(
        approval_state(action)
        for action in actions
    )

    return {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "source_generated_at": plan.get("source_generated_at"),
        "mode": "READ_ONLY",
        "action_count": len(actions),
        "approval_counts": {
            state: counts.get(state, 0)
            for state in APPROVAL_STATES
        },
    }


def save_plan(plan: dict[str, Any]) -> None:
    normalize_plan(plan)
    plan["updated_at"] = utc_timestamp()
    plan["action_count"] = len(plan.get("actions", []))

    atomic_write_json(APPROVAL_PLAN, plan)
    atomic_write_json(
        APPROVAL_SUMMARY,
        build_summary(plan),
    )

    approved = [
        dict(action)
        for action in plan.get("actions", [])
        if approval_state(action) == "APPROVED"
    ]

    approved_plan = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "source_plan": str(APPROVAL_PLAN),
        "source_generated_at": plan.get("generated_at"),
        "mode": "READ_ONLY",
        "action_count": len(approved),
        "actions": approved,
    }

    atomic_write_json(
        APPROVED_ACTIONS,
        approved_plan,
    )


def initialize(*, reset: bool) -> None:
    if APPROVAL_PLAN.exists() and not reset:
        raise RuntimeError(
            "Approval plan already exists. "
            "Use 'status' to inspect it or "
            "'init --reset' to recreate it."
        )

    preview = read_json(INPUT_PLAN)
    preview_actions = preview.get("actions")

    if not isinstance(preview_actions, list):
        raise ValueError(
            f"Invalid actions list in {INPUT_PLAN}"
        )

    actions: list[dict[str, Any]] = []

    for source_action in preview_actions:
        if not isinstance(source_action, dict):
            raise ValueError(
                "Every Preview action must be an object."
            )

        action = dict(source_action)
        action["approval"] = "PENDING"
        action["decision_at"] = None
        actions.append(action)

    generated_at = utc_timestamp()

    plan = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "updated_at": generated_at,
        "source_plan": str(INPUT_PLAN),
        "source_generated_at": preview.get("generated_at"),
        "mode": "READ_ONLY",
        "action_count": len(actions),
        "actions": actions,
    }

    save_plan(plan)

    print("KINTYRE Approval Engine")
    print(f"Initialized actions: {len(actions)}")
    print(f"Created: {APPROVAL_PLAN}")
    print(f"Created: {APPROVAL_SUMMARY}")


def set_decision(action_id: str, decision: str) -> None:
    plan = normalize_plan(
        read_json(APPROVAL_PLAN)
    )
    actions = plan.get("actions")

    if not isinstance(actions, list):
        raise ValueError(
            f"Invalid actions list in {APPROVAL_PLAN}"
        )

    matches = [
        action
        for action in actions
        if action.get("id") == action_id
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one action matching {action_id}; "
            f"found {len(matches)}."
        )

    action = matches[0]
    if decision not in APPROVAL_STATES:
        raise ValueError(
            f"Unsupported approval decision: {decision}"
        )

    previous = approval_state(action)

    if previous == decision:
        print(
            f"{action_id}: already {decision}; "
            "no state change."
        )
        return

    recorded_at = utc_timestamp()
    action["approval"] = decision
    action["decision_at"] = (
        None
        if decision == "PENDING"
        else recorded_at
    )

    save_plan(plan)
    append_audit_events(
        [
            {
                "recorded_at": recorded_at,
                "operation": "single",
                "action_id": action_id,
                "previous_state": previous,
                "new_state": decision,
            }
        ]
    )

    print(f"{action_id}: {previous} -> {decision}")


def set_bulk_decision(
    filters: list[tuple[str, str, str]],
    decision: str,
    *,
    select_all: bool = False,
) -> None:
    """Apply one approval decision to matching or all actions."""
    if not filters and not select_all:
        raise ValueError(
            "Bulk decisions require at least one filter."
        )

    if decision not in APPROVAL_STATES:
        raise ValueError(
            f"Unsupported approval decision: {decision}"
        )

    plan = normalize_plan(
        read_json(APPROVAL_PLAN)
    )
    actions = plan.get("actions")

    if not isinstance(actions, list):
        raise ValueError(
            f"Invalid actions list in {APPROVAL_PLAN}"
        )

    matches = list(actions) if select_all else filter_actions(actions, filters)

    if not matches:
        raise ValueError(
            "No actions matched the supplied filters."
        )

    changed = 0
    unchanged = 0
    recorded_at = utc_timestamp()
    decision_at = (
        None
        if decision == "PENDING"
        else recorded_at
    )
    audit_events: list[dict[str, Any]] = []

    for action in matches:
        previous = approval_state(action)

        if previous == decision:
            unchanged += 1
            continue

        action["approval"] = decision
        action["decision_at"] = decision_at
        changed += 1

        audit_events.append(
            {
                "recorded_at": recorded_at,
                "operation": "bulk",
                "action_id": action.get("id"),
                "previous_state": previous,
                "new_state": decision,
                "filters": (
                    [{"all": True}]
                    if select_all
                    else [
                        {
                            "field": field,
                            "operator": operator,
                            "value": value,
                        }
                        for field, operator, value in filters
                    ]
                ),
            }
        )

    if changed:
        save_plan(plan)
        append_audit_events(audit_events)

    print(f"Matched: {len(matches)}")
    print(f"Changed: {changed}")
    print(f"Unchanged: {unchanged}")
    print(f"Decision: {decision}")


def parse_filter_expression(
    expression: str,
) -> tuple[str, str, str]:
    """Parse FIELD=VALUE or FIELD~VALUE filter syntax."""
    if "~" in expression:
        field, value = expression.split("~", 1)
        operator = "contains"
    elif "=" in expression:
        field, value = expression.split("=", 1)
        operator = "eq"
    else:
        raise ValueError(
            "Invalid filter expression. "
            "Use FIELD=VALUE or FIELD~VALUE."
        )

    field = field.strip()
    value = value.strip()

    if not field or not value:
        raise ValueError(
            "Filter field and value must not be empty."
        )

    validate_filter(field, operator)
    return field, operator, value


def show_status() -> None:
    plan = normalize_plan(
        read_json(APPROVAL_PLAN)
    )
    save_plan(plan)
    summary = build_summary(plan)

    print("KINTYRE Approval Status")
    print(f"Actions: {summary['action_count']}")

    for state, count in summary["approval_counts"].items():
        print(f"{state}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record reviewer decisions without "
            "modifying Preview artifacts."
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Create the approval working copy.",
    )
    init_parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard existing decisions and rebuild from Preview.",
    )

    subparsers.add_parser(
        "status",
        help="Display approval counts.",
    )

    for command in DECISIONS:
        decision_parser = subparsers.add_parser(
            command,
            help=(
                f"Mark one or more actions "
                f"{DECISIONS[command]}."
            ),
        )
        decision_parser.add_argument(
            "action_id",
            nargs="?",
            help="Action ID for a single-action decision.",
        )
        decision_parser.add_argument(
            "--filter",
            action="append",
            default=[],
            metavar="FIELD=VALUE",
            help=(
                "Select actions using FIELD=VALUE "
                "or FIELD~VALUE. May be repeated."
            ),
        )
        decision_parser.add_argument(
            "--all",
            action="store_true",
            dest="all_actions",
            help="Select every action in the approval plan.",
        )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "init":
        initialize(reset=args.reset)
    elif args.command == "status":
        show_status()
    else:
        selectors = sum(
            bool(value)
            for value in (
                args.action_id,
                args.filter,
                args.all_actions,
            )
        )
        if selectors > 1:
            raise ValueError(
                "Use exactly one of action_id, --filter, or --all."
            )

        if args.action_id:
            set_decision(
                args.action_id,
                DECISIONS[args.command],
            )
        elif args.filter:
            filters = [
                parse_filter_expression(expression)
                for expression in args.filter
            ]
            set_bulk_decision(
                filters,
                DECISIONS[args.command],
            )
        elif args.all_actions:
            set_bulk_decision(
                [],
                DECISIONS[args.command],
                select_all=True,
            )
        else:
            raise ValueError(
                "Provide an action_id, at least one --filter, or --all."
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
