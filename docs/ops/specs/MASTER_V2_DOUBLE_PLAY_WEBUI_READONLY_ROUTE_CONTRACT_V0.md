---
title: "Master V2 Double Play WebUI Read-only Route Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0"
---

# Master V2 Double Play WebUI Read-only Route Contract v0

## 1. Purpose

This contract defines the **future** boundary for a **read-only** WebUI HTTP route that **displays** the Master V2 / Double Play **Dashboard Display DTO** (`DoublePlayDashboardDisplaySnapshot` from `build_dashboard_display_snapshot`), without granting **control authority**, trading permission, or Live/Testnet enablement.

It exists to prevent confusion between:

```text
GET read-only dashboard display (labels / snapshot only)
authorizing trading, Testnet, Live, allocation, sessions, scanner runs, or exchange interaction
```

**This document is docs-only.** It does **not** register routes, implement handlers, start the WebUI, add templates, or change code or tests.

## 2. Non-authority note

This file is **non-authorizing**. It does not:

- implement or merge FastAPI routes, routers, or templates
- start the WebUI, Docker, uvicorn, or any server
- fetch market data, call exchanges, or run scanners
- start Paper, Shadow, Testnet, Live, bounded-pilot, or execution sessions
- write Evidence, mutate `out&#47;`, S3, registry artifacts, caches, MLflow stores, or experiment stores
- grant Double Play operational go, PRE_LIVE completion, First-Live readiness, or operator permission

**Displaying a snapshot does not authorize it.** Responses must preserve **display-only** semantics: **`live_authorization` remains false**, **`display_only` true**, **`no_live_banner_visible` true**, and **`trading_ready` / `testnet_ready` / `live_ready` false** for the v0 fixture-backed path described here.

## 3. Scope

**In scope (this contract):**

- target application and **attachment pattern** (`create_app()` on the general WebUI)
- **HTTP shape** for a future v0 route (GET-only, read-only)
- **DTO source strategy** for v0 (pure fixtures; no runtime producer requirement)
- **JSON response boundary** and caching guidance
- **forbidden imports** and operational boundaries
- **test placement** guidance (for a future slice; no tests in this doc PR)
- **implementation staging** (order of future work)

**Out of scope:**

- concrete handler code, OpenAPI registration details, or template HTML/CSS
- wiring operational scanners, ETL, or session registry into the DTO
- evidence packs, gate automation, or operator signoff procedures

## 4. Audit basis

This contract aligns with the static **WebUI route placement audit** (read-only; no repo mutation at audit time):

- **Target app:** `src&#47;webui&#47;app.py` — **`create_app()`** registers multiple `include_router` calls and many inline routes; this is the **preferred host** for a future Double Play read-only display slice.
- **Do not attach** Double Play v0 display to `src&#47;webui&#47;market_surface.py` — that surface is **Kraken/OHLCV/dummy** lineage and a different contract ([FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md)).
- **Do not attach** Double Play v0 display to `src&#47;live&#47;web&#47;app.py` — that is a **separate** Live/paper run WebUI with different semantics.
- **Useful precedent:** JSON snapshot + `TestClient(create_app())` patterns (e.g. `tests&#47;test_live_status_snapshot_api.py`).

## 5. Target app and placement

**Target application (future implementation):** the Peak Trade **general WebUI** behind `src&#47;webui&#47;app.py`.

**Placement (recommended):**

1. Add a **dedicated** router module under `src&#47;webui&#47;` (exact filename is a future implementation choice), exporting an `APIRouter` with **GET-only** handlers.
2. Register that router inside **`create_app()`** via `app.include_router(...)`, alongside existing read-only routers (e.g. execution watch, health), **not** inside `market_surface.create_market_router`.

**Do not start the WebUI from this document.** **Do not implement the route in this document.**

## 6. Route shape

**Method:** **GET only** for v0. No POST, PUT, PATCH, or DELETE on this contract path.

**Suggested path (v0, canonical for planning):**

```text
GET /api/master-v2/double-play/dashboard-display.json
```

Rationale: avoids collision with `api&#47;r_and_d`, `api&#47;live`, execution-watch, and `api&#47;market` namespaces. Final path may be adjusted in implementation if governance prefers, but must remain under a **clear Master V2 / Double Play** prefix.

**Query parameters (v0):** none required. Future versions must not add parameters that select exchanges, enable Live, trigger scanners, or mutate state.

## 7. DTO source strategy

**v0 (fixture-backed):** the handler should obtain inputs only from **pure** construction paths that mirror:

- `tests&#47;trading&#47;master_v2&#47;test_double_play_dashboard_display.py`
- `tests&#47;trading&#47;master_v2&#47;test_double_play_pure_stack_contract.py`

