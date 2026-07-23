#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import mutagen

from common import (
    RUNTIME_DIR,
    SUPPORTED_AUDIO_EXTENSIONS,
    load_config,
)
from copy_album import (
    COPY_REPORT,
    DESTINATION_MANIFEST,
    SCHEMA_VERSION,
    SOURCE_MANIFEST,
    TRANSACTIONS_DIRNAME,
    build_manifest,
    manifest_digest,
    validate_transaction_id,
    write_json,
)
from fix_album import (
    AFTER_MANIFEST,
    AUDIO_ESSENCE_AFTER,
    AUDIO_ESSENCE_BEFORE,
    BEFORE_MANIFEST,
    FIX_DIRNAME,
    FIX_REPORT,
)

REVIEW_DIRNAME = "review"
REVIEW_REPORT = "review-report.json"
REVIEW_FINDINGS = "review-findings.json"
REVIEW_SUMMARY = "review-summary.md"

NORMALIZED_FIELDS: dict[str, tuple[str, ...]] = {
    "title": ("title",),
    "artist": ("artist",),
    "album": ("album",),
    "albumartist": (
        "albumartist",
        "album artist",
        "album_artist",
    ),
    "tracknumber": ("tracknumber", "track"),
    "discnumber": ("discnumber", "disc"),
    "date": ("date", "year"),
    "genre": ("genre",),
    "musicbrainz_trackid": (
        "musicbrainz_trackid",
        "musicbrainz track id",
    ),
    "musicbrainz_recordingid": (
        "musicbrainz_recordingid",
        "musicbrainz recording id",
    ),
    "musicbrainz_albumid": (
        "musicbrainz_albumid",
        "musicbrainz album id",
    ),
    "musicbrainz_releasegroupid": (
        "musicbrainz_releasegroupid",
        "musicbrainz release group id",
    ),
    "musicbrainz_artistid": (
        "musicbrainz_artistid",
        "musicbrainz artist id",
    ),
    "musicbrainz_albumartistid": (
        "musicbrainz_albumartistid",
        "musicbrainz album artist id",
    ),
}


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


def _safe_manifest_digest(payload: dict[str, Any]) -> str:
    return manifest_digest(payload)


def _normalise_values(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, bytes):
        values: Iterable[Any] = [value.decode("utf-8", errors="replace")]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]

    result: list[str] = []

    for item in values:
        if isinstance(item, bytes):
            text = item.decode("utf-8", errors="replace").strip()
        else:
            text = str(item).strip()

        if text and text not in result:
            result.append(text)

    return result


def _tag_values(tags: Any, names: tuple[str, ...]) -> list[str]:
    if not tags:
        return []

    lowered: dict[str, Any] = {}

    try:
        items = tags.items()
    except AttributeError:
        return []

    for key, value in items:
        lowered[str(key).strip().lower()] = value

    for name in names:
        if name.lower() in lowered:
            return _normalise_values(lowered[name.lower()])

    return []


def _embedded_artwork_state(audio: Any) -> bool | None:
    if audio is None:
        return None

    pictures = getattr(audio, "pictures", None)
    if pictures:
        return True

    tags = getattr(audio, "tags", None)
    if not tags:
        return False

    try:
        keys = [str(key).lower() for key in tags.keys()]
    except AttributeError:
        return None

    artwork_keys = (
        "apic",
        "covr",
        "coverart",
        "metadata_block_picture",
        "wm/picture",
    )

    return any(
        key == marker
        or key.startswith(f"{marker}:")
        or marker in key
        for key in keys
        for marker in artwork_keys
    )


