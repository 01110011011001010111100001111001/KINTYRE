# KINTYRE v2 Roadmap

## Governance

v1 is released and frozen as the historical baseline. Future architecture is v2. No v1 feature roadmap carries forward automatically.

Every milestone delivers one complete testable outcome, protects production until approval, updates documentation, adds tests, verifies rollback where writes exist, and ends committed, pushed and clean.

## Release acceptance

A milestone or release is accepted only when:

- implementation is complete;
- relevant tests pass;
- documentation reflects the verified state;
- the capability directly improves the library or is essential to delivering a
  defined measurable improvement;
- the expected improvement and verification evidence are explicit; and
- any production write has a tested recovery or rollback path.

Before roadmap work begins, ask:

> Will this leave the user's library in a measurably better state?

If the answer is **No**, the work does not proceed.

Progress is measured by the quality, completeness and functionality of the
resulting library, not by feature count or pipeline activity.

## D0 — Documentation baseline

Status: Complete — 23 July 2026

Replace the discarded certification-platform model with `COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK` across all documentation. Preserve accurate v1 facts while making v2 the target contract.

## D1 — Read-only toolchain inventory

Status: Complete — 23 July 2026

Recorded exact installed versions, paths, plugins and effective configuration for the proposed OSS toolchain. Verified that no Beets or Picard configuration references `/data/Music`. Proved an isolated Beets invocation using explicit no-copy, no-move, no-write and no-autotag controls: the disposable source checksum remained unchanged, no media was copied, one isolated database record was created and the production repository remained clean.

## D2 — COPY

Select one representative CONTEMPORARY album, create an isolated system-drive transaction, record an immutable source manifest and copy the complete album without changing production.


D2 completed — 23 July 2026: `src/copy_album.py` implements isolated, verified, read-only album COPY transactions with immutable manifests and security checks. The representative commissioning transaction `D2-COPY-ABBA-VOYAGE-20260723` copied ABBA/Voyage in full: 11 files, including 10 audio files, 81,569,309 bytes. Production and staged manifests matched by size and SHA-256; the retained report status is PASS.

## D3 — FIX

Completed — 23 July 2026: `src/fix_album.py` runs one bounded Beets/MusicBrainz workflow against a retained successful COPY transaction only. It uses an isolated configuration, database and cache; disables copy, move and resume; writes only the staged album; captures executable, version, invocation, configuration fingerprint, stdout, stderr and exit state; and verifies the complete file set and ffprobe packet-data hashes before and after execution. Ambiguous quiet-mode matches are skipped. Production is never passed to the external tool.

Commissioning succeeded against retained transaction `D2-COPY-ABBA-VOYAGE-20260723`. Beets 2.12.0 produced a 100% MusicBrainz match for ABBA — Voyage using release `034779cb-e14d-4845-a9db-6001c635928d`. All 10 staged audio files received metadata changes, the audio packet-data hashes remained unchanged, Beets exited with status 0, no verification errors were recorded, all FIX evidence was retained read-only, and 75 tests passed.

## D4 — REVIEW

Completed — 23 July 2026: `src/review_album.py` produces deterministic,
immutable machine-readable and human-readable review evidence from a retained
successful COPY and FIX transaction. It performs no external remediation and
modifies neither the staged album nor production.

REVIEW independently verifies transaction identity, evidence digests, the
current staged manifest and unchanged ffprobe audio essence. For every
configured supported audio extension it independently reads and compares album
artist, artist, album, title, track, disc, genre, date, MusicBrainz identifiers
and embedded artwork state. It records per-file differences, warnings,
blockers, concrete expected library improvements and a PASS or BLOCK
recommendation in `review-report.json`, `review-findings.json` and
`review-summary.md`.

Six tests cover successful certification, audio-essence blocking, immutable
overwrite protection, missing FIX evidence, all supported audio extensions and
warning-only metadata unavailability. The full repository suite passes:
81 tests. REVIEW recommends; D5 APPROVE alone records the human decision.

## D5 — APPROVE

Status: Complete — 23 July 2026

`src/approve_transaction.py` consumes only successful immutable REVIEW evidence,
records one album-level `PENDING`, `APPROVED`, `REJECTED` or `DEFERRED` decision,
and binds it to the exact REVIEW files and staged album through SHA-256 and
manifest digests. It independently revalidates the staged album against the FIX
after-manifest, refuses missing or non-PASS REVIEW evidence, and never overwrites
an existing approval. APPROVE modifies neither staged media nor production. Seven
focused tests cover the stage contract. Commissioning completed successfully
against retained transaction `D2-COPY-ABBA-VOYAGE-20260723`: REVIEW status and
recommendation were PASS, operator Richard recorded APPROVED, the immutable
approval report was verified against the exact REVIEW evidence, all 88 tests
passed, and production remained untouched.

## D6 — REPLACE

Verify the production before-state, create and verify a complete backup, replace one album and prove whole-album rollback.

## D7 — CHECK

Verify media readability, tags, artwork, audio essence and Music Assistant representation. Define closure and rollback conditions.

## D8 — First bounded production album

Run the full workflow on one approved representative album and retain complete evidence.

## D9 — Bounded contemporary batches

Add resumability, failure isolation and controlled batch selection without weakening album-level review and replacement.

## Later

Only after the workflow is proven: ambiguous contemporary albums, compilations, unknown albums, classical remediation, artwork campaigns, duplicate/structural analysis, UI and performance work.
