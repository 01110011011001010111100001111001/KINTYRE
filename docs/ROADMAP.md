# KINTYRE Roadmap

## Purpose

This document is the authoritative plan for future KINTYRE releases.

The roadmap defines release priorities and intended outcomes. Detailed implementation tasks may be added during development, but must remain aligned with the release objectives documented here.

## Permanent design principles

All future development must preserve these principles:

- The music library is the authoritative source of truth.
- Music Assistant is a rebuildable consumer of the library.
- The data drive contains media and data only.
- Applications, databases, reports, logs, caches, staging files and temporary files remain on the system drive.
- Library changes follow: Audit → Analysis → Preview → Approval → Apply → Verify.
- No production-library modification occurs without explicit approval.
- Every applied change must be traceable.
- Original metadata or files must be recoverable where changes are supported.
- Identity-changing operations require certification before production use.
- CONTEMPORARY and CLASSICAL remain separate logical libraries.
- Production Music Assistant data must not be used as the only record of library identity.
- The web interface and command-line interface must use the same application services, state model and safety controls.
- No interface may bypass Preview, Approval, Apply, backup, audit, verification or certification controls.

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
## v1.0.1 — Safe KINTYRE naming normalization

Status: Next maintenance release

### Release objective

Use **KINTYRE** consistently as the current product and application name without rewriting history or making risky filesystem, repository or deployment changes.

### Scope and safeguards

- inventory current references to `KINTYRE DAM`, `kintyre-dam` and equivalent legacy names;
- update current documentation to use `KINTYRE`;
- update current user-facing text, application identifiers and hard-coded defaults where the change is safe;
- update hard-coded paths or configuration keys only where they are genuinely application-controlled and a safe migration or compatibility path exists;
- preserve the public Git repository name unless a separate repository migration is explicitly approved;
- preserve Git history, tags, release history and historical changelog entries;
- do not rewrite prior commits;
- do not alter historical evidence merely to modernize wording;
- do not rename the local project directory automatically;
- do not break existing installations, scripts, services, virtual environments or operator procedures;
- retain compatibility aliases or migration guidance where an old name may still be in active use;
- verify documentation links, commands, tests and clean-clone installation after the normalization.

### v1.0.1 acceptance criteria

v1.0.1 is complete only when:

- current documentation and current user-facing application text use KINTYRE consistently;
- remaining legacy-name references are documented as intentional historical or compatibility references;
- no Git history, release tag or historical changelog content has been rewritten;
- existing installations continue to work without an unsafe forced path rename;
- the full automated test suite passes;
- a clean clone installs and runs successfully.
## v1.1 — Library quality and duplicate detection

Status: Planned

### Release objective

Detect structural, duplication and audio-quality problems beyond ordinary metadata fields.

### Duplicate Detection Engine

Objective: Provide safe, repeatable identification of duplicate content without modifying the authoritative music library.

Planned capabilities:

- exact duplicate file detection using audio hashes;
- duplicate track detection across folders;
- duplicate album detection;
- duplicate artist identity detection;
- duplicate embedded artwork detection;
- duplicate folder artwork detection;
- probable duplicate detection using audio and metadata evidence;
- confidence scoring: Exact, Very High, High and Possible;
- duplicate reports grouped by duplicate class;
- preview of proposed duplicate resolution;
- approval before any duplicate-related operation;
- no automatic deletion or merge;
- optional merge workflows only in a future certified release;
- verification after approved duplicate resolution.

Additional quality capabilities:

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

### v1.1 acceptance criteria

- duplicate classes are reported separately;
- confidence scores are documented;
- duplicate detection is deterministic between runs;
- no duplicate operation modifies the production library without approval;
- automated regression tests cover duplicate detection algorithms and quality rules.
## v1.2 — Guided operations dashboard and pipeline manager

Status: Planned
Priority: Highest feature release

### Release objective

Provide a professional local web interface that guides the operator through the complete protected KINTYRE workflow and exposes all application runtime actions, reports and key process metrics from one place.

The dashboard is an operational interface for running KINTYRE. It is not a general-purpose server administration panel and must not introduce an alternate path around application safety controls.

### Interface foundation

Use a mature, maintained Python web-interface framework to minimize custom front-end development while retaining a professional result.

Preferred implementation direction:

- NiceGUI for the guided operational interface, forms, tables, dialogs and workflow controls;
- FastAPI-backed application services;
- Grafana OSS for professional metrics dashboards, trends, logs, alerts and operational observability;
- a lightweight metrics and logging layer, selected through an architecture decision, to provide Grafana-compatible structured data;
- existing KINTYRE Python engines as the authoritative processing layer;
- one shared state model for command-line, web and observability views;
- no duplicated pipeline logic in page handlers or Grafana dashboards;
- no direct shell-command construction from unvalidated browser input.

