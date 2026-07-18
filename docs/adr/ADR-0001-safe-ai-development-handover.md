# ADR-0001 — Safe AI development handover

Status: Accepted
Date: 2026-07-18

## Context

Long AI-assisted development chats can become slow or lose practical continuity. Chat memory is not authoritative project state.

## Decision

Implement a repository-driven, secret-redacted Markdown handover generator as the first post-v1.0 task, with optional JSON. The receiving AI must verify repository state before changes.

## Consequences

Tests are required for evidence collection, deterministic formatting, redaction and missing data.

## Rejected alternatives

Manual summaries, full transcript copying and reliance on AI memory.

## Review trigger

Repository or runtime-state structure changes materially.
