#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from common import (
    ANALYSIS_DIR,
    DATA_ROOT,
    INDEX_DIR,
    PROJECT_ROOT,
    REPORTS_DIR,
    ensure_runtime_directories,
    utc_timestamp,
)

ALBUM_INDEX = INDEX_DIR / "album-index.csv"

METADATA_REPORTS = (
    REPORTS_DIR / "contemporary-metadata-issues.csv",
    REPORTS_DIR / "classical-metadata-issues.csv",
)

OUTPUTS = {
    "summary":
        ANALYSIS_DIR / "analysis-summary.json",
    "single_artist":
        ANALYSIS_DIR / "single-artist-candidates.csv",
    "various_artist":
        ANALYSIS_DIR / "various-artist-candidates.csv",
    "unknown_albums":
        ANALYSIS_DIR / "unknown-albums.csv",
    "folder_quality":
        ANALYSIS_DIR / "folder-quality.csv",
}

BASE_FIELDS = (
    "library",
    "folder",
    "tracks",
    "artist_count",
    "albumartist_count",
    "album_count",
    "date_count",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only KINTYRE DAM library "
            "analysis engine"
        )
    )

    parser.add_argument(
        "--album-index",
        type=Path,
        default=ALBUM_INDEX,
        help="Album index CSV input",
    )

    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=REPORTS_DIR,
        help=(
            "Directory containing metadata "
            "issue CSV reports"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ANALYSIS_DIR,
        help=(
            "Analysis output directory; must be "
            "runtime/analysis"
        ),
    )

    return parser.parse_args()


def canonical_key(value: str) -> str:
    return "".join(
        character
        for character in value.strip().lower()
        if character.isalnum()
    )


def normalized_row(
    row: Mapping[str, Any],
) -> dict[str, str]:
    return {
        canonical_key(str(key)): (
            ""
            if value is None
            else str(value).strip()
        )
        for key, value in row.items()
        if key is not None
    }


def first_value(
    row: Mapping[str, str],
    *names: str,
) -> str:
    for name in names:
        value = row.get(
            canonical_key(name),
            "",
        )

        if value:
            return value

    return ""


def as_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def read_csv(
    path: Path,
    *,
    required: bool,
) -> list[dict[str, str]]:
    if not path.is_file():
        if required:
            raise FileNotFoundError(
                f"Required input not found: {path}"
            )

        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError(
                f"CSV has no header: {path}"
            )

        return [
            normalized_row(row)
            for row in reader
        ]


def canonical_folder(value: str) -> str:
    text = (
        value.strip()
        .replace("\\", "/")
        .rstrip("/")
    )

    if not text:
        return ""

    try:
        path = Path(text)

        if path.is_absolute():
            try:
                relative = path.relative_to(DATA_ROOT)
                return (
                    str(relative)
                    .replace("\\", "/")
                    .casefold()
                )
            except ValueError:
                return (
                    str(path)
                    .replace("\\", "/")
                    .casefold()
                )

    except (OSError, ValueError):
        pass

    return text.lstrip("./").casefold()


def issue_folder(
    row: Mapping[str, str],
) -> str:
    folder = first_value(
        row,
        "folder",
        "album_folder",
        "directory",
        "parent",
        "path",
        "file",
        "filename",
    )

    if not folder:
        return ""

    path = Path(folder)

    if path.suffix:
        folder = str(path.parent)

    return canonical_folder(folder)


def issue_description(
    row: Mapping[str, str],
) -> str:
    return (
        first_value(
            row,
            "issue",
            "error",
            "problem",
            "message",
            "reason",
            "status",
        )
        or "metadata issue"
    )


def index_issue_rows(
    rows: Iterable[Mapping[str, str]],
) -> tuple[
    Counter[str],
    dict[str, set[str]],
]:
    counts: Counter[str] = Counter()

    descriptions: dict[str, set[str]] = defaultdict(
        set
    )

    for row in rows:
        folder = issue_folder(row)

        if not folder:
            continue

        counts[folder] += 1
        descriptions[folder].add(
            issue_description(row)
        )

    return counts, descriptions


