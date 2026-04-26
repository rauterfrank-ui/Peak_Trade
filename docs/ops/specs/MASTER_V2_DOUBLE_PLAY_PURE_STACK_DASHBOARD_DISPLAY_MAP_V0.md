---
title: "Master V2 Double Play Pure Stack Dashboard Display Map v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0"
---

# Master V2 Double Play Pure Stack Dashboard Display Map v0

## 1. Purpose

This **display map** defines how a **future** read-only dashboard may **present** Master V2 / Double Play **pure-stack** decisions (Futures Input through Composition) as **labels and snapshots only**.

It exists to prevent confusion between:

```text
displaying a pure decision
authorizing trading, Testnet, Live, allocation, sessions, or scanner/selector behavior
```

**This document is docs-only.** It does **not** implement routes, templates, WebUI startup, data fetches, or governance signoff.

## 2. Non-authority note

This file is **non-authorizing**. It does not:

- start the WebUI, Docker, or any server
- implement or register HTTP routes
- fetch market data, call exchanges, or run scanners
- start Paper, Shadow, Testnet, Live, bounded-pilot, or execution sessions
- write Evidence, mutate `out/`, S3, registry artifacts, caches, or MLflow stores
- grant Double Play operational go, PRE_LIVE completion, First-Live readiness, or operator permission

**Displaying a decision does not authorize it.** **`live_authorization` remains false** in all pure-stack semantics; the dashboard must not override that with UI copy or badges.

## 3. Scope

**In scope:**

- recommended **host** for a future read-only surface (conceptual)
- panels and **display boundaries** per pure layer
- DTO/snapshot, route, template, and **data-source** boundaries for a future implementation slice
- explicit **non-selection** of certain existing apps/routes for v0 display of this stack
- alignment with the futures read-only market dashboard contract (display semantics)

**Out of scope:**

- concrete FastAPI path registration, HTML/CSS implementation
- adapter code, producer pipelines, or scanner wiring
- evidence or gate automation

## 4. Audit basis

This map is consistent with the static audit conclusion (read-only, no repo mutation at audit time):

- The **general WebUI** application (`src&#47;webui&#47;app.py`) is the **best initial host** for a future read-only Double Play pure-stack display slice.
- **`src&#47;live&#47;web&#47;app.py`** (Shadow/Paper run monitoring) is **not** the first target for pure-stack **model** display — different contract and runtime adjacency.
- **`src&#47;webui&#47;market_surface.py`** (Market Surface v0: OHLCV chart, optional Kraken public REST) must **not** be mixed with Double Play pure-stack display in v0 — different data lineage and exchange-touching path.

See also: [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) for pure module inventory.

## 5. Recommended display entrypoint

**Recommended v0 host (future implementation):** the **Peak Trade Web Dashboard** FastAPI app behind `src&#47;webui&#47;app.py` (started only under separate operator procedure; **not** started by this document).

A future slice should add a **dedicated** router or route namespace for Double Play pure-stack **display only**, rather than overloading unrelated panels (R&D, live sessions, market OHLCV).

## 6. Surfaces not selected for v0

| Surface | Reason to defer for Double Play pure-stack v0 display |
|---------|--------------------------------------------------------|
| `src&#47;live&#47;web&#47;app.py` | Run/snapshot monitoring semantics; not the pure DTO stack |
| `src&#47;webui&#47;market_surface.py` | OHLCV/Kraken/dummy lineage; must not imply Double Play authority |
| Knowledge POST paths | Mutation; unrelated |
| R&D experiment HTML/API | Evidence/report adjacency; unrelated to pure-stack labels |

## 7. Pure stack display panels

Future read-only UI may expose **separate panels** (or one consolidated snapshot view) for:

1. **Futures Input** — snapshot readiness / block reasons (data-only).
2. **State / Dynamic Scope** — side state, transition labels (non-runtime).
3. **Survival Envelope** — status / pre-authorization eligibility **as data** (not a simulation).
4. **Strategy Suitability** — projection class and pool flags (not activation).
5. **Capital Slot** — ratchet/release **decision labels** (not ledger or allocation).
6. **Composition** — `ELIGIBLE_MODEL_ONLY` / blocked / chop / kill-all **as model status** (not orders).

Each panel must show **source** (e.g. fixture path, “operator supplied”, future adapter id) and **timestamp** if available.

