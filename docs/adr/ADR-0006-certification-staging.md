# ADR-0006: Supersede certification-platform staging

- Status: Superseded
- Date: 2026-07-23

The earlier certification workspace, adapter, comparator and policy-engine architecture is replaced by:

```text
COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK
```

An isolated working copy remains mandatory, but it implements COPY rather than defining a separate platform layer.