Grafana is an observability component, not the authoritative workflow engine. It may display KINTYRE status and link to the guided interface, but it must not directly execute Apply, change approval state or bypass application safety controls.

A short architecture decision record must confirm the interface and observability stack before implementation. The decision must compare at least:

- NiceGUI and Streamlit for guided workflow, approvals, reports and long-running operations;
- Grafana OSS for metrics, logs, historical trends, alerts and operational health;
- Prometheus-compatible metrics, SQLite or PostgreSQL reporting data, and Loki-compatible logs where justified;
- embedded, linked and reverse-proxied deployment options;
- resource consumption and maintenance burden on KINTYRE.

The selected design must minimize custom front-end work while keeping installation, backup, upgrade and recovery procedures understandable.

### Guided end-to-end workflow

The interface must guide:

Validate → Scan → Audit → Analysis → Preview → Approval → Apply → Verify

Planned capabilities:

- one command or managed service to start KINTYRE;
- display the local or LAN web address clearly;
- dashboard home page showing library health and current pipeline state;
- step-by-step pipeline navigation;
- clear Ready, Running, Completed, Warning, Blocked and Failed states;
- explicit prerequisites for each stage;
- automatic prevention of invalid stage transitions;
- safe pause and resume;
- safe restart after a corrected failure;
- immediate stop after a failed or blocked stage;
- persistent run identifiers and timestamps;
- consolidated run summary;
- CONTEMPORARY and CLASSICAL filtering throughout;
- links between summary metrics, issue records, proposed actions and final outcomes.

### Actions available from the interface

The interface must allow the operator to:

- validate environment, configuration, dependencies and library access;
- start and monitor Scan;
- start and monitor metadata and artwork audits;
- run Analysis;
- generate Preview and approval plans;
- inspect proposed changes before approval;
- approve, reject or reset individual actions;
- perform controlled bulk approval and rejection;
- start approved dry-run Apply;
- start approved production Apply only after a second explicit confirmation;
- run post-Apply verification;
- inspect backups, transactions, audit events and rollback information;
- open, filter and export generated reports;
- view run logs and actionable error messages;
- cancel only operations that are explicitly designed to be safely cancellable.

Apply must remain unavailable until all relevant approvals, validation checks and certification requirements are satisfied.

### Reports and metrics

The dashboard must expose metrics already produced by KINTYRE and add a stable metrics contract for future engines.

Key metrics include:

- configured libraries and paths;
- total files, albums and storage size;
- readable and unreadable files;
- files scanned and scan duration;
- audit issue totals by type and severity;
- issue totals by logical library;
- analyzed folders and candidate counts;
- proposed action counts by operation;
- approved, rejected, pending and reset action counts;
- dry-run validation totals;
- blocked, successful and failed transaction counts;
- backup counts;
- verification outcomes;
- current stage, elapsed time and completion percentage where measurable;
- last successful run per stage;
- application version, configuration identity and report timestamps.

Metrics must come from structured engine outputs or application services, not by scraping formatted terminal text.

### Grafana observability

Grafana OSS should provide read-only operational dashboards for:

- current and historical pipeline duration;
- files and albums processed over time;
- issue totals and severity trends;
- proposed, approved, rejected, blocked, successful and failed action totals;
- Apply and verification outcomes;
- backup creation and transaction history;
- worker and application health;
- runtime resource use relevant to KINTYRE;
- Music Assistant reconciliation health when that integration is introduced;
- Bluetooth transport health and diagnostic results when that integration is introduced;
- logs and alerts for failed, blocked or unexpectedly long operations.

Grafana dashboards and data-source configuration must be provisioned as version-controlled files where practical. Dashboard definitions must contain no secrets and must be reproducible after a clean installation.

The guided KINTYRE interface may embed or link to Grafana panels, but the system must remain operable if Grafana is unavailable. Grafana failure must never invalidate pipeline state or prevent safe command-line recovery.

### Runtime management

Runtime management is limited to the KINTYRE application:

- application start and orderly stop;
- pipeline job status;
- controlled job cancellation where supported;
- configuration validation;
- report and runtime-directory health;
- worker or task status;
- application logs;
- version and dependency information;
- database or state-store health where introduced.

The dashboard must not become a general root-level system administration console.

### Security and safety

- default to local access;
- require an explicit configuration decision before LAN exposure;
- bind conservatively;
- do not run the web process as root;
- protect state-changing routes;
- prevent concurrent conflicting Apply operations;
- require explicit production confirmation;
- record operator actions in the audit log;
- avoid exposing secrets in pages, logs or reports;
- define authentication requirements before any access beyond a trusted local network.

