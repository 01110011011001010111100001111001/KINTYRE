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

Begin roadmap D4 REVIEW using the retained D3 FIX evidence from transaction `D2-COPY-ABBA-VOYAGE-20260723`. REVIEW must interpret and present the captured external-tool evidence without modifying the staged copy or production.

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

The v1 modules remain frozen and untouched. D2 completed on 23 July 2026
with transaction `D2-COPY-ABBA-VOYAGE-20260723`: 11 files, 10 audio files
and 81,569,309 bytes copied from ABBA/Voyage. The retained source and
destination manifests match by size and SHA-256 and the COPY report is PASS.
The immediate next step is D3 FIX against this retained copy; production remains
protected and must not be modified.

## v2 D3 FIX implementation checkpoint

The FIX stage is implemented in `src/fix_album.py`. It accepts only an existing
successful COPY transaction, verifies that `album/` still matches immutable D2
destination evidence, and invokes Beets with an isolated configuration, library
database and cache. Copying, moving and resume are disabled; quiet fallback
skips ambiguity. The exact executable, version, command, configuration digest,
stdout, stderr, exit code, before/after manifests and ffprobe audio packet-data
hashes are retained under `transaction/fix/` and made read-only. A changed file
set, changed audio essence or non-zero Beets exit produces retained FAIL
evidence. Production is never provided to Beets.

The module is deliberately one verified workflow, not a generic adapter
framework.

D3 commissioning completed successfully on 23 July 2026 against retained
transaction `D2-COPY-ABBA-VOYAGE-20260723`. Beets 2.12.0 reported a 100% match
for ABBA — Voyage using MusicBrainz release
`034779cb-e14d-4845-a9db-6001c635928d`. All 10 staged audio files received
metadata changes. The complete file set was preserved, ffprobe audio
packet-data hashes were identical before and after, Beets exited with status 0,
no verification errors were recorded, all evidence under `fix/` was made
read-only, and 75 tests passed. Production remained untouched. D3 is complete;
D4 REVIEW is next.
