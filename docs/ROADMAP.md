# KINTYRE Roadmap

## Purpose

This document is the authoritative plan for future KINTYRE releases.

The roadmap defines release priorities and intended outcomes. Detailed
implementation tasks may be added during development, but must remain aligned
with the release objectives documented here.

## Permanent design principles

All future development must preserve these principles:

- The music library is the authoritative source of truth.
- Music Assistant is a rebuildable consumer of the library.
- The data drive contains media and data only.
- Applications, databases, reports, logs, caches, staging files and temporary
  files remain on the system drive.
- Library changes follow:
  Audit → Analysis → Preview → Approval → Apply.
- No production-library modification occurs without explicit approval.
- Every applied change must be traceable.
- Original metadata or files must be recoverable where changes are supported.
- Identity-changing operations require certification before production use.
- CONTEMPORARY and CLASSICAL remain separate logical libraries.
- Production Music Assistant data must not be used as the only record of
  library identity.

## v1.0 — Released baseline

Status: Released

Completed capabilities:

- Scan Engine
- Metadata Audit Engine
- Analysis Engine
- Preview Engine
- Approval Engine
- Apply Engine
- approval state model
- generic filtering
- bulk approval
- approval audit logging
- Apply dry-run
- controlled live-write foundations
- backup and rollback handling
- Apply outcome integration
- automated regression testing
- clean-clone installation validation
- operational and architecture documentation

## v1.1 — Images and Music Assistant integration

Status: Next release

Priority: Highest

### Release objective

Improve the visible completeness and reliability of the Music Assistant
library while keeping the filesystem library authoritative and protected.

Images and Music Assistant integration are co-equal priorities for v1.1.

### Images and artwork

Planned capabilities:

- audit album artwork availability;
- audit artist image availability;
- identify albums with no usable image;
- identify artists with no usable image;
- detect missing folder artwork;
- detect missing embedded artwork;
- detect unreadable or corrupt images;
- detect artwork below a configurable minimum resolution;
- detect excessively large artwork;
- detect unsupported image formats;
- detect conflicting embedded and folder artwork;
- detect inconsistent artwork across tracks in one album;
- detect multiple embedded front-cover images;
- report artwork dimensions, format and file size;
- generate album-artwork completeness reports;
- generate artist-image completeness reports;
- generate artwork quality scores;
- preview proposed artwork operations;
- require approval before artwork changes;
- preserve original artwork before replacement;
- verify artwork after Apply;
- support rollback of applied artwork changes;
- support configurable preferred image dimensions and formats;
- support approved artwork-provider integration only after provider,
  licensing and provenance rules are documented;
- record artwork source and provenance where artwork is acquired;
- prevent low-confidence automated artwork assignment;
- keep artwork operations separate from identity-changing metadata changes.

### Music Assistant integration

Planned capabilities:

- document the supported Music Assistant deployment model;
- detect whether Music Assistant can reach each configured library path;
- audit Music Assistant library-provider configuration;
- compare filesystem albums with Music Assistant-visible albums;
- compare filesystem artists with Music Assistant-visible artists;
- identify albums absent from Music Assistant;
- identify artists absent from Music Assistant;
- identify stale Music Assistant albums;
- identify stale Music Assistant artists;
- identify duplicate Music Assistant album identities;
- identify duplicate Music Assistant artist identities;
- identify orphaned Music Assistant records;
- identify failed or incomplete Music Assistant scans;
- identify incorrect album grouping;
- identify unexpected compilation grouping;
- identify stale artwork and image cache results;
- generate a Music Assistant health report;
- generate a filesystem-to-Music-Assistant reconciliation report;
- provide safe rescan guidance;
- provide safe provider removal and re-add procedures;
- provide safe Music Assistant database rebuild procedures;
- distinguish cache problems from metadata identity problems;
- verify Music Assistant results after approved library changes;
- support a disposable Music Assistant certification environment;
- keep production and certification Music Assistant databases separate;
- prevent direct manipulation of the production Music Assistant database
  unless a separately certified maintenance operation is introduced.

### v1.1 acceptance criteria

v1.1 is complete only when:

- image and artwork audits are repeatable;
- missing and low-quality images are reported clearly;
- no artwork operation can modify the production library without approval;
- Music Assistant reconciliation can identify missing, stale and duplicate
  entities;
- Music Assistant rebuild procedures are documented and tested;
- production and certification environments remain isolated;
- automated tests cover all new report and state transitions;
- documentation is updated before release;
- a clean clone can install and run the complete v1.1 test suite.

## v1.2 — Certification environment

Status: Planned

### Release objective

Provide a permanent, disposable environment for proving metadata and image
operations before they are allowed against the production library.

Planned capabilities:

