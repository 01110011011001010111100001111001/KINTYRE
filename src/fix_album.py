#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

from common import RUNTIME_DIR, SUPPORTED_AUDIO_EXTENSIONS, load_config, utc_timestamp
from copy_album import (
    COPY_REPORT,
    DESTINATION_MANIFEST,
    SCHEMA_VERSION,
    TRANSACTIONS_DIRNAME,
    build_manifest,
    manifest_digest,
    validate_transaction_id,
    write_json,
)

FIX_DIRNAME = "fix"
FIX_REPORT = "fix-report.json"
BEFORE_MANIFEST = "before-manifest.json"
AFTER_MANIFEST = "after-manifest.json"
AUDIO_ESSENCE_BEFORE = "audio-essence-before.json"
AUDIO_ESSENCE_AFTER = "audio-essence-after.json"
BEETS_CONFIG = "beets-config.yaml"
STDOUT_LOG = "stdout.txt"
STDERR_LOG = "stderr.txt"
BEETS_LIBRARY = "beets-library.db"


def _configured_staging_root(config: dict[str, Any]) -> Path:
    storage = config.get("storage", {})
    if isinstance(storage, dict) and storage.get("staging_dir"):
        return Path(str(storage["staging_dir"]))
    runtime = config.get("runtime", {})
    if isinstance(runtime, dict) and runtime.get("staging_dir"):
        return Path(str(runtime["staging_dir"]))
    return RUNTIME_DIR / "staging"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _verify_copy_evidence(transaction: Path, album: Path) -> dict[str, Any]:
    copy_report = _read_json(transaction / COPY_REPORT)
    if copy_report.get("stage") != "COPY" or copy_report.get("status") != "PASS":
        raise ValueError("Transaction does not contain a successful COPY report.")
    destination = _read_json(transaction / DESTINATION_MANIFEST)
    current = build_manifest(album)
    for key in ("file_count", "audio_file_count", "total_bytes", "files"):
        if destination.get(key) != current.get(key):
            raise ValueError(f"Staged album no longer matches COPY evidence: {key}")
    return destination