def folder_issue_data(
    folder: str,
    issue_counts: Counter[str],
    issue_descriptions: Mapping[str, set[str]],
) -> tuple[int, list[str]]:
    key = canonical_folder(folder)

    exact_count = issue_counts.get(key, 0)

    exact_descriptions = set(
        issue_descriptions.get(key, set())
    )

    if exact_count:
        return (
            exact_count,
            sorted(exact_descriptions),
        )

    total = 0
    descriptions: set[str] = set()
    prefix = key.rstrip("/") + "/"

    for issue_key, count in issue_counts.items():
        if issue_key.startswith(prefix):
            total += count
            descriptions.update(
                issue_descriptions.get(
                    issue_key,
                    set(),
                )
            )

    return total, sorted(descriptions)


def base_record(
    row: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "library":
            first_value(
                row,
                "library",
            ),
        "folder":
            first_value(
                row,
                "folder",
                "path",
                "directory",
            ),
        "tracks":
            as_int(
                first_value(
                    row,
                    "tracks",
                    "track_count",
                    "files",
                )
            ),
        "artist_count":
            as_int(
                first_value(
                    row,
                    "artist_count",
                    "artists",
                )
            ),
        "albumartist_count":
            as_int(
                first_value(
                    row,
                    "albumartist_count",
                    "album_artist_count",
                    "albumartists",
                )
            ),
        "album_count":
            as_int(
                first_value(
                    row,
                    "album_count",
                    "albums",
                )
            ),
        "date_count":
            as_int(
                first_value(
                    row,
                    "date_count",
                    "dates",
                    "year_count",
                )
            ),
    }


def derive_flags(
    record: Mapping[str, Any],
    issue_types: Sequence[str],
) -> list[str]:
    flags: list[str] = []
    folder = str(record["folder"])

    if record["artist_count"] == 0:
        flags.append("missing_artist")
    elif record["artist_count"] > 1:
        flags.append("multiple_artists")

    if record["albumartist_count"] == 0:
        flags.append("missing_albumartist")
    elif record["albumartist_count"] > 1:
        flags.append("multiple_albumartists")

    if record["album_count"] == 0:
        flags.append("missing_album_tag")
    elif record["album_count"] > 1:
        flags.append("multiple_album_tags")

    if record["date_count"] == 0:
        flags.append("missing_date")
    elif record["date_count"] > 1:
        flags.append("multiple_dates")

    if "unknown album" in folder.casefold():
        flags.append("unknown_album_folder")

    if "unknown artist" in folder.casefold():
        flags.append("unknown_artist_folder")

    if "metadata_error" in issue_types:
        flags.append("metadata_read_error")

    return flags


def score_folder(
    flags: Sequence[str],
    issue_count: int,
) -> int:
    penalties = {
        "missing_artist": 30,
        "multiple_artists": 4,
        "missing_albumartist": 12,
        "multiple_albumartists": 8,
        "missing_album_tag": 25,
        "multiple_album_tags": 15,
        "missing_date": 5,
        "multiple_dates": 8,
        "unknown_album_folder": 30,
        "unknown_artist_folder": 30,
        "metadata_read_error": 35,
    }

    score = 100 - sum(
        penalties.get(flag, 0)
        for flag in flags
    )

    if issue_count > 1:
        score -= min(
            15,
            issue_count - 1,
        )

    return max(0, score)


def quality_grade(score: int) -> str:
    if score >= 95:
        return "A"

    if score >= 85:
        return "B"

    if score >= 70:
        return "C"

    if score >= 50:
        return "D"

    return "E"