def read_metadata(path: Path) -> dict[str, Any]:
    easy_audio = mutagen.File(path, easy=True)

    if easy_audio is None:
        return {
            "status": "unavailable",
            "error": "Mutagen returned no metadata handler.",
            "fields": {
                name: []
                for name in NORMALIZED_FIELDS
            },
            "embedded_artwork": None,
        }

    tags = easy_audio.tags or {}

    fields = {
        name: _tag_values(tags, aliases)
        for name, aliases in NORMALIZED_FIELDS.items()
    }

    try:
        raw_audio = mutagen.File(path, easy=False)
        artwork = _embedded_artwork_state(raw_audio)
    except Exception:
        artwork = None

    return {
        "status": "readable",
        "error": "",
        "fields": fields,
        "embedded_artwork": artwork,
    }


def iter_audio_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ):
            yield path


def build_metadata_manifest(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    formats: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()

    for path in iter_audio_files(root):
        suffix = path.suffix.lower()
        formats[suffix] += 1

        try:
            metadata = read_metadata(path)
        except Exception as exc:
            metadata = {
                "status": "error",
                "error": str(exc),
                "fields": {
                    name: []
                    for name in NORMALIZED_FIELDS
                },
                "embedded_artwork": None,
            }

        status_counts[metadata["status"]] += 1
        files.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "extension": suffix,
                **metadata,
            }
        )

    if not files:
        raise ValueError(
            f"No supported audio files in album: {root}"
        )

    return {
        "declared_supported_extensions": sorted(
            SUPPORTED_AUDIO_EXTENSIONS
        ),
        "observed_formats": dict(sorted(formats.items())),
        "metadata_status_counts": dict(
            sorted(status_counts.items())
        ),
        "files": files,
    }


def _files_by_path(
    manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        str(entry["relative_path"]): entry
        for entry in manifest.get("files", [])
    }


def compare_metadata(
    before: dict[str, Any],
    after: dict[str, Any],
) -> list[dict[str, Any]]:
    before_files = _files_by_path(before)
    after_files = _files_by_path(after)
    changes: list[dict[str, Any]] = []

    for relative_path in sorted(
        set(before_files) | set(after_files)
    ):
        before_entry = before_files.get(relative_path)
        after_entry = after_files.get(relative_path)

        if before_entry is None:
            changes.append(
                {
                    "relative_path": relative_path,
                    "change": "audio_file_added",
                }
            )
            continue

        if after_entry is None:
            changes.append(
                {
                    "relative_path": relative_path,
                    "change": "audio_file_removed",
                }
            )
            continue

        before_fields = before_entry.get("fields", {})
        after_fields = after_entry.get("fields", {})

        for field in sorted(NORMALIZED_FIELDS):
            old = before_fields.get(field, [])
            new = after_fields.get(field, [])

            if old != new:
                changes.append(
                    {
                        "relative_path": relative_path,
                        "change": "metadata",
                        "field": field,
                        "before": old,
                        "after": new,
                    }
                )

        old_artwork = before_entry.get("embedded_artwork")
        new_artwork = after_entry.get("embedded_artwork")

        if old_artwork != new_artwork:
            changes.append(
                {
                    "relative_path": relative_path,
                    "change": "embedded_artwork",
                    "before": old_artwork,
                    "after": new_artwork,
                }
            )

    return changes


def _field_values(
    manifest: dict[str, Any],
    field: str,
) -> list[str]:
    values: list[str] = []

    for entry in manifest.get("files", []):
        for value in entry.get("fields", {}).get(field, []):
            if value not in values:
                values.append(value)

    return values


