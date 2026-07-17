# KINTYRE Architecture

**Version:** 1.0
**Status:** Released

## Purpose

KINTYRE is a deterministic, audit-first platform for commissioning and maintaining music libraries consumed by Music Assistant. The media library is authoritative. Music Assistant is a rebuildable consumer.

## Principles

- Protect source media.
- Separate observation from modification.
- Require explicit approval before Apply.
- Keep generated data off the media drive.
- Preserve decision and execution history.
- Prefer conservative, reversible operations.
- Certify identity-changing operations before production use.

## Storage separation

The media drive contains media only. The system drive contains source code, configuration, virtual environments, reports, indexes, approvals, audit records, logs, caches, staging, backups and application databases.

## Pipeline

```text
Media Library → Scan → Metadata Audit → Analysis → Preview → Approval → Apply → Verification
```

## Engine responsibilities

| Engine | Responsibility | Writes media |
|---|---|---:|
| Scan | Discover media and build indexes | No |
| Metadata Audit | Read tags and report findings | No |
| Analysis | Aggregate findings | No |
| Preview | Produce deterministic proposed actions | No |
| Approval | Record decisions and export approved actions | No |
| Apply | Validate and execute approved actions | Yes |
| Verification | Rescan, re-audit and inspect results | No |

## Preview Engine

Canonical directory: `runtime/preview/`.

Primary outputs:

- `preview-summary.json`
- `apply-plan.json`
- `albumartist-fixes.csv`
- `review-summary.json`

## Approval Engine

States:

- `PENDING`
- `APPROVED`
- `REJECTED`
- `DEFERRED`

Supports single and bulk decisions, exact and contains filters, logical AND across filters, idempotent updates, reset to `PENDING`, atomic persistence, approved-action export and append-only audit events.

Outputs are stored under `runtime/approval/`.

## Apply Engine

Apply consumes approved actions. Controls include dry-run, validation, blocked-transaction handling, explicit live confirmation, backups, rollback handling, post-write verification, non-zero failure behaviour and Apply outcome events.

Outputs are stored under `runtime/apply/`.

## Identity-changing operations

Changes to AlbumArtist, album title, artist identity, compilation status, MusicBrainz identifiers or folder identity can change consumer grouping. They must first be tested in a disposable certification environment with a separate Music Assistant instance and database.

## Repository privacy

Do not commit production inventories, media file lists, collection statistics, generated reports, commissioning evidence, backups, caches, databases, secrets or machine-specific private data.
