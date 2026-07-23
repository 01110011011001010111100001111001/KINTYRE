# KINTYRE Changelog

## Unreleased — v2 simplified architecture baseline

### Added

- Completed the D1 read-only OSS toolchain inventory.
- Recorded verified executable paths and versions for Python, Beets, MusicBrainz Picard, Chromaprint and FFprobe.
- Proved a fully isolated Beets invocation with unchanged source checksum, no copied media and no production access.

### Changed

- Advanced the immediate v2 milestone from D1 inventory to D2 COPY.
- Documented that Beets must be invoked with explicit no-copy, no-move, no-write and no-autotag controls when used for isolated inspection.
- Replaced the discarded certification-platform architecture with `COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK`.
- Established one album as the transaction, approval, replacement and rollback boundary.
- Reduced KINTYRE's target responsibility to orchestration, safety, evidence, approval, backup, replacement, rollback and checking.
- Assigned music identification, release matching, metadata/artwork retrieval and staged tagging to mature external OSS.
- Froze v1 as the historical implementation baseline rather than the future architecture.
- Replaced the previous multi-engine roadmap with thin vertical milestones.
- Deferred dashboards, generic frameworks, policy engines, custom metadata intelligence, AI matching and multi-user work.

## v1.0 — 17 July 2026

Released the deterministic Scan, Metadata Audit, Analysis, Preview, Approval and Apply baseline with backup, rollback, verification and automated tests. Post-v1 work added Music Assistant artwork commissioning, read-only artwork verification and engineering continuity documentation.
