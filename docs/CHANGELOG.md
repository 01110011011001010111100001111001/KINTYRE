# KINTYRE Changelog

## Unreleased

### Engineering continuity

- Added `docs/HANDOVER.md` as the self-contained continuity and engineering
  briefing for an incoming AI assistant.
- Established mandatory repository-first startup, evidence, testing,
  documentation and sprint-completion rules.
- Clarified that the future generated handover described by ADR-0001 will
  complement, not replace, the maintained handover document.

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


## Music Assistant artwork commissioning

- Added non-destructive, authenticated Music Assistant artwork commissioning for albums and artists.
- Added dry-run, explicit live confirmation, pagination, rate limiting, resumable state, structured reporting and regression tests.
- Documented the strict boundary: Music Assistant API only; no media writes and no direct database manipulation.

### Artwork commissioning operational validation

- Validated token-file authentication, paginated enumeration and complete commissioning through the supported API.
- Validated resumable state, `SKIPPED_COMPLETED` behaviour and deliberate recommissioning after archiving state.
- Clarified that `TOUCHED` records API success, not guaranteed artwork.
- Clarified that downstream enrichment is asynchronous and provider-dependent.
- Documented metadata remediation, Music Assistant rescan or rebuild, commissioning and artwork verification as distinct stages.
- Corrected examples so deployment-specific values are explicitly assigned rather than presented as literal filenames or URLs.
- Kept credentials, endpoints, production names, counts, logs, reports and runtime state out of the public repository.

## Music Assistant artwork verification

- Added a read-only Artwork Verification Engine for albums and artists.
- Verified artwork presence from canonical Music Assistant entity-detail
  responses and `metadata.images`.
- Added `PRESENT`, `MISSING`, `NON_PRIMARY_ONLY`, and `ERROR` outcomes.
- Added deterministic JSON reporting with artwork counts, image types,
  provenance providers and explicit evidence boundaries.
- Added regression tests for missing artwork, primary artwork, non-primary-only
  artwork, API failures and report semantics.
- Live-validated a bounded album sample without modifying Music Assistant or
  `/data/Music`.
- Explicitly records image retrievability and validity as `NOT_TESTED`.

### Roadmap decision

- Added an optional AI Metadata Recovery Assistant for cases unresolved by deterministic tools and conventional metadata services.
- AI output is advisory only and must enter the normal Preview, Approval and Apply controls before any production modification.
