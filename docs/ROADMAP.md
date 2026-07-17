# KINTYRE DAM Roadmap

## Vision

KINTYRE DAM is a deterministic, audit-first Digital Asset Management system
for preparing large music libraries for Music Assistant.

The project follows a staged workflow in which every metadata change is
planned, reviewed and approved before execution.

---

## Current Status

### v1.0

Completed

- Scan Engine
- Metadata Audit
- Album Index
- Analysis Engine
- Read-only validation
- Project documentation

---

## v0.3 — Completed

Preview Engine

Delivered

- Implement preview.py
- Generate apply-plan.json
- Generate preview-summary.json
- Produce human-readable preview reports
- Remain completely read-only

---

## v0.4 — Completed

Apply Engine

Delivered

- Execute approved actions
- Transaction logging
- Dry-run support
- Error reporting

---

## v0.5

Verify Engine

Objectives

- Re-scan the library
- Re-audit metadata
- Compare before and after state
- Produce verification reports

---

## v1.0 — Released

Production Release

Delivered

- Stable interfaces
- Complete documentation
- Automated testing
- Repeatable workflows
- Production-ready metadata management

---

## Long-Term Principles

- Protect the master music archive.
- Keep media and application data separate.
- Preserve deterministic behaviour.
- Maintain complete traceability.
- Prefer simple, maintainable architecture.
- Require explicit approval before metadata modification.
