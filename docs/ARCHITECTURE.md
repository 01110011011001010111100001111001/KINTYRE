# KINTYRE v2 Architecture

## Status

This document defines the target v2 architecture. The released v1 implementation remains a frozen historical baseline.

## Architectural model

```text
Authoritative album in /data/Music
                │
                ▼
              COPY
                │
                ▼
        isolated working copy
                │
                ▼
               FIX
        verified external OSS
                │
                ▼
             REVIEW
      before/after + evidence
                │
                ▼
            APPROVE
       explicit album decision
                │
                ▼
            REPLACE
     backup + bounded replacement
                │
                ▼
              CHECK
 library + Music Assistant + rollback proof
```

The stage names are the architecture. Internal code serves these stages rather than creating a second conceptual platform.

## Transaction boundary

One album directory is one transaction. It contains the source manifest, working copy, tool/version/configuration evidence, before/after review, decision, backup, replacement result, CHECK result and rollback result when used.

Per-file details remain visible, but approval and replacement occur at album level.

## Trust boundaries

- `/data/Music` is authoritative and protected.
- Workspaces, caches, logs, reports and backups remain on the system drive.
- External tools may modify only the working copy.
- Music Assistant is checked after replacement but is not the identity authority.

## Stage contracts

### COPY

Validate the selected production album, record the before-state, copy the complete album and prove production remained unchanged.

### FIX

Run verified OSS only against the copy. Capture executable, version, invocation, configuration fingerprint, logs and exit state. Preserve audio essence and unresolved ambiguity.

### REVIEW

Show all file, metadata, artwork, identity, track-mapping and audio-integrity differences. Unexpected or unexplained changes block approval.

### APPROVE

Record `PENDING`, `APPROVED`, `REJECTED` or `DEFERRED`. Approval is tied to the exact reviewed source and proposed manifests. Any later working-copy change invalidates it.

### REPLACE

Revalidate the production before-state, verify backup capacity, create and verify a complete backup, then replace the album as one bounded operation. Any partial failure triggers whole-album rollback.

### CHECK

Verify expected files, readability, approved metadata/artwork, unchanged audio essence, absence of unapproved changes and intended Music Assistant representation.

## Simplicity constraint

Do not introduce separate certification, comparator, policy, workspace-manager, promotion or adapter products. Small modules may perform those functions internally, but the public and architectural model remains the six-stage workflow.
