# KINTYRE DAM Architecture

**Version:** 0.2
**Status:** Baseline Architecture
**Date:** 13 July 2026

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
                runtime/index
                         │
                         ▼
                      Audit
                         │
                         ▼
               runtime/reports
                         │
                         ▼
                    Analysis
                         │
                         ▼
              runtime/analysis
                         │
                         ▼
                    Preview
                         │
                         ▼
              runtime/preview
                         │
                  Human Approval
                         │
                         ▼
                      Apply
                         │
                         ▼
                    /data/Music
                         │
                         ▼
                      Verify
                         │
                         ▼
              runtime/verify

Each phase is independent.

Each phase is repeatable.

Each phase produces explicit artefacts.

---

# 5. Current Status

## Completed

- Scan Engine
- Metadata Audit
- Album Index
- Analysis Engine
- Read-only validation

## Planned

- Preview Engine
- Apply Engine
- Verify Engine

---

# 6. Current Library Baseline

Current validated library:

- Audio files: 39,832
- Album folders: 4,099
- Library size: 365.15 GiB

Libraries:

- CONTEMPORARY
- CLASSICAL

Current metadata baseline:

- Metadata findings: 29,959
- Affected files: 19,950
- Affected folders: 2,680
- Genuine damaged media files: 1

The damaged file is intentionally excluded from future automatic processing.

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
    May modify metadata only after explicit approval.

Verify:
    Read Only

No phase except Apply may modify /data/Music.

