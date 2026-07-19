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

## Music Assistant artwork commissioning development rules

Commissioning code must remain read-only with respect to the authoritative library, use supported Music Assistant APIs, be deterministic, dry-run by default, explicitly confirmed for execution, rate-limited, resumable, idempotent from KINTYRE's perspective and complete in per-entity reporting.

`TOUCHED` means that the entity-detail request completed successfully. It must never be represented as proof that artwork was resolved, downloaded, decoded, cached or displayed.

External integration behaviour must be described at three separate levels: request accepted; downstream processing scheduled or performed; final outcome independently verified. Do not infer external behaviour from API success alone. Assertions must be grounded in automated tests, verified upstream implementation or captured operational evidence.

## Optional AI metadata recovery development rules

AI-assisted recovery is a last-resort advisory stage after deterministic evidence and conventional metadata services are exhausted. Implementations must use a provider abstraction, be disabled by default, keep credentials outside the repository, support local or remote providers where configured, send only permitted evidence, record provider/model/prompt provenance, require validated structured output, fail closed, never write directly to the authoritative library, convert accepted suggestions into normal preview actions and preserve Approval, certification, Apply, backup, verification and audit.
