# KINTYRE Developer Guide

**Version:** 1.0

## Requirements

Components must be deterministic, testable, explicit, conservative, traceable and safe by default.

## Layout

```text
config/     generic configuration
docs/       public documentation
runtime/    generated local artifacts
src/        application source
tests/      automated tests
```

Generated operational data under `runtime/` must not be committed.

## Canonical runtime directories

```text
runtime/index/
runtime/reports/
runtime/analysis/
runtime/preview/
runtime/approval/
runtime/apply/
runtime/logs/
runtime/cache/
runtime/staging/
```

The canonical Preview directory is `runtime/preview/`.

## Modules

- `scan.py`
- `audit_metadata.py`
- `analyze_library.py`
- `preview.py`
- `approve.py`
- `apply.py`
- `common.py`

## Approval rules

Bulk updates must require at least one filter, combine filters with logical AND, reject zero matches, update each action once, preserve idempotency, persist atomically and log only meaningful transitions.

## Apply rules

Apply must consume approved actions only, validate before writing, support dry-run, block invalid work, back up before writes, verify after writes, report rollback failures, return failure status for blocked or failed execution and record outcomes in the audit trail.

## Testing

```bash
python -m py_compile src/*.py tests/*.py
python -m unittest discover -s tests -v
```

The v1 release baseline contains 42 passing tests.
