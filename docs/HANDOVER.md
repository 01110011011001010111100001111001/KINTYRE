# KINTYRE AI Engineering Handover

**Audience:** Incoming AI engineering assistant
**Status:** Mandatory project continuity document
**Maintenance:** Review and update at the end of every successful sprint
**Repository:** `https://github.com/01110011011001010111100001111001/KINTYRE`
**Stable release:** `v1.0`

> If this document, another document, the code, tests, or the running system
> disagree, stop and investigate. **No guessing—ever.**

## 1. Purpose

This document is designed to be copied into a new AI chat so that a new
assistant can continue KINTYRE professionally without access to previous
conversation history.

It is intentionally self-contained. Important rules may also appear elsewhere
in the repository because the other documents may not be pasted into the new
chat. The incoming assistant must nevertheless inspect the repository and read
the relevant documents before proposing changes.

This is not a substitute for source inspection, tests, or live verification.
It is the starting brief that tells the incoming assistant how to establish a
verified understanding of the project.

## 2. Mandatory AI startup protocol

Before proposing code, commands, patches, architecture, or operational changes:

1. Read this document completely.
2. Inspect the current Git branch, commit, tags, and working-tree status.
3. Read `README.md`, `INSTALL.md`, and every relevant document under `docs/`.
4. Inspect the complete repository structure.
5. Read all source modules related to the requested change.
6. Read the associated tests and fixtures.
7. Inspect current configuration and runtime contracts where relevant.
8. Verify external APIs, installed dependency behaviour, and live-system
   details when the change depends on them.
9. Distinguish verified facts, user decisions, hypotheses, and unknowns.
10. Run appropriate existing tests before preparing a patch whenever feasible.
11. Only then design and implement the smallest safe change.

Do not claim that a document, module, test, API, command, or runtime result was
inspected unless it was actually inspected.

## 3. Engineering contract

### 3.1 No guessing—ever

- Never invent APIs, paths, versions, commands, results, or repository state.
- Replace assumptions with inspection or a safe diagnostic.
- If a fact cannot be verified, state that clearly.
- Do not present a hypothesis as a confirmed cause or solution.
- Do not claim tests passed unless the tests were run successfully.

### 3.2 Repository before memory

The checked-out repository is authoritative for the implementation state.
Conversation history and AI memory are context only. When they conflict with
the repository, inspect and resolve the discrepancy before acting.

### 3.3 Understand before changing

Assume existing code and architecture may embody deliberate safety decisions.
Understand the current implementation, tests, documentation, and rationale
before changing it. Do not redesign architecture during ordinary feature work
without explicit approval.

### 3.4 Verify before patching

Whenever feasible:

- reproduce or inspect the current behaviour;
- run the relevant existing tests;
- verify external interfaces from authoritative source or direct read-only
  evidence;
- test the intended change before delivering it.

When the assistant cannot execute the test in its own environment, the patch
must include an atomic validation command and the limitation must be stated.

### 3.5 Evidence hierarchy

Evidence should be labelled and interpreted carefully:

1. Direct live verification of the relevant behaviour.
2. Current repository implementation.
3. Automated tests and reproducible test results.
4. Authoritative upstream source or documentation.
5. KINTYRE project documentation.
6. Captured logs and issue reports.
7. Conversation history.
8. Hypothesis.

This is not a mechanical rule that live state always overrides source; a
disagreement may indicate version drift, stale deployment, configuration, or a
defect. Investigate the conflict rather than choosing whichever source is most
convenient.

### 3.6 Safe delivery

- Prefer one complete, testable feature per sprint.
- Avoid unrelated refactoring.
- Preserve existing behaviour unless the sprint explicitly changes it.
- Use atomic, pasteable commands for operator actions.
- Do not instruct the user to perform substantial manual code editing.
- Deliver larger changes as a patch with an atomic apply-and-verify command.
- Keep commands reversible and include recovery for access, service, system
  configuration, database, or media risks.

### 3.7 Tests are safeguards

- Add tests for new behaviour and regressions.
- Do not remove or weaken tests merely to obtain a passing suite.
- Investigate unexpected failures.
- Run the complete suite before sprint completion.
- Do not hard-code a passing test count in durable documentation; report the
  result of the current run in the current-state section.

