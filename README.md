# KINTYRE DAM

Digital Asset Management for Music Assistant

---

## Overview

KINTYRE DAM is a deterministic, audit-first Digital Asset Management system
designed to prepare large music libraries for Music Assistant.

The project separates discovery, inspection, analysis, planning and execution
into independent phases to ensure that every metadata change is explicit,
reviewable and reproducible.

The master music archive is treated as protected storage.

No media is modified until an approved execution plan is applied.

---

## Project Status

Current Version

    v1.0

Status

    Production Release

Release State

    Stable v1.0 baseline

---

## Workflow

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
           Human Approval
                   │
                   ▼
                 Apply
                   │
                   ▼
                 Verify

---

## Repository

src/

    scan.py
    audit_metadata.py
    common.py
    analyze_library.py

docs/

    ARCHITECTURE.md
    USER_GUIDE.md
    DEVELOPER_GUIDE.md
    REPORT_FORMATS.md
    CHANGELOG.md
    ROADMAP.md

runtime/

    index/
    reports/
    analysis/
    preview/
    apply/
    verify/


---

## Safety

The following phases are completely read-only

    Scan

    Audit

    Analysis

    Preview

    Verify

Only Apply may modify metadata.

No phase except Apply may write to

    /data/Music

---

## Documentation

Architecture

    docs/ARCHITECTURE.md

Operations

    docs/USER_GUIDE.md

Development

    docs/DEVELOPER_GUIDE.md

Report Schemas

    docs/REPORT_FORMATS.md

Roadmap

    docs/ROADMAP.md

Change History

    docs/CHANGELOG.md

---

## Repository Privacy

Generated runtime reports and production-library inventories are local operational data and are not part of the public repository.

## License

See the repository licensing information.
