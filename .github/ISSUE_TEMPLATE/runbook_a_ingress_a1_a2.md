---
name: "Runbook A: Ingress (A1/A2)"
about: "Track Ingress Taxonomy (A1) and NormalizedEvent contract (A2)"
title: "[Runbook A] Ingress: A1 taxonomy / A2 contract"
labels: ["docs", "ops", "runbook-a"]
assignees: []
---

## Context
- Runbook: `docs/runbooks/RUNBOOK_A_ingress_orchestrator_layers_learning.md`
- Appendix:
  - `docs/runbooks/appendix/A1_incoming_taxonomy.md`
  - `docs/runbooks/appendix/A1_incoming_taxonomy_evidence.md`

## A1 – Incoming Taxonomy (DoD)
- [ ] Each ingress domain has **producer** (module/service) identified.
- [ ] Transport recorded: WS / REST / file / internal queue.
- [ ] Raw schema(s) referenced (links/paths).
- [ ] Shadow vs Testnet vs Live differences recorded + gating points.
- [ ] Storage path(s) and retention policy recorded (if any).
- [ ] Sensitivity classification confirmed (public/internal/restricted).

## A2 – NormalizedEvent Contract (DoD)
- [ ] Minimal contract agreed:
  - `event_id`, `ts_ms`, `source`, `kind`, `scope`, `tags`, `sensitivity`, `payload`
- [ ] Writer design chosen: JSONL append-only + sha256 chaining/manifest.
- [ ] Deterministic serialization rules documented (ordering, float formatting, etc.).
- [ ] Replay invariants defined (idempotency, dedup, monotonic timestamps).
- [ ] Tests added (schema validation + golden samples).
