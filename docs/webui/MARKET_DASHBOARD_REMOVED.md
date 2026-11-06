# Market Dashboard — Historical Removal Evidence

```text
DOCUMENT_CLASS=HISTORICAL_EVIDENCE_ONLY
CURRENT_ARCHITECTURE_AUTHORITY=false
CURRENT_TOMBSTONE_CONTRACT=false
CURRENT_NEGATIVE_NON_REGRESSION_GUARD=false
CURRENT_LIVE_GUARD=false
CURRENT_BOUNDARY_CONTRACT=false
```

This file is **historical evidence only**. It is not current architecture,
not a live guard, not a current boundary contract, and not a current
negative non-regression requirement.

**Current visual/operator consumer (authoritative for today):**
[`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md)

Current path:

- Landscape V2 package `src/webui/market_dashboard_landscape_v2/`
- Shell router `src/webui/market_dashboard_landscape_shell_router_v2.py`
- Route `GET &#47;market`
- Template `templates/peak_trade_dashboard/market_landscape_v2.html`

`DASHBOARD_AUTHORITY_EFFECT=NONE`. Landscape is a read-only consumer. It
does not own trading, signal, selection, risk, planning, execution, or
live-permit authority.

## Historical facts (non-authoritative)

The former **legacy** Market Dashboard product, including legacy
`market_surface`, was intentionally removed. That removal is Git history.
Git history may remain. This document does **not** require a current
tombstone test, `DELETED_PACKAGES` invariant, or negative non-regression
guard to keep Landscape valid.

Do not treat this file as a reason to resurrect the legacy product.
Do not treat this file as a reason to keep a current tombstone contract.
Resurrection of deleted legacy Dashboard code from Git history still
requires explicit operator authorization; that is a future GO, not a
standing current tombstone architecture.