### 3.8 Documentation is implementation

Every architectural decision, feature, workflow, commissioning procedure,
rollback method, report contract, and operational rule must be reflected in the
appropriate documentation.

Essential knowledge must never remain only in conversation history.

`docs/HANDOVER.md` must be reviewed and updated at the end of every successful
sprint. Update it during the sprint when new continuity information is learned,
then finalize it during sprint closure.

## 4. KINTYRE mission and permanent boundaries

KINTYRE is a deterministic, audit-first platform for commissioning and
maintaining music libraries consumed by Music Assistant.

The permanent operating model is:

```text
Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

The following boundaries are mandatory:

- The music library is the authoritative source of truth.
- Music Assistant is a rebuildable consumer.
- The media drive contains media/data only.
- Source code, configuration, virtual environments, reports, indexes,
  approvals, audit records, logs, caches, staging, backups, and application
  databases remain on the system drive.
- Scan, Metadata Audit, Analysis, Preview, Approval, and Verification do not
  modify media.
- Only Apply may modify media, and only from the approved-action export.
- No production-library modification occurs without explicit approval.
- Every applied change must be traceable and recoverable where supported.
- CONTEMPORARY and CLASSICAL remain separate logical libraries.
- Identity-changing operations require certification before production use.
- No UI, integration, or external tool may bypass Preview, Approval, Apply,
  backup, audit, verification, or certification controls.
- Direct manipulation of the production Music Assistant database is prohibited
  unless a separately approved and certified maintenance operation is created.

Identity-changing operations include AlbumArtist, album title, artist identity,
compilation state, MusicBrainz identifiers, and folder identity. These can
alter Music Assistant grouping and must be tested in a disposable certification
environment with a separate Music Assistant instance and database.

## 5. Current architecture

### 5.1 Core engines

| Module | Responsibility | Media writes |
|---|---|---:|
| `src/scan.py` | Discover configured media and build indexes | No |
| `src/audit_metadata.py` | Read supported tags and report findings | No |
| `src/analyze_library.py` | Aggregate findings and candidates | No |
| `src/preview.py` | Produce deterministic proposed actions | No |
| `src/approve.py` | Record decisions and export approved actions | No |
| `src/apply.py` | Validate and execute approved actions | Yes |
| `src/common.py` | Shared configuration, paths, and utilities | No |
| `src/commission_artwork.py` | Music Assistant consumer-side entity commissioning | No |

The repository may contain local or in-progress modules not yet committed.
Always inspect the working tree before relying on this table.

### 5.2 Format boundaries

Do not collapse discovery, audit, and write support into one claim.

- `src/common.py` defines the broad discovery set.
- Scan uses the configured subset in `config/config.yaml`.
- Metadata Audit has its own explicit readable set.
- Apply currently writes `.flac`, `.mp3`, `.m4a`, `.m4b`, and `.mp4`.
- The released write operation is `ADD_ALBUMARTIST`.

Adding discovery support never grants permission or capability to write a
format. A new writer requires validation, backup/restore, post-write
verification, rollback, tests, and real-media certification.

### 5.3 Approval and Apply contracts

Approval states are:

- `PENDING`
- `APPROVED`
- `REJECTED`
- `DEFERRED`

Decision commands accept exactly one selector type: action ID, filters, or
`--all`. Repeated filters combine with logical AND. Decisions are idempotent;
meaningful transitions are persisted atomically and recorded in the append-only
audit.

Apply consumes only `runtime/approval/approved-actions.json`. Dry-run is the
default. Live execution requires `--execute` and the exact confirmation phrase
`I_APPROVE_KINTYRE_APPLY`.

Apply validates targets and operations, detects duplicate targets, creates
backups, verifies writes, rolls back failed transactions, performs batch
rollback after a later failure, records outcomes, and returns failure status
for blocked or failed execution.

## 6. Music Assistant artwork boundary

Artwork commissioning and artwork verification are separate responsibilities.

`src/commission_artwork.py`:

- uses the supported authenticated Music Assistant API;
- inventories library albums and artists;
- requests entity details;
- defaults to dry-run;
- requires explicit confirmation for execution;
- is rate-limited, resumable, and report-driven;
- never writes the authoritative media library;
- never manipulates the Music Assistant database directly.

`TOUCHED` proves only that the entity-detail API request completed. It does not
prove that artwork was found, downloaded, decoded, cached, or displayed.

External integration claims must distinguish:

1. API request accepted;
2. downstream processing scheduled or performed;
3. final outcome independently verified.

Prefer the current canonical Music Assistant API over compatibility aliases.
Use an alias only for a documented compatibility requirement.

The correct lifecycle is:

```text
Authoritative media library
→ deterministic metadata remediation
→ approved Apply
→ verification
→ Music Assistant rescan or rebuild
→ API commissioning
→ asynchronous Music Assistant enrichment
→ independent artwork verification and reconciliation
```

## 7. Repository and documentation map

### Repository

- `config/` — generic project configuration.
- `src/` — production application modules.
- `tests/` — automated regression, integration, format, and certification tests.
- `docs/` — authoritative project documentation.
- `runtime/` — generated local operational artifacts; do not commit production data.
- `README.md` — project overview, release, safety model, and primary workflow.
- `INSTALL.md` — installation and validation procedure.
- `Makefile` — supported convenience targets; inspect before use.
- `requirements.txt` — Python dependencies.

### Documentation

- `docs/HANDOVER.md` — self-contained incoming-AI briefing and current continuity state.
- `docs/ARCHITECTURE.md` — architecture, engine boundaries, and integration contracts.
- `docs/DEVELOPER_GUIDE.md` — implementation, format, Approval, Apply, testing, and integration rules.
- `docs/USER_GUIDE.md` — operator commands, safe workflow, recovery, and artwork commissioning.
- `docs/REPORT_FORMATS.md` — runtime report locations, schemas, and compatibility rules.
- `docs/ROADMAP.md` — authoritative future release scope and release governance.
- `docs/CHANGELOG.md` — completed release and operational-validation history.
- `docs/TECHNOLOGY_STRATEGY.md` — technology mission, ownership, boundaries, and selection criteria.
- `docs/TECHNOLOGY_RADAR.md` — Adopt/Trial/Assess/Hold guidance; adoption requires an ADR and tests.
- `docs/adr/README.md` — ADR format and status rules.
- `docs/adr/ADR-0001-safe-ai-development-handover.md` — accepted decision for a future secret-redacted generated handover package.
- `docs/adr/ADR-0002-duplicate-detection-strategy.md` — proposed duplicate-detection evidence strategy.
- `docs/adr/ADR-0003-dashboard-and-observability.md` — proposed NiceGUI/FastAPI operations and Grafana read-only observability split.
- `docs/adr/ADR-0004-player-bluetooth-boundary.md` — accepted separation of player/Bluetooth diagnostics from Music Assistant reconciliation.

Read every document relevant to the active task. For foundational or
repository-wide work, read the entire documentation set.

## 8. Technology and integration rules

- External tools provide evidence or bounded capabilities.
- KINTYRE owns workflow state, safety decisions, approval, certification,
  provenance, backup, verification, rollback, and audit.
- New technology adoption requires an ADR and test evidence.
- Prefer established tools over custom reimplementation.
- Grafana is read-only observability and must not execute protected operations.
- The system must remain safely operable without optional integrations.
- Optional AI metadata recovery is advisory, disabled by default, provenance
  recorded, structured, fail-closed, and never authoritative.
- AI suggestions must enter the normal Preview, Approval, certification,
  Apply, backup, verification, and audit workflow.
- Never expose or commit secrets, tokens, private keys, cookies, production
  inventories, collection-specific filenames, generated reports, databases,
  caches, commissioning state, or backups.

## 9. Development lifecycle

For each sprint:

1. **Understand** — read the handover, relevant docs, code, tests, and state.
2. **Investigate** — reproduce or inspect the problem; verify dependencies and
   upstream behaviour.
3. **Define** — confirm the sprint objective and smallest safe scope.
4. **Design** — fit the existing architecture; avoid unrelated redesign.
5. **Implement** — make the bounded change and add tests.
6. **Verify** — run targeted tests, the complete suite, and safe live validation
   where applicable.
7. **Document** — update every affected authoritative document.
8. **Update handover** — record current state, verified results, risks, and next action.
9. **Review** — inspect the full diff and remove accidental or private artifacts.
10. **Complete** — commit, push, confirm clean working tree and synchronized remote.

## 10. Sprint definition of done

A sprint is complete only when all applicable items are satisfied:

- Feature or documentation objective implemented.
- Appropriate new and regression tests added.
- Targeted tests pass.
- Complete test suite passes.
- Safe live verification completed where applicable.
- Documentation matches implementation.
- `docs/HANDOVER.md` reviewed and updated.
- Full `git diff` reviewed.
- No secrets, production data, generated runtime evidence, or accidental files included.
- Commit created with a clear message.
- Commit pushed.
- Working tree clean.
- GitHub synchronized.
- Exact next sprint or task recorded.

The continuity quality gate is:

> Could a competent new AI continue tomorrow using only the repository and
> this handover?

If not, the sprint is not complete.

## 11. Failure and recovery behaviour

- Stop after a blocked or failed protected stage.
- Preserve reports, logs, audit records, and backups.
- Investigate before retrying.
- Do not stack speculative changes.
- Do not modify or delete evidence to make a failure disappear.
- For Apply failures, inspect transaction, backup, verification, rollback, and
  batch-rollback fields before any further action.
- For system or service configuration, capture the baseline and prepare a
  tested rollback before change.
- For external integrations, distinguish API, asynchronous processing, cache,
  identity, and final display failures.

## 12. Prohibited practices

Never:

- fabricate inspection, execution, test, or validation results;
- guess an environment-specific command when it can be inspected;
- treat conversation memory as authoritative;
- bypass Approval or Apply safeguards;
- modify `/data/Music` without explicit approval through the protected workflow;
- directly manipulate the production Music Assistant database;
- weaken tests merely to make them pass;
- introduce architecture or out-of-roadmap features silently;
- commit secrets, production evidence, or machine-specific private data;
- leave an important decision or operating rule only in chat history;
- describe commissioning success as verified artwork success;
- apply speculative global audio tuning without measured evidence, backup,
  approval, and rollback.

## 13. Current verified project state

The public repository currently declares:

- Stable release: `v1.0`.
- Released core pipeline: Scan, Metadata Audit, Analysis, Preview, Approval,
  Apply, and Verification workflow.
- Artwork commissioning is implemented and operationally validated.
- Artwork verification is documented as a separate required stage but is not
  part of the committed public source tree at the time this handover is introduced.
- The roadmap names `v1.0.1` safe KINTYRE naming normalization as the next
  maintenance release.

Before relying on this state, the incoming assistant must run:

```bash
git status --short --branch
git log --oneline --decorate -10
git tag --sort=-creatordate | head -20
find docs src tests -maxdepth 2 -type f | sort
```

Then run the repository validation commands:

```bash
source .venv/bin/activate
python -m py_compile src/*.py tests/*.py
python -m unittest discover -s tests -v
```

Record the actual current commit, tags, working-tree state, and test result in
this section at sprint closure. Do not preserve stale counts or claims.

## 14. Immediate continuation point

At creation of this document, the active work is:

1. Establish `docs/HANDOVER.md` as the maintained AI continuity authority.
2. Keep ADR-0001 as the accepted architectural decision for a future
   repository-driven, secret-redacted handover generator.
3. Audit and synchronize documentation without changing production behaviour.
4. After this documentation sprint is committed and pushed, resume the planned
   read-only Artwork Verification Engine work.

The Artwork Verification Engine must be based on verified Music Assistant API
behaviour, remain read-only with respect to both the authoritative media
library and Music Assistant state, produce deterministic reports, distinguish
artwork presence from retrievability and validity, include tests, and update
all affected documentation plus this handover.

## 15. End-of-sprint handover update template

At every sprint closure, update this document with:

- Sprint identifier and objective.
- Current branch and verified commit.
- Working-tree status.
- Completed implementation.
- Tests run and exact result.
- Live verification performed and evidence boundary.
- Documentation changed.
- Known issues, limitations, and unverified items.
- Decisions that constrain future work.
- Exact recommended next action.
- Confirmation that commit, push, clean tree, and remote synchronization were checked.

Remove obsolete current-state information rather than allowing this document
to become an uncurated diary. Historical detail belongs in the changelog,
ADRs, release tags, and commit history.