def determine_library_improvements(
    before: dict[str, Any],
    after: dict[str, Any],
    changes: list[dict[str, Any]],
) -> list[str]:
    improvements: list[str] = []

    before_albumartists = _field_values(
        before,
        "albumartist",
    )
    after_albumartists = _field_values(
        after,
        "albumartist",
    )

    if not before_albumartists and after_albumartists:
        improvements.append(
            "AlbumArtist identity was added, improving "
            "album grouping and artist attribution."
        )

    before_album_ids = _field_values(
        before,
        "musicbrainz_albumid",
    )
    after_album_ids = _field_values(
        after,
        "musicbrainz_albumid",
    )

    if not before_album_ids and after_album_ids:
        improvements.append(
            "A MusicBrainz release identifier was added, "
            "improving release identity and interoperability."
        )

    before_release_group_ids = _field_values(
        before,
        "musicbrainz_releasegroupid",
    )
    after_release_group_ids = _field_values(
        after,
        "musicbrainz_releasegroupid",
    )

    if (
        not before_release_group_ids
        and after_release_group_ids
    ):
        improvements.append(
            "A MusicBrainz release-group identifier was "
            "added, improving album-family identity."
        )

    changed_fields = {
        str(change.get("field"))
        for change in changes
        if change.get("change") == "metadata"
    }

    if changed_fields & {
        "title",
        "artist",
        "album",
        "albumartist",
    }:
        improvements.append(
            "Core identity metadata was normalized, "
            "improving consistent browsing and search."
        )

    if changed_fields & {
        "tracknumber",
        "discnumber",
    }:
        improvements.append(
            "Track or disc ordering metadata was normalized."
        )

    return improvements


def _write_markdown(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing evidence: {path}"
        )

    temporary = path.with_name(f".{path.name}.tmp")

    try:
        with temporary.open(
            "x",
            encoding="utf-8",
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        temporary.replace(path)
        path.chmod(
            stat.S_IRUSR
            | stat.S_IRGRP
            | stat.S_IROTH
        )
    finally:
        if temporary.exists():
            temporary.unlink()


def _summary_markdown(
    transaction_id: str,
    status: str,
    findings: dict[str, Any],
) -> str:
    lines = [
        "# KINTYRE v2 Review Certification",
        "",
        f"- Transaction: `{transaction_id}`",
        f"- Recommendation: **{status}**",
        (
            "- Metadata changes: "
            f"{len(findings['metadata_changes'])}"
        ),
        (
            "- Library improvements: "
            f"{len(findings['library_improvements'])}"
        ),
        f"- Warnings: {len(findings['warnings'])}",
        (
            "- Blocking conditions: "
            f"{len(findings['blocking_conditions'])}"
        ),
        "",
        "## Library improvements",
        "",
    ]

    improvements = findings["library_improvements"]

    if improvements:
        lines.extend(
            f"- {item}"
            for item in improvements
        )
    else:
        lines.append("- No specific improvement was inferred.")

    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )

    warnings = findings["warnings"]

    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Blocking conditions",
            "",
        ]
    )

    blockers = findings["blocking_conditions"]

    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")

    lines.append("")
    return "\n".join(lines)


