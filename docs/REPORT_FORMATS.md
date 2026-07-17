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

Typical location: `runtime/index/album-index.csv`.

## Metadata audit

Stored under `runtime/reports/`.

## Analysis

Stored under `runtime/analysis/`.

## Preview

Stored under `runtime/preview/`.

- `preview-summary.json`
- `apply-plan.json`
- `albumartist-fixes.csv`
- `review-summary.json`

## Approval

Stored under `runtime/approval/`.

- `approval-plan.json`
- `approval-summary.json`
- `approved-actions.json`
- `approval-audit.json`

## Apply

Stored under `runtime/apply/`.

- `apply-report.json`

Do not rename released fields without migration. Prefer additive fields. Never manually edit generated reports. Never commit production reports or inventories.
