#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from mutagen.flac import FLAC

from common import (
    PROJECT_ROOT,
    SUPPORTED_AUDIO_EXTENSIONS,
    timestamp_slug,
    utc_timestamp,
)
from approve import append_audit_events

APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"
APPLY_DIR = PROJECT_ROOT / "runtime" / "apply"

INPUT = APPROVAL_DIR / "approved-actions.json"
REPORT = APPLY_DIR / "apply-report.json"
BACKUP_ROOT = APPLY_DIR / "backups"

SUPPORTED_OPERATIONS = {
    "ADD_ALBUMARTIST",
}

CONFIRMATION_PHRASE = "I_APPROVE_KINTYRE_APPLY"


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
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

    temporary.replace(path)


def media_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.iterdir()
        if (
            path.is_file()
            and not path.name.startswith("._")
            and path.suffix.lower()
            in SUPPORTED_AUDIO_EXTENSIONS
        )
    )


def inspect_flac_album(
    folder: Path,
    proposed_value: str,
) -> dict[str, Any]:
    audio_files = media_files(folder)

    flac_files = [
        path
        for path in audio_files
        if path.suffix.lower() == ".flac"
    ]

    non_flac_files = [
        path
        for path in audio_files
        if path.suffix.lower() != ".flac"
    ]

    files_to_update: list[str] = []
    already_matching: list[str] = []
    conflicts: list[dict[str, Any]] = []
    metadata_errors: list[dict[str, str]] = []

    expected = proposed_value.strip().casefold()

    for path in flac_files:
        try:
            audio = FLAC(path)
            current_values = [
                str(value).strip()
                for value in audio.get(
                    "albumartist",
                    [],
                )
                if str(value).strip()
            ]
        except Exception as exc:
            metadata_errors.append(
                {
                    "path": str(path),
                    "error": str(exc),
                }
            )
            continue

        if not current_values:
            files_to_update.append(str(path))
            continue

        normalized = {
            value.casefold()
            for value in current_values
        }

        if normalized == {expected}:
            already_matching.append(str(path))
        else:
            conflicts.append(
                {
                    "path": str(path),
                    "existing_values":
                        current_values,
                }
            )

    return {
        "audio_file_count": len(audio_files),
        "flac_file_count": len(flac_files),
        "non_flac_files": [
            str(path)
            for path in non_flac_files
        ],
        "files_to_update": files_to_update,
        "already_matching":
            already_matching,
        "conflicts": conflicts,
        "metadata_errors":
            metadata_errors,
    }


def validate_action(
    action: dict[str, Any],
) -> dict[str, Any]:
    target = Path(
        str(action.get("folder", ""))
    )
    operation = str(
        action.get("action", "")
    )
    value = action.get("proposed_value")

    value_present = (
        isinstance(value, str)
        and bool(value.strip())
    )

    inspection: dict[str, Any] = {
        "audio_file_count": 0,
        "flac_file_count": 0,
        "non_flac_files": [],
        "files_to_update": [],
        "already_matching": [],
        "conflicts": [],
        "metadata_errors": [],
    }

    if (
        target.is_dir()
        and operation == "ADD_ALBUMARTIST"
        and value_present
    ):
        inspection = inspect_flac_album(
            target,
            str(value),
        )

    checks = {
        "folder_exists":
            target.is_dir(),
        "supported_operation":
            operation in SUPPORTED_OPERATIONS,
        "value_present":
            value_present,
        "approval_confirmed":
            action.get("approval")
            == "APPROVED",
        "contains_flac":
            inspection["flac_file_count"] > 0,
        "only_flac_audio":
            not inspection["non_flac_files"],
        "metadata_readable":
            not inspection["metadata_errors"],
        "no_existing_conflicts":
            not inspection["conflicts"],
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
        "audio_file_count":
            inspection["audio_file_count"],
        "flac_file_count":
            inspection["flac_file_count"],
        "files_to_update":
            inspection["files_to_update"],
        "already_matching":
            inspection["already_matching"],
        "non_flac_files":
            inspection["non_flac_files"],
        "conflicts":
            inspection["conflicts"],
        "metadata_errors":
            inspection["metadata_errors"],
    }


def restore_backups(
    backup_pairs: list[
        tuple[Path, Path]
    ],
) -> tuple[list[str], list[str]]:
    restored: list[str] = []
    failures: list[str] = []

    for original, backup in reversed(
        backup_pairs
    ):
        try:
            if not backup.is_file():
                failures.append(
                    f"Missing backup: {backup}"
                )
                continue

            shutil.copy2(
                backup,
                original,
            )
            restored.append(
                str(original)
            )

        except Exception as exc:
            failures.append(
                f"{original}: {exc}"
            )

    return restored, failures


