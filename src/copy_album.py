#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any, Iterable

from common import (
    LIBRARIES,
    RUNTIME_DIR,
    SUPPORTED_AUDIO_EXTENSIONS,
    load_config,
    timestamp_slug,
    utc_timestamp,
)

SCHEMA_VERSION = "2.0"
TRANSACTIONS_DIRNAME = "transactions"
SOURCE_MANIFEST = "source-manifest.json"
DESTINATION_MANIFEST = "destination-manifest.json"
COPY_REPORT = "copy-report.json"


def write_json(path: Path, payload: dict[str, Any], *, immutable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        if immutable:
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    finally:
        if temporary.exists():
            temporary.unlink()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _configured_contemporary_root(config: dict[str, Any]) -> Path:
    libraries = config.get("libraries", {})
    if isinstance(libraries, dict):
        entry = libraries.get("contemporary") or libraries.get("CONTEMPORARY")
        if isinstance(entry, dict) and entry.get("root"):
            return Path(str(entry["root"]))
        if isinstance(entry, str):
            return Path(entry)
    return LIBRARIES["CONTEMPORARY"]


def _configured_staging_root(config: dict[str, Any]) -> Path:
    storage = config.get("storage", {})
    if isinstance(storage, dict) and storage.get("staging_dir"):
        return Path(str(storage["staging_dir"]))
    runtime = config.get("runtime", {})
    if isinstance(runtime, dict) and runtime.get("staging_dir"):
        return Path(str(runtime["staging_dir"]))
    return RUNTIME_DIR / "staging"


def _reject_symlink_components(path: Path, root: Path) -> None:
    relative = path.relative_to(root)
    current = root
    if current.is_symlink():
        raise ValueError(f"Library root must not be a symbolic link: {root}")
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"Symbolic links are not allowed in source path: {current}")


def validate_source(source: Path, library_root: Path) -> tuple[Path, Path]:
    root_absolute = library_root.expanduser().absolute()
    source_absolute = source.expanduser().absolute()
    if not is_within(source_absolute, root_absolute) or source_absolute == root_absolute:
        raise ValueError(f"Album must be below CONTEMPORARY root: {root_absolute}")
    _reject_symlink_components(source_absolute, root_absolute)
    root_resolved = root_absolute.resolve(strict=True)
    source_resolved = source_absolute.resolve(strict=True)
    if not is_within(source_resolved, root_resolved) or source_resolved == root_resolved:
        raise ValueError(f"Resolved album escapes CONTEMPORARY root: {source}")
    if not source_resolved.is_dir():
        raise ValueError(f"Album source is not a directory: {source_resolved}")
    return source_resolved, root_resolved


def iter_source_files(source: Path) -> Iterable[Path]:
    for current_text, directory_names, file_names in os.walk(source, topdown=True, followlinks=False):
        current = Path(current_text)
        directory_names.sort()
        file_names.sort()
        for name in directory_names:
            candidate = current / name
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"Symbolic links are not allowed: {candidate}")
            if not stat.S_ISDIR(mode):
                raise ValueError(f"Unsupported directory entry: {candidate}")
        for name in file_names:
            candidate = current / name
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"Symbolic links are not allowed: {candidate}")
            if not stat.S_ISREG(mode):
                raise ValueError(f"Only regular files may be copied: {candidate}")
            yield candidate


