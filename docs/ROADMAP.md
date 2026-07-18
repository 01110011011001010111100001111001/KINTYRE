# KINTYRE Roadmap

## Purpose

This is the authoritative release plan for KINTYRE. The release order is now stable. Future changes should refine scope without casually renumbering or restructuring the roadmap.

## Permanent principles

- The music library is authoritative; Music Assistant is a rebuildable consumer.
- The data drive contains media and data only.
- Applications, databases, reports, logs, caches, staging and temporary files remain on the system drive.
- Changes follow Audit → Analysis → Preview → Approval → Apply → Verify.
- No production change occurs without explicit approval.
- Applied changes are traceable, recoverable and verifiable.
- Identity-changing operations require certification before production.
- CONTEMPORARY and CLASSICAL remain separate logical libraries.
- CLI and web interfaces use the same services, state and safeguards.
- No interface bypasses approval, backup, audit, verification or certification.
- Maintained OSS is evaluated before equivalent custom development.
- KINTYRE integrates, safeguards and orchestrates proven OSS rather than reimplementing mature functionality.
- Significant technology decisions require an ADR.

## OSS-first policy

For every applicable capability, assess maintained candidates for licence, activity, security, automation, determinism, read-only operation, offline suitability, scale, data location, backup, rollback, integration effort and long-term maintenance.

Preferred order:

1. configure an existing OSS solution;
2. integrate an existing library or CLI behind KINTYRE controls;
3. extend or contribute upstream;
4. implement only missing KINTYRE orchestration;
5. build custom functionality only when documented requirements cannot otherwise be met safely.

Candidate names below are recommended starting points, not automatic selections.

## Technology direction

- Workflow UI: NiceGUI with FastAPI-backed services.
- Observability: Grafana OSS.
- Metrics/logs: Prometheus- and Loki-compatible components where justified.
- Media inspection: FFmpeg and ffprobe.
- Exact duplicate evidence: cryptographic hashes.
- Acoustic evidence: Chromaprint; optional AcoustID-compatible lookup.
- Library tooling: beets where it fits KINTYRE safeguards.
- Metadata identity: MusicBrainz and MusicBrainz Picard.
- Images: Pillow, ImageMagick and imagehash; OpenCV only when justified.
- Database exploration: Datasette where useful and read-only.
- Search: SQLite FTS5 initially; OpenSearch only if justified by evidence.
- Linux audio diagnostics: BlueZ, PipeWire, WirePlumber and ALSA tools/APIs.
- Configuration: Pydantic Settings.
- CLI modernization: Typer where justified.
- Documentation: MkDocs Material when publishing is introduced.

## Release plan

### v1.0 — Released baseline

Released capabilities: Scan, Metadata Audit, Analysis, Preview, Approval, Apply, approval state, filtering, bulk approval, approval audit logging, dry-run Apply, live-write foundations, backup/rollback, Apply outcome integration, regression tests, clean-clone validation and core documentation.

### v1.0.1 — Safe AI development handover

Status: First post-v1.0 task
Priority: Immediate

#### Objective

Generate a deterministic, secret-safe handover so development can continue accurately in a new AI chat when the current one becomes slow or unreliable.

#### Scope

- one CLI command for paste-ready Markdown;
- optional JSON;
- concise and extended modes;
- repository, branch, commit, tags and working-tree state;
- recent relevant commits;
- active release and exact next task;
- completed work, tests, failures and blocked work;
- pipeline state and report locations;
- relevant versions and runtime paths;
- permanent decisions, rejected approaches, risks and unresolved questions;
- separation of verified facts, user decisions, assumptions and proposals;
- commit/timestamp freshness markers;
- deterministic ordering;
- automatic secret redaction;
- configurable private-path exclusion;
- validation of minimum required content;
- explicit instruction that the receiving AI verifies repository state before changes.

The handover records evidence and decisions, not private AI reasoning.

#### Acceptance

- one documented command produces valid Markdown;
- facts, decisions, assumptions and proposals are distinct;
- secrets are redacted;
- unchanged source produces deterministic output;
- stale handovers are detectable;
- missing optional evidence is handled safely;
- automated tests cover collection, formatting, redaction and missing data;
- clean-clone generation succeeds.

### v1.0.2 — Safe KINTYRE naming normalization

Status: Planned maintenance release

Use KINTYRE consistently in current documentation and current code/configuration where safe.

Safeguards:

- preserve Git history, tags and historical changelog entries;
- preserve the public repository name unless separately approved;
- do not rename the local project directory automatically;
- change paths/config keys only with safe compatibility or migration;
- document intentional historical or compatibility references;
- verify commands, links, tests and clean-clone installation.

### v1.1 — Library quality and duplicate intelligence

Status: Planned
Priority: Core functionality

#### OSS assessment

Evaluate:

- standard cryptographic hashing;
- dupeGuru, rdfind and fdupes for duplicate behavior and concepts;
- Chromaprint;
- AcoustID-compatible lookup where privacy/connectivity allow;
- beets duplicate and chroma capabilities;
- FFmpeg/ffprobe;
- rsgain or equivalent ReplayGain tooling;
- imagehash, Pillow and ImageMagick.

