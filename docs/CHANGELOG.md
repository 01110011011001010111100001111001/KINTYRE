# KINTYRE Changelog

## v1.0 — 17 July 2026

### Added

- Scan, Metadata Audit, Analysis and Preview engines
- stable action identifiers
- four-state Approval model
- generic exact and contains filters
- single-action, filtered bulk and explicit `--all` Approval operations
- atomic Approval persistence
- Approval summaries and approved-action export
- append-only Approval audit logging
- Apply dry run and explicitly confirmed live execution
- FLAC, MP3, M4A, M4B and MP4 AlbumArtist metadata writers
- duplicate-target detection
- per-transaction backups and post-write verification
- transaction rollback and batch rollback after a later failure
- Apply outcome audit events
- automated regression and real-media certification tests

### Production validation

The production-approved plan contained 1,205 transactions. Live execution completed with 1,205 successful transactions and zero failures after the full automated test suite passed.

### Documentation correction

Documentation now distinguishes discovery, audit and writable format support; documents `approve --all`; and provides the exact end-to-end production workflow and confirmation phrase used by the released CLI.
