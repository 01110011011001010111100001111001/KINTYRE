# KINTYRE v2 Vision

## Product definition

KINTYRE v2 makes mature music-remediation tools safe to use against an authoritative production library.

It is not a replacement for beets, Picard, MusicBrainz, AcoustID or artwork providers. It is the controlled bridge between their work on a copy and an approved replacement in production.

## Mission

Transform the existing music collection into a complete, accurate, consistent
and fully functioning digital library, album by album, without sacrificing
safety, evidence, operator control or recoverability.

The workflow is a means to that outcome, not the outcome itself.

## Primary success criterion

KINTYRE succeeds only when the resulting library is measurably better and works
correctly in Music Assistant and other downstream consumers.

Success is not measured by feature count, lines of code, metadata fields changed
or pipeline stages completed. It is measured by improvements such as:

- correct artist, album and compilation grouping;
- complete and accurate metadata;
- reliable artwork;
- improved search, browsing and interoperability;
- fewer unknown, duplicate or inconsistent identities;
- appropriate classical metadata;
- preserved audio essence; and
- verified recoverability of every promoted change.

Before work begins on any capability, the project must answer:

> Will this leave the user's library in a measurably better state?

If the answer is **No**, the capability is not built. Essential infrastructure
is permitted only when it directly enables a defined and measurable library
improvement.

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

## Outcome gate

Every remediation admitted to KINTYRE must identify:

1. the concrete library problem it solves;
2. the expected improvement to the resulting library;
3. the evidence that will verify that improvement; and
4. the safe reversal path if the result is wrong.

REVIEW must explain the expected library benefit before APPROVE can authorize
promotion.

## Non-goals

v2 will not initially build a proprietary metadata matcher, generic policy
engine, adapter framework, dashboard-first platform, multi-user service,
AI-first identification engine or direct Music Assistant database repair.

Architectural elegance, abstraction, reporting and monitoring are not sufficient
reasons to build a capability unless they directly improve the library or are
essential to safely delivering a defined library improvement.