- isolated certification music library;
- separate Music Assistant instance;
- separate Music Assistant database;
- repeatable environment creation;
- repeatable environment destruction;
- controlled representative test fixtures;
- before-and-after metadata comparison;
- before-and-after image comparison;
- before-and-after Music Assistant identity comparison;
- certification reports;
- recorded certification evidence;
- operation-level certification status;
- explicit promotion criteria for production eligibility.

## v1.3 — Identity management

Status: Planned

### Release objective

Safely support metadata operations that can change album or artist identity.

Planned capabilities:

- AlbumArtist correction;
- artist-name normalization;
- album-title normalization;
- compilation detection and correction;
- MusicBrainz identifier auditing;
- MusicBrainz identifier correction;
- folder rename preview;
- folder move preview;
- path-collision detection;
- cross-library move prevention;
- Music Assistant identity-impact preview;
- certified Apply operations;
- complete backups;
- post-Apply verification;
- rollback support.

All identity-changing operations remain certification-only until individually
validated and approved for production.

## v1.4 — Library quality

Status: Planned

### Release objective

Detect structural and audio-quality problems beyond ordinary metadata fields.


### Duplicate Detection Engine

Objective:

Provide safe, repeatable identification of duplicate content without modifying
the authoritative music library.

Planned capabilities:

- exact duplicate file detection using audio hashes;
- duplicate track detection across folders;
- duplicate album detection;
- duplicate artist identity detection;
- duplicate Music Assistant album detection;
- duplicate Music Assistant artist detection;
- duplicate embedded artwork detection;
- duplicate folder artwork detection;
- confidence scoring (Exact, Very High, High, Possible);
- duplicate reports grouped by duplicate class;
- preview of proposed duplicate resolution;
- approval before any duplicate-related operation;
- no automatic deletion or merge;
- optional merge workflows in future releases;
- verification after approved duplicate resolution.

Acceptance criteria:

- duplicate classes are reported separately;
- confidence scores are documented in reports;
- duplicate detection is deterministic between runs;
- no duplicate operation modifies the production library without approval;
- automated regression tests cover duplicate detection algorithms.


Planned capabilities:

- duplicate-track detection;
- duplicate-album detection;
- probable duplicate detection using audio and metadata evidence;
- missing-track detection;
- unexpected track-number gaps;
- empty-folder detection;
- unsupported-file detection;
- invalid-filename detection;
- unreadable-file detection;
- corrupt-audio detection;
- folder and tag consistency checks;
- ReplayGain audit;
- embedded-image consistency checks;
- configurable quality thresholds;
- quality trend reporting.

## v1.5 — Classical metadata intelligence

Status: Planned

### Release objective

Improve analysis and certification of classical music metadata without forcing
contemporary-music assumptions onto the CLASSICAL library.

Planned capabilities:

- composer normalization;
- conductor normalization;
- ensemble normalization;
- soloist-role analysis;
- work detection;
- movement detection;
- work and movement grouping;
- opus and catalogue-number analysis;
- multi-disc classical-set analysis;
- classical AlbumArtist policy;
- classical folder-structure analysis;
- classical-specific reports;
- certification fixtures for representative classical releases.

## v1.6 — Performance and incremental operation

Status: Planned

### Release objective

Reduce processing time while preserving determinism, traceability and safety.

Planned capabilities:

- incremental scanning;
- changed-file detection;
- persistent indexes;
- cached metadata fingerprints;
- safe parallel metadata reading;
- resumable long-running operations;
- selective audit by library or path;
- selective analysis by issue type;
- selective preview regeneration;
- performance metrics;
- regression benchmarks;
- controlled cache invalidation.

## v2.0 — Library management platform

Status: Future

### Release objective

Provide an integrated operational interface over the certified KINTYRE
workflow.

Potential capabilities:

- web interface;
- dashboard;
- search and filtering;
- approval interface;
- audit-history viewer;
- artwork review interface;
- Music Assistant health dashboard;
- scheduled audits;
- scheduled reconciliation;
- notifications;
- multi-library configuration;
- REST API;
- plugin architecture;
- role-based access;
- exportable operational reports.

No v2.0 interface may bypass Preview, Approval, Apply, backup, audit or
certification controls.

## Release governance

For every release:

1. Define the intended scope in this roadmap.
2. Create implementation tasks linked to that scope.
3. Add or update automated tests.
4. Update user, architecture and developer documentation.
5. Run the complete test suite.
6. Validate installation from a clean clone.
7. Confirm the working tree is clean.
8. Commit all release content.
9. Create an immutable release tag.
10. Record completed changes in `docs/CHANGELOG.md`.

Features not listed in the active release scope must not be introduced without
first updating this roadmap.
