#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from common import RUNTIME_DIR, load_config, utc_timestamp
from copy_album import (
    SCHEMA_VERSION,
    TRANSACTIONS_DIRNAME,
    build_manifest,
    manifest_digest,
    validate_transaction_id,
    write_json,
)
from fix_album import AFTER_MANIFEST, FIX_DIRNAME
from review_album import (
    REVIEW_DIRNAME,
    REVIEW_FINDINGS,
    REVIEW_REPORT,
    REVIEW_SUMMARY,
)

APPROVAL_DIRNAME = "approval"
APPROVAL_REPORT = "approval-report.json"
ALLOWED_DECISIONS = frozenset(
    {"PENDING", "APPROVED", "REJECTED", "DEFERRED"}
)


def _configured_staging_root(config: dict[str, Any]) -> Path:
    storage = config.get("storage", {})
    if isinstance(storage, dict) and storage.get("staging_dir"):
        return Path(str(storage["staging_dir"]))

    runtime = config.get("runtime", {})
    if isinstance(runtime, dict) and runtime.get("staging_dir"):
        return Path(str(runtime["staging_dir"]))

    return RUNTIME_DIR / "staging"


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


def validate_decision(value: str) -> str:
    decision = value.strip().upper()
    if decision not in ALLOWED_DECISIONS:
        allowed = ", ".join(sorted(ALLOWED_DECISIONS))
        raise ValueError(f"Decision must be one of: {allowed}.")
    return decision


def run_approve(
    transaction_id: str,
    decision: str,
    *,
    operator: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    txid = validate_transaction_id(transaction_id)
    selected_config = load_config() if config is None else config
    staging_root = _configured_staging_root(
        selected_config
    ).expanduser().resolve()

    transaction = staging_root / TRANSACTIONS_DIRNAME / txid
    album = transaction / "album"
    review_dir = transaction / REVIEW_DIRNAME
    approval_dir = transaction / APPROVAL_DIRNAME

    if not transaction.is_dir() or not album.is_dir():
        raise FileNotFoundError(
            f"Retained transaction not found: {transaction}"
        )

    if approval_dir.exists():
        raise FileExistsError(
            "Refusing to overwrite existing APPROVE evidence: "
            f"{approval_dir}"
        )

    review_paths = (
        review_dir / REVIEW_REPORT,
        review_dir / REVIEW_FINDINGS,
        review_dir / REVIEW_SUMMARY,
    )
    after_manifest_path = transaction / FIX_DIRNAME / AFTER_MANIFEST
    required_paths = (*review_paths, after_manifest_path)
    missing = [str(path) for path in required_paths if not path.is_file()]

    if missing:
        raise FileNotFoundError(
            "Required REVIEW/FIX evidence is missing: "
            + ", ".join(missing)
        )

    review_report = _read_json(review_dir / REVIEW_REPORT)
    review_findings = _read_json(review_dir / REVIEW_FINDINGS)
    after_manifest = _read_json(after_manifest_path)

    if (
        review_report.get("stage") != "REVIEW"
        or review_report.get("status") != "PASS"
    ):
        raise ValueError(
            "Transaction does not contain a successful REVIEW report."
        )

    if review_findings.get("stage") != "REVIEW":
        raise ValueError("REVIEW findings stage is invalid.")

    for label, payload in (
        ("REVIEW report", review_report),
        ("REVIEW findings", review_findings),
        ("FIX after manifest", after_manifest),
    ):
        if payload.get("transaction_id") != txid:
            raise ValueError(f"{label} transaction ID does not match.")

    if review_findings.get("recommendation") != "PASS":
        raise ValueError("REVIEW findings do not recommend PASS.")

    current_manifest = build_manifest(album)
    for key in ("file_count", "audio_file_count", "total_bytes", "files"):
        if current_manifest.get(key) != after_manifest.get(key):
            raise ValueError(
                "Staged album changed after REVIEW and cannot be approved: "
                f"{key}."
            )

    selected_decision = validate_decision(decision)
    selected_operator = operator.strip() if operator else None

    evidence = {
        "review_report": {
            "path": str(review_dir / REVIEW_REPORT),
            "sha256": sha256_file(review_dir / REVIEW_REPORT),
        },
        "review_findings": {
            "path": str(review_dir / REVIEW_FINDINGS),
            "sha256": sha256_file(review_dir / REVIEW_FINDINGS),
        },
        "review_summary": {
            "path": str(review_dir / REVIEW_SUMMARY),
            "sha256": sha256_file(review_dir / REVIEW_SUMMARY),
        },
        "fix_after_manifest": {
            "path": str(after_manifest_path),
            "sha256": sha256_file(after_manifest_path),
            "manifest_sha256": manifest_digest(after_manifest),
        },
        "staged_album_manifest_sha256": manifest_digest(current_manifest),
    }

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_timestamp(),
        "stage": "APPROVE",
        "status": "RECORDED",
        "transaction_id": txid,
        "transaction_directory": str(transaction),
        "album": str(album),
        "decision": selected_decision,
        "operator": selected_operator,
        "review_status": review_report.get("status"),
        "review_recommendation": review_findings.get("recommendation"),
        "evidence": evidence,
        "approval_valid": True,
    }

    approval_dir.mkdir(parents=False, exist_ok=False)
    try:
        write_json(
            approval_dir / APPROVAL_REPORT,
            report,
            immutable=True,
        )
    except Exception:
        if approval_dir.exists():
            for path in approval_dir.iterdir():
                path.chmod(0o600)
                path.unlink()
            approval_dir.rmdir()
        raise

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record an immutable album-level decision for one successful "
            "KINTYRE v2 REVIEW transaction."
        )
    )
    parser.add_argument(
        "transaction_id",
        help="Existing successful REVIEW transaction identifier.",
    )
    parser.add_argument(
        "decision",
        choices=sorted(ALLOWED_DECISIONS),
        type=str.upper,
        help="Album-level decision.",
    )
    parser.add_argument(
        "--operator",
        help="Optional operator name or identifier retained in evidence.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_approve(
        args.transaction_id,
        args.decision,
        operator=args.operator,
    )

    print("KINTYRE v2 APPROVE")
    print(f"Transaction: {report['transaction_id']}")
    print(f"Decision: {report['decision']}")
    print(
        "Evidence: "
        f"{Path(report['transaction_directory']) / APPROVAL_DIRNAME}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
