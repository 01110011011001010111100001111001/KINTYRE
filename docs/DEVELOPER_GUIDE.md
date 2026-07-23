# KINTYRE v2 Developer Guide

## Contract

Implement exactly:

```text
COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK
```

Do not recreate the discarded certification-platform architecture under new names.

## Rules

- Inspect repository, tests, documentation and live dependencies before change.
- Distinguish verified facts, decisions, hypotheses and unknowns.
- One sprint delivers one complete testable outcome.
- Use atomic commands; do not require substantial manual editing.
- Never modify `/data/Music` during investigation or development.
- Add tests before claiming a stage complete.
- Update all affected documentation in the same sprint.
- Commit and push only after validation.

## Implementation order

Build one thin vertical path: COPY one album, invoke one verified FIX workflow, generate REVIEW evidence, persist APPROVE, back up and REPLACE, then CHECK and rollback. Generalise only after that path works end to end.

## External tools

Capture executable path, version, arguments, exit code, stdout/stderr and redacted configuration fingerprint. Use isolated configuration and databases. Never pass a writable production path.

## Integrity

COPY and REVIEW hash source and working files. REPLACE validates the expected production before-state immediately before writing. CHECK verifies readability, approved metadata/artwork and unchanged audio essence.

## Replacement

Replacement is album-level and all-or-nothing. Verify backup capacity, create and verify a complete backup, perform bounded replacement, verify the final album and restore the complete backup on failure.

## Required tests

Cover path containment, symlink escape, deterministic manifests, production unchanged before REPLACE, approval invalidation, stale before-state, insufficient backup capacity, partial failure, complete rollback, unreadable output, unexpected files and audio-essence change.