#### Scope

- exact duplicate files;
- same-audio fingerprints;
- duplicate tracks, albums, artist identities and artwork;
- evidence-based confidence classes;
- no automatic deletion or merge;
- missing tracks, numbering gaps and empty folders;
- unsupported, unreadable and corrupt media;
- filename, folder/tag and image consistency;
- ReplayGain audit;
- configurable quality thresholds and trends.

#### Acceptance

- ADR with reproducible candidate tests;
- deterministic results;
- documented evidence and confidence;
- documented false-positive handling;
- no production modification without Approval/Apply;
- regression tests pass.

### v1.2 — Guided operations dashboard and pipeline manager

Status: Planned
Priority: High

#### Architecture

Evaluate NiceGUI, Streamlit and maintained alternatives against long-running jobs, persistent state, large tables, approvals, progress, recovery, authentication and maintenance.

Preferred direction:

- NiceGUI for guided operations;
- FastAPI-backed services;
- Grafana OSS for read-only observability;
- shared CLI/web orchestration and safeguards;
- structured metrics/logs;
- no direct unvalidated shell construction;
- safe operation remains possible without Grafana.

#### Scope

Validate → Scan → Audit → Analysis → Preview → Approval → Apply → Verify

Provide state, prerequisites, progress, reports, searchable issues/actions, controlled bulk decisions, dry-run/production separation, second confirmation, backups, transactions, audit events, rollback information and recovery.

Grafana dashboards cover run duration, throughput, library metrics, issue trends, approval/Apply outcomes, verification, backups, application health, host resources, later MA reconciliation and later player diagnostics.

### v1.3 — Integration platform

Status: Planned

Create a standard adapter framework for OSS tools:

- capability and version discovery;
- typed configuration;
- normalized structured results;
- progress/cancellation contracts;
- error normalization;
- structured logs and metrics;
- dry-run/read-only declaration;
- data-location declaration;
- timeouts/resource limits;
- security boundaries;
- reproducible fixtures;
- safe degradation when optional tools are absent.

### v1.4 — Images and artwork

Status: Planned

Evaluate MusicBrainz Cover Art Archive, Picard/plugins, fanart.tv where licensing permits, Pillow, ImageMagick, imagehash and OpenCV only where needed.

Provide completeness, corruption, resolution, format, size, conflict, consistency and perceptual-duplicate audits; provenance; Preview/Approval/Apply/Verify; backup and rollback.

### v1.5 — Certification environment

Status: Planned

Provide an isolated disposable certification library, separate Music Assistant instance/database, repeatable creation/destruction, representative fixtures, before/after comparisons, certification reports/evidence and explicit production-promotion criteria.

### v1.6 — Identity management

Status: Planned

Evaluate MusicBrainz, Picard, beets and maintained compatible libraries.

Provide certified AlbumArtist, artist, album-title, compilation and MusicBrainz-ID workflows; rename/move Preview; collision checks; cross-library protection; MA identity-impact Preview; backup, verification and rollback.

### v1.7 — Music Assistant integration

Status: Planned

Keep Music Assistant a rebuildable consumer.

Provide provider/path audit, filesystem-to-MA reconciliation, missing/stale/duplicate/orphaned entity detection, scan/grouping/cache diagnostics, health reports, safe rescan/provider-readd/database-rebuild procedures, production/certification isolation and no direct production DB manipulation unless separately certified.

### v1.8 — Player performance and Bluetooth audio reliability

Status: Planned

This is separate from Music Assistant library integration.

Use BlueZ, PipeWire, WirePlumber, ALSA and FFmpeg-derived test evidence before custom probes.

Provide controller/device/codec/profile inventory, sample-rate and graph evidence, buffering/resampling diagnostics, log collection, underrun/reconnect detection, repeatable start-of-track tests, before/after measurements, per-device profiles, conservative reversible tuning, backups and rollback. Music Assistant may be one test source but is not required.

### v1.9 — Classical metadata intelligence

Status: Planned

Evaluate MusicBrainz classical relationships, Picard, beets plugins and maintained classical-metadata projects.

Provide composer, conductor, ensemble, soloist, work, movement, opus/catalogue, multi-disc, AlbumArtist and folder-structure intelligence with classical-specific reports and fixtures.

### v1.10 — Performance and incremental operation

Status: Planned

Provide incremental scanning, changed-file detection, persistent indexes, cached fingerprints, safe parallel reads, resumable operations, selective processing, benchmarks, controlled cache invalidation and dashboard throughput metrics.

### v2.0 — Multi-user library management platform

Status: Future

Potential scope: authentication, roles, approval delegation, schedules, notifications, multi-library configuration, REST API, plugin ecosystem, retention policies, deployment management and high availability only if justified.

## Release governance

For every release:

1. confirm scope and dependency order;
2. complete the applicable OSS assessment;
3. create/update ADRs;
4. define implementation tasks;
5. add/update tests;
6. update user, architecture and developer documentation;
7. run the complete test suite;
8. validate a clean clone;
9. confirm a clean working tree;
10. commit release content;
11. tag completed releases;
12. update `docs/CHANGELOG.md`.

Features outside active scope require a documented reason and must preserve dependency order.