## 8. Futures Input display boundary

- May show: readiness status, block reasons, missing fields, ranking **as context**, freshness, non-authority labels.
- **Must not** imply: scanner run, exchange proof, selector choice, Top-N **trading** authority, or Live.
- **Displaying Top-20 or rank does not authorize trading.** Align with [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md).

## 9. State / Dynamic Scope display boundary

- May show: `SideState`, transition event summaries, scope-related **model** outputs.
- **Must not** imply: runtime state machine authority, hot-path switch permission, or Kill-All override by dashboard.

## 10. Survival Envelope display boundary

- May show: envelope status, blocked vs OK, key metric **labels** already computed offline.
- **Must not** imply: arithmetic kernel execution, path simulation, or backtest run from the dashboard.

## 11. Strategy Suitability display boundary

- May show: suitability class, pool flags, metadata presence.
- **Must not** imply: strategy activation, registry mutation, or “go” to trade.

## 12. Capital Slot display boundary

- May show: ratchet target, can_ratchet, release state, block reasons **as text**.
- **Must not** imply: allocation, capital movement, or that **displaying** release **performs** release. **Displaying capital-slot status does not allocate or release capital.**

## 13. Composition display boundary

- May show: composition status, block reasons, requested side vs outcome.
- **Must not** imply: order placement or session start. **Displaying composition status does not place orders.**

## 14. DTO / snapshot boundary

Future implementations should use a **versioned display snapshot** (conceptual name: **DoublePlayPureStackDisplaySnapshotV0**) that:

- contains only **serializable** fields derived from `src&#47;trading&#47;master_v2&#47;` outputs or **explicit fixtures**
- includes explicit `live_authorization: false` (or omits any live flag; never `true` from this path)
- never embeds raw exchange credentials or unfettered OHLCV payloads as mandatory fields for Double Play v0

Pure modules remain **I/O-free**; snapshot **assembly** for the dashboard belongs **outside** `master_v2` when implemented.

## 15. Route boundary

This document **does not** define production URLs. When implemented, routes should be **namespaced** (e.g. under a dedicated `/api/double_play/...` or `/double_play/...` prefix) and **GET-oriented** for v0 display.

No route defined here; **do not implement routes** as part of this docs slice.

## 16. Template / UI boundary

Templates under `templates&#47;peak_trade_dashboard&#47;` may later host a read-only page; v0 requires:

- prominent **no-live** / **non-authority** banner
- no control widgets that trigger scanner, session, or order flows from this view

## 17. Data-source boundary

**Fixture-first** is recommended:

- checked-in JSON fixtures and/or operator-supplied files with explicit provenance string
- no requirement in v0 for live market-data or scanner pipelines to render the pure stack

## 18. Runtime / scanner / exchange / evidence boundary

The dashboard display path must **not**:

- invoke scanners or selectors
- fetch market data or call exchanges **for the purpose of** proving Double Play pure-stack readiness
- write evidence or mutate operational stores

Operational producers may exist elsewhere; they are **not** authority surfaces for this display map.

## 19. Dashboard no-live boundary

A **no-live banner** (or equivalent persistent disclosure) is **required** on any page showing Double Play pure-stack decisions.

**Testnet and Live remain unauthorized** by this display map. Align display semantics with [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) where futures context appears.

## 20. Validation / future tests

When code exists, future tests may include:

- JSON schema or contract tests for **DoublePlayPureStackDisplaySnapshotV0**
- WebUI route tests asserting **no** POST side effects on read-only Double Play endpoints
- invariant: snapshot JSON never contains `live_authorization: true` for this path

This docs change: run `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot` as for sibling ops specs.

## 21. Implementation staging

1. **Docs** — this display map and cross-links (current slice).
2. **Fixture pack** (future) — static JSON under `tests/` or `docs` examples only if governed.
3. **Adapter** (future) — maps allowed inputs to display snapshot; **no** exchange inside `master_v2`.
4. **WebUI** (future) — new router + template; operator runbook for local only.

## 22. References

- [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) — future WebUI **GET** read-only JSON route boundary for this display DTO (docs-only; no implementation here).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — pure stack inventory and model boundaries.
- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md) — Futures Input Snapshot read model.
- [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — futures read-only dashboard display contract (F5).
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play trading-logic semantics; non-authority.
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) — PRE_LIVE navigation index.
