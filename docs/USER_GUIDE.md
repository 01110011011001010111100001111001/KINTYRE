# KINTYRE v2 User Guide

## Status

This guide defines target v2 operation. Current v1 commands remain available through their built-in `--help` until v2 stage commands exist.

## Rule

Never allow an identification or tagging tool to work directly on `/data/Music`.

## Workflow

1. **COPY** — select exactly one album; record its production before-state; copy it to an isolated system-drive transaction.
2. **FIX** — run the verified OSS workflow against the copy only.
3. **REVIEW** — inspect every metadata, artwork, file-layout, identifier, track-mapping and audio-integrity change.
4. **APPROVE** — approve, reject or defer the exact reviewed transaction.
5. **REPLACE** — revalidate production, verify a complete backup and replace the album as one action.
6. **CHECK** — verify files, tags, artwork, audio essence and Music Assistant.

## Decisions

- `PENDING` — not reviewed.
- `APPROVED` — exact reviewed album may be replaced.
- `REJECTED` — proposal must not be used.
- `DEFERRED` — unresolved and retained for later work.

## Recovery

At any unexpected result: stop, preserve evidence, do not rerun FIX against production, compare production with the recorded before-state, restore the complete verified backup when replacement was attempted, then run CHECK again.

Music Assistant is checked after the authoritative files are correct. Do not repair its database as a substitute for correcting or rescanning the library.
