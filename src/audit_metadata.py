#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import mutagen
import yaml

PROJECT_ROOT = Path.home() / "kintyre-dam"
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".m4p",
    ".wma",
    ".wav",
    ".aif",
    ".aiff",
    ".ogg",
}


def first_value(tags: Any, names: tuple[str, ...]) -> str:
    if not tags:
        return ""

    for name in names:
        value = tags.get(name)

        if value is None:
            continue

        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""

        value = str(value).strip()

        if value:
            return value

    return ""

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".m4p",
    ".wma",
    ".wav",
    ".aif",
    ".aiff",
    ".ogg",
}


def first_value(tags: Any, names: tuple[str, ...]) -> str:
    if not tags:
        return ""

    for name in names:
        value = tags.get(name)

        if value is None:
            continue

        if isinstance(value, (list, tuple)):
            value = value[0] if value else ""

        value = str(value).strip()

        if value:
            return value

    return ""


def read_metadata(path: Path) -> dict[str, str]:
    audio = mutagen.File(path, easy=True)

    if audio is None:
        raise ValueError("Unsupported or unreadable audio metadata")

    tags = audio.tags or {}

    return {
        "title": first_value(tags, ("title",)),
        "artist": first_value(tags, ("artist",)),
        "album": first_value(tags, ("album",)),
        "albumartist": first_value(
            tags,
            ("albumartist", "album artist", "album_artist"),
        ),
        "tracknumber": first_value(tags, ("tracknumber", "track")),
        "date": first_value(tags, ("date", "year")),
        "genre": first_value(tags, ("genre",)),
    }


def load_config() -> dict[str, Any]:
    with CONFIG_FILE.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    protection = config.get("protection", {})

    if protection.get("read_only") is not True:
        raise RuntimeError("Safety check failed: read_only must be true")

    for setting in (
        "allow_tag_writes",
        "allow_renames",
        "allow_moves",
        "allow_deletes",
    ):
        if protection.get(setting) is not False:
            raise RuntimeError(
                f"Safety check failed: {setting} must be false"
            )

    return config


def audit_library(name: str, root: Path, reports_dir: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    format_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    audio_count = 0

    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or path.name.startswith("._")
            or path.suffix.lower() not in SUPPORTED_EXTENSIONS
        ):
            continue

        audio_count += 1
        format_counts[path.suffix.lower().lstrip(".")] += 1

        try:
            metadata = read_metadata(path)
        except Exception as exc:
            issue_counts["metadata_error"] += 1
            issues.append({
                "library": name,
                "path": str(path),
                "issue": "metadata_error",
                "value": str(exc),
            })
            continue

        required_fields = {
            "missing_title": metadata["title"],
            "missing_artist": metadata["artist"],
            "missing_album": metadata["album"],
            "missing_albumartist": metadata["albumartist"],
            "missing_tracknumber": metadata["tracknumber"],
            "missing_date": metadata["date"],
        }

        for issue, value in required_fields.items():
            if not value:
                issue_counts[issue] += 1
                issues.append({
                    "library": name,
                    "path": str(path),
                    "issue": issue,
                    "value": "",
                })

        if metadata["album"].strip().lower() == "unknown album":
            issue_counts["unknown_album"] += 1
            issues.append({
                "library": name,
                "path": str(path),
                "issue": "unknown_album",
                "value": metadata["album"],
            })

        if metadata["artist"].strip().lower() == "unknown artist":
            issue_counts["unknown_artist"] += 1
            issues.append({
                "library": name,
                "path": str(path),
                "issue": "unknown_artist",
                "value": metadata["artist"],
            })

    csv_path = reports_dir / f"{name.lower()}-metadata-issues.csv"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["library", "path", "issue", "value"],
        )
        writer.writeheader()
        writer.writerows(issues)

    return {
        "library": name,
        "root": str(root),
        "audio_files": audio_count,
        "formats": dict(sorted(format_counts.items())),
        "issue_counts": dict(sorted(issue_counts.items())),
        "issue_rows": len(issues),
        "csv_report": str(csv_path),
    }


def main() -> int:
    config = load_config()

    reports_dir = Path(config["storage"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    for library in config["libraries"].values():
        if not library.get("enabled", False):
            continue

        name = library["name"]
        root = Path(library["root"])

        if not root.is_dir():
            raise FileNotFoundError(f"Library path not found: {root}")

        print(f"Auditing {name}: {root}")
        results.append(audit_library(name, root, reports_dir))

    summary_path = reports_dir / "metadata-audit-summary.json"

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)

    print()

    for result in results:
        print(
            f"{result['library']}: "
            f"{result['audio_files']} audio files, "
            f"{result['issue_rows']} issues"
        )

    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
