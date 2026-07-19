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

## Modules

- `scan.py`
- `audit_metadata.py`
- `analyze_library.py`
- `preview.py`
- `approve.py`
- `apply.py`
- `common.py`

## Format contracts

Do not collapse format support into one claim.

- `common.SUPPORTED_AUDIO_EXTENSIONS` is the broad core discovery set.
- Scan intersects configured `scan.include` entries with that set.
- Audit maintains an explicit readable set appropriate to its tag readers.
- Apply maintains `WRITABLE_AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.m4b', '.mp4'}`.

Adding a discovery extension does not authorize metadata writes. New writable formats require a writer implementation, validation, backup/restore support, post-write verification and real-media certification tests.

## Approval rules

Decision commands must accept exactly one selector type: action ID, one or more filters, or `--all`. Repeated filters combine with logical AND. Filtered and all-action operations reject zero matches, update each action once, preserve idempotency, persist atomically and log only meaningful transitions.

The supported commands are `approve`, `reject`, `defer` and `reset`; `reset` returns the selected actions to `PENDING`.

## Apply rules

Apply must consume approved actions only, validate before writing, default to dry run, block unsupported operations or formats, detect duplicate targets, require explicit live confirmation, back up before writes, verify after writes, roll back a failed transaction, roll back earlier transactions when a batch later fails, return failure status for blocked or failed execution and record outcomes in the approval audit trail.

The released operation is `ADD_ALBUMARTIST`. Writable extensions are FLAC, MP3, M4A, M4B and MP4.

## Testing

```bash
python -m py_compile src/*.py tests/*.py
python -m unittest discover -s tests -v
```

Do not hard-code a passing-test count in long-lived documentation. The authoritative count is the result of the current complete test run.
