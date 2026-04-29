---
title: "Master V2 Futures Class A Capability Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-29"
docs_token: "DOCS_TOKEN_MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0"
---

# Master V2 Futures Class A Capability Contract v0

## 1. Purpose and status

This file is a **docs-only** **capability contract** with explicit **non-claims**. It records what the **current** Class A Shadow/Paper GitHub Actions probe demonstrates versus what would be required for a **hypothetical** **Futures Class A** bounded probe — **without** granting **non-authorizing** permission to trade, run Testnet or Live, or change operational posture.

This contract:

- is **docs-only** and **non-authorizing**,
- introduces **no** runtime wiring, code, workflow, or config change by its existence alone,
- does **not** enable Testnet or Live,
- does **not** call exchanges, private APIs, AWS, S3, or rclone,
- does **not** alter the **current** Class A **BTC/EUR** spot-like workflow (`.github&#47;workflows&#47;class-a-shadow-paper-scheduled-probe-v1.yml`).

Operational Class A runs (manual or guarded schedule) remain governed by their **separate** workflow and repository settings; this document **does not** dispatch or start them.

## 2. Current Class A baseline (spot infrastructure smoke)

The **current** Class A probe on **`main`**:

- uses **`workflow_dispatch`** and a **guarded** `schedule` (repository variable gate) on the workflow above,
- runs a **bounded** paper-mode session via `scripts&#47;run_shadow_paper_session.py` (typical **BTC/EUR**, **ma_crossover**, short duration, artifact upload),
- has produced **success** conclusions for **manual** and **scheduled** runs with downloadable artifacts,
- artifacts include **`meta.json`** and typically **`events.parquet`** (or CSV per logging config), **mode paper**,

and is **useful** as:

- **spot infrastructure smoke** for CI, uv install, public market-data polling, run logging, and artifact chain discipline.

It is **not** a **Futures** or **Perp** proof: the runner and provider path are **spot-oriented** (see §3–§4). **BTC/EUR Class A** artifacts **must not** be read as **Futures Class A prerequisite** satisfaction or as **non-claims** violations pretending they are Perp-ready.

## 3. Capability classification table

Cross-layer labels (read-only assessment; **non-authorizing**):

| Layer | Classification |
|-------|----------------|
| Runner (`scripts&#47;run_shadow_paper_session.py` + Kraken live candle source) | **SPOT_ONLY** |
| Paper/Shadow execution loop (`ShadowPaperSession` + paper order path) | **FUTURES_ADJACENT_BUT_INCOMPLETE** |
| WP1B `src&#47;execution&#47;paper&#47;engine.py` engine | **SPOT_SIM_ONLY** |
| Master V2 Futures DTO / Producer (`trading.master_v2.double_play_futures_input*`) | **PURE_DTO_READY**; binding to Shadow runner: **RUNTIME_NOT_WIRED** |
| Provider path used by Class A | **SPOT_PUBLIC_ONLY** |

**pure DTO ready** means the read-model and adapter tests can evaluate **futures-shaped** packets **without** exchange I/O. **runtime not wired** means those surfaces are **not** connected to `scripts&#47;run_shadow_paper_session.py` or the Class A workflow today.

## 4. Futures Class A gap map (top 10)

Before any **Futures Class A** **runtime** probe, these **prerequisites** remain open (order is not a priority ranking):

1. **Instrument / symbol convention** — Perp/Future vs **spot** naming and exchange mapping (not only `BTC&#47;EUR`).
2. **Futures public market-data feed / market type** — configurable **market type** and correct **public** endpoint (not assumed spot OHLC only).
3. **Contract size / tick / step** — sizing math for notionals vs contracts.
4. **Margin and leverage model** — account state beyond **spot** cash + scalar position.
5. **Funding (perpetuals)** — ingest or proxy rules and PnL semantics if Perp is in scope.
6. **Liquidation / maintenance margin** — absent from current Shadow paper loop.
7. **Short semantics** — **spot sell** vs **margin short** / hedge semantics must be explicit.
8. **Mark / index / last** — futures price references vs single OHLC **close** proxy.
9. **Futures evidence fields** — `meta.json` / events should record **market_type**, instrument metadata pointers, and derivatives context if claimed.
10. **Config / safety gates** — prevent **spot/futures** mixups and accidental non-paper modes.

## 5. Non-claims / prohibited interpretations

Readers **must not** treat **BTC/EUR Class A** as proof of:

