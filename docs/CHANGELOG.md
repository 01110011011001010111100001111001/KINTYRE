## 23 July 2026 — outcome-driven library mission documented

- Defined KINTYRE's primary success criterion as a measurably improved,
  complete and working music library.
- Established the permanent rule that work is not built unless it directly
  improves the library or is essential to a defined measurable improvement.
- Required every capability to identify its concrete library problem, expected
  benefit, verification evidence and reversal path.
- Expanded D4 REVIEW to explain expected library benefit and downstream
  behaviour before approval.
- Corrected stale HANDOVER statements so D2 COPY and D3 FIX are recorded as
  complete and D4 REVIEW is the active milestone.

## 23 July 2026 — v2 D3 FIX completed

- Added `src/fix_album.py`, a bounded Beets/MusicBrainz FIX workflow for retained COPY transactions.
- Added isolated tool configuration, database and cache plus immutable execution evidence.
- Added before/after file manifests and ffprobe packet-data verification to protect audio essence.
- Added five FIX tests covering isolation, COPY-evidence validation, audio-integrity failure and evidence collision.
- Commissioned FIX against retained transaction `D2-COPY-ABBA-VOYAGE-20260723`.
- Beets 2.12.0 produced a 100% MusicBrainz match for ABBA — Voyage using release `034779cb-e14d-4845-a9db-6001c635928d`.
- All 10 staged audio files received metadata changes while ffprobe packet-data hashes remained unchanged.
- Beets exited with status 0, no verification errors were recorded, all evidence was retained read-only, and 75 tests passed.
- Production remained untouched. D3 is complete and D4 REVIEW is next.

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


### Added
- Implemented the v2 COPY transaction engine for one CONTEMPORARY album.
- Added complete-directory copying, immutable manifests, SHA-256 verification, path/symlink protection and deterministic JSON evidence.
- Added unit tests for successful copying, source isolation, symlink rejection, transaction collision and transaction-ID traversal rejection.
- Completed D2 commissioning with transaction `D2-COPY-ABBA-VOYAGE-20260723`: 11 files, 10 audio files and 81,569,309 bytes copied and independently revalidated against the immutable source and destination manifests.

## v1.0 — 17 July 2026

Released the deterministic Scan, Metadata Audit, Analysis, Preview, Approval and Apply baseline with backup, rollback, verification and automated tests. Post-v1 work added Music Assistant artwork commissioning, read-only artwork verification and engineering continuity documentation.
