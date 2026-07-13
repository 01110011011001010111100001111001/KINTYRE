#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from common import (
    ANALYSIS_DIR,
    INDEX_DIR,
    PROJECT_ROOT,
    utc_timestamp,
)

INDEX_FILE = INDEX_DIR / "album-index.csv"
PREVIEW_DIR = PROJECT_ROOT / "runtime" / "preview"
SUMMARY_FILE = PREVIEW_DIR / "preview-summary.json"
PLAN_FILE = PREVIEW_DIR / "apply-plan.json"


def read_album_count() -> int:
    if not INDEX_FILE.is_file():
        raise FileNotFoundError(
            f"Required input not found: {INDEX_FILE}"
        )

    with INDEX_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        return sum(1 for _ in reader)


def write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")



def album_id(library: str, folder: str) -> str:
    key = f"{library}|{folder}"
    digest = hashlib.sha1(
        key.encode("utf-8")
    ).hexdigest()
    return "ALB-" + digest[:8].upper()



def main() -> int:
    PREVIEW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    album_count = read_album_count()

    with INDEX_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        albums = list(csv.DictReader(handle))

    album_ids = {
        album_id(
            row.get("library", ""),
            row.get("folder", ""),
        )
        for row in albums
    }

    if len(album_ids) != album_count:
        raise RuntimeError(
            "Album ID collision or incomplete album index detected."
        )

    generated_at = utc_timestamp()

    summary = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "mode": "READ_ONLY",
        "status": "PREVIEW_READY",
        "album_count": album_count,
        "action_count": 0,
    }

    apply_plan = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "mode": "READ_ONLY",
        "album_count": album_count,
        "action_count": 0,
        "actions": [],
    }

    write_json(SUMMARY_FILE, summary)
    write_json(PLAN_FILE, apply_plan)

    print("KINTYRE DAM Preview Engine")
    print(f"Albums analysed: {album_count}")
    print("Actions: 0")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Created: {PLAN_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
