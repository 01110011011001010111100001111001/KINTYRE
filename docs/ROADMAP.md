# KINTYRE v2 Roadmap

## Governance

v1 is released and frozen as the historical baseline. Future architecture is v2. No v1 feature roadmap carries forward automatically.

Every milestone delivers one complete testable outcome, protects production until approval, updates documentation, adds tests, verifies rollback where writes exist, and ends committed, pushed and clean.

## D0 — Documentation baseline

Status: Current

Replace the discarded certification-platform model with `COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK` across all documentation. Preserve accurate v1 facts while making v2 the target contract.

## D1 — Read-only toolchain inventory

Status: Complete — 23 July 2026

Recorded exact installed versions, paths, plugins and effective configuration for the proposed OSS toolchain. Verified that no Beets or Picard configuration references `/data/Music`. Proved an isolated Beets invocation using explicit no-copy, no-move, no-write and no-autotag controls: the disposable source checksum remained unchanged, no media was copied, one isolated database record was created and the production repository remained clean.

## D2 — COPY

Select one representative CONTEMPORARY album, create an isolated system-drive transaction, record an immutable source manifest and copy the complete album without changing production.


D2 implementation checkpoint — 23 July 2026: `src/copy_album.py` now implements isolated, verified, read-only album COPY transactions with immutable manifests and security checks. Unit coverage is present. D2 remains open until one representative CONTEMPORARY album is copied and its retained evidence is reviewed.

## D3 — FIX

Run one verified OSS workflow against the copy and capture exact evidence. Do not build a generic adapter framework.

## D4 — REVIEW

Produce complete before/after metadata, artwork, file-layout and audio-integrity evidence. Unexpected changes and ambiguity are visible and blocking.

## D5 — APPROVE

Persist an album-level decision tied to the exact reviewed evidence. Any change invalidates approval.

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
