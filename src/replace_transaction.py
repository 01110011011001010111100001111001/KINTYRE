#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from common import LIBRARIES, RUNTIME_DIR, load_config, utc_timestamp
from copy_album import (
    SCHEMA_VERSION,
    SOURCE_MANIFEST,
    TRANSACTIONS_DIRNAME,
    build_manifest,
    compare_manifests,
    is_within,
    manifest_digest,
    validate_transaction_id,
    write_json,
)
from fix_album import AFTER_MANIFEST, FIX_DIRNAME
from approve_transaction import (
    APPROVAL_DIRNAME,
    APPROVAL_REPORT,
)
from review_album import (
    REVIEW_DIRNAME,
    REVIEW_FINDINGS,
    REVIEW_REPORT,
    REVIEW_SUMMARY,
)

REPLACE_DIRNAME = "replacement"
REPLACE_REPORT = "replacement-report.json"
BACKUPS_DIRNAME = "backups"
CONFIRMATION_PHRASE = "I_APPROVE_KINTYRE_REPLACE"
BACKUP_FREE_SPACE_MARGIN_BYTES = 1024 * 1024 * 1024


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _configured_staging_root(config: dict[str, Any]) -> Path:
    storage = config.get("storage", {})
    if isinstance(storage, dict) and storage.get("staging_dir"):
        return Path(str(storage["staging_dir"]))

    runtime = config.get("runtime", {})
    if isinstance(runtime, dict) and runtime.get("staging_dir"):
        return Path(str(runtime["staging_dir"]))

    return RUNTIME_DIR / "staging"


def _configured_replacement_root(config: dict[str, Any]) -> Path:
    storage = config.get("storage", {})
    if isinstance(storage, dict) and storage.get("replacement_dir"):
        return Path(str(storage["replacement_dir"]))

    runtime = config.get("runtime", {})
    if isinstance(runtime, dict) and runtime.get("replacement_dir"):
        return Path(str(runtime["replacement_dir"]))

    return RUNTIME_DIR / "replacement"


def _configured_contemporary_root(config: dict[str, Any]) -> Path:
    libraries = config.get("libraries", {})
    if isinstance(libraries, dict):
        entry = (
            libraries.get("contemporary")
            or libraries.get("CONTEMPORARY")
        )
        if isinstance(entry, dict) and entry.get("root"):
            return Path(str(entry["root"]))
        if isinstance(entry, str):
            return Path(entry)

    return LIBRARIES["CONTEMPORARY"]


def _manifest_core(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in (
            "file_count",
            "audio_file_count",
            "total_bytes",
            "files",
        )
    }


def _assert_manifest_matches(
    actual: dict[str, Any],
    expected: dict[str, Any],
    label: str,
) -> None:
    errors = compare_manifests(
        _manifest_core(expected),
        _manifest_core(actual),
    )
    if errors:
        raise ValueError(
            f"{label} manifest does not match retained evidence: "
            + ", ".join(errors)
        )


def _verify_file_evidence(
    evidence: dict[str, Any],
    key: str,
    path: Path,
) -> None:
    item = evidence.get(key)
    if not isinstance(item, dict):
        raise ValueError(f"APPROVE evidence is missing {key}.")

    if item.get("path") != str(path):
        raise ValueError(f"APPROVE evidence path changed for {key}.")

    if item.get("sha256") != sha256_file(path):
        raise ValueError(f"APPROVE evidence digest changed for {key}.")


def _copy_complete_album(source: Path, destination: Path) -> None:
    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing directory: {destination}"
        )
    shutil.copytree(
        source,
        destination,
        symlinks=False,
        copy_function=shutil.copy2,
    )


def _remove_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError(
                f"Unsafe replacement directory entry: {path}"
            )
        shutil.rmtree(path)


