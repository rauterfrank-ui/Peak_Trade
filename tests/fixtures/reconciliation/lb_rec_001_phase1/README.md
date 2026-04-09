# LB-REC-001 Phase 1 — recorded reconciliation fixtures

Deterministic JSON cases for `ReconciliationEngine` + `ExternalSnapshot` harness tests.

- **Mock-only / Phase 0** — no exchange API, no network.
- **Does not** establish live-approved reconciliation or close LB-REC-001 for real reporting.

Schema: `lb_rec_001_phase1_v1` (see `case_*.json`).

- `internal.fill`: single recorded fill (existing cases).
- `internal.fills`: optional array of fills for multi-symbol ledgers (Phase 2 slice); mutually exclusive with `fill` in practice — use one style per case.

`expect` may include `min_warn`, `min_info`, `first_severity` for severity assertions (see newer `case_*.json`).
