# KINTYRE Report Formats

**Version:** 1.0

## Runtime layout

```text
runtime/
  index/
  reports/
  analysis/
  preview/
  approval/
  apply/
```

## Scan

Scan indexes are stored under `runtime/index/`; the principal album index is `album-index.csv`. Scan output reflects the configured extension subset, not Apply write support.

## Metadata Audit

Audit reports are stored under `runtime/reports/` and describe readable tag findings for the audit engine's supported formats.

## Analysis

Analysis artifacts are stored under `runtime/analysis/`.

## Preview

Stored under `runtime/preview/`:

- `preview-summary.json`
- `apply-plan.json`
- `albumartist-fixes.csv`
- `review-summary.json`

`apply-plan.json` is proposed work only and is never consumed directly for live writes.

## Approval

Stored under `runtime/approval/`:

- `approval-plan.json` — working copy with `PENDING`, `APPROVED`, `REJECTED` or `DEFERRED` decisions
- `approval-summary.json` — decision counts
- `approved-actions.json` — only actions currently approved; this is Apply's input
- `approval-audit.json` — append-only decision and Apply outcome events

## Apply

Stored under `runtime/apply/`:

- `apply-report.json`

The report schema is currently `1.2` and includes:

- execution `mode` (`DRY_RUN` or `EXECUTE`);
- `preflight_passed`;
- transaction, success and failure counts;
- per-transaction validation and status;
- target-file and writable-format validation;
- duplicate-target results;
- backup and verification results;
- rollback and batch-rollback results where applicable.

Apply reports may reference backup paths on the system drive. Backups and reports must not be placed on the authoritative media drive or committed to the public repository.

## Compatibility rules

Do not rename released fields without migration. Prefer additive schema changes. Never manually edit generated reports, approval plans or audits. Never commit production reports, inventories, backups or collection-specific evidence.


## Artwork commissioning report

Path: `runtime/music-assistant/artwork-commissioning-report.json`

Fields include `mode`, `media_types`, `target_count`, status `counts`, `state_path`, and per-entity `outcomes`. Outcome statuses are `PLANNED`, `TOUCHED`, `SKIPPED_COMPLETED`, or `FAILED`. The separate state file contains completed entity keys and enables safe resume after interruption.
