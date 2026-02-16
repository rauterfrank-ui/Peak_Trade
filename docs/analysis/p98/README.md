# P98 — Ops Loop Orchestrator v1

**Goal:** One-shot orchestrator that validates the running ops loop and refreshes artifacts safely (paper/shadow only).

## What it runs (in order)

- `P95` ops meta gate
- `P96` P91 kickstart guard (supports `DRY_RUN=YES`)
- `P93` status dashboard one-shot
- `P92` retention for P91 audit snapshots
- `P94` retention for P93 status dashboard artifacts

## Non-goals

- No live/record enablement.
- No supervisor start/stop.