- **Futures** or **Perp** / **swap** readiness,
- **margin**, **leverage**, **funding**, or **liquidation** handling,
- **Master V2 Double Play** operational **runtime** wiring (DTOs may be **pure DTO ready** while **runtime not wired**),
- **Testnet** or **Live** readiness,
- **trading authority** or external **approval** to trade,
- justification to **retarget** the **current** scheduled workflow to **Futures** symbols **immediately** without a **separate** governed slice.

This section is **non-claims** language only; it does not accuse past runs of misuse — it **constrains** future **evidence** interpretation.

## 6. Safe future route

- **Retain** the **current** **spot** Class A workflow as **spot infrastructure smoke** (bounded, paper, public data, artifacts).
- **Offline futures paper accounting v0 (pure-model anchor):** `src&#47;execution&#47;paper&#47;futures_accounting.py` is a **side-effect-free**, **deterministic** kernel for notional, linear long/short PnL, margin **estimates**, funding **placeholder**, and a **conservative** liquidation-proximity label — **not** venue-accurate liquidation, **not** wired to the Class A runner or WP1B hot path, **non-authorizing**, and **does not** close §4–§8 or Futures Class A by itself.
- Keep **next Futures work** in **docs** / **pure-model** / **read-only** lanes first until §4 gaps have **explicit** contracts and tests.
- Any **first** **Futures Class A** **runtime** candidate should be **separate** from the **spot** workflow (new workflow or gated path), with its own **non-live** / **no-testnet** guards and **evidence schema**.
- Require, before such a probe: **Futures instrument metadata** contract alignment, **public read-only** provider contract, a **futures paper accounting** model (even if minimal), **risk** gates, and **evidence** fields — none of which are satisfied by **BTC/EUR** Class A alone.

## 7. WP1B / Futures Accounting adapter seam planning v0

This subsection is **seam planning only** (hypothetical adapter boundary). It **does not** implement wiring, **does not** change `PaperExecutionEngine` or WP1B behavior, and **does not** grant authority.

### 7.1 Current boundary

- `src&#47;execution&#47;paper&#47;futures_accounting.py` is a **pure / offline** accounting kernel (deterministic primitives; not venue-accurate liquidation).
- WP1B (`src&#47;execution&#47;paper&#47;engine.py`) remains **SPOT_SIM_ONLY** and is **not** wired to Futures Accounting v0 today.
- `tests&#47;execution&#47;paper&#47;test_paper_engine_futures_seam_v0.py` **characterizes** import/runtime separation: paper-engine modules do not import the futures accounting kernel, and the kernel does not import engine/broker/runtime stacks.
- Accounting regression and projection coverage live in `tests&#47;execution&#47;paper&#47;test_futures_accounting_v0.py` and `tests&#47;execution&#47;paper&#47;test_futures_accounting_invariants_v0.py` — **tests-only**; **non-authorizing**.

### 7.2 Hypothetical future adapter inputs (preconditions only)

If a **future** governed adapter were introduced (**not** part of current `main`), it would need upstream to supply at minimum:

- **F1** instrument metadata projected onto `FuturesInstrumentSpec` (subset only; full **F1** is not required in the v0 kernel).
- **F1** margin metadata projected onto `FuturesMarginSpec`.
- **F2** semantics: an **explicit mark-price scalar** chosen by an upstream selector — the kernel does not choose last vs index vs mark (see [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)).
- Position state: side, quantity, entry price, mark price, plus realized/funding/fees as carried by the adapter.
- **Wallet / equity** context where liquidation-proximity estimates are required (`estimate_liquidation_proximity_v0` is a conservative placeholder).
- **Funding** rate or payment source when funding PnL is applied.
- **Fee policy** (e.g. bps-on-notional) aligned with simulation bounds.

### 7.3 Hypothetical future adapter outputs (preconditions only)

Outputs already expressible from the v0 API surface (still **not** wired to WP1B today):

- Notional (`notional_value`).
- Initial and maintenance margin requirements (`initial_margin_required`, `maintenance_margin_required`).
- Unrealized PnL (`unrealized_pnl`).
- Realized PnL on reduce/close (`reduce_position`, `realize_pnl_on_close`).
- Funding PnL (`apply_funding_payment`, `funding_payment_quote`).
- Fees (`apply_fee_on_notional` or explicit `fee_quote` on close paths).
- Liquidation proximity v0 (`estimate_liquidation_proximity_v0`).

Whether a **stable snapshot DTO** wraps these values is a **separate** design decision for a future slice; this contract **does not** mandate one.

### 7.4 Preconditions before any wiring

Before any change under `src&#47;execution&#47;` that connects WP1B to Futures Accounting v0:

