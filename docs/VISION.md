# KINTYRE v2 Vision

## Product definition

KINTYRE v2 makes mature music-remediation tools safe to use against an authoritative production library.

It is not a replacement for beets, Picard, MusicBrainz, AcoustID or artwork providers. It is the controlled bridge between their work on a copy and an approved replacement in production.

## Mission

Correct the library album by album without sacrificing safety, evidence, operator control or recoverability.

## Permanent workflow

```text
COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK
```

One album is one transaction.

## Ownership

External OSS owns identification, release matching, metadata retrieval, fingerprint evidence, artwork retrieval and staged tag/artwork changes.

KINTYRE owns album selection, safe copying, isolation, before-state evidence, review, approval, verified backup, complete-album replacement, rollback, checking and audit history.

## Source of truth

The files in `/data/Music` are authoritative. Music Assistant and other consumer databases are disposable and rebuildable.

## Safety principles

- Production is read-only until explicit album approval.
- Tools work only on copied files.
- Audio essence must not change during metadata/artwork remediation.
- Unexpected file additions, removals, track mapping changes or unreadable output block replacement.
- Ambiguity produces deferral, not guessing.
- Replacement is all-or-nothing at album level.
- A verified backup exists before production changes.
- Rollback restores the complete prior album.
- CHECK validates both the library and downstream consumer.

## Non-goals

v2 will not initially build a proprietary metadata matcher, generic policy engine, adapter framework, dashboard-first platform, multi-user service, AI-first identification engine or direct Music Assistant database repair.
