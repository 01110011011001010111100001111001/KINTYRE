# KINTYRE User Guide

**Version:** 1.0

## Operating model

```text
Scan → Audit → Analysis → Preview → Approval → Apply → Verify
```

The media library remains unchanged until Apply executes explicitly approved actions.

## Activate

```bash
cd /home/richard/kintyre-dam
source .venv/bin/activate
```

## Read-only pipeline

```bash
python src/scan.py
python src/audit_metadata.py
python src/analyze_library.py
python src/preview.py
```

Review outputs under `runtime/index/`, `runtime/reports/`, `runtime/analysis/` and `runtime/preview/`.

## Approval

```bash
python src/approve.py --help
```

States are `PENDING`, `APPROVED`, `REJECTED` and `DEFERRED`. Decisions are persisted separately from Preview output. Bulk operations require filters and reject zero matches. Repeating the same decision is idempotent.

Approval records and approved-action exports are stored under `runtime/approval/`.

## Apply

```bash
python src/apply.py --help
```

Before live execution confirm successful dry-run, expected paths and values, explicit approvals, backups, certification of identity-changing operations and the intended target library.

## Post-apply verification

After Apply:

1. rerun Scan;
2. rerun Metadata Audit;
3. compare findings;
4. inspect Apply and audit records;
5. refresh or rebuild the disposable Music Assistant consumer where required;
6. verify album, artist and artwork behaviour.

A metadata write can succeed while Music Assistant retains stale database identities.

## Recovery

For failed live execution, stop further work, preserve reports and logs, inspect rollback results, restore from transaction backups where required, then rerun Scan and Audit.
