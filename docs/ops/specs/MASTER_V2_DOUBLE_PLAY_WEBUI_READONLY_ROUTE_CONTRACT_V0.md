---
title: "Master V2 Double Play WebUI Read-only Route Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-27"
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
- **test anchors** for the **read-only JSON route** (`TestClient` **authority-invariant** coverage; see §9) and **route-independent** **`snapshot_to_jsonable`** **JSON serialization** (see §9; Dashboard Display Map §20)
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

## 8. Producer adapter stack test anchors (non-authority)

This **read-only route** contract describes a **downstream display surface** only: HTTP serves JSON derived from the **pure** dashboard display DTO and the **static, fixture-backed** construction path in §7. It is **not** a producer, **not** a **provider**, **not** runtime integration, and **not** an **authority** surface.

For the **pure stack** regression story of **`FuturesProducerPacket` → `adapt_producer_packet_to_futures_input_snapshot` → readiness → composition → `build_dashboard_display_snapshot`**, see **test anchors** in [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) **§20** (and cross-links in [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) §11 and [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) §20). Those anchors name **`test_contract_32`–`test_contract_37`** in `tests/trading/master_v2/test_double_play_pure_stack_contract.py`, including:

- **Positive path:** producer packet through the adapter into the existing gates and **display-only** dashboard snapshot.
- **Fail-closed paths:** incomplete instrument metadata, incomplete provenance, perpetual/swap funding gaps — readiness and display panels stay in **non-authorizing** blocked or missing states as asserted in tests.
- **Runtime handle:** adapter blocks before snapshot creation; tests show an honest **display gap**, not fabricated data-ready labels.
- **Stripped flag:** producer candidate `live_authorization=True` is **not** propagated onto the snapshot candidate in the pure model; the stack stays **non-authorizing**.

**This WebUI route contract does not claim** — and those **test anchors** do not prove — **scanner** or operational **producer** integration, **market-data ingestion**, **provider** behavior beyond static fixtures, WebUI **HTML** or control UI, operational permission for Testnet or Live, permission to **trade**, or any external sign-off treated as execution permission. For **HTTP JSON surface** **authority-invariant test coverage** on this **read-only JSON route**, see **§9** (downstream of the pure model; does **not** replace [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) **§20**).

## 9. Read-only JSON route authority-invariant test anchors (non-authority)

**Test file:** `tests&#47;webui&#47;test_double_play_dashboard_display_json_route.py` — **non-authorizing** **authority-invariant test coverage** for the **read-only JSON route** (`GET &#47;api&#47;master-v2&#47;double-play&#47;dashboard-display.json`) using `TestClient(create_app())`. It guards the **downstream display surface** only; it does **not** prove operational **producer** wiring, **market-data ingestion**, WebUI **HTML** or control UI, Testnet or Live operational **readiness**, permission to **trade**, or any external sign-off treated as execution permission.

**Route-independent JSON serialization test anchor:** `tests&#47;trading&#47;master_v2&#47;test_double_play_dashboard_display.py` — **non-authorizing** **test anchors** for the same **`snapshot_to_jsonable`** **JSON serialization** mapping **without** HTTP or `TestClient`, summarized in [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) **§20** (full-stack snapshot, blocked survival / **display-blocked** path, empty snapshot; **JSON-native** values; **`json.dumps`**; exact key surfaces; **display-only** / **non-authorizing** flags; recursive forbidden keys). This **complements** the WebUI route **test anchors** above and **does not** replace the route-module AST guard, cache/header HTTP checks, or [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) **§20** producer-adapter **test anchors**.

**Linkage:** This route remains **downstream** of the **pure** dashboard DTO. Cross-module **pure stack** and producer-adapter anchors stay in [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) **§20** (`test_contract_32`–`37`). The WebUI tests below do **not** substitute for those anchors.

**Coverage (summary):**

- **Exact top-level key surface** — JSON object keys match the serialized snapshot contract only (no extra control fields).
- **Exact per-panel key surface** — each panel object exposes only the expected display fields.
- **Display-only top-level flags** — `display_only` true, `no_live_banner_visible` true; **`trading_ready`**, **`testnet_ready`**, **`live_ready`**, **`live_authorization`** remain **false** (explicit **safety** booleans, not permission to go operational).
- **Panel-level flags** — each panel keeps **`live_authorization`**, **`is_authority`**, **`is_signal`** false for the static fixture path.
- **Forbidden JSON keys** — recursive key scan rejects control / runtime / **provider** / **scanner** / **exchange** / session / credential-like key names in the payload tree (keys that are legitimate DTO safety flags are asserted false separately, not banned by name).
- **Route-module AST guard** — static parse of `double_play_dashboard_display_json_route_v0.py` forbids imports from scanner / **exchange** / session / **backtest** / network-style roots (e.g. `ccxt`, `requests`, `subprocess`, `src.exchange`) outside the allowed **`trading.master_v2`** surface.