def _tool_version(executable: str) -> str:
    result = subprocess.run(
        [executable, "version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0 or not output:
        raise RuntimeError(f"Unable to determine Beets version using {executable}")
    return output.splitlines()[0]


def _ffprobe_packet_hashes(path: Path, executable: str) -> dict[str, Any]:
    command = [
        executable,
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_packets",
        "-show_entries",
        "packet=stream_index,size,data_hash",
        "-show_data_hash",
        "sha256",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    packets = payload.get("packets", [])
    normalized = [
        {
            "stream_index": packet.get("stream_index"),
            "size": packet.get("size"),
            "data_hash": packet.get("data_hash"),
        }
        for packet in packets
    ]
    if not normalized:
        raise RuntimeError(f"No audio packets reported by ffprobe: {path}")
    encoded = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "packet_count": len(normalized),
        "packet_data_sha256": sha256_bytes(encoded),
    }


def build_audio_essence_manifest(album: Path, ffprobe_executable: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for path in sorted(album.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
            evidence = _ffprobe_packet_hashes(path, ffprobe_executable)
            files.append({"relative_path": path.relative_to(album).as_posix(), **evidence})
    if not files:
        raise ValueError(f"No supported audio files in staged album: {album}")
    return {"files": files}


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_beets_config(album: Path, fix_dir: Path) -> str:
    return "\n".join(
        [
            f"directory: {_yaml_quote(str(album))}",
            f"library: {_yaml_quote(str(fix_dir / BEETS_LIBRARY))}",
            "plugins: musicbrainz",
            "import:",
            "  write: yes",
            "  copy: no",
            "  move: no",
            "  autotag: yes",
            "  resume: no",
            "  incremental: no",
            "  quiet: yes",
            "  quiet_fallback: skip",
            "  duplicate_action: skip",
            "musicbrainz:",
            "  search_limit: 5",
            "  data_source_mismatch_penalty: 0.5",
            "  search_query_ascii: no",
            "  genres: no",
            "  external_ids:",
            "    discogs: no",
            "    bandcamp: no",
            "    spotify: no",
            "    deezer: no",
            "    tidal: no",
            "",
        ]
    )


def _make_read_only(path: Path) -> None:
    if path.is_file():
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def run_fix(
    transaction_id: str,
    *,
    config: dict[str, Any] | None = None,
    beet_executable: str | None = None,
    ffprobe_executable: str | None = None,
) -> dict[str, Any]:
    txid = validate_transaction_id(transaction_id)
    selected_config = load_config() if config is None else config
    staging_root = _configured_staging_root(selected_config).expanduser().resolve()
    transaction = staging_root / TRANSACTIONS_DIRNAME / txid
    album = transaction / "album"
    if not transaction.is_dir() or not album.is_dir():
        raise FileNotFoundError(f"Retained COPY transaction not found: {transaction}")

    fix_dir = transaction / FIX_DIRNAME
    if fix_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing FIX evidence: {fix_dir}")

    _verify_copy_evidence(transaction, album)

    beet = beet_executable or shutil.which("beet")
    ffprobe = ffprobe_executable or shutil.which("ffprobe")
    if not beet:
        raise FileNotFoundError("Beets executable not found.")
    if not ffprobe:
        raise FileNotFoundError("ffprobe executable not found.")

    fix_dir.mkdir(parents=False, exist_ok=False)

    started_at = utc_timestamp()
    report: dict[str, Any] | None = None
    try:
        before = build_manifest(album)
        before_payload = {
            "schema_version": SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **before,
        }
        write_json(fix_dir / BEFORE_MANIFEST, before_payload)

        essence_before = {
            "schema_version": SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **build_audio_essence_manifest(album, ffprobe),
        }
        write_json(fix_dir / AUDIO_ESSENCE_BEFORE, essence_before)

        config_text = build_beets_config(album, fix_dir)
        config_path = fix_dir / BEETS_CONFIG
        config_path.write_text(config_text, encoding="utf-8")

        version = _tool_version(beet)
        command = [
            beet,
            "-c",
            str(config_path),
            "-l",
            str(fix_dir / BEETS_LIBRARY),
            "-d",
            str(album),
            "-p",
            "musicbrainz",
            "import",
            "--quiet",
            "--nocopy",
            "--nomove",
            "--write",
            "--autotag",
            "--noresume",
            str(album),
        ]
        environment = os.environ.copy()
        environment["XDG_CACHE_HOME"] = str(fix_dir / "cache")
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
            env=environment,
        )
        (fix_dir / STDOUT_LOG).write_text(result.stdout, encoding="utf-8")
        (fix_dir / STDERR_LOG).write_text(result.stderr, encoding="utf-8")

        after = build_manifest(album)
        after_payload = {
            "schema_version": SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **after,
        }
        write_json(fix_dir / AFTER_MANIFEST, after_payload)

        essence_after = {
            "schema_version": SCHEMA_VERSION,
            "transaction_id": txid,
            "stage": "FIX",
            **build_audio_essence_manifest(album, ffprobe),
        }
        write_json(fix_dir / AUDIO_ESSENCE_AFTER, essence_after)

        errors: list[str] = []
        before_paths = [entry["relative_path"] for entry in before["files"]]
        after_paths = [entry["relative_path"] for entry in after["files"]]
        if before_paths != after_paths:
            errors.append("FIX changed the staged album file set.")
        if essence_before["files"] != essence_after["files"]:
            errors.append("FIX changed audio essence.")
        if result.returncode != 0:
            errors.append(f"Beets exited with status {result.returncode}.")

        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": utc_timestamp(),
            "stage": "FIX",
            "status": "PASS" if not errors else "FAIL",
            "transaction_id": txid,
            "transaction_directory": str(transaction),
            "album": str(album),
            "tool": {
                "name": "beets",
                "executable": beet,
                "version": version,
                "configuration": str(config_path),
                "configuration_sha256": sha256_file(config_path),
                "command": command,
            },
            "execution": {
                "started_at": started_at,
                "finished_at": utc_timestamp(),
                "exit_code": result.returncode,
                "stdout": str(fix_dir / STDOUT_LOG),
                "stderr": str(fix_dir / STDERR_LOG),
            },
            "evidence": {
                "before_manifest": str(fix_dir / BEFORE_MANIFEST),
                "before_manifest_sha256": manifest_digest(before_payload),
                "after_manifest": str(fix_dir / AFTER_MANIFEST),
                "after_manifest_sha256": manifest_digest(after_payload),
                "audio_essence_before": str(fix_dir / AUDIO_ESSENCE_BEFORE),
                "audio_essence_after": str(fix_dir / AUDIO_ESSENCE_AFTER),
            },
            "file_hashes_changed": before["files"] != after["files"],
            "verification_errors": errors,
        }
        write_json(fix_dir / FIX_REPORT, report)

        for path in sorted(fix_dir.rglob("*")):
            _make_read_only(path)

        if errors:
            raise RuntimeError("FIX verification failed; inspect retained evidence.")
        return report
    except Exception:
        if report is None and fix_dir.exists():
            shutil.rmtree(fix_dir)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the bounded KINTYRE v2 FIX workflow against one retained COPY transaction."
    )
    parser.add_argument("transaction_id", help="Existing successful COPY transaction identifier.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_fix(args.transaction_id)
    print("KINTYRE v2 FIX")
    print(f"Transaction: {report['transaction_id']}")
    print(f"Tool: {report['tool']['version']}")
    print(f"Tags changed: {'yes' if report['file_hashes_changed'] else 'no'}")
    print(f"Status: {report['status']}")
    print(f"Evidence: {Path(report['transaction_directory']) / FIX_DIRNAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
