# KINTYRE v2 Technology Decisions

1. `/data/Music` is authoritative; Music Assistant is rebuildable.
2. The v2 architecture is `COPY → FIX → REVIEW → APPROVE → REPLACE → CHECK`.
3. One album is one transaction.
4. External OSS performs music intelligence.
5. External tools operate only on copied files.
6. KINTYRE owns isolation, evidence, approval, backup, replacement, rollback, checking and audit.
7. v1 is frozen as the historical baseline.
8. Documentation precedes v2 code.
9. The first implementation is thin and vertical.
10. Ambiguity is deferred.

## Superseded

The previous separately named certification workspace, adapter, comparator, policy, promotion and reconciliation engine architecture is superseded. Those functions may exist internally but do not define v2.
