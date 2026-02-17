# P126 — Networked transport stub v1 (networkless)

## Goal
Introduce a **hard network boundary** that is still **disabled by default**.

## What it is
- `http_client_stub_v1.py`: a stub "HTTP client" that enforces:
  - entry contract guards (`mode ∈ {shadow,paper}`, `dry_run=True`, deny env, no secret env)
  - transport gate (`transport_allow` is checked; `YES` is denied in v1)
  - **always raises** unless `test_allow_network_stub=True` (tests only)

## Why
We need a clean seam for later transport v2 without accidentally enabling any real network execution.

## Tests
`pytest -q tests&#47;p126 -q`
