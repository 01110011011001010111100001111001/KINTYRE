# ADR-0001 — Safe AI development handover

Status: Accepted
Date: 2026-07-18

## Context

Long AI-assisted development chats can become slow or lose practical continuity. Chat memory is not authoritative project state.

## Decision

Maintain `docs/HANDOVER.md` as the self-contained continuity and engineering
briefing that can be pasted into a new AI chat. It must be reviewed and updated
at the end of every successful sprint. The receiving AI must still inspect the
repository, documentation, implementation and tests before proposing changes.

Separately, implement the repository-driven, secret-redacted Markdown handover
generator described in the roadmap, with optional JSON. The generator will
collect current repository and runtime evidence and complement
`docs/HANDOVER.md`; it will not replace the maintained engineering contract and
continuity guidance.

## Consequences

- `docs/HANDOVER.md` is a mandatory sprint deliverable.
- The document may repeat essential project rules because it is intended to be
  pasted without the rest of the documentation.
- Current state must be verified rather than copied forward blindly.
- Tests remain required for generated evidence collection, deterministic
  formatting, redaction and missing data.

## Rejected alternatives

- Full transcript copying.
- Reliance on AI memory.
- A generated status package with no stable engineering contract.
- A maintained document that replaces repository inspection.

## Review trigger

Repository or runtime-state structure changes materially, or the sprint
workflow and continuity requirements change.
