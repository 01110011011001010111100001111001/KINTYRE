# ADR-0003 — Dashboard and observability split

Status: Proposed
Date: 2026-07-18

## Context

KINTYRE needs both guided protected operations and professional metrics visualization.

## Decision

Trial NiceGUI with FastAPI-backed services for operations. Use Grafana OSS for read-only observability. Grafana cannot change workflow state or execute Apply.

## Consequences

KINTYRE exposes structured metrics/logs and remains safely operable without Grafana.

## Rejected alternatives

Grafana as the complete workflow interface; custom React before Python-native options are proven insufficient.

## Review trigger

After the v1.2 prototype and resource measurements.
