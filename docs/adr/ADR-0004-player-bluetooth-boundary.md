# ADR-0004 — Player and Bluetooth diagnostics boundary

Status: Accepted
Date: 2026-07-18

## Context

Bluetooth pitch and timing instability concerns the host/player audio path, not Music Assistant library reconciliation.

## Decision

Create a separate Player Performance and Bluetooth Audio Reliability release. Use BlueZ, PipeWire, WirePlumber and ALSA evidence before custom probes. Music Assistant may be a test source but is not required.

## Consequences

System audio changes require separate approval, backup and rollback.

## Rejected alternatives

Bundling Bluetooth with Music Assistant integration and speculative global tuning.

## Review trigger

Additional player transports are introduced.