i.e. call `build_dashboard_display_snapshot(...)` with **keyword arguments** supplying pure decisions produced by existing `trading.master_v2.double_play_*` evaluators — **no** scanner, **no** session registry, **no** evidence writers.

**Non-goal for v0:** producing the snapshot from “live” runtime decisions inside the WebUI process. If ever required, that is a **separate** governed slice with its own contract and gates.

## 8. JSON response boundary

**Payload:** JSON serialization of `DoublePlayDashboardDisplaySnapshot` and nested panel DTOs:

- Enum fields (e.g. panel status, overall status) serialize as **string values** (`.value`), not opaque integers.
- Tuples become JSON arrays; preserve field names consistent with the dataclass attributes.
- The response must remain **self-describing display data** only — no embedded executable content, no HTML in JSON fields unless already a documented display string from pure layers (prefer plain text summaries).

**Error behavior (implementation guidance):** prefer **500 with a safe error body** or **503** only for true dependency failure; do **not** fabricate `live_authorization: true` or trading-ready flags to mask errors.

**Caching:** recommend **`Cache-Control: no-store`** on this JSON response for parity with other operator snapshot endpoints (see `tests&#47;test_live_status_snapshot_api.py`).

## 9. Optional template boundary

A future **HTML** page may render the same snapshot (Jinja under `templates&#47;peak_trade_dashboard&#47;`). **v0 contract prioritizes JSON.** Any HTML slice must:

- reuse the **same** display-only semantics
- not introduce CTAs that imply order placement, Live enablement, or scanner triggers
- not mix Double Play panels into `market_v0.html` or market API routes

## 10. Tests / TestClient boundary

**Out of scope for this docs-only PR:** adding tests.

**Future slice (non-authoritative naming):** add tests under `tests&#47;` using `TestClient(create_app())`, asserting e.g.:

- `GET` returns 200 and parseable JSON
- top-level flags: `display_only`, `no_live_banner_visible`, and absence of trading readiness
- **no** POST side effects on adjacent paths from this test module

Follow patterns in `tests&#47;test_live_status_snapshot_api.py` and `tests&#47;live&#47;test_execution_watch_api_v0.py`.

## 11. Imports that must be forbidden

Future route implementation **must not** import or transitively rely on:

- execution engines, order routers, allocation runtime
- exchange adapters, `ccxt`, or market-data fetchers for trading
- scanner drivers, selector pipelines, or workflow runners
- session starters for Paper, Shadow, Testnet, Live, bounded pilot
- evidence writers, artifact mutators, or S3 clients for operator evidence packs

**Allowed:** `fastapi` (router, responses), `trading.master_v2.double_play_*` **pure** modules, stdlib, typing.

## 12. Runtime / scanner / exchange / evidence boundary

The route **must not**:

- import scanner, exchange, session, runtime integration, or evidence surfaces
- fetch market data or call exchanges
- run scanners or scheduled selector jobs
- start or stop sessions
- write evidence or **`out&#47;`** artifacts
- allocate or release capital
- select futures or instruments for trading
- activate strategies or place orders

## 13. WebUI no-control boundary

The route **must not** become a **control endpoint**: no side effects, no toggles, no “enable”, no “submit”, no operator actions that change system state. **GET-only** for v0 reinforces this.

## 14. Dashboard no-live boundary

The dashboard response **must** communicate **no-live / display-only** semantics consistent with [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md):

- **Testnet and Live remain unauthorized** by this route.
- UI copy (future HTML) must not claim go-live, permission to trade, or scanner authority.

## 15. Fail-closed semantics

If pure inputs are missing or contradictory, the snapshot builder already encodes **DISPLAY_MISSING**, **DISPLAY_WARNING**, **DISPLAY_BLOCKED**, or **DISPLAY_ERROR** at panel level — the HTTP route **must not** “upgrade” those into success or permission states. **Fail closed** on authority: never emit `live_authorization: true` for this v0 path.

## 16. Validation / future tests

**This docs PR validation** (operator / CI):

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
uv run python scripts/ops/validate_docs_token_policy.py --changed --base origin/main
```

If supported:

```bash
bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Future implementation PR:** add `pytest` for the new route module; run `ruff` on touched Python. **Not part of this contract PR.**

## 17. Implementation staging

1. **Docs** — this contract + cross-links (current slice).
2. **Router module** (future) — GET JSON handler + `include_router` in `create_app()`.
3. **Tests** (future) — `TestClient` JSON assertions + cache header if required.
4. **Optional HTML** (future) — template page consuming the same snapshot payload.

## 18. References

- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) — display panels and DTO vocabulary (docs-only).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — pure stack inventory vs runtime.
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) — PRE_LIVE reading index; peer context only.
- [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — style reference for read-only dashboard contracts (different surface).
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play trading-logic semantics; non-authority for display.
