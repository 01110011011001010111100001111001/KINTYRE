# KINTYRE DAM User Guide

**Version:** 1.0 RC1
**Audience:** Operators and Administrators

---

# 1. Introduction

KINTYRE DAM is a read-first Digital Asset Management system for preparing large
music collections for Music Assistant.

The system separates inspection from modification.

No metadata is written until an execution plan has been reviewed and approved.

Normal workflow:

    Scan
      ↓
    Audit
      ↓
   Analysis
      ↓
    Preview
      ↓
 Human Approval
      ↓
     Apply
      ↓
    Verify

---

# 2. System Requirements

Operating System
    Ubuntu Desktop LTS

Python
    3.12+

Music Library

    /data/Music

Project

    /home/richard/kintyre-dam

---

# 3. Directory Layout

Project

    config/
    docs/
    runtime/
    src/
    templates/
    tests/
    static/

Runtime

    runtime/index/
    runtime/reports/
    runtime/analysis/
    runtime/preview/
    runtime/apply/
    runtime/verify/
    runtime/logs/

---

# 4. First Time Setup

Activate the virtual environment.

    cd /home/richard/kintyre-dam

    source .venv/bin/activate

---

# 5. Running the Scan

Generate the album index.

    python src/scan.py

Output

    runtime/index/album-index.csv

---

# 6. Running the Metadata Audit

Inspect every supported audio file.

    python src/audit_metadata.py

Outputs

    runtime/reports/

The audit is completely read-only.

---

# 7. Running the Analysis

Generate album-level analysis.

    python src/analyze_library.py

Outputs

    runtime/analysis/

No music files are modified.

---

# 8. Understanding the Reports

Album Index

    One record per album folder.

Metadata Reports

    One record per metadata finding.

Analysis Reports

    Aggregated information by album.

Quality Report

    Overall quality score for each album folder.

Unknown Albums

    Albums requiring manual review.

Single Artist Candidates

    Albums suitable for AlbumArtist assignment.

Various Artist Candidates

    Compilation albums.

---

# 9. Importing New Music

Copy music into

    /data/Music

Then execute

    Scan

    Audit

    Analysis

Do not modify metadata before reviewing the Preview reports.

---

# 10. Safety

During Scan, Audit, Analysis and Preview

    NO metadata writes

    NO file moves

    NO folder renames

    NO deletions

The master music library remains protected.

---

# 11. Backup

Before Apply

Back up

    /data/Music

and

    /home/richard/kintyre-dam

Retain the runtime reports for audit purposes.

---

# 12. Troubleshooting

If Scan fails

    Verify the music library is mounted.

If Audit fails

    Check file permissions.

If Analysis fails

    Confirm album-index.csv exists.

If Preview fails

    Confirm Analysis completed successfully.

---

# 13. Recovery

The project can always be rebuilt from

    /data/Music

using

    Scan

    Audit

    Analysis

No runtime artefacts are required for recovery.