def _restore_production(
    production: Path,
    displaced: Path,
    backup_album: Path,
    expected_before: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if production.exists():
        _remove_directory(production)

    if displaced.is_dir():
        os.replace(displaced, production)
        method = "DISPLACED_DIRECTORY"
    elif backup_album.is_dir():
        _copy_complete_album(backup_album, production)
        method = "VERIFIED_BACKUP"
    else:
        raise RuntimeError(
            "Rollback impossible: neither displaced production nor "
            "verified backup exists."
        )

    restored_manifest = build_manifest(production)
    _assert_manifest_matches(
        restored_manifest,
        expected_before,
        "Rolled-back production",
    )
    return method, restored_manifest


def _verify_preconditions(
    txid: str,
    transaction: Path,
    contemporary_root: Path,
) -> dict[str, Any]:
    album = transaction / "album"
    source_manifest_path = transaction / SOURCE_MANIFEST
    after_manifest_path = transaction / FIX_DIRNAME / AFTER_MANIFEST
    approval_path = (
        transaction / APPROVAL_DIRNAME / APPROVAL_REPORT
    )
    review_dir = transaction / REVIEW_DIRNAME

    required = (
        source_manifest_path,
        after_manifest_path,
        approval_path,
        review_dir / REVIEW_REPORT,
        review_dir / REVIEW_FINDINGS,
        review_dir / REVIEW_SUMMARY,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Required D2-D5 evidence is missing: "
            + ", ".join(missing)
        )

    if not album.is_dir():
        raise FileNotFoundError(
            f"Staged album is missing: {album}"
        )

    source_manifest = _read_json(source_manifest_path)
    after_manifest = _read_json(after_manifest_path)
    approval = _read_json(approval_path)

    if source_manifest.get("transaction_id") != txid:
        raise ValueError("COPY transaction ID does not match.")
    if after_manifest.get("transaction_id") != txid:
        raise ValueError("FIX transaction ID does not match.")
    if approval.get("transaction_id") != txid:
        raise ValueError("APPROVE transaction ID does not match.")

    if approval.get("stage") != "APPROVE":
        raise ValueError("Approval stage is invalid.")
    if approval.get("status") != "RECORDED":
        raise ValueError("Approval status is invalid.")
    if approval.get("decision") != "APPROVED":
        raise ValueError(
            "REPLACE requires an exact APPROVED decision."
        )
    if approval.get("approval_valid") is not True:
        raise ValueError("Approval is not valid.")
    if approval.get("review_status") != "PASS":
        raise ValueError("Approved REVIEW status is not PASS.")
    if approval.get("review_recommendation") != "PASS":
        raise ValueError(
            "Approved REVIEW recommendation is not PASS."
        )

    evidence = approval.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("APPROVE evidence is invalid.")

    _verify_file_evidence(
        evidence,
        "review_report",
        review_dir / REVIEW_REPORT,
    )
    _verify_file_evidence(
        evidence,
        "review_findings",
        review_dir / REVIEW_FINDINGS,
    )
    _verify_file_evidence(
        evidence,
        "review_summary",
        review_dir / REVIEW_SUMMARY,
    )
    _verify_file_evidence(
        evidence,
        "fix_after_manifest",
        after_manifest_path,
    )

    fix_evidence = evidence["fix_after_manifest"]
    if (
        fix_evidence.get("manifest_sha256")
        != manifest_digest(after_manifest)
    ):
        raise ValueError(
            "FIX after-manifest digest no longer matches APPROVE."
        )

    production = Path(str(source_manifest.get("source", "")))
    if not production.is_absolute():
        raise ValueError(
            "Production album path must be absolute."
        )
    if not production.is_dir():
        raise FileNotFoundError(
            f"Production album is missing: {production}"
        )
    if production.is_symlink():
        raise ValueError(
            "Production album must not be a symbolic link."
        )

    library_root = contemporary_root.expanduser().resolve(strict=True)
    production_resolved = production.resolve(strict=True)
    if (
        production_resolved == library_root
        or not is_within(production_resolved, library_root)
    ):
        raise ValueError(
            "Production album is outside the configured "
            "CONTEMPORARY library."
        )

    staged_manifest = build_manifest(album)
    production_manifest = build_manifest(production_resolved)

    _assert_manifest_matches(
        staged_manifest,
        after_manifest,
        "Staged album",
    )
    _assert_manifest_matches(
        production_manifest,
        source_manifest,
        "Production before-state",
    )

    if (
        evidence.get("staged_album_manifest_sha256")
        != manifest_digest(staged_manifest)
    ):
        raise ValueError(
            "Staged album no longer matches exact APPROVE evidence."
        )

    return {
        "transaction": transaction,
        "album": album,
        "production": production_resolved,
        "source_manifest": source_manifest,
        "after_manifest": after_manifest,
        "approval": approval,
        "production_manifest": production_manifest,
        "staged_manifest": staged_manifest,
        "approval_path": approval_path,
    }


def _verify_backup_capacity(
    replacement_root: Path,
    required_bytes: int,
) -> dict[str, int]:
    replacement_root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(replacement_root).free
    margin = max(
        BACKUP_FREE_SPACE_MARGIN_BYTES,
        required_bytes // 10,
    )
    if free < required_bytes + margin:
        raise RuntimeError(
            "Insufficient system-drive space for verified backup: "
            f"required={required_bytes} margin={margin} free={free}"
        )
    return {
        "required_backup_bytes": required_bytes,
        "safety_margin_bytes": margin,
        "free_bytes": free,
    }


def run_replace(
    transaction_id: str,
    *,
    execute: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    txid = validate_transaction_id(transaction_id)
    selected_config = load_config() if config is None else config

    staging_root = _configured_staging_root(
        selected_config
    ).expanduser().resolve()
    replacement_root = _configured_replacement_root(
        selected_config
    ).expanduser().resolve()
    contemporary_root = _configured_contemporary_root(
        selected_config
    )

    transaction = staging_root / TRANSACTIONS_DIRNAME / txid
    replace_dir = transaction / REPLACE_DIRNAME
    report_path = replace_dir / REPLACE_REPORT

    if not transaction.is_dir():
        raise FileNotFoundError(
            f"Retained transaction not found: {transaction}"
        )
    if replace_dir.exists():
        raise FileExistsError(
            "Refusing to overwrite existing REPLACE evidence: "
            f"{replace_dir}"
        )

    verified = _verify_preconditions(
        txid,
        transaction,
        contemporary_root,
    )

    production: Path = verified["production"]
    staged: Path = verified["album"]
    production_manifest = verified["production_manifest"]
    staged_manifest = verified["staged_manifest"]

    capacity = _verify_backup_capacity(
        replacement_root,
        production_manifest["total_bytes"],
    )

    preflight = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "stage": "REPLACE",
        "status": "READY" if not execute else "IN_PROGRESS",
        "transaction_id": txid,
        "transaction_directory": str(transaction),
        "production_album": str(production),
        "staged_album": str(staged),
        "approval_report": str(verified["approval_path"]),
        "approval_report_sha256": sha256_file(
            verified["approval_path"]
        ),
        "production_before_manifest_sha256":
            manifest_digest(production_manifest),
        "staged_manifest_sha256":
            manifest_digest(staged_manifest),
        "backup_capacity": capacity,
        "production_modified": False,
    }

    if not execute:
        return preflight

    backup_root = (
        replacement_root / BACKUPS_DIRNAME / txid
    )
    backup_album = backup_root / "album"
    if backup_root.exists():
        raise FileExistsError(
            "Refusing to overwrite existing D6 backup: "
            f"{backup_root}"
        )

    incoming = production.parent / f".kintyre-{txid}-incoming"
    displaced = production.parent / f".kintyre-{txid}-before"

    if incoming.exists() or displaced.exists():
        raise FileExistsError(
            "A prior incomplete replacement workspace exists beside "
            f"production: {incoming} or {displaced}"
        )

    backup_manifest: dict[str, Any] | None = None
    production_after: dict[str, Any] | None = None

    production_displaced = False

    try:
        _copy_complete_album(production, backup_album)
        backup_manifest = build_manifest(backup_album)
        _assert_manifest_matches(
            backup_manifest,
            production_manifest,
            "Verified complete backup",
        )

        _copy_complete_album(staged, incoming)
        incoming_manifest = build_manifest(incoming)
        _assert_manifest_matches(
            incoming_manifest,
            staged_manifest,
            "Prepared replacement",
        )

        os.replace(production, displaced)
        production_displaced = True
        os.replace(incoming, production)

        production_after = build_manifest(production)
        _assert_manifest_matches(
            production_after,
            staged_manifest,
            "Production after-state",
        )

    except Exception as exc:
        if incoming.exists():
            _remove_directory(incoming)

        if not production_displaced:
            failure = {
                **preflight,
                "status": "FAILED_PRE_REPLACE",
                "production_modified": False,
                "failure": str(exc),
                "backup_directory": str(backup_album),
                "backup_manifest_sha256": (
                    manifest_digest(backup_manifest)
                    if backup_manifest is not None
                    else None
                ),
                "rollback_method": None,
                "rollback_manifest_sha256": None,
                "rollback_error": None,
            }

            replace_dir.mkdir(parents=False, exist_ok=False)
            write_json(report_path, failure, immutable=True)

            raise RuntimeError(
                "REPLACE failed before production displacement; "
                f"production remained unchanged: {exc}"
            ) from exc

        rollback_method = None
        rollback_manifest = None
        rollback_error = None

        try:
            rollback_method, rollback_manifest = (
                _restore_production(
                    production,
                    displaced,
                    backup_album,
                    production_manifest,
                )
            )
        except Exception as rollback_exc:
            rollback_error = str(rollback_exc)

        failure = {
            **preflight,
            "status": (
                "ROLLED_BACK"
                if rollback_error is None
                else "ROLLBACK_FAILED"
            ),
            "production_modified": True,
            "failure": str(exc),
            "backup_directory": str(backup_album),
            "backup_manifest_sha256": (
                manifest_digest(backup_manifest)
                if backup_manifest is not None
                else None
            ),
            "rollback_method": rollback_method,
            "rollback_manifest_sha256": (
                manifest_digest(rollback_manifest)
                if rollback_manifest is not None
                else None
            ),
            "rollback_error": rollback_error,
        }

        replace_dir.mkdir(parents=False, exist_ok=False)
        write_json(report_path, failure, immutable=True)

        if rollback_error is not None:
            raise RuntimeError(
                "REPLACE failed and whole-album rollback failed: "
                f"{exc}; rollback: {rollback_error}"
            ) from exc

        raise RuntimeError(
            "REPLACE failed; whole-album rollback succeeded: "
            f"{exc}"
        ) from exc

    if incoming.exists():
        _remove_directory(incoming)
    if displaced.exists():
        _remove_directory(displaced)

    report = {
        **preflight,
        "generated_at": utc_timestamp(),
        "status": "PASS",
        "production_modified": True,
        "backup_directory": str(backup_album),
        "backup_manifest_sha256":
            manifest_digest(backup_manifest),
        "production_after_manifest_sha256":
            manifest_digest(production_after),
        "file_count": production_after["file_count"],
        "audio_file_count":
            production_after["audio_file_count"],
        "total_bytes": production_after["total_bytes"],
        "rollback_available": True,
    }

    replace_dir.mkdir(parents=False, exist_ok=False)
    write_json(report_path, report, immutable=True)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify, back up and replace one approved KINTYRE v2 "
            "album transaction."
        )
    )
    parser.add_argument(
        "transaction_id",
        help="Existing exact APPROVED transaction identifier.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Perform the production replacement.",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help=(
            "Required for execution: "
            f"{CONFIRMATION_PHRASE}"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if (
        args.execute
        and args.confirm != CONFIRMATION_PHRASE
    ):
        raise RuntimeError(
            "Live replacement refused. Supply both --execute and "
            f"--confirm {CONFIRMATION_PHRASE}."
        )

    report = run_replace(
        args.transaction_id,
        execute=args.execute,
    )

    print("KINTYRE v2 REPLACE")
    print(f"Transaction: {report['transaction_id']}")
    print(f"Status: {report['status']}")
    print(
        f"Production: {report['production_album']}"
    )
    print(
        "Production modified: "
        f"{report['production_modified']}"
    )
    if report.get("backup_directory"):
        print(f"Backup: {report['backup_directory']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
