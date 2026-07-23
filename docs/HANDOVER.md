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

v1 is released and frozen. The v2 documentation baseline and roadmap D1 toolchain inventory are complete. No v2 workflow stage is implemented yet. Target capability must never be documented as live.

### Verified D1 toolchain

- Project Python: 3.14.4 at `/home/richard/kintyre-dam/.venv/bin/python`
- Beets: 2.12.0 at `/home/richard/kintyre-dam/.venv/bin/beet`
- Beets plugin verified: `musicbrainz`
- MusicBrainz Picard: 2.13.3 at `/usr/bin/picard`
- Chromaprint: `fpcalc` 1.6.0 at `/usr/bin/fpcalc`
- FFprobe: 8.0.1 at `/usr/bin/ffprobe`
- Mutagen: 1.48.1
- pyacoustid: 1.3.1
- Beets defaults can copy and write; KINTYRE must therefore invoke it with explicit bounded controls.
- No Beets or Picard configuration reference to `/data/Music` was found.
- Isolated Beets operation was proved with `--nocopy --nomove --nowrite --noautotag --noresume`.
- The proof preserved the source SHA-256 checksum, created no copied media and left the repository clean.
- `metaflac` and `id3v2` were not installed and are not treated as available capabilities.

## Immediate next step

Implement roadmap D2 COPY for one representative CONTEMPORARY album. Begin with repository-first inspection of the existing source, tests, configuration and runtime-path conventions. Do not implement FIX or invoke external tagging against production.

## Mandatory startup

Read relevant documentation; inspect branch, commit, tags, status, source and tests; run tests when feasible; verify live dependencies; label facts and unknowns; deliver the smallest complete change with atomic commands; protect production; update docs and tests; verify diff, secrets, tests, commit, push and clean status.

## v2 D2 COPY implementation checkpoint

The COPY stage is implemented in `src/copy_album.py`; do not name it `src/copy.py`
because `src/` is inserted before the standard library during tests and that name
would shadow Python's `copy` module.

COPY accepts exactly one album below the configured CONTEMPORARY root, rejects
path escape, traversal, symbolic links and special files, copies the complete
directory into `runtime/staging/transactions/<transaction-id>/album`, writes
read-only source and destination manifests, verifies sizes and SHA-256 hashes,
and writes a deterministic sorted JSON report. It never writes production.

The v1 modules remain frozen and untouched. D2 is not complete until one
representative production album has been copied read-only and the retained
transaction evidence has been reviewed. The immediate next step is that bounded
D2 commissioning run; do not begin FIX.
