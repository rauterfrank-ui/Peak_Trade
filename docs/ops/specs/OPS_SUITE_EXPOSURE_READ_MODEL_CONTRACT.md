# OPS Suite — Exposure Read Model Contract

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Canonical read-model contract for exposure_state in OPS Suite / Ops Cockpit
docs_token: DOCS_TOKEN_OPS_SUITE_EXPOSURE_READ_MODEL_CONTRACT

## Scope
This document defines the canonical schema and real-signal mapping for `exposure_state` in the OPS Suite Dashboard. It is a read-model specification only. No execution authority is introduced.

## Non-Goals
- no execution authority
- no bypass of risk gates or caps
- no live-trading enablement
- no broker/exchange integration in this contract

## Context
- **Confirmed gap (2026-03-12):** `exposure_state` in Ops Cockpit has no real-signal mapping; it is a placeholder.
- **Baseline:** main@b78522b8
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC Phase 3, RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE

---

## 1. Canonical Schema: exposure_state

### 1.1 Required Fields

| Field | Type | Allowed Values | Description |
|-------|------|----------------|-------------|
| `summary` | string | `no_live_context` \| `ok` \| `warn` \| `critical` \| `unknown` | Operator-facing exposure summary |
| `treasury_separation` | string | `enforced` \| `unknown` \| `degraded` | Treasury separation posture |
| `caps_configured` | list | Array of cap objects | Configured exposure caps (see 1.2) |
| `risk_status` | string | `ok` \| `warn` \| `critical` \| `unknown` | Risk status derived from evidence |

### 1.2 Cap Object (when caps_configured populated)

| Field | Type | Description |
|-------|------|-------------|
| `limit_id` | string | e.g. `max_total_exposure`, `max_symbol_exposure` (aligned with strategy_risk_telemetry) |
| `cap_value` | number | Cap in ccy units |
| `ccy` | string | Currency (e.g. EUR, BTC) |
| `source` | string | `config` \| `runtime` \| `unknown` |

### 1.3 Optional Fields (future)

| Field | Type | Description |
|-------|------|-------------|
| `observed_exposure` | number | Observed gross exposure (ccy units) when real signal available |
| `observed_ccy` | string | Currency of observed exposure |
| `strategy_exposures` | list | Per-strategy exposure when multi-strategy |
| `last_updated_utc` | string | ISO8601 timestamp of last real-signal read |
| `data_source` | string | `prometheus` \| `telemetry_log` \| `session_metrics` \| `none` |

---

## 2. Real-Signal Mapping

### 2.1 Existing Real Signals

| Source | Metric / Location | Writer | Labels / Shape |
|--------|------------------|--------|----------------|
| strategy_risk_telemetry | `peaktrade_strategy_position_gross_exposure{strategy_id, ccy}` | LiveSessionRunner, ShadowPaperSession | Gauge, abs(notional) |
| strategy_risk_telemetry | `peaktrade_risk_limit_utilization{limit_id}` | Risk layer | Gauge 0..1 |
| strategy_risk_telemetry | `peaktrade_risk_blocks_total{reason}` | Risk layer | Counter |
| config | Risk caps (max_total_exposure etc.) | config.toml / risk config | Static |

### 2.2 Mapping Rules

| exposure_state field | Real signal | Fallback when no signal |
|----------------------|-------------|-------------------------|
| `summary` | Derived from observed_exposure vs caps | `no_live_context` |
| `treasury_separation` | From guard_state / policy (no direct telemetry) | `enforced` or `unknown` |
| `caps_configured` | From config / risk layer | `[]` |
| `risk_status` | From peaktrade_risk_limit_utilization, peaktrade_risk_blocks_total | `unknown` |
| `observed_exposure` | Sum of peaktrade_strategy_position_gross_exposure | omit |

### 2.3 Summary Derivation (when real signal available)

| Condition | summary |
|-----------|---------|
| No live context / no scrape | `no_live_context` |
| observed &lt; cap, utilization &lt; 0.8 | `ok` |
| observed &gt;= cap * 0.8 or utilization &gt;= 0.8 | `warn` |
| observed &gt;= cap or blocks &gt; 0 | `critical` |
| Data stale or source error | `unknown` |

---

## 3. Data Source Options

### 3.1 Option A: Prometheus Scrape

- **Endpoint:** Live web app `/metrics` (uses default prometheus REGISTRY; includes strategy_risk_telemetry)
- **Pros:** Real-time, already written by Live/Shadow sessions
- **Cons:** Ops Cockpit is stateless; requires scrape target or in-process registry access
- **Architecture:** Ops Cockpit must either (a) run in same process as live app, or (b) scrape external /metrics, or (c) use shared multiproc dir (PEAKTRADE_METRICS_MODE=B)

### 3.2 Option B: Telemetry Logs

- **Location:** `telemetry_root` (e.g. `logs/execution`)
- **Pros:** File-based, audit-friendly, no runtime dependency
- **Cons:** Requires structured log format for exposure; may need new log sink
- **Architecture:** Ops Cockpit reads parsed log files; freshness from mtime

### 3.3 Option C: Session Metrics (live_panel_data)

- **Source:** `session.metrics` (total_notional, exposure)
- **Pros:** Already aggregated in live panel
- **Cons:** Only when live session active; tight coupling to session lifecycle
- **Architecture:** Ops Cockpit would need session context; not suitable for stateless truth-first mode

### 3.4 Option D: Placeholder (current)

- **Behavior:** Hardcoded `no_live_context`, `unknown`
- **Use when:** No live context; operator uses runbooks + manual checks

### 3.5 Decision Criteria (to be resolved before implementation)

- Ops Cockpit deployment model: standalone vs. co-located with live app
- Operator workflow: real-time vs. post-hoc review
- Audit requirements: file-based evidence vs. Prometheus scrape
- RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE: requires "observed exposure vs intended cap" — implies Option A or B for pilot phase

---

## 4. Runbook Alignment

RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE requires:

| Requirement | exposure_state support |
|-------------|------------------------|
| confirm current exposure vs bounded pilot caps | `observed_exposure`, `caps_configured` |
| verify position truth and recent fills | Out of scope (evidence_state, reconciliation) |
| observed exposure | `observed_exposure` when data source available |
| intended cap | `caps_configured` |

This contract enables the runbook once a data source is chosen and implemented.

---

## 5. Implementation Prerequisites

Before opening an implementation branch for exposure mapping:

1. **Data source decision:** Resolve Option A/B/C per deployment model.
2. **Registry alignment:** If Option A — clarify whether Ops Cockpit can read default prometheus REGISTRY or needs scrape.
3. **Backward compatibility:** `summary: no_live_context` remains valid when no real signal; UI must not assume `observed_exposure` present.
4. **Tests:** Extend `test_exposure_state_section_present` for real-signal paths when implemented.

---

## 6. References

- `src/webui/ops_cockpit.py` — current exposure_state placeholder
- `src/obs/strategy_risk_telemetry.py` — real signals
- `docs/ops/specs/OPS_SUITE_DASHBOARD_VNEXT_SPEC.md` — Phase 3
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md`
- `docs/ops/runbooks/RUNBOOK_OPS_SUITE_DASHBOARD_VNEXT_PLAN.md` — Phase B
