# LB-REC-001 Phase 1 — recorded reconciliation fixtures

Deterministic JSON cases for `ReconciliationEngine` + `ExternalSnapshot` harness tests.

- **Mock-only / Phase 0** — no exchange API, no network.
- **Does not** establish live-approved reconciliation or close LB-REC-001 for real reporting.

Schema: `lb_rec_001_phase1_v1` (see `case_*.json`).

- `internal.fill`: single recorded fill (existing cases).
- `internal.fills`: optional array of fills for multi-symbol ledgers (Phase 2 slice); mutually exclusive with `fill` in practice — use one style per case.

`expect` may include `min_warn`, `min_info`, `first_severity` for severity assertions (see newer `case_*.json`).

**Phase 3 (LB-REC-001):** `case_buy_then_sell_warn.json` (multi-fill with SELL); `case_position_and_cash_fail.json` (stacked POSITION + CASH FAIL). Mock-only; not live-approved reconciliation.

**Phase 4 (LB-REC-001):** `case_multi_symbol_exchange_omits_eth.json` (internal two symbols, external omits one row); `case_position_external_zero_qty_fail.json` (external zero qty vs internal position). Mock-only; does not close LB-REC-001 or imply live-approved reconciliation.

**Phase 5 (LB-REC-001):** `case_netted_flat_empty_external.json` (BUY+SELL net flat; ledger row qty 0; external `positions` empty). Mock-only; not an exchange baseline.
