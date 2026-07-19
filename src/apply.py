#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from mutagen.flac import FLAC
from mutagen.id3 import ID3, ID3NoHeaderError, TPE2
from mutagen.mp4 import MP4

from common import PROJECT_ROOT, SUPPORTED_AUDIO_EXTENSIONS, timestamp_slug, utc_timestamp
from approve import append_audit_events

APPROVAL_DIR = PROJECT_ROOT / "runtime" / "approval"
APPLY_DIR = PROJECT_ROOT / "runtime" / "apply"
INPUT = APPROVAL_DIR / "approved-actions.json"
REPORT = APPLY_DIR / "apply-report.json"
BACKUP_ROOT = APPLY_DIR / "backups"
SUPPORTED_OPERATIONS = {"ADD_ALBUMARTIST"}
WRITABLE_AUDIO_EXTENSIONS = frozenset({".flac", ".mp3", ".m4a", ".m4b", ".mp4"})
CONFIRMATION_PHRASE = "I_APPROVE_KINTYRE_APPLY"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def media_files(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.iterdir()
        if path.is_file()
        and not path.name.startswith("._")
        and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def metadata_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".flac":
        return "FLAC"
    if suffix == ".mp3":
        return "MP3"
    if suffix in {".m4a", ".m4b", ".mp4"}:
        return "MP4"
    raise ValueError(f"Unsupported writable audio format: {path}")


def read_albumartist(path: Path) -> list[str]:
    format_name = metadata_format(path)
    if format_name == "FLAC":
        values: Any = FLAC(path).get("albumartist", [])
    elif format_name == "MP3":
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            values = []
        else:
            frame = tags.get("TPE2")
            values = list(frame.text) if frame is not None else []
    elif format_name == "MP4":
        audio = MP4(path)
        values = (audio.tags or {}).get("aART", [])
    else:  # pragma: no cover
        raise RuntimeError(f"Unhandled metadata format: {format_name}")
    if isinstance(values, str):
        values = [values]
    return [str(value).strip() for value in values if str(value).strip()]


def inspect_album(folder: Path, proposed_value: str) -> dict[str, Any]:
    audio_files = media_files(folder)
    writable_files = [p for p in audio_files if p.suffix.lower() in WRITABLE_AUDIO_EXTENSIONS]
    unsupported = [p for p in audio_files if p.suffix.lower() not in WRITABLE_AUDIO_EXTENSIONS]
    format_counts = {"FLAC": 0, "MP3": 0, "MP4": 0}
    files_to_update: list[str] = []
    already_matching: list[str] = []
    conflicts: list[dict[str, Any]] = []
    metadata_errors: list[dict[str, str]] = []
    expected = proposed_value.strip().casefold()

    for file_path in writable_files:
        try:
            format_name = metadata_format(file_path)
            format_counts[format_name] += 1
            current_values = read_albumartist(file_path)
        except Exception as exc:
            metadata_errors.append({"path": str(file_path), "error": str(exc)})
            continue
        if not current_values:
            files_to_update.append(str(file_path))
        elif {value.casefold() for value in current_values} == {expected}:
            already_matching.append(str(file_path))
        else:
            conflicts.append({"path": str(file_path), "existing_values": current_values})

    return {
        "audio_file_count": len(audio_files),
        "writable_file_count": len(writable_files),
        "flac_file_count": format_counts["FLAC"],
        "mp3_file_count": format_counts["MP3"],
        "mp4_file_count": format_counts["MP4"],
        "format_counts": format_counts,
        "unsupported_audio_files": [str(p) for p in unsupported],
        "non_flac_files": [str(p) for p in audio_files if p.suffix.lower() != ".flac"],
        "files_to_update": files_to_update,
        "already_matching": already_matching,
        "conflicts": conflicts,
        "metadata_errors": metadata_errors,
    }


def empty_inspection() -> dict[str, Any]:
    return {
        "audio_file_count": 0,
        "writable_file_count": 0,
        "flac_file_count": 0,
        "mp3_file_count": 0,
        "mp4_file_count": 0,
        "format_counts": {"FLAC": 0, "MP3": 0, "MP4": 0},
        "unsupported_audio_files": [],
        "non_flac_files": [],
        "files_to_update": [],
        "already_matching": [],
        "conflicts": [],
        "metadata_errors": [],
    }


def validate_action(action: dict[str, Any]) -> dict[str, Any]:
    target = Path(str(action.get("folder", "")))
    operation = str(action.get("action", ""))
    value = action.get("proposed_value")
    value_present = isinstance(value, str) and bool(value.strip())
    inspection = empty_inspection()
    if target.is_dir() and operation == "ADD_ALBUMARTIST" and value_present:
        inspection = inspect_album(target, str(value))

    checks = {
        "folder_exists": target.is_dir(),
        "supported_operation": operation in SUPPORTED_OPERATIONS,
        "value_present": value_present,
        "approval_confirmed": action.get("approval") == "APPROVED",
        "contains_writable_audio": inspection["writable_file_count"] > 0,
        "only_writable_audio": not inspection["unsupported_audio_files"],
        "metadata_readable": not inspection["metadata_errors"],
        "no_existing_conflicts": not inspection["conflicts"],
    }
    passed = all(checks.values())
    return {
        "id": action.get("id"),
        "operation": operation,
        "status": "SIMULATED" if passed else "BLOCKED",
        "validation": "PASS" if passed else "FAIL",
        "target": str(target),
        "value": value,
        "checks": checks,
        **inspection,
    }


def detect_duplicate_file_targets(transactions: list[dict[str, Any]]) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for transaction in transactions:
        if transaction.get("validation") != "PASS":
            continue
        action_id = str(transaction.get("id"))
        for item in transaction.get("files_to_update", []):
            owners.setdefault(str(Path(item).resolve()), []).append(action_id)
    return {path: ids for path, ids in owners.items() if len(ids) > 1}


def mark_duplicate_targets(transactions: list[dict[str, Any]]) -> None:
    duplicates = detect_duplicate_file_targets(transactions)
    if not duplicates:
        return
    affected = {action_id for ids in duplicates.values() for action_id in ids}
    for transaction in transactions:
        if str(transaction.get("id")) in affected:
            transaction["validation"] = "FAIL"
            transaction["status"] = "BLOCKED"
            transaction["reason"] = "File targeted by multiple approved actions."
            transaction["duplicate_file_targets"] = {
                path: ids for path, ids in duplicates.items()
                if str(transaction.get("id")) in ids
            }


def restore_backups(backup_pairs: list[tuple[Path, Path]]) -> tuple[list[str], list[str]]:
    restored: list[str] = []
    failures: list[str] = []
    for original, backup in reversed(backup_pairs):
        try:
            if not backup.is_file():
                failures.append(f"Missing backup: {backup}")
                continue
            shutil.copy2(backup, original)
            if sha256_file(original) != sha256_file(backup):
                raise RuntimeError("restored file does not match backup")
            restored.append(str(original))
        except Exception as exc:
            failures.append(f"{original}: {exc}")
    return restored, failures


def set_albumartist(path: Path, value: str) -> None:
    existing = read_albumartist(path)
    if existing:
        raise RuntimeError(f"AlbumArtist appeared after validation; refusing overwrite: {path}")
    format_name = metadata_format(path)
    if format_name == "FLAC":
        audio = FLAC(path)
        audio["albumartist"] = [value]
        audio.save()
    elif format_name == "MP3":
        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()
        tags.delall("TPE2")
        tags.add(TPE2(encoding=3, text=[value]))
        tags.save(path)
    elif format_name == "MP4":
        audio = MP4(path)
        if audio.tags is None:
            audio.add_tags()
        audio["aART"] = [value]
        audio.save()
    else:  # pragma: no cover
        raise RuntimeError(f"Unhandled metadata format: {format_name}")
    if {item.casefold() for item in read_albumartist(path)} != {value.casefold()}:
        raise RuntimeError(f"Post-write verification failed: {path}")


def backup_files(files: list[Path], backup_dir: Path) -> list[tuple[Path, Path]]:
    backup_dir.mkdir(parents=True, exist_ok=False)
    pairs: list[tuple[Path, Path]] = []
    for source in files:
        if not source.is_file():
            raise RuntimeError(f"Source file disappeared: {source}")
        backup = backup_dir / source.name
        if backup.exists():
            raise RuntimeError(f"Backup filename collision: {backup}")
        shutil.copy2(source, backup)
        if sha256_file(source) != sha256_file(backup):
            raise RuntimeError(f"Backup verification failed: {source}")
        pairs.append((source, backup))
    return pairs


def write_albumartist(transaction: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
    value = str(transaction["value"]).strip()
    files = [Path(item) for item in transaction["files_to_update"]]
    action_id = str(transaction.get("id", "UNKNOWN"))
    if not files:
        return {**transaction, "status": "NO_CHANGE", "validation": "PASS", "files_updated": [], "files_updated_count": 0}

    run_slug = run_id or timestamp_slug()
    backup_dir = BACKUP_ROOT / run_slug / action_id
    counter = 1
    base = backup_dir
    while backup_dir.exists():
        backup_dir = Path(f"{base}-{counter}")
        counter += 1

    backup_pairs: list[tuple[Path, Path]] = []
    updated: list[str] = []
    try:
        backup_pairs = backup_files(files, backup_dir)
        for source, _backup in backup_pairs:
            set_albumartist(source, value)
            updated.append(str(source))
    except Exception as exc:
        restored, restore_failures = restore_backups(backup_pairs)
        return {
            **transaction,
            "status": "ROLLED_BACK",
            "validation": "FAIL",
            "reason": str(exc),
            "files_updated_before_failure": updated,
            "files_restored": restored,
            "restore_failures": restore_failures,
            "backup_directory": str(backup_dir),
            "backup_files": [{"original": str(o), "backup": str(b)} for o, b in backup_pairs],
        }

    return {
        **transaction,
        "status": "APPLIED",
        "validation": "PASS",
        "files_updated": updated,
        "files_updated_count": len(updated),
        "backup_directory": str(backup_dir),
        "backup_files": [{"original": str(o), "backup": str(b)} for o, b in backup_pairs],
    }


def execute_transaction(transaction: dict[str, Any], *, execute: bool, run_id: str | None = None) -> dict[str, Any]:
    if transaction["validation"] != "PASS" or not execute:
        return transaction
    if transaction["operation"] == "ADD_ALBUMARTIST":
        return write_albumartist(transaction, run_id=run_id)
    return {**transaction, "status": "BLOCKED", "validation": "FAIL", "reason": "Unsupported operation."}


def rollback_applied_transactions(transactions: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    pairs: list[tuple[Path, Path]] = []
    for transaction in transactions:
        for item in transaction.get("backup_files", []):
            pairs.append((Path(item["original"]), Path(item["backup"])))
    return restore_backups(pairs)


def execute_batch(validated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_id = timestamp_slug()
    results: list[dict[str, Any]] = []
    for index, transaction in enumerate(validated):
        result = execute_transaction(transaction, execute=True, run_id=run_id)
        results.append(result)
        if result.get("validation") == "FAIL":
            prior_applied = [item for item in results[:-1] if item.get("status") == "APPLIED"]
            restored, failures = rollback_applied_transactions(prior_applied)
            for prior in prior_applied:
                prior["status"] = "ROLLED_BACK_BATCH"
                prior["validation"] = "FAIL"
                prior["batch_rollback_restored"] = restored
                prior["batch_rollback_failures"] = failures
            for remaining in validated[index + 1:]:
                results.append({**remaining, "status": "SKIPPED", "validation": "FAIL", "reason": "Earlier transaction failed; batch execution stopped."})
            break
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate or execute approved metadata transactions.")
    parser.add_argument("--execute", action="store_true", help="Enable live metadata writes.")
    parser.add_argument("--confirm", default="", help=f"Required confirmation phrase for live execution: {CONFIRMATION_PHRASE}")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.execute and args.confirm != CONFIRMATION_PHRASE:
        raise RuntimeError(f"Live execution refused. Supply both --execute and --confirm {CONFIRMATION_PHRASE}.")
    if not INPUT.is_file():
        raise FileNotFoundError(f"Approved action plan not found: {INPUT}")

    mode = "EXECUTE" if args.execute else "DRY_RUN"
    with INPUT.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    actions = plan.get("actions")
    if not isinstance(actions, list):
        raise ValueError("Approved action plan has no valid actions list.")

    validated = [validate_action(action) for action in actions]
    mark_duplicate_targets(validated)
    preflight_failed = any(item["validation"] != "PASS" for item in validated)
    if args.execute and preflight_failed:
        transactions = validated
    elif args.execute:
        transactions = execute_batch(validated)
    else:
        transactions = validated

    successful = sum(1 for item in transactions if item["validation"] == "PASS")
    failed = len(transactions) - successful
    generated_at = utc_timestamp()
    report = {
        "schema_version": "1.2",
        "generated_at": generated_at,
        "mode": mode,
        "preflight_passed": not preflight_failed,
        "transaction_count": len(transactions),
        "successful": successful,
        "failed": failed,
        "transactions": transactions,
    }
    write_json(REPORT, report)
    append_audit_events([
        {
            "recorded_at": generated_at,
            "operation": "apply",
            "action_id": transaction.get("id"),
            "apply_mode": mode,
            "apply_status": transaction.get("status"),
            "validation": transaction.get("validation"),
        }
        for transaction in transactions
    ])

    print("KINTYRE Apply Engine")
    print(f"Transactions: {len(transactions)}")
    print(f"Validated: {successful}")
    print(f"Blocked: {failed}")
    print(f"Mode: {mode}")
    print(f"Created: {REPORT}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