def assert_safe_output_dir(
    output_dir: Path,
) -> Path:
    resolved = output_dir.expanduser().resolve()
    allowed = ANALYSIS_DIR.resolve()
    protected = DATA_ROOT.resolve()
    project = PROJECT_ROOT.resolve()

    if resolved != allowed:
        raise ValueError(
            "Refusing output directory outside the "
            f"fixed analysis location: {resolved}"
        )

    if (
        resolved == protected
        or protected in resolved.parents
    ):
        raise ValueError(
            "Refusing to write beneath protected "
            f"media root: {resolved}"
        )

    if project not in resolved.parents:
        raise ValueError(
            "Refusing output outside project root: "
            f"{resolved}"
        )

    return resolved


def atomic_write_csv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )

    try:
        with os.fdopen(
            descriptor,
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

            for row in rows:
                writer.writerow(row)

            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(
            temporary_name,
            0o644,
        )

        os.replace(
            temporary_name,
            path,
        )

    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass

        raise


def atomic_write_json(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )

            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.chmod(
            temporary_name,
            0o644,
        )

        os.replace(
            temporary_name,
            path,
        )

    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass

        raise


def analyze(
    album_rows: Sequence[Mapping[str, str]],
    issue_rows: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    issue_counts, issue_types_by_folder = (
        index_issue_rows(issue_rows)
    )

    single_artist: list[dict[str, Any]] = []
    various_artist: list[dict[str, Any]] = []
    unknown_albums: list[dict[str, Any]] = []
    folder_quality: list[dict[str, Any]] = []

    library_counts: Counter[str] = Counter()
    grade_counts: Counter[str] = Counter()

    total_tracks = 0

    for raw in album_rows:
        record = base_record(raw)

        library_counts[
            str(record["library"])
        ] += 1

        total_tracks += int(record["tracks"])

        issue_count, issue_types = folder_issue_data(
            str(record["folder"]),
            issue_counts,
            issue_types_by_folder,
        )

        flags = derive_flags(
            record,
            issue_types,
        )

        score = score_folder(
            flags,
            issue_count,
        )

        grade = quality_grade(score)
        grade_counts[grade] += 1

        quality = {
            **record,
            "quality_score": score,
            "quality_grade": grade,
            "issue_count": issue_count,
            "flags": ";".join(flags),
            "issue_descriptions":
                "; ".join(issue_types),
        }

        folder_quality.append(quality)

        if record["artist_count"] == 1:
            single_artist.append(
                {
                    **record,
                    "candidate_reason": (
                        "exactly_one_distinct_track_artist"
                    ),
                    "needs_albumartist": (
                        "yes"
                        if record[
                            "albumartist_count"
                        ] == 0
                        else "no"
                    ),
                    "quality_score": score,
                    "flags": ";".join(flags),
                }
            )

        if record["artist_count"] > 1:
            albumartist_count = record[
                "albumartist_count"
            ]

            if albumartist_count == 0:
                albumartist_state = "missing"
            elif albumartist_count == 1:
                albumartist_state = "single"
            else:
                albumartist_state = "multiple"

            various_artist.append(
                {
                    **record,
                    "candidate_reason": (
                        "multiple_distinct_track_artists"
                    ),
                    "existing_albumartist_state":
                        albumartist_state,
                    "quality_score": score,
                    "flags": ";".join(flags),
                }
            )

        folder_text = str(
            record["folder"]
        ).casefold()

        if (
            "unknown album" in folder_text
            or record["album_count"] == 0
        ):
            reasons: list[str] = []

            if "unknown album" in folder_text:
                reasons.append(
                    "unknown_album_folder"
                )

            if record["album_count"] == 0:
                reasons.append(
                    "missing_album_tag"
                )

            unknown_albums.append(
                {
                    **record,
                    "candidate_reason":
                        ";".join(reasons),
                    "quality_score": score,
                    "issue_count": issue_count,
                    "flags": ";".join(flags),
                }
            )

    def sort_key(
        row: Mapping[str, Any],
    ) -> tuple[str, str]:
        return (
            str(row.get("library", "")),
            str(
                row.get("folder", "")
            ).casefold(),
        )

    single_artist.sort(key=sort_key)
    various_artist.sort(key=sort_key)
    unknown_albums.sort(key=sort_key)

    folder_quality.sort(
        key=lambda row: (
            int(row["quality_score"]),
            *sort_key(row),
        )
    )

    return {
        "single_artist": single_artist,
        "various_artist": various_artist,
        "unknown_albums": unknown_albums,
        "folder_quality": folder_quality,
        "summary": {
            "generated_at": utc_timestamp(),
            "engine": (
                "KINTYRE DAM Analysis Engine"
            ),
            "mode": "read-only",
            "inputs": {
                "album_index":
                    str(ALBUM_INDEX),
                "metadata_reports": [
                    str(path)
                    for path in METADATA_REPORTS
                ],
            },
            "outputs": {
                name: str(path)
                for name, path in OUTPUTS.items()
            },
            "album_folders":
                len(album_rows),
            "tracks_indexed":
                total_tracks,
            "folders_by_library":
                dict(
                    sorted(
                        library_counts.items()
                    )
                ),
            "metadata_issue_rows":
                len(issue_rows),
            "single_artist_candidates":
                len(single_artist),
            "various_artist_candidates":
                len(various_artist),
            "unknown_album_candidates":
                len(unknown_albums),
            "folders_by_quality_grade":
                dict(
                    sorted(
                        grade_counts.items()
                    )
                ),
            "safety": {
                "media_root":
                    str(DATA_ROOT),
                "media_writes": 0,
                "tag_modifications": 0,
                "renames": 0,
                "moves": 0,
            },
        },
    }


def main() -> int:
    args = parse_args()

    output_dir = assert_safe_output_dir(
        args.output_dir
    )

    ensure_runtime_directories()

    album_index = (
        args.album_index
        .expanduser()
        .resolve()
    )

    album_rows = read_csv(
        album_index,
        required=True,
    )

    reports_dir = (
        args.reports_dir
        .expanduser()
        .resolve()
    )

    report_paths = (
        reports_dir
        / "contemporary-metadata-issues.csv",
        reports_dir
        / "classical-metadata-issues.csv",
    )

    issue_rows: list[dict[str, str]] = []
    found_reports: list[str] = []
    missing_reports: list[str] = []

    for path in report_paths:
        rows = read_csv(
            path,
            required=False,
        )

        if path.is_file():
            found_reports.append(str(path))
            issue_rows.extend(rows)
        else:
            missing_reports.append(str(path))

    results = analyze(
        album_rows,
        issue_rows,
    )

    results["summary"]["inputs"] = {
        "album_index":
            str(album_index),
        "metadata_reports_found":
            found_reports,
        "metadata_reports_missing":
            missing_reports,
    }

    output_paths = {
        name: output_dir / path.name
        for name, path in OUTPUTS.items()
    }

    atomic_write_csv(
        output_paths["single_artist"],
        (
            *BASE_FIELDS,
            "candidate_reason",
            "needs_albumartist",
            "quality_score",
            "flags",
        ),
        results["single_artist"],
    )

    atomic_write_csv(
        output_paths["various_artist"],
        (
            *BASE_FIELDS,
            "candidate_reason",
            "existing_albumartist_state",
            "quality_score",
            "flags",
        ),
        results["various_artist"],
    )

    atomic_write_csv(
        output_paths["unknown_albums"],
        (
            *BASE_FIELDS,
            "candidate_reason",
            "quality_score",
            "issue_count",
            "flags",
        ),
        results["unknown_albums"],
    )

    atomic_write_csv(
        output_paths["folder_quality"],
        (
            *BASE_FIELDS,
            "quality_score",
            "quality_grade",
            "issue_count",
            "flags",
            "issue_descriptions",
        ),
        results["folder_quality"],
    )

    results["summary"]["outputs"] = {
        name: str(path)
        for name, path in output_paths.items()
    }

    atomic_write_json(
        output_paths["summary"],
        results["summary"],
    )

    print(
        json.dumps(
            results["summary"],
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        raise SystemExit(2)