def write_albumartist_flac(
    transaction: dict[str, Any],
) -> dict[str, Any]:
    value = str(
        transaction["value"]
    ).strip()

    files = [
        Path(path)
        for path
        in transaction["files_to_update"]
    ]

    action_id = str(
        transaction.get(
            "id",
            "UNKNOWN",
        )
    )

    backup_dir = (
        BACKUP_ROOT
        / timestamp_slug()
        / action_id
    )

    backup_pairs: list[
        tuple[Path, Path]
    ] = []

    updated: list[str] = []

    try:
        backup_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        for source in files:
            backup = backup_dir / source.name

            if backup.exists():
                raise RuntimeError(
                    "Backup filename collision: "
                    f"{backup}"
                )

            shutil.copy2(
                source,
                backup,
            )

            backup_pairs.append(
                (source, backup)
            )

        for source, _backup in backup_pairs:
            audio = FLAC(source)

            existing = [
                str(item).strip()
                for item in audio.get(
                    "albumartist",
                    [],
                )
                if str(item).strip()
            ]

            if existing:
                raise RuntimeError(
                    "AlbumArtist appeared after "
                    "validation; refusing overwrite: "
                    f"{source}"
                )

            audio["albumartist"] = [value]
            audio.save()

            verified = FLAC(source).get(
                "albumartist",
                [],
            )

            normalized = {
                str(item).strip().casefold()
                for item in verified
                if str(item).strip()
            }

            if normalized != {
                value.casefold()
            }:
                raise RuntimeError(
                    "Post-write verification failed: "
                    f"{source}"
                )

            updated.append(str(source))

    except Exception as exc:
        restored, restore_failures = restore_backups(
            backup_pairs
        )

        return {
            **transaction,
            "status": "ROLLED_BACK",
            "validation": "FAIL",
            "reason": str(exc),
            "files_updated_before_failure":
                updated,
            "files_restored":
                restored,
            "restore_failures":
                restore_failures,
            "backup_directory":
                str(backup_dir),
        }

    return {
        **transaction,
        "status":
            "APPLIED"
            if files
            else "NO_CHANGE",
        "validation": "PASS",
        "files_updated": updated,
        "files_updated_count":
            len(updated),
        "backup_directory":
            str(backup_dir),
    }


def handle_add_albumartist(
    transaction: dict[str, Any],
    *,
    execute: bool,
) -> dict[str, Any]:
    if not execute:
        return transaction

    return write_albumartist_flac(
        transaction
    )


def execute_transaction(
    transaction: dict[str, Any],
    *,
    execute: bool,
) -> dict[str, Any]:
    if transaction["validation"] != "PASS":
        return transaction

    if (
        transaction["operation"]
        == "ADD_ALBUMARTIST"
    ):
        return handle_add_albumartist(
            transaction,
            execute=execute,
        )

    return {
        **transaction,
        "status": "BLOCKED",
        "validation": "FAIL",
        "reason":
            "Unsupported operation.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or execute approved "
            "metadata transactions."
        )
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
            "Required confirmation phrase "
            "for live execution: "
            f"{CONFIRMATION_PHRASE}"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if (
        args.execute
        and args.confirm
        != CONFIRMATION_PHRASE
    ):
        raise RuntimeError(
            "Live execution refused. Supply "
            "both --execute and --confirm "
            f"{CONFIRMATION_PHRASE}."
        )

    if not INPUT.is_file():
        raise FileNotFoundError(
            f"Approved action plan not found: {INPUT}"
        )

    mode = (
        "EXECUTE"
        if args.execute
        else "DRY_RUN"
    )

    with INPUT.open(
        "r",
        encoding="utf-8",
    ) as handle:
        plan = json.load(handle)

    actions = plan.get("actions")

    if not isinstance(actions, list):
        raise ValueError(
            "Approved action plan has no "
            "valid actions list."
        )

    validated = [
        validate_action(action)
        for action in actions
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

    failed = (
        len(transactions)
        - successful
    )

    report = {
        "schema_version": "1.1",
        "generated_at": utc_timestamp(),
        "mode": mode,
        "transaction_count":
            len(transactions),
        "successful": successful,
        "failed": failed,
        "transactions": transactions,
    }

    write_json(
        REPORT,
        report,
    )

    append_audit_events(
        [
            {
                "recorded_at": report["generated_at"],
                "operation": "apply",
                "action_id": transaction.get("id"),
                "apply_mode": mode,
                "apply_status": transaction.get("status"),
                "validation": transaction.get("validation"),
            }
            for transaction in transactions
        ]
    )

    print("KINTYRE Apply Engine")
    print(
        f"Transactions: "
        f"{len(transactions)}"
    )
    print(
        f"Validated: {successful}"
    )
    print(
        f"Blocked: {failed}"
    )
    print(f"Mode: {mode}")
    print(f"Created: {REPORT}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
