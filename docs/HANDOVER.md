# KINTYRE AI Engineering Handover

**Repository:** `https://github.com/01110011011001010111100001111001/KINTYRE`
**Released baseline:** v1
**Active direction:** v2 documentation-first redesign

> Repository, tests and live evidence outrank memory. No guessing—ever.

## Current decision

The earlier target built around certification workspaces, adapters, comparator, policy and promotion engines has been discarded as unnecessarily complex.

The permanent v2 model is:

```text
COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK
```

One album is one transaction.

Do not reintroduce the discarded architecture. Small modules may perform comparison, backup or verification, but they are not separate product layers.

## Responsibilities

External OSS performs identification, release matching, metadata/artwork retrieval, fingerprint evidence and staged tagging.

KINTYRE performs safe copy, production isolation, evidence, review, approval, backup, complete-album replacement, rollback, checking and audit history.

## Permanent rules

- `/data/Music` is authoritative and protected.
- Runtime data, staging, backups, logs and databases stay on the system drive.
- External tools never write production.
- Production remains unchanged through COPY, FIX, REVIEW and APPROVE.
- REPLACE requires exact approval and verified complete backup.
- CHECK validates files, metadata, artwork, audio essence and Music Assistant.
- Music Assistant is a rebuildable consumer.
- Ambiguous cases are deferred.
- CONTEMPORARY and CLASSICAL remain separate logical libraries.
- No production data, reports, secrets or inventories are committed.

## Status

v1 is released and frozen. v2 is not yet implemented. Target capability must never be documented as live.

## Immediate next step

After approval of this documentation baseline, perform roadmap D1, then implement D2 COPY for one representative CONTEMPORARY album.

## Mandatory startup

Read relevant documentation; inspect branch, commit, tags, status, source and tests; run tests when feasible; verify live dependencies; label facts and unknowns; deliver the smallest complete change with atomic commands; protect production; update docs and tests; verify diff, secrets, tests, commit, push and clean status.
