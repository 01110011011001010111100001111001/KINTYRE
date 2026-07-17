# KINTYRE DAM Changelog

All notable changes to this project are recorded in this document.

The format is based on semantic project milestones rather than software
packages.

---

## v0.2 — Audit and Analysis Baseline
**Date:** 13 July 2026

### Added

- Project directory structure
- Scan Engine
- Metadata Audit Engine
- Analysis Engine
- Album index generation
- Folder quality analysis
- Single artist candidate detection
- Various artist candidate detection
- Unknown album detection
- Runtime analysis reports

### Fixed

- AppleDouble (._*) files excluded from scanning
- Metadata read errors separated from ordinary metadata deficiencies
- Read-only safety validation


### Safety

- No metadata written
- No files moved
- No folders renamed
- No deletions
- No modifications to /data/Music

---

## Planned

### v0.3

Preview Engine

### v0.4

Apply Engine

### v0.5

Verify Engine

### v1.0

Production Release
