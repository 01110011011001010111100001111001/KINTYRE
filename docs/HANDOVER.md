# KINTYRE AI Engineering Handover

**Repository:** `https://github.com/01110011011001010111100001111001/KINTYRE`
**Released baseline:** v1
**Active direction:** v2 implementation — D6 REPLACE

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

v1 is released and frozen. The v2 documentation baseline, D1 toolchain
inventory, D2 COPY, D3 FIX, D4 REVIEW, D5 APPROVE, D6 REPLACE and D7 CHECK are
complete. The retained commissioning transaction
`D2-COPY-ABBA-VOYAGE-20260723` progressed through the complete evidence chain.
The workflow is now COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK. Target
capability must never be documented as live before implementation and
commissioning are complete.

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

Begin roadmap D6 REPLACE with repository-first inspection. D6 must consume
only a currently valid exact D5 approval, revalidate the authoritative production
before-state, create and verify a complete backup, perform one bounded album
replacement, and prove whole-album rollback without weakening the established
COPY → FIX → REVIEW → APPROVE evidence chain.

## Permanent outcome rule

Before beginning any sprint, answer:

> Will this work leave the user's library in a measurably better state?

If the answer is **No**, do not build it. Essential infrastructure is allowed
only when it directly enables a defined, measurable library improvement.

Each accepted capability must identify:

- the concrete library problem;
- the expected improvement;
- the evidence that will verify it; and
- the reversal path.

This outcome rule takes precedence over feature count, abstraction,
architectural elegance, dashboards and reports.

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
D2 is complete. Its retained transaction is the commissioned input used by D3
FIX and the current evidence source for D4 REVIEW. Production remains protected
and must not be modified.

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
read-only, and 75 tests passed. Production remained untouched. D3 is complete.

## v2 D4 REVIEW implementation checkpoint

The REVIEW stage is implemented in `src/review_album.py`. It accepts only an
existing transaction with successful COPY and FIX evidence, independently
revalidates retained evidence and the current staged album, and performs no
external remediation or write to staged or production media.

REVIEW reads metadata independently for every configured supported audio
extension and compares authoritative and staged values for album artist, artist,
album, title, track, disc, genre, date, MusicBrainz identifiers and embedded
artwork state. It verifies transaction consistency, manifest digests, staged
file integrity and unchanged ffprobe audio essence. Metadata that cannot be read
is retained as a warning; missing or inconsistent required evidence, changed
audio essence, unexpected file changes and unexplained or non-beneficial changes
block progression.

The stage writes immutable transaction-scoped evidence under `review/`:

- `review-report.json` — canonical stage status, recommendation, evidence links,
  counts, warnings and blockers;
- `review-findings.json` — deterministic per-file metadata differences and
  identified library improvements;
- `review-summary.md` — human-readable review of changes, trust, expected benefit
  and readiness for approval.

REVIEW recommends `PASS` or `BLOCK`; it never records the human decision.
Six D4 tests cover successful certification, audio-essence blocking, overwrite
protection, missing FIX evidence, all supported audio extensions and warning-only
metadata unavailability. The complete repository suite passes: 81 tests.
Production remains untouched. D4 implementation is complete; D5 APPROVE is next.


## v2 D5 APPROVE implementation checkpoint

The APPROVE stage is implemented in `src/approve_transaction.py`. It accepts only
an existing transaction with successful immutable D4 REVIEW evidence and a valid
`PENDING`, `APPROVED`, `REJECTED` or `DEFERRED` album-level decision. It verifies
transaction identity, requires PASS in both the REVIEW report and findings, and
revalidates the current staged album against the retained FIX after-manifest.

APPROVE writes one immutable `approval/approval-report.json` containing the
decision, optional operator, exact REVIEW evidence paths and SHA-256 digests, the
FIX after-manifest digest and the current staged-album manifest digest. Existing
approval evidence is never overwritten. The stage modifies neither staged media
nor production. Seven focused tests cover successful recording, non-PASS REVIEW,
missing evidence, changed staged content, overwrite protection, invalid decisions
and exact evidence binding. Commissioning completed successfully on 23 July
2026 against retained transaction `D2-COPY-ABBA-VOYAGE-20260723`. The REVIEW
status and recommendation were PASS, operator Richard recorded the album-level
decision APPROVED, `approval/approval-report.json` was verified read-only and
bound to the exact REVIEW evidence, all 88 tests passed, and production remained
untouched. D5 is complete; D6 REPLACE is next.
