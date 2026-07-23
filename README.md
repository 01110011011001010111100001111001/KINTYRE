# KINTYRE

KINTYRE is a safety and orchestration layer for repairing a production music library with mature open-source tools.

KINTYRE does not replace beets, MusicBrainz Picard, MusicBrainz, Chromaprint/AcoustID or the Cover Art Archive. Those tools perform music-domain identification and remediation. KINTYRE controls how their work reaches the authoritative library.

## Permanent v2 workflow

```text
COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK
```

One album is one transaction.

- **COPY** — copy one production album into an isolated system-drive workspace.
- **FIX** — run verified OSS tools only against the copy.
- **REVIEW** — show the complete before/after result and supporting evidence.
- **APPROVE** — record an explicit album-level decision.
- **REPLACE** — back up and replace the production album as one controlled action.
- **CHECK** — verify files, tags, artwork, audio integrity and Music Assistant.

## Permanent boundaries

- `/data/Music` is the authoritative production library.
- The data drive contains media/data only.
- Applications, reports, logs, caches, staging, backups and temporary files remain on the system drive.
- External remediation tools never receive production write access.
- Ambiguous albums are deferred, never forced.
- Music Assistant is a rebuildable downstream consumer.
- Every replacement is reviewable, approved, traceable and reversible.

## Project status

### v1 — frozen historical baseline

The released v1 code provides Scan, Metadata Audit, Analysis, Preview, Approval, Apply, backup, rollback, verification and Music Assistant artwork utilities. It remains the historical baseline but is not the future architecture.

### v2 — active implementation

The v2 workflow is under active implementation. D1 toolchain inventory, D2 COPY, D3 FIX and D4 REVIEW are complete and covered by 81 passing tests. D5 APPROVE is the active milestone. Production remains unchanged through the implemented COPY, FIX and REVIEW stages.

## Documentation

- [Vision](docs/VISION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [AI Engineering Handover](docs/HANDOVER.md)
- [Technology Strategy](docs/TECHNOLOGY_STRATEGY.md)
- [Technology Radar](docs/TECHNOLOGY_RADAR.md)
- [Technology Decisions](docs/TECHNOLOGY_DECISIONS.md)
- [Report Formats](docs/REPORT_FORMATS.md)
- [Changelog](docs/CHANGELOG.md)
