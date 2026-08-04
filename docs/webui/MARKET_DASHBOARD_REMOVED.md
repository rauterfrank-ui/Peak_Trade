# Market Dashboard — Legacy Product Fully Removed

**STATUS:** `REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS`

```text
Legacy market_surface is fully removed and is not an architectural component.
Negative non-regression guards exist solely to prevent its reintroduction.
No tombstone route, module, presenter, template, source, slot, fallback, compatibility path, authority, producer, read model, or runtime path exists.
```

Legacy `market_surface` is fully removed and is not an architectural component.
Negative non-regression guards exist solely to prevent its reintroduction.
No tombstone route, module, presenter, template, source, slot, fallback,
compatibility path, authority, producer, read model, or runtime path exists.

## Canonical removal facts

The Peak Trade **legacy** Market Dashboard product (including legacy
`market_surface`) was intentionally removed and completely deleted.

- Legacy packages, templates, Chart.js market shells, OHLCV/depth APIs, and
  reset-shell markers remain deleted.
- Legacy aliases (`&#47;market&#47;double-play`, `&#47;market&#47;futures`,
  `&#47;api&#47;market&#47;ohlcv`, `&#47;api&#47;market&#47;depth`) remain
  intentionally absent (normal not-found).
- There is **no** registry slot, contract, route, module, template, presenter,
  binder, read model, producer, fallback, authority, runtime path, or
  reactivation option for legacy `market_surface`.
- Independent domain producers (trading, risk, execution, economic,
  diagnostics, market-data) remain domain-owned.

**Current authorized read-only surface (already on main):**  
`GET &#47;market` remains the **Market Dashboard Landscape V2** read-only
consumer shell. Exact route/template/static/bindings stay owned by the
canonical Landscape V2 master runbook; this removal notice does **not**
redefine them.

- Pure read-only GET route; no write/action/order/runtime controls.
- Unbound or missing producers render as `NOT_BOUND` / `MISSING` / `STALE` /
  `INVALID`.
- Does **not** authorize runtime activation, orders, scheduler,
  shadow/paper/testnet, capital changes, promotion, or live trading.
- `OPERATOR_PRODUCT_GATE=true` is recorded from the Operator Product Review on
  exact commit `88f2241819dcc160c3ce688a9c7397e7cc8becec` (post PR #5568;
  read-only daily observation surface). PR #5569 later added docs-only
  Consumer / Anti-SSOT wording and did not invalidate that review. PR #5577
  bound Regime/Bull-Bear/Switch read-only (explicit injection). Final closeout
  docs hygiene reconciles Class-C drift only (`NEXT_CANONICAL_ACTION=STOP_IDLE`).
  Technical or Chrome evidence alone must **not** be re-inferred as a new
  Product PASS. Dashboard remains non-authority / non-SSOT / non-truth-owner.
  Documentation Anchor = documentary index only.

Canonical planning/execution authority:  
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Do not resurrect deleted legacy Dashboard / `market_surface` code from Git
history without explicit operator authorization. Absence is enforced by
negative non-regression guards only; absence is not a reactivatable surface.
