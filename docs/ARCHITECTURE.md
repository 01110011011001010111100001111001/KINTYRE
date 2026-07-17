# KINTYRE DAM Architecture

**Version:** 1.0 RC1
**Status:** Release Candidate
**Date:** 14 July 2026

---

# 1. Purpose

KINTYRE DAM (Digital Asset Management) is a deterministic, audit-driven music
library management system designed to prepare large music collections for
Music Assistant.

The project manages a protected master music archive while ensuring that every
metadata change is planned, reviewable, traceable and reproducible.

Unlike conventional tag editors, KINTYRE DAM deliberately separates
inspection, analysis, planning and execution into independent phases.

No metadata is modified until an explicit execution plan has been reviewed and
approved.

---

# 2. Design Objectives

The primary objectives are:

- Produce a clean, reliable Music Assistant library.
- Preserve the integrity of the master music archive.
- Keep all processing deterministic and repeatable.
- Separate observation from modification.
- Produce a complete audit trail.
- Allow the entire system to be rebuilt from source media.

Safety and reproducibility take priority over automation.

---

# 3. Core Principles

## Protected Media

The music archive resides under:

    /data/Music

This directory is protected.

During Scan, Audit, Analysis and Preview there are:

- no metadata writes
- no file moves
- no folder renames
- no deletions

Only the Apply phase may modify media, and only after explicit approval.

---

## System Drive

The system drive contains:

- source code
- runtime reports
- documentation
- logs
- Docker
- configuration
- caches
- databases

The data drive contains media only.

---

## Deterministic Processing

Identical inputs must always produce identical outputs.

Report generation must never depend upon filesystem ordering or hidden state.

---

## Separation of Responsibility

Each engine has exactly one responsibility.

| Engine | Responsibility |
|----------|----------------|
| Scan | Discover media |
| Audit | Inspect metadata |
| Analysis | Aggregate findings |
| Preview | Produce proposed changes |
| Apply | Execute approved changes |
| Verify | Confirm results |

---

# 4. Processing Pipeline

                    /data/Music
                         │
                         ▼
                      Scan
                         │
                         ▼
                      Audit
                         │
                         ▼
                    Analysis
                         │
                         ▼
                    Preview
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
 preview-summary   apply-plan.json  albumartist-fixes.csv
                         │
                         ▼
               review-summary.json
                         │
                         ▼
                  Human Approval
                         │
                         ▼
                      Apply
                         │
                         ▼
                      Verify

Each phase is independent.

Each phase is repeatable.

Each phase produces explicit artefacts.

---

# 5. Current Status

## Completed

- Scan Engine
- Metadata Audit Engine
- Album Index
- Analysis Engine
- Preview Engine
- Deterministic Album IDs
- Read-only Preview Pipeline
- Preview Review Summary
- Human Review CSV Generation

Current Preview outputs:

- runtime/preview/preview-summary.json
- runtime/preview/apply-plan.json
- runtime/preview/albumartist-fixes.csv
- runtime/preview/review-summary.json

Current Preview capabilities:

- Stable Album IDs
- Stable Action IDs
- High-confidence ADD_ALBUMARTIST recommendations
- Automatic proposed AlbumArtist resolution
- Confidence assessment
- Risk assessment
- Human review workflow

## Implemented in v1.0

- Approval state model
- Generic action filtering
- Bulk approval operations
- Approval audit logging
- Apply Engine dry-run support
- Apply outcome audit integration
- Certified live-write foundation
- Automated regression tests

---


---


## Public Repository Privacy

The public repository contains application code, generic documentation,
tests and report schemas.

Production-library inventories, file counts, storage totals, collection names,
paths containing personal information, generated reports and commissioning
results must remain outside Git.

Runtime data is local and rebuildable and must not be committed.

---

# 7. Safety Contract

The following rules are mandatory.

Scan:
    Read Only

Audit:
    Read Only

Analysis:
    Read Only

Preview:
    Read Only

Apply:
    Explicit approval required before modifying media.

Verify:
    Read Only

The protected music library remains unchanged until the Apply phase executes approved actions.