### Safe AI development handover

The interface and command line must provide a safe handover generator for continuing KINTYRE development or troubleshooting in a new AI chat when the current conversation becomes slow, too long or unreliable.

Planned capabilities:

- dashboard action and CLI command to generate a handover package;
- concise Markdown output suitable for direct pasting into a new AI chat;
- optional structured JSON output for machine processing;
- repository URL, local project path, branch, commit, tags and working-tree state;
- recent relevant commits;
- active roadmap release and current implementation task;
- completed work and verified results;
- full test totals, failures and blocked tests;
- current pipeline state and latest report locations;
- relevant application, dependency and configuration versions;
- important runtime paths without embedding machine-specific assumptions as product defaults;
- permanent architecture and safety principles;
- approved decisions and rejected approaches that must not be reconsidered without cause;
- known defects, unresolved questions and operational risks;
- the exact recommended next action;
- clear separation between verified facts, user decisions, assumptions and suggested work;
- source commit and generation timestamp;
- warning when the repository has changed since the handover was generated;
- automatic redaction of passwords, tokens, cookies, API keys, private keys and other secrets;
- configurable exclusion of private paths or environment details;
- deterministic output ordering so handovers can be compared;
- size controls that preserve essential context while avoiding unnecessary transcript duplication;
- validation that the generated package contains the minimum information required for safe continuation.

The handover must describe the repository state rather than attempting to reproduce private AI reasoning. A receiving AI must be instructed to inspect the repository and verify the recorded state before proposing or applying changes.

### v1.2 acceptance criteria

v1.2 is complete only when:

- one supported command or service starts the dashboard;
- every protected pipeline stage can be run and monitored through the interface;
- the command-line and web interfaces use the same orchestration and safety logic;
- stage status, warnings, failures, reports and key metrics are visible;
- Grafana dashboards display provisioned KINTYRE metrics, trends and operational health without controlling protected workflow actions;
- loss of Grafana does not prevent safe operation or recovery through the guided interface or command line;
- issue and action tables are searchable and filterable;
- approval controls cannot be bypassed;
- production Apply requires explicit approval and a second confirmation;
- interrupted or failed runs have a documented safe recovery path;
- the dashboard and CLI generate a secret-redacted, paste-ready handover tied to the current source commit;
- generated handovers distinguish verified state from assumptions and identify the exact next action;
- automated tests cover routing, state transitions, authorization boundaries and approval enforcement;
- documentation includes installation, operation, recovery and upgrade procedures;
- a clean clone installs and runs the complete v1.2 test suite.
## v1.3 — Images and artwork

Status: Planned

### Release objective

Improve library artwork completeness and quality while keeping image operations separate from identity-changing metadata operations.

### Planned capabilities

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
- support approved artwork-provider integration only after provider, licensing and provenance rules are documented;
- record artwork source and provenance where artwork is acquired;
- prevent low-confidence automated artwork assignment.
## v1.4 — Certification environment

Status: Planned

### Release objective

Provide a permanent, disposable environment for proving metadata, image and identity-changing operations before they are allowed against the production library.

### Planned capabilities

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
## v1.5 — Identity management

Status: Planned

### Release objective

Safely support metadata operations that can change album or artist identity.

### Planned capabilities

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

All identity-changing operations remain certification-only until individually validated and approved for production.
## v1.6 — Music Assistant integration and Bluetooth playback reliability

Status: Planned

### Release objective

Reconcile the cleaned and certified authoritative library with Music Assistant after core library quality, certification and identity work is complete.

Music Assistant remains a consumer. Filesystem findings remain authoritative over Music Assistant state.

### Music Assistant reconciliation

Planned capabilities:

- document the supported Music Assistant deployment model;
- detect whether Music Assistant can reach each configured library path;
- audit Music Assistant library-provider configuration;
- compare filesystem albums with Music Assistant-visible albums;
- compare filesystem artists with Music Assistant-visible artists;
- identify albums absent from Music Assistant;
- identify artists absent from Music Assistant;
- identify stale Music Assistant albums and artists;
- identify duplicate Music Assistant album and artist identities;
- identify orphaned Music Assistant records;
- identify failed or incomplete Music Assistant scans;
- identify incorrect album grouping;
- identify unexpected compilation grouping;
- identify stale artwork and image-cache results;
- generate a Music Assistant health report;
- generate a filesystem-to-Music-Assistant reconciliation report;
- provide safe rescan guidance;
- provide safe provider removal and re-add procedures;
- provide safe Music Assistant database rebuild procedures;
- distinguish cache problems from metadata identity problems;
- verify Music Assistant results after approved library changes;
- keep production and certification Music Assistant databases separate;
- prevent direct manipulation of the production Music Assistant database unless a separately certified maintenance operation is introduced.