def build_manifest(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    audio_count = 0
    total_bytes = 0
    for path in iter_source_files(root):
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        if path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
            audio_count += 1
        total_bytes += size
        files.append({"relative_path": relative, "size_bytes": size, "sha256": sha256_file(path)})
    files.sort(key=lambda item: item["relative_path"])
    if not files:
        raise ValueError(f"Album directory is empty: {root}")
    if audio_count == 0:
        raise ValueError(f"Album contains no supported audio files: {root}")
    return {"file_count": len(files), "audio_file_count": audio_count, "total_bytes": total_bytes, "files": files}


def manifest_digest(manifest: dict[str, Any]) -> str:
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def copy_files(source: Path, destination: Path, manifest: dict[str, Any]) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for entry in manifest["files"]:
        relative = Path(entry["relative_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe manifest path: {entry['relative_path']}")
        source_file = source / relative
        destination_file = destination / relative
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file, follow_symlinks=False)


def compare_manifests(source_manifest: dict[str, Any], destination_manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("file_count", "audio_file_count", "total_bytes", "files"):
        if source_manifest.get(key) != destination_manifest.get(key):
            errors.append(f"Manifest mismatch: {key}")
    return errors


def default_transaction_id(source: Path) -> str:
    suffix = hashlib.sha256(str(source).encode("utf-8")).hexdigest()[:12]
    return f"{timestamp_slug()}-{suffix}"


def validate_transaction_id(value: str) -> str:
    if not value or value in {".", ".."} or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in value):
        raise ValueError("Transaction ID may contain only letters, numbers, hyphens and underscores.")
    return value


def run_copy(source: Path, *, transaction_id: str | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_config = load_config() if config is None else config
    library_root = _configured_contemporary_root(selected_config)
    source_resolved, library_resolved = validate_source(source, library_root)
    staging_root = _configured_staging_root(selected_config).expanduser().absolute()
    staging_root.mkdir(parents=True, exist_ok=True)
    staging_resolved = staging_root.resolve(strict=True)
    if is_within(staging_resolved, library_resolved) or is_within(library_resolved, staging_resolved):
        raise ValueError("Staging and production library roots must be separate.")
    txid = validate_transaction_id(transaction_id or default_transaction_id(source_resolved))
    transaction = staging_resolved / TRANSACTIONS_DIRNAME / txid
    album_copy = transaction / "album"
    transaction.mkdir(parents=True, exist_ok=False)
    try:
        source_manifest = build_manifest(source_resolved)
        source_payload = {"schema_version": SCHEMA_VERSION, "transaction_id": txid, "library": "CONTEMPORARY", "source": str(source_resolved), **source_manifest}
        write_json(transaction / SOURCE_MANIFEST, source_payload, immutable=True)
        copy_files(source_resolved, album_copy, source_manifest)
        source_after = build_manifest(source_resolved)
        if source_after != source_manifest:
            raise RuntimeError("Source album changed during COPY; transaction is invalid.")
        destination_manifest = build_manifest(album_copy)
        destination_payload = {"schema_version": SCHEMA_VERSION, "transaction_id": txid, "destination": str(album_copy), **destination_manifest}
        write_json(transaction / DESTINATION_MANIFEST, destination_payload, immutable=True)
        errors = compare_manifests(source_manifest, destination_manifest)
        report = {"schema_version": SCHEMA_VERSION, "generated_at": utc_timestamp(), "stage": "COPY", "status": "PASS" if not errors else "FAIL", "transaction_id": txid, "transaction_directory": str(transaction), "library": "CONTEMPORARY", "source": str(source_resolved), "destination": str(album_copy), "source_manifest": str(transaction / SOURCE_MANIFEST), "source_manifest_sha256": manifest_digest(source_payload), "destination_manifest": str(transaction / DESTINATION_MANIFEST), "destination_manifest_sha256": manifest_digest(destination_payload), "file_count": source_manifest["file_count"], "audio_file_count": source_manifest["audio_file_count"], "total_bytes": source_manifest["total_bytes"], "verification_errors": errors}
        write_json(transaction / COPY_REPORT, report, immutable=True)
        if errors:
            raise RuntimeError("Destination verification failed.")
        return report
    except Exception:
        if transaction.exists() and not (transaction / COPY_REPORT).exists():
            shutil.rmtree(transaction)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and verify an isolated COPY transaction for one CONTEMPORARY album.")
    parser.add_argument("album", type=Path, help="Existing album directory below the configured CONTEMPORARY root.")
    parser.add_argument("--transaction-id", help="Optional unique transaction identifier.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_copy(args.album, transaction_id=args.transaction_id)
    print("KINTYRE v2 COPY")
    print(f"Transaction: {report['transaction_id']}")
    print(f"Files: {report['file_count']}")
    print(f"Bytes: {report['total_bytes']}")
    print(f"Status: {report['status']}")
    print(f"Created: {report['transaction_directory']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

