# ADR-0002 — Duplicate detection strategy

Status: Proposed
Date: 2026-07-18

## Context

Duplicate detection needs exact, acoustic, metadata and artwork evidence.

## Candidates

Cryptographic hashes, Chromaprint, AcoustID-compatible lookup, beets, dupeGuru, rdfind, fdupes, imagehash and custom algorithms.

## Decision

Use hashes for exact evidence. Trial Chromaprint for same-audio evidence and imagehash for artwork similarity. Evaluate existing tools for reusable behavior. KINTYRE owns scoring, reporting, approval and resolution workflow.

## Rejected alternatives

A fully custom fingerprint implementation unless established tools fail documented requirements.

## Review trigger

After benchmark and false-positive evidence is available.
