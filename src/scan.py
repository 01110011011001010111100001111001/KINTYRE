#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml


PROJECT_ROOT = Path.home() / "kintyre-dam"
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError("Configuration file is empty or invalid.")

    protection = config.get("protection", {})
    if protection.get("read_only") is not True:
        raise RuntimeError("Safety check failed: read_only must be true.")

    forbidden = (
        "allow_tag_writes",
        "allow_renames",
        "allow_moves",
        "allow_deletes",
    )

    for setting in forbidden:
        if protection.get(setting) is not False:
            raise RuntimeError(f"Safety check failed: {setting} must be false.")

    return config


def scan_library(config: dict) -> dict:
    storage = config["storage"]
    scan_config = config["scan"]

    music_root = Path(storage["music_root"])
    reports_dir = Path(storage["reports_dir"])

    if not music_root.is_dir():
        raise FileNotFoundError(f"Music root not found: {music_root}")

    reports_dir.mkdir(parents=True, exist_ok=True)

    supported = {
        f".{extension.lower().lstrip('.')}"
        for extension in scan_config.get("include", [])
    }

    excluded = set(scan_config.get("exclude_directories", []))
    follow_links = bool(scan_config.get("follow_symbolic_links", False))

    format_counts: Counter[str] = Counter()
    total_audio_files = 0
    total_audio_bytes = 0
    unreadable_files: list[str] = []

    for path in music_root.rglob("*"):
        try:
            if path.is_symlink() and not follow_links:
                continue

            if any(part in excluded for part in path.parts):
                continue

            if not path.is_file():
                continue

            if path.name.startswith("._"):
                continue

            extension = path.suffix.lower()

            if extension not in supported:
                continue

            total_audio_files += 1
            format_counts[extension.lstrip(".")] += 1

            try:
                total_audio_bytes += path.stat().st_size
            except OSError:
                unreadable_files.append(str(path))

        except OSError:
            unreadable_files.append(str(path))

    timestamp = datetime.now().astimezone()

    return {
        "project": config["project"]["name"],
        "mode": config["project"]["mode"],
        "read_only": True,
        "scan_started": timestamp.isoformat(),
        "music_root": str(music_root),
        "total_audio_files": total_audio_files,
        "total_audio_bytes": total_audio_bytes,
        "total_audio_gib": round(total_audio_bytes / (1024 ** 3), 2),
        "formats": dict(sorted(format_counts.items())),
        "unreadable_file_count": len(unreadable_files),
        "unreadable_files": unreadable_files,
    }


def main() -> int:
    try:
        config = load_config()
        report = scan_library(config)

        reports_dir = Path(config["storage"]["reports_dir"])
        output_path = reports_dir / "scan-summary.json"

        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)

        print(f"Audio files: {report['total_audio_files']}")
        print(f"Audio size:  {report['total_audio_gib']} GiB")
        print(f"Unreadable:  {report['unreadable_file_count']}")
        print(f"Report:      {output_path}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