## 10. JSON response boundary

**Payload:** JSON serialization of `DoublePlayDashboardDisplaySnapshot` and nested panel DTOs:

- Enum fields (e.g. panel status, overall status) serialize as **string values** (`.value`), not opaque integers.
- Tuples become JSON arrays; preserve field names consistent with the dataclass attributes.
- The response must remain **self-describing display data** only — no embedded executable content, no HTML in JSON fields unless already a documented display string from pure layers (prefer plain text summaries).

**Error behavior (implementation guidance):** prefer **500 with a safe error body** or **503** only for true dependency failure; do **not** fabricate `live_authorization: true` or flags that imply permission to trade to mask errors.

**Caching:** recommend **`Cache-Control: no-store`** on this JSON response for parity with other operator snapshot endpoints (see `tests&#47;test_live_status_snapshot_api.py`).

## 11. Optional template boundary

A future **HTML** page may render the same snapshot (Jinja under `templates&#47;peak_trade_dashboard&#47;`). **v0 contract prioritizes JSON.** Any HTML slice must:

- reuse the **same** display-only semantics
- not introduce CTAs that imply order placement, Live enablement, or scanner triggers
- not mix Double Play panels into `market_v0.html` or market API routes

## 12. Tests / TestClient boundary

**Present:** **`TestClient`** **authority-invariant** coverage for this route is documented in **§9** (`tests&#47;webui&#47;test_double_play_dashboard_display_json_route.py`). **Route-independent** **`snapshot_to_jsonable`** **JSON serialization** **test anchors** are documented in **§9** (`tests&#47;trading&#47;master_v2&#47;test_double_play_dashboard_display.py`) and cross-linked from the Dashboard Display Map **§20**.

**Future extensions (non-authoritative):** additional assertions may follow the same patterns (e.g. cache headers, expanded key hygiene) without changing **display-only** / **non-authorizing** semantics. Follow precedents in `tests&#47;test_live_status_snapshot_api.py` and `tests&#47;live&#47;test_execution_watch_api_v0.py`.

## 13. Imports that must be forbidden

Future route implementation **must not** import or transitively rely on:

- execution engines, order routers, allocation runtime
- exchange adapters, `ccxt`, or market-data fetchers for trading
- scanner drivers, selector pipelines, or workflow runners
- session starters for Paper, Shadow, Testnet, Live, bounded pilot
- evidence writers, artifact mutators, or S3 clients for operator evidence packs

**Allowed:** `fastapi` (router, responses), `trading.master_v2.double_play_*` **pure** modules, stdlib, typing.

## 14. Runtime / scanner / exchange / evidence boundary

The route **must not**:

- import scanner, exchange, session, runtime integration, or evidence surfaces
- fetch market data or call exchanges
- run scanners or scheduled selector jobs
- start or stop sessions
- write evidence or **`out&#47;`** artifacts
- allocate or release capital
- select futures or instruments for trading
- activate strategies or place orders

## 15. WebUI no-control boundary

The route **must not** become a **control endpoint**: no side effects, no toggles, no “enable”, no “submit”, no operator actions that change system state. **GET-only** for v0 reinforces this.

## 16. Dashboard no-live boundary

The dashboard response **must** communicate **no-live / display-only** semantics consistent with [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md):

- **Testnet and Live remain unauthorized** by this route.
- UI copy (future HTML) must not claim go-live, permission to trade, or scanner authority.

## 17. Fail-closed semantics

If pure inputs are missing or contradictory, the snapshot builder already encodes **DISPLAY_MISSING**, **DISPLAY_WARNING**, **DISPLAY_BLOCKED**, or **DISPLAY_ERROR** at panel level — the HTTP route **must not** “upgrade” those into success or permission states. **Fail closed** on authority: never emit `live_authorization: true` for this v0 path.

## 18. Validation / future tests

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

**Route module:** `pytest` coverage for the JSON handler is anchored in **§9**; extend tests in future PRs if governance adds fields or routes.

## 19. Implementation staging

1. **Docs** — this contract + cross-links (current slice).
2. **Router module** (implemented) — GET JSON handler + `include_router` in `create_app()`; keep **read-only** semantics.
3. **Tests** — **`TestClient`** **authority-invariant** anchors in **§9**; extend if JSON shape evolves.
4. **Optional HTML** (future) — template page consuming the same snapshot payload.

## 20. References

- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) — producer handoff boundary; **§20** **test anchors** for **`test_contract_32`–`37`** (**non-authority**).
- [MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md) — **parked** runtime-producer → **downstream display** **prerequisites** (**non-authorizing** **parking map**).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) — display panels and DTO vocabulary (docs-only).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — pure stack inventory vs runtime.
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) — PRE_LIVE reading index; peer context only.
- [FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md](FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — style reference for read-only dashboard contracts (different surface).
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play trading-logic semantics; non-authority for display.
