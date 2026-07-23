# KINTYRE v2 Architecture

## Status

This document defines the target v2 architecture. The released v1 implementation remains a frozen historical baseline.

## Outcome principle

The purpose of the KINTYRE pipeline is to produce a complete, accurate,
consistent and fully functioning music library while protecting the
authoritative collection.

The pipeline is not itself the product outcome. Every stage must either:

- directly produce a measurable library improvement; or
- provide an essential safety, evidence, approval, promotion or verification
  capability required to deliver that defined improvement.

Before a capability is accepted into the roadmap, it must identify the concrete
library problem, expected user-visible or measurable benefit, verification
evidence and reversal path. If it cannot do so, it is not built.

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

Show all file, metadata, artwork, identity, track-mapping and audio-integrity
differences. Unexpected or unexplained changes block approval.

REVIEW must answer four questions:

1. What changed?
2. Is the result trustworthy?
3. How will the proposed changes improve the resulting library and its
   downstream behaviour?
4. Is the exact reviewed transaction ready to proceed to APPROVE?

REVIEW records evidence and a recommendation. It does not make the human
approval decision.

### APPROVE

Record `PENDING`, `APPROVED`, `REJECTED` or `DEFERRED`. Approval is tied to the exact reviewed source and proposed manifests. Any later working-copy change invalidates it.

### REPLACE

Revalidate the production before-state, verify backup capacity, create and verify a complete backup, then replace the album as one bounded operation. Any partial failure triggers whole-album rollback.

### CHECK

Verify expected files, readability, approved metadata/artwork, unchanged audio essence, absence of unapproved changes and intended Music Assistant representation.

## Simplicity constraint

Do not introduce separate certification, comparator, policy, workspace-manager, promotion or adapter products. Small modules may perform those functions internally, but the public and architectural model remains the six-stage workflow.
