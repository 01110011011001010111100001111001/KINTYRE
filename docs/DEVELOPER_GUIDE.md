# KINTYRE DAM Developer Guide

**Version:** 0.2
**Audience:** Developers and Maintainers

---

# 1. Purpose

This document defines the engineering standards used throughout the KINTYRE
DAM project.

The objective is to ensure every component is deterministic, testable,
maintainable and safe.

---

# 2. Development Principles

The following principles are mandatory.

- Deterministic behaviour.
- Reproducible outputs.
- Explicit approval before modification.
- Single responsibility per engine.
- Complete traceability.
- Conservative change management.

---

# 3. Repository Layout

Project root

    config/
    docs/
    runtime/
    src/
    templates/
    tests/
    static/

Generated files belong only under

    runtime/

No generated data belongs inside src/.

---

# 4. Engine Responsibilities

Scan

    Discover media.

Produces

    runtime/index/

Audit

    Inspect metadata.

Produces

    runtime/reports/

Analysis

    Aggregate metadata.

Produces

    runtime/analysis/

Preview

    Generate proposed actions.

Produces

    runtime/preview/

Apply

    Execute approved metadata updates.

Produces

    runtime/apply/

Verify

    Confirm post-Apply results.

Produces

    runtime/verify/

Each engine has exactly one responsibility.

---

# 5. Coding Standards

Target Python 3.12+

Use

- type hints
- pathlib
- standard library where practical

Prefer

- small functions
- explicit names
- deterministic ordering

Avoid

- hidden side effects
- global mutable state
- duplicated logic

---

# 6. Protected Media

The following directory is protected

    /data/Music

Scan

    Read only

Audit

    Read only

Analysis

    Read only

Preview

    Read only

Verify

    Read only

Only Apply may modify media.

---

# 7. Runtime Rules

Every report is generated under

    runtime/

Reports must be recreated from source data.

Never edit generated reports manually.

---

# 8. Error Handling

Fail early.

Provide clear error messages.

Never continue after corrupted input.

Never silently ignore failures.

---

# 9. Testing

Tests belong under

    tests/

Regression tests should cover

- scanner
- metadata audit
- analysis
- preview
- apply
- verify

Every fixed defect should receive a regression test.

---

# 10. Versioning

Current roadmap

v0.1

Foundation

v0.2

Audit and Analysis

v0.3

Preview

v0.4

Apply

v0.5

Verify

v1.0

Production

---

# 11. Git Workflow

Recommended workflow

feature branch

↓

development

↓

testing

↓

commit

↓

tag

↓

merge

Tag validated milestones.

Keep commits focused on one logical change.

---

# 12. Future Development

Future work should extend the existing architecture rather than redesign it.

The protected media principle and the

Audit

↓

Analysis

↓

Preview

↓

Apply

↓

Verify

pipeline are considered stable.