### v1.6 acceptance criteria

v1.6 is complete only when:

- reconciliation identifies missing, stale, duplicate and orphaned Music Assistant entities;
- Music Assistant rebuild procedures are documented and tested;
- production and certification environments remain isolated;
- no production Music Assistant database is changed without explicit approval;
- automated tests cover Music Assistant reconciliation reports and state transitions.
## v1.7 — Player performance and Bluetooth audio reliability

Status: Planned

### Release objective

Provide repeatable diagnostics and conservative, reversible tuning for KINTYRE host audio and Bluetooth players, including faults such as pitch fluctuation, speed variation, timing instability or underruns during the first seconds of a track.

This release concerns player and system audio performance. It is separate from Music Assistant library reconciliation and must remain useful for any supported audio source capable of exercising the affected player.

### Bluetooth playback diagnostics and tuning

Objective: Diagnose and reduce playback instability such as pitch fluctuation, speed variation, underruns or timing instability during the first seconds of a track.

Planned capabilities:

- inventory the Bluetooth controller, player, codec, profile and audio stack;
- detect BlueZ, PipeWire, WirePlumber, ALSA and relevant service versions;
- record the active A2DP codec and profile;
- inspect negotiated sample rates and channel formats;
- inspect PipeWire graph rate, quantum, buffering and resampling state;
- collect relevant service logs and runtime diagnostics;
- detect underruns, overruns, transport interruptions and repeated reconnects where observable;
- test whether instability correlates with track sample-rate changes;
- test whether instability correlates with player activation, stream start, codec negotiation, buffering or clock-rate matching;
- provide a repeatable short test sequence using representative tracks;
- capture before-and-after measurements;
- support per-device diagnostic profiles;
- recommend conservative, reversible tuning for codec, sample-rate, resampling, buffering and service configuration;
- back up every changed system audio configuration;
- provide rollback instructions before applying a tuning change;
- apply no system-level tuning automatically without explicit approval;
- avoid global tuning when a device-specific rule is sufficient;
- distinguish library or decoder problems from Bluetooth transport problems;
- expose Bluetooth health, active codec, recent errors and test results in the KINTYRE dashboard;
- document known limitations where the receiving Bluetooth device controls behaviour that KINTYRE cannot correct.

Additional scope:

- establish a reproducible baseline before changing system audio settings;
- identify whether the fault originates in decoding, resampling, buffering, Bluetooth transport, receiver behaviour or player activation;
- support Music Assistant as one test source without making Music Assistant a prerequisite for diagnostics;
- expose player-performance diagnostics and results through the KINTYRE dashboard;
- retain system audio configuration on the system drive;
- document every modified system file and service;
- require explicit approval before changing PipeWire, WirePlumber, BlueZ, ALSA or service configuration;
- restart audio services only through a documented, recoverable procedure;
- preserve a tested rollback path for every tuning profile.

### v1.7 acceptance criteria

v1.7 is complete only when:

- the active Bluetooth controller, device, profile, codec and audio path can be reported;
- a repeatable diagnostic captures relevant sample-rate, buffering and timing information;
- the start-of-track pitch or timing fault can be tested using a documented procedure;
- recommendations are based on captured evidence rather than speculative tuning;
- changes are reversible and preferably device-specific;
- before-and-after results show whether a proposed change improved or worsened playback;
- Music Assistant is not required for the underlying diagnostic framework;
- no system audio configuration is changed without explicit approval;
- rollback procedures are documented and tested;
- application-level diagnostic parsing is covered by automated tests where practical.
## v1.8 — Classical metadata intelligence

Status: Planned

### Release objective

Improve analysis and certification of classical music metadata without forcing contemporary-music assumptions onto the CLASSICAL library.

### Planned capabilities

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
## v1.9 — Performance and incremental operation

Status: Planned

### Release objective

Reduce processing time while preserving determinism, traceability and safety.

### Planned capabilities

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
- controlled cache invalidation;
- dashboard progress and throughput metrics for long-running operations.
## v2.0 — Multi-user library management platform

Status: Future

### Release objective

Expand the guided KINTYRE dashboard into a broader, secured multi-user operational platform without replacing or bypassing the certified workflow.

### Potential capabilities

- authenticated multi-user access;
- role-based access;
- approval delegation;
- scheduled audits;
- scheduled reconciliation;
- notifications;
- multi-library configuration;
- REST API;
- plugin architecture;
- operational report retention policies;
- external monitoring integration;
- deployment and upgrade management;
- high-availability options only if justified.

No v2.0 interface may bypass Preview, Approval, Apply, backup, audit, verification or certification controls.

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

Features not listed in the active release scope must not be introduced without first updating this roadmap.
