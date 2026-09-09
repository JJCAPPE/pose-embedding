# 0002 — Accept the Supabase Oregon production region

- **Status:** Accepted
- **Date:** 2026-09-09
- **Decision owner:** Researcher

## Context

The implementation plan named East US/Ohio (`us-east-2`) for the dedicated
Supabase project. The provisioned `pose-embedding-tracker` project is instead
in Oregon (`us-west-2`). It was still empty when the discrepancy was found.

## Decision

The researcher explicitly accepted Oregon on September 9, 2026. The existing
project remains the tracker production database.

## Consequences and controls

- This is an infrastructure deviation only; it does not change the scientific
  protocol, project dates, access model, or result interpretation.
- The tracker stores public-safe planning metadata, not participant data,
  licensed datasets, model checkpoints, credentials, or private correspondence.
- The production region must be recorded in deployment and final handoff notes.
- Revisit the region only if BU governance, residency requirements, or measured
  latency require a move. A move must preserve tracker history and checksums.
