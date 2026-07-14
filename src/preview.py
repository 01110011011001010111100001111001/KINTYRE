#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from mutagen import File

from common import (
    ANALYSIS_DIR,
    INDEX_DIR,
    PROJECT_ROOT,
    utc_timestamp,
)

INDEX_FILE = INDEX_DIR / "album-index.csv"
SINGLE_ARTIST_FILE = ANALYSIS_DIR / "single-artist-candidates.csv"
PREVIEW_DIR = PROJECT_ROOT / "runtime" / "preview"
SUMMARY_FILE = PREVIEW_DIR / "preview-summary.json"
PLAN_FILE = PREVIEW_DIR / "apply-plan.json"
ALBUMARTIST_CSV = PREVIEW_DIR / "albumartist-fixes.csv"
REVIEW_SUMMARY_FILE = PREVIEW_DIR / "review-summary.json"


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





def proposed_albumartist(folder: str) -> str | None:
    artists: set[str] = set()

    for media in sorted(Path(folder).iterdir()):
        if not media.is_file() or media.name.startswith("._"):
            continue

        audio = File(media, easy=True)

        if audio is None:
            continue

        artists.update(
            value.strip()
            for value in audio.get("artist", [])
            if value.strip()
        )

        if len(artists) > 1:
            return None

    if len(artists) == 1:
        return next(iter(artists))

    return None


def build_actions() -> list[dict]:
    actions = []

    with SINGLE_ARTIST_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        action_no = 1

        for row in reader:
            if row["needs_albumartist"] != "yes":
                continue

            if int(row["quality_score"]) < 80:
                continue

            actions.append(
                {
                    "id": f"ACT-{action_no:06d}",
                    "album_id": album_id(
                        row["library"],
                        row["folder"],
                    ),
                    "library": row["library"],
                    "folder": row["folder"],
                    "action": "ADD_ALBUMARTIST",
                    "proposed_value": proposed_albumartist(
                        row["folder"]
                    ),
                    "reason": "Single distinct track artist and missing AlbumArtist",
                    "confidence": "HIGH",
                    "risk": "LOW",
                    "approval": "PENDING",
                }
            )

            action_no += 1

    return actions



def write_albumartist_csv() -> None:
    with PLAN_FILE.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)

    fieldnames = [
        "id",
        "album_id",
        "library",
        "folder",
        "action",
        "proposed_value",
        "confidence",
        "risk",
        "reason",
        "approval",
    ]

    actions = [
        action
        for action in plan["actions"]
        if action["action"] == "ADD_ALBUMARTIST"
    ]

    with ALBUMARTIST_CSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(actions)



def write_review_summary() -> None:
    from collections import Counter

    with PLAN_FILE.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)

    actions = plan["actions"]

    summary = {
        "schema_version": "1.0",
        "generated_at": plan["generated_at"],
        "mode": "READ_ONLY",
        "total_actions": len(actions),
        "resolved_proposed_values": sum(
            1 for action in actions
            if action.get("proposed_value")
        ),
        "unresolved_proposed_values": sum(
            1 for action in actions
            if not action.get("proposed_value")
        ),
        "actions_by_type": dict(
            sorted(
                Counter(
                    action["action"]
                    for action in actions
                ).items()
            )
        ),
        "actions_by_library": dict(
            sorted(
                Counter(
                    action["library"]
                    for action in actions
                ).items()
            )
        ),
        "actions_by_confidence": dict(
            sorted(
                Counter(
                    action["confidence"]
                    for action in actions
                ).items()
            )
        ),
        "actions_by_risk": dict(
            sorted(
                Counter(
                    action["risk"]
                    for action in actions
                ).items()
            )
        ),
        "actions_by_approval": dict(
            sorted(
                Counter(
                    action["approval"]
                    for action in actions
                ).items()
            )
        ),
    }

    write_json(REVIEW_SUMMARY_FILE, summary)


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

    actions = build_actions()

    summary = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "mode": "READ_ONLY",
        "status": "PREVIEW_READY",
        "album_count": album_count,
        "action_count": len(actions),
    }

    apply_plan = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "mode": "READ_ONLY",
        "album_count": album_count,
        "action_count": len(actions),
        "actions": actions,
    }

    write_json(SUMMARY_FILE, summary)
    write_json(PLAN_FILE, apply_plan)
    write_albumartist_csv()
    write_review_summary()

    print("KINTYRE DAM Preview Engine")
    print(f"Albums analysed: {album_count}")
    print(f"Actions: {len(actions)}")
    print(f"Created: {SUMMARY_FILE}")
    print(f"Created: {PLAN_FILE}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
