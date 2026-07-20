# KINTYRE

Deterministic, audit-first commissioning and metadata management for Music Assistant libraries.

## Release

Current stable release: **v1.0**

## Workflow

```text
Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

## Implemented in v1.0

- Scan, Metadata Audit, Analysis and Preview engines
- Four-state approval model: `PENDING`, `APPROVED`, `REJECTED`, `DEFERRED`
- Single-action, filtered bulk and explicit all-action approval operations
- Atomic approval persistence, approved-action export and append-only audit logging
- Apply dry-run and explicitly confirmed live execution
- FLAC, MP3 and MP4-family AlbumArtist metadata writes
- Transaction backups, post-write verification and batch rollback on failure
- Duplicate-target detection and automated regression/certification tests

## Supported media formats

KINTYRE deliberately distinguishes discovery from metadata writing.

- **Core discovery set:** AAC, AIFF/AIF, ALAC, APE, DFF, DSF, FLAC, M4A, M4B, MP3, MP4, OGA, OGG, Opus, WAV, WMA and WavPack. The active Scan set is configured by `scan.include` in `config/config.yaml`.
- **Metadata Audit:** reads the formats explicitly supported by `src/audit_metadata.py`.
- **Apply writes:** `.flac`, `.mp3`, `.m4a`, `.m4b` and `.mp4` only.

A format being discoverable or auditable does not imply that Apply can write it.

## Safety model

The media library is authoritative and protected. Scan, Metadata Audit, Analysis, Preview and Approval are read-only with respect to media. Only Apply may modify metadata, and only for actions exported as `APPROVED`.

Applications, reports, logs, databases, caches, staging, backups and generated runtime files belong on the system drive. The media drive contains media only.

## Complete command sequence

```bash
python src/scan.py
python src/audit_metadata.py
python src/analyze_library.py
python src/preview.py
python src/approve.py init
python src/approve.py approve --all
python src/approve.py status
python src/apply.py
python src/apply.py --execute --confirm I_APPROVE_KINTYRE_APPLY
python src/scan.py
python src/audit_metadata.py
```

Use `approve --all` only after reviewing the Preview plan. Running `apply.py` without `--execute` is the mandatory dry run.

## Documentation

- [AI Engineering Handover](docs/HANDOVER.md)
- [Installation](INSTALL.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Report Formats](docs/REPORT_FORMATS.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](docs/CHANGELOG.md)

## Repository privacy

The public repository contains source code, tests and generic documentation. Production-library inventories, collection statistics, filenames, generated reports, commissioning results, databases, caches and backups must not be committed.
