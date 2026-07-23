# KINTYRE v2 Report Formats

JSON is canonical. Human-readable Markdown or CSV may be derived. Reports are transaction-scoped, schema-versioned and secret-free.

## Common fields

`schema_version`, `transaction_id`, `album_path`, `stage`, `state`, timestamps, warnings and errors.

## COPY

Validated source path, source manifest and hash, copied manifest, copy verification, production-unchanged result and working-directory reference.

## FIX

Tool name/path/version, redacted configuration fingerprint, arguments, times, exit status, logs, provider evidence and working manifest.

## REVIEW

Before/after inventory, metadata changes, artwork validation, track mapping, audio-integrity evidence, unexpected changes, ambiguity, blockers and proposed manifest hash.

## APPROVE

Decision, timestamp, operator where available, reviewed source/proposed hashes, reason and invalidation state.

## REPLACE

Preconditions, before-state revalidation, backup path/manifest/verification, replacement operations, final manifest, rollback state and failures.

## CHECK

Readability, metadata, artwork, audio essence, unexpected-file check, Music Assistant result, final disposition and backup-retention decision.

Existing v1 reports retain their v1 contracts. v2 must not silently reuse a v1 filename or schema with changed meaning.