- A **proven** upstream path supplies **mark price** with **F2**-consistent provenance and explicit price-type discipline.
- F1/F2 projection into accounting specs remains **deterministic** and **test-backed** (see projection tests in `test_futures_accounting_v0.py`).
- A **snapshot/DTO** choice is made **if** it reduces adapter ambiguity; otherwise primitive outputs remain explicit.
- **Characterization / adapter tests** are added **before** behavioral implementation (extend `test_paper_engine_futures_seam_v0.py` or add adjacent tests); **`docs_truth_map.yaml`** execution-layer rules require **paired** canonical doc updates whenever code under `src&#47;execution&#47;` changes.
- **No** additional Master V2 / Double Play **runtime** authority, **no** Live/Testnet approval, **no** bypass of Scope/Capital, Risk/KillSwitch, or Execution/Live Gates.

### 7.5 Explicit non-claims

- **No** `PaperExecutionEngine` wiring on **`main`** from this planning text alone.
- **No** exchange or provider implementation obligation.
- **No** Futures Class A **readiness** from documentation or pure tests alone.
- **No** Testnet or Live permission.
- **No** implied derogation from Master V2 / Double Play governance, Scope/Capital, Risk/KillSwitch, or staged execution enablement.

## 8. Minimal prerequisites before Futures Class A runtime (checklist)

A future **Futures Class A** bounded probe should not be scheduled until **at least** the following are specified and reviewed (docs + tests as appropriate):

- **Futures symbol convention** and exchange mapping.
- **Market type** field and feed selection (future / perpetual / swap vs spot).
- **Instrument metadata DTO** alignment (peer: futures instrument metadata specs in `docs&#47;ops&#47;specs&#47;`).
- **Funding / readiness data** policy for Perp, if Perp is in scope.
- **Margin / leverage** configuration semantics (simulation bounds).
- **Contract sizing** rules (tick, step, multiplier).
- **Long/short position model** distinct from **spot** inventory where needed.
- **Futures risk limits** (exposure, notional caps) in the simulation loop.
- **Evidence / log fields** for futures context in **`meta.json`** and events.
- **Explicit non-live / no-testnet** guards and **no private API** default for Class-A-style probes.

## 9. References

**Master V2 / Double Play (pure, non-authority):**

- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md) — Futures Input Snapshot vocabulary; **data-only**.
- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) — producer adapter boundary; **§20** test anchors.
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — **pure stack** vs runtime adjacency.
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) — **downstream display** map.
- [MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_RUNTIME_PRODUCER_DASHBOARD_PREREQUISITE_PARKING_MAP_V0.md) — **parked** runtime producer prerequisites.
- [MASTER_V2_DOUBLE_PLAY_PURE_DISPLAY_BASELINE_CLOSEOUT_INDEX_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_DISPLAY_BASELINE_CLOSEOUT_INDEX_V0.md) — **pure display baseline** reading order.

**Runtime architecture (context, not permission):**

- [REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md](REAL_MARKET_247_RUNTIME_ARCHITECTURE_V1.md) — high-level runtime narrative; **non-authorizing** consumption only.

**Futures capability — F1/F2 peer contracts (gap-owner navigation only):**

These entries are **read-order / ownership pointers** for themes named in §4–§8 (instrument identity, `market_type`, sizing, public market-data shape, mark/index/last, freshness, provenance). They **do not** close Futures Class A gaps by reference alone, **do not** authorize Testnet or Live, **do not** wire runtime or providers, and **do not** bypass Master V2 / Double Play, Scope/Capital, Risk/KillSwitch, or Execution Gates.

- [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) — **F1** instrument metadata contract (docs-only): symbol and exchange-facing identity, explicit `market_type`, contract size / tick / step / lot expectations, and related fields — **not** runtime implementation.
- [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) — **F2** market-data provenance contract (docs-only): data identity, last/mark/index boundaries where applicable, funding availability, freshness and source metadata — **not** Fetch execution or dashboard wiring.
- [FUTURES_CAPABILITY_SPEC_V0.md](FUTURES_CAPABILITY_SPEC_V0.md) — staged futures capability program (**F1**, **F2**, later stages); use for **inventory and exit-criteria context** only — **not** evidence of completion.

**Navigation (peer index):**

- [MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) — PRE_LIVE navigation index; **no** implication of First-Live readiness from this contract.

**Test anchors (pure `master_v2`; not Shadow runner integration):**

- `tests&#47;trading&#47;master_v2&#47;test_double_play_futures_input_producer.py`
- `tests&#47;trading&#47;master_v2&#47;test_double_play_pure_stack_contract.py`
- `tests&#47;trading&#47;master_v2&#47;test_double_play_dashboard_display.py`
