# KINTYRE Architecture

**Version:** 1.0

**Status:** Released

## Purpose

KINTYRE is a deterministic, audit-first platform for commissioning and maintaining music libraries consumed by Music Assistant. The media library is authoritative. Music Assistant is a rebuildable consumer.

## Principles

- Protect source media.
- Separate observation from modification.
- Require explicit approval before Apply.
- Keep generated data off the media drive.
- Preserve decision and execution history.
- Prefer conservative, reversible operations.
- Certify identity-changing operations before production use.

## Storage separation

The media drive contains media only. The system drive contains source code, configuration, virtual environments, reports, indexes, approvals, audit records, logs, caches, staging, backups and application databases.

## Pipeline

```text
Media Library → Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

## Engine responsibilities

| Engine | Responsibility | Writes media |
|---|---|---:|
| Scan | Discover configured media and build indexes | No |
| Metadata Audit | Read supported tags and report findings | No |
| Analysis | Aggregate findings | No |
| Preview | Produce deterministic proposed actions | No |
| Approval | Record decisions and export approved actions | No |
| Apply | Validate and execute approved actions | Yes |
| Verification | Rescan, re-audit and inspect results | No |

## Format boundaries

Format support is deliberately layered.

1. `SUPPORTED_AUDIO_EXTENSIONS` in `src/common.py` is the core discovery set.
2. Scan uses the subset enabled by `scan.include` in `config/config.yaml`.
3. Metadata Audit has its own explicit readable-extension set.
4. Apply has a narrower writable set: `.flac`, `.mp3`, `.m4a`, `.m4b` and `.mp4`.

This prevents the system from treating discovery support as permission or capability to write tags.

## Preview Engine

Canonical directory: `runtime/preview/`.

Primary outputs:

- `preview-summary.json`
- `apply-plan.json`
- `albumartist-fixes.csv`
- `review-summary.json`

## Approval Engine

States are `PENDING`, `APPROVED`, `REJECTED` and `DEFERRED`.

The engine supports:

- one action selected by ID;
- filtered batches using exact and contains operators;
- logical AND across repeated filters;
- explicit whole-plan selection with `--all`;
- idempotent decisions;
- reset to `PENDING`;
- atomic persistence;
- approved-action export;
- append-only audit events.

Exactly one selector type is accepted for a decision command. Outputs are stored under `runtime/approval/`.

## Apply Engine

Apply consumes `runtime/approval/approved-actions.json`. Running without `--execute` is dry run. Live writes require both `--execute` and the exact confirmation phrase `I_APPROVE_KINTYRE_APPLY`.

Controls include validation, duplicate-target detection, blocked-transaction handling, backups, post-write verification, transaction rollback, batch rollback after a failure, non-zero failure status and Apply outcome audit events.

The released write operation is `ADD_ALBUMARTIST`; writable containers are FLAC, MP3 and MP4-family (`.m4a`, `.m4b`, `.mp4`). Outputs are stored under `runtime/apply/`.

## Identity-changing operations

Changes to AlbumArtist, album title, artist identity, compilation status, MusicBrainz identifiers or folder identity can change consumer grouping. They must first be tested in a disposable certification environment with a separate Music Assistant instance and database.

## Repository privacy

Do not commit production inventories, media file lists, collection statistics, generated reports, commissioning evidence, backups, caches, databases, secrets or machine-specific private data.


## Music Assistant artwork commissioning boundary

`src/commission_artwork.py` is a consumer-side commissioning utility. It calls Music Assistant's authenticated HTTP/JSON-RPC API, inventories library albums and artists, and reads entity details to provoke normal metadata and image resolution. It never writes `/data/Music`, never opens the Music Assistant database, and does not bypass Music Assistant provider logic. Dry-run is the default; live operation requires an exact confirmation phrase. Runtime reports and resumable state remain on the system drive.

## Artwork commissioning lifecycle

```text
Authoritative media library → deterministic metadata remediation → approved Apply → verification → Music Assistant rescan or rebuild → entity commissioning through the supported API → asynchronous Music Assistant enrichment → artwork verification and reconciliation
```

KINTYRE owns target enumeration, execution evidence, resumable state and reporting. Music Assistant owns provider selection, metadata resolution, image retrieval, image decoding and caching.

A successful entity request is recorded as `TOUCHED`. This establishes API success only and is distinct from the later operational outcome of obtaining valid artwork.

Commissioning cannot compensate for unresolved identity defects. Missing or incorrect Artist, AlbumArtist, album title, compilation state or external identifiers must return to the normal Audit → Analysis → Preview → Approval → Apply → Verify pipeline.

## Integration evidence rule

KINTYRE documentation and implementation must distinguish successful API communication, asynchronous downstream processing and independently verified final outcome. Claims about external-system behaviour must be supported by automated tests, verified upstream implementation or direct operational evidence.