def run_review(
    transaction_id: str,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    txid = validate_transaction_id(transaction_id)
    selected_config = (
        load_config()
        if config is None
        else config
    )
    staging_root = _configured_staging_root(
        selected_config
    ).expanduser().resolve()

    transaction = (
        staging_root
        / TRANSACTIONS_DIRNAME
        / txid
    )
    album = transaction / "album"
    fix_dir = transaction / FIX_DIRNAME
    review_dir = transaction / REVIEW_DIRNAME

    if not transaction.is_dir() or not album.is_dir():
        raise FileNotFoundError(
            "Retained COPY transaction not found: "
            f"{transaction}"
        )

    if review_dir.exists():
        raise FileExistsError(
            "Refusing to overwrite existing REVIEW evidence: "
            f"{review_dir}"
        )

    required_paths = (
        transaction / COPY_REPORT,
        transaction / SOURCE_MANIFEST,
        transaction / DESTINATION_MANIFEST,
        fix_dir / FIX_REPORT,
        fix_dir / BEFORE_MANIFEST,
        fix_dir / AFTER_MANIFEST,
        fix_dir / AUDIO_ESSENCE_BEFORE,
        fix_dir / AUDIO_ESSENCE_AFTER,
    )

    missing = [
        str(path)
        for path in required_paths
        if not path.is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Required COPY/FIX evidence is missing: "
            + ", ".join(missing)
        )

    copy_report = _read_json(
        transaction / COPY_REPORT
    )
    fix_report = _read_json(
        fix_dir / FIX_REPORT
    )

    if (
        copy_report.get("stage") != "COPY"
        or copy_report.get("status") != "PASS"
    ):
        raise ValueError(
            "Transaction does not contain a successful "
            "COPY report."
        )

    if (
        fix_report.get("stage") != "FIX"
        or fix_report.get("status") != "PASS"
    ):
        raise ValueError(
            "Transaction does not contain a successful "
            "FIX report."
        )

    source_manifest = _read_json(
        transaction / SOURCE_MANIFEST
    )
    destination_manifest = _read_json(
        transaction / DESTINATION_MANIFEST
    )
    before_manifest = _read_json(
        fix_dir / BEFORE_MANIFEST
    )
    after_manifest = _read_json(
        fix_dir / AFTER_MANIFEST
    )
    essence_before = _read_json(
        fix_dir / AUDIO_ESSENCE_BEFORE
    )
    essence_after = _read_json(
        fix_dir / AUDIO_ESSENCE_AFTER
    )

    blockers: list[str] = []
    warnings: list[str] = []

    evidence_payloads = (
        ("source manifest", source_manifest),
        ("destination manifest", destination_manifest),
        ("FIX before manifest", before_manifest),
        ("FIX after manifest", after_manifest),
        ("audio essence before", essence_before),
        ("audio essence after", essence_after),
    )

    for label, payload in evidence_payloads:
        if payload.get("transaction_id") != txid:
            blockers.append(
                f"{label} transaction ID does not match."
            )

    expected_source_digest = copy_report.get(
        "source_manifest_sha256"
    )
    if (
        expected_source_digest
        and expected_source_digest
        != _safe_manifest_digest(source_manifest)
    ):
        blockers.append(
            "COPY source-manifest digest does not match "
            "the COPY report."
        )

    expected_destination_digest = copy_report.get(
        "destination_manifest_sha256"
    )
    if (
        expected_destination_digest
        and expected_destination_digest
        != _safe_manifest_digest(destination_manifest)
    ):
        blockers.append(
            "COPY destination-manifest digest does not "
            "match the COPY report."
        )

    current_staged_manifest = build_manifest(album)

    for key in (
        "file_count",
        "audio_file_count",
        "total_bytes",
        "files",
    ):
        if (
            current_staged_manifest.get(key)
            != after_manifest.get(key)
        ):
            blockers.append(
                "Staged album no longer matches FIX after "
                f"evidence: {key}."
            )

    if essence_before.get("files") != essence_after.get(
        "files"
    ):
        blockers.append(
            "FIX audio-essence evidence does not match."
        )

    source_text = copy_report.get("source")
    source = (
        Path(str(source_text))
        if source_text
        else None
    )

    source_metadata: dict[str, Any] | None = None

    if source is None or not source.is_dir():
        blockers.append(
            "Authoritative source album is unavailable "
            "for independent metadata comparison."
        )
    else:
        current_source_manifest = build_manifest(source)

        for key in (
            "file_count",
            "audio_file_count",
            "total_bytes",
            "files",
        ):
            if (
                current_source_manifest.get(key)
                != source_manifest.get(key)
            ):
                blockers.append(
                    "Authoritative source album no longer "
                    f"matches COPY evidence: {key}."
                )

        source_metadata = build_metadata_manifest(source)

    staged_metadata = build_metadata_manifest(album)

    for side, metadata in (
        ("source", source_metadata),
        ("staged", staged_metadata),
    ):
        if metadata is None:
            continue

        counts = metadata.get(
            "metadata_status_counts",
            {},
        )

        unavailable = int(counts.get("unavailable", 0))
        errors = int(counts.get("error", 0))

        if unavailable:
            warnings.append(
                f"{side.capitalize()} metadata was "
                f"unavailable for {unavailable} audio file(s)."
            )

        if errors:
            warnings.append(
                f"{side.capitalize()} metadata could not "
                f"be read for {errors} audio file(s)."
            )

    metadata_changes = (
        compare_metadata(
            source_metadata,
            staged_metadata,
        )
        if source_metadata is not None
        else []
    )

    improvements = (
        determine_library_improvements(
            source_metadata,
            staged_metadata,
            metadata_changes,
        )
        if source_metadata is not None
        else []
    )

    recommendation = (
        "BLOCK"
        if blockers
        else "PASS"
    )

    findings = {
        "schema_version": SCHEMA_VERSION,
        "stage": "REVIEW",
        "transaction_id": txid,
        "metadata_changes": metadata_changes,
        "library_improvements": improvements,
        "warnings": warnings,
        "blocking_conditions": blockers,
        "recommendation": recommendation,
    }

    report = {
        "schema_version": SCHEMA_VERSION,
        "stage": "REVIEW",
        "status": recommendation,
        "transaction_id": txid,
        "transaction_directory": str(transaction),
        "album": str(album),
        "inputs": {
            "copy_report": str(
                transaction / COPY_REPORT
            ),
            "fix_report": str(
                fix_dir / FIX_REPORT
            ),
            "source_manifest": str(
                transaction / SOURCE_MANIFEST
            ),
            "destination_manifest": str(
                transaction / DESTINATION_MANIFEST
            ),
            "before_manifest": str(
                fix_dir / BEFORE_MANIFEST
            ),
            "after_manifest": str(
                fix_dir / AFTER_MANIFEST
            ),
            "audio_essence_before": str(
                fix_dir / AUDIO_ESSENCE_BEFORE
            ),
            "audio_essence_after": str(
                fix_dir / AUDIO_ESSENCE_AFTER
            ),
        },
        "technical_verification": {
            "copy_status": copy_report.get("status"),
            "fix_status": fix_report.get("status"),
            "file_count": current_staged_manifest[
                "file_count"
            ],
            "audio_file_count": current_staged_manifest[
                "audio_file_count"
            ],
            "audio_essence_preserved": (
                essence_before.get("files")
                == essence_after.get("files")
            ),
            "observed_formats": staged_metadata[
                "observed_formats"
            ],
            "metadata_status_counts": staged_metadata[
                "metadata_status_counts"
            ],
            "declared_supported_extensions": (
                staged_metadata[
                    "declared_supported_extensions"
                ]
            ),
        },
        "findings": str(
            review_dir / REVIEW_FINDINGS
        ),
        "summary": str(
            review_dir / REVIEW_SUMMARY
        ),
        "verification_errors": blockers,
    }

    review_dir.mkdir(
        parents=False,
        exist_ok=False,
    )

    try:
        write_json(
            review_dir / REVIEW_FINDINGS,
            findings,
            immutable=True,
        )
        write_json(
            review_dir / REVIEW_REPORT,
            report,
            immutable=True,
        )
        _write_markdown(
            review_dir / REVIEW_SUMMARY,
            _summary_markdown(
                txid,
                recommendation,
                findings,
            ),
        )
    except Exception:
        for path in sorted(
            review_dir.glob("*"),
            reverse=True,
        ):
            path.chmod(
                stat.S_IRUSR
                | stat.S_IWUSR
            )
            path.unlink()
        review_dir.rmdir()
        raise

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independently certify one successful "
            "KINTYRE v2 COPY/FIX transaction."
        )
    )
    parser.add_argument(
        "transaction_id",
        help=(
            "Existing successful COPY/FIX transaction "
            "identifier."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_review(args.transaction_id)

    print("KINTYRE v2 REVIEW / CERTIFICATION")
    print(f"Transaction: {report['transaction_id']}")
    print(
        "Audio files: "
        f"{report['technical_verification']['audio_file_count']}"
    )
    print(f"Recommendation: {report['status']}")
    print(
        "Evidence: "
        f"{Path(report['transaction_directory']) / REVIEW_DIRNAME}"
    )

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
