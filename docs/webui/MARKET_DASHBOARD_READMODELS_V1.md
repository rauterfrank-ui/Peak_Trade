# Market Dashboard ReadModels v1

Ownership: `src/webui/market_dashboard_readmodels_v1/` — typed consumer contracts for the Market Dashboard architecture reset.

Authority / SSOT reference (do not duplicate):

- `docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md`

## Import direction

```text
Domain producers → ReadModel contracts (this package) → Presenter / UI
```

This package must not import templates, Jinja, Flask/FastAPI route modules, or CSS/JS concerns. It must not call Trading Core producers, Double Play composition, execution clients, or order actions.

## Available vs unavailable

- Available domain snapshots are immutable typed contracts with mandatory provenance.
- Missing / unbound / stale / malformed sources use `UnavailableSnapshotV1` with explicit `DashboardAvailabilityStateV1`.
- Missing metrics remain `None` — never fabricated `0.0`, safe/blocked defaults, market prices, or decisions.

## Provenance

`DashboardSnapshotProvenanceV1` requires schema identity, producer module, timezone-aware timestamps, source kind, freshness state, and `source_reference` or `evidence_digest`. Presenter-generated provenance is prohibited.

## Validation and serialization

- Central validators live in `validation.py` (fail-closed).
- Deterministic serialization lives in `serialization.py` (`allow_nan=False`, stable field order, ISO-8601 timezone-aware timestamps).
- No domain calculation, authority derivation, or ranking re-computation beyond deterministic ordering of already-supplied items.

## PR boundaries

- Producer binding belongs to **PR-C** (`adapters&#47;` subdirectory).
- UI / `&#47;market` page binding belongs to **PR-D**
  (`docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md`).
- This package remains free of template/Jinja/CSS concerns; the page aggregate
  builder in `page_builder.py` composes adapter outputs only.

## Adapters (PR-C)

`src&#47;webui&#47;market_dashboard_readmodels_v1&#47;adapters&#47;` projects already-produced
canonical sources onto the typed contracts above. Adapters are deterministic,
side-effect free, accept explicit source objects, and emit
`UnavailableSnapshotV1` when sources are absent, unbound, or malformed.

Adapters must not call `integrated_offline_trading_logic_replay_v1`, must not
import `build_static_dashboard_display_dict`, must not recalculate economic
metrics, and must not invent authority/execution permission from UI constants.
