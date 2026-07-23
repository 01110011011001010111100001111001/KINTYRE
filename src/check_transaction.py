#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import SUPPORTED_AUDIO_EXTENSIONS, load_config, utc_timestamp
from copy_album import (
    SCHEMA_VERSION,
    TRANSACTIONS_DIRNAME,
    build_manifest,
    manifest_digest,
    validate_transaction_id,
    write_json,
)
from fix_album import AFTER_MANIFEST, FIX_DIRNAME
from replace_transaction import (
    REPLACE_DIRNAME,
    REPLACE_REPORT,
    _assert_manifest_matches,
    _configured_contemporary_root,
    _configured_staging_root,
    _read_json,
    sha256_file,
)
from review_album import read_metadata

CHECK_DIRNAME = "check"
CHECK_REPORT = "check-report.json"


def _audio_paths(album: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in album.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ),
        key=lambda path: path.relative_to(album).as_posix(),
    )


def _verify_metadata(album: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    unreadable: list[str] = []
    embedded_artwork_files = 0

    for path in _audio_paths(album):
        relative = path.relative_to(album).as_posix()

        try:
            metadata = read_metadata(path)
        except Exception as exc:
            metadata = {
                "status": "unavailable",
                "error": str(exc),
                "fields": {},
                "embedded_artwork": None,
            }

        status = str(metadata.get("status", "unavailable"))
        if status != "readable":
            unreadable.append(relative)

        if metadata.get("embedded_artwork") is True:
            embedded_artwork_files += 1

        records.append(
            {
                "path": relative,
                "status": status,
                "error": str(metadata.get("error", "")),
                "fields": metadata.get("fields", {}),
                "embedded_artwork": metadata.get(
                    "embedded_artwork"
                ),
            }
        )

    external_artwork = sorted(
        path.relative_to(album).as_posix()
        for path in album.rglob("*")
        if path.is_file()
        and path.suffix.lower()
        in {".jpg", ".jpeg", ".png", ".webp"}
    )

    return {
        "audio_file_count": len(records),
        "readable_audio_file_count": (
            len(records) - len(unreadable)
        ),
        "unreadable_audio_files": unreadable,
        "embedded_artwork_file_count": embedded_artwork_files,
        "external_artwork_files": external_artwork,
        "artwork_present": bool(
            embedded_artwork_files or external_artwork
        ),
        "records": records,
    }


def run_check(
    transaction_id: str,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    txid = validate_transaction_id(transaction_id)
    selected_config = load_config() if config is None else config

    staging_root = _configured_staging_root(
        selected_config
    ).expanduser().resolve()
    contemporary_root = _configured_contemporary_root(
        selected_config
    ).expanduser().resolve(strict=True)

    transaction = staging_root / TRANSACTIONS_DIRNAME / txid
    replace_dir = transaction / REPLACE_DIRNAME
    replace_report_path = replace_dir / REPLACE_REPORT
    check_dir = transaction / CHECK_DIRNAME
    report_path = check_dir / CHECK_REPORT

    if not transaction.is_dir():
        raise FileNotFoundError(
            f"Retained transaction not found: {transaction}"
        )
    if check_dir.exists():
        raise FileExistsError(
            "Refusing to overwrite existing CHECK evidence: "
            f"{check_dir}"
        )
    if not replace_report_path.is_file():
        raise FileNotFoundError(
            f"Successful REPLACE evidence is missing: "
            f"{replace_report_path}"
        )

    replacement = _read_json(replace_report_path)

    if replacement.get("stage") != "REPLACE":
        raise ValueError("Replacement stage is invalid.")
    if replacement.get("status") != "PASS":
        raise ValueError(
            "CHECK requires a successful REPLACE report."
        )
    if replacement.get("transaction_id") != txid:
        raise ValueError(
            "REPLACE transaction ID does not match."
        )
    if replacement.get("production_modified") is not True:
        raise ValueError(
            "REPLACE does not record a completed production change."
        )

    production = Path(
        str(replacement.get("production_album", ""))
    )
    backup = Path(
        str(replacement.get("backup_directory", ""))
    )
    staged = transaction / "album"
    after_manifest_path = (
        transaction / FIX_DIRNAME / AFTER_MANIFEST
    )

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

    production_resolved = production.resolve(strict=True)
    try:
        production_resolved.relative_to(contemporary_root)
    except ValueError as exc:
        raise ValueError(
            "Production album is outside the configured "
            "CONTEMPORARY library."
        ) from exc

    if production_resolved == contemporary_root:
        raise ValueError(
            "Production album must not be the library root."
        )
    if not staged.is_dir():
        raise FileNotFoundError(
            f"Staged album is missing: {staged}"
        )
    if not backup.is_dir():
        raise FileNotFoundError(
            f"Verified backup is missing: {backup}"
        )
    if not after_manifest_path.is_file():
        raise FileNotFoundError(
            f"FIX after-manifest is missing: "
            f"{after_manifest_path}"
        )

    retained_after = _read_json(after_manifest_path)
    production_manifest = build_manifest(production_resolved)
    staged_manifest = build_manifest(staged)
    backup_manifest = build_manifest(backup)

    _assert_manifest_matches(
        production_manifest,
        retained_after,
        "Current production",
    )
    _assert_manifest_matches(
        production_manifest,
        staged_manifest,
        "Current production versus staged album",
    )

    expected_production_digest = replacement.get(
        "production_after_manifest_sha256"
    )
    if (
        expected_production_digest
        != manifest_digest(production_manifest)
    ):
        raise ValueError(
            "Current production digest does not match "
            "REPLACE evidence."
        )

    expected_backup_digest = replacement.get(
        "backup_manifest_sha256"
    )
    if (
        expected_backup_digest
        != manifest_digest(backup_manifest)
    ):
        raise ValueError(
            "Current backup digest does not match "
            "REPLACE evidence."
        )

    metadata = _verify_metadata(production_resolved)
    warnings: list[str] = []

    if metadata["unreadable_audio_files"]:
        warnings.append(
            "One or more production audio files could not be "
            "read independently by Mutagen."
        )
    if not metadata["artwork_present"]:
        warnings.append(
            "No embedded or external album artwork was detected."
        )

    status = "PASS_WITH_WARNINGS" if warnings else "PASS"

    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "stage": "CHECK",
        "status": status,
        "transaction_id": txid,
        "transaction_directory": str(transaction),
        "production_album": str(production_resolved),
        "backup_directory": str(backup.resolve()),
        "replace_report": str(replace_report_path),
        "replace_report_sha256": sha256_file(
            replace_report_path
        ),
        "production_manifest_sha256": manifest_digest(
            production_manifest
        ),
        "staged_manifest_sha256": manifest_digest(
            staged_manifest
        ),
        "backup_manifest_sha256": manifest_digest(
            backup_manifest
        ),
        "file_count": production_manifest["file_count"],
        "audio_file_count": production_manifest[
            "audio_file_count"
        ],
        "total_bytes": production_manifest["total_bytes"],
        "checks": {
            "replacement_evidence": "PASS",
            "production_matches_approved_staging": "PASS",
            "unexpected_file_check": "PASS",
            "backup_integrity": "PASS",
            "audio_essence": (
                "PASS_BOUND_TO_VERIFIED_FIX_AND_BYTE_IDENTICAL_COPY"
            ),
            "metadata_readability": (
                "PASS"
                if not metadata["unreadable_audio_files"]
                else "WARNING"
            ),
            "artwork": (
                "PASS"
                if metadata["artwork_present"]
                else "WARNING"
            ),
            "music_assistant": "NOT_RUN",
        },
        "metadata": metadata,
        "music_assistant": {
            "status": "NOT_RUN",
            "reason": (
                "Transaction-scoped Music Assistant lookup is not "
                "yet implemented; MA remains a non-authoritative "
                "consumer."
            ),
        },
        "warnings": warnings,
        "final_disposition": (
            "CERTIFIED"
            if status == "PASS"
            else "CERTIFIED_WITH_WARNINGS"
        ),
        "backup_retention_recommendation": "KEEP",
    }

    check_dir.mkdir(parents=False, exist_ok=False)
    write_json(report_path, report, immutable=True)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Certify one completed KINTYRE v2 album replacement."
        )
    )
    parser.add_argument(
        "transaction_id",
        help="Existing successful REPLACE transaction identifier.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(args.transaction_id)

    print(f"Status: {report['status']}")
    print(
        "Disposition: "
        f"{report['final_disposition']}"
    )
    print(
        "Evidence: "
        f"{Path(report['transaction_directory']) / CHECK_DIRNAME}"
    )
    return 0 if report["status"] in {
        "PASS",
        "PASS_WITH_WARNINGS",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
