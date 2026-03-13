# OPS Suite — Policy State Real-Signal Review (Read-Only)

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Read-only review of policy_state real-signal gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_POLICY_STATE_REVIEW

## Scope
This document is a **read-only review** of `policy_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends real-signal mapping options for future implementation.

## Baseline
- **main@a8dcbadc**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, operator_state (config + kill_switch hardened), guard_state (enabled/armed/dry_run from config)

---

## 1. Current policy_state Implementation

### 1.1 Schema (ops_cockpit.py ~439–448)

| Field | Current Source | Real Signal? |
|-------|----------------|--------------|
| `action` | Hardcoded `"NO_TRADE"` | **Placeholder** |
| `confirm_token_required` | `guard_state["confirm_token_required"]` | **Placeholder** — always True |
| `enabled` | `guard_state["enabled"]` | **Hardened** — from config |
| `armed` | `guard_state["armed"]` | **Hardened** — from config |
| `dry_run` | `guard_state["dry_run"]` | **Hardened** — from config |
| `blocked` | `(not enabled) or (not armed)` | **Partial** — inputs hardened, logic correct |
| `summary` | blocked / armed | **Partial** — does not consider kill_switch |

### 1.2 guard_state Inheritance

After PR #1786, `guard_state` provides:
- `enabled`, `armed`, `dry_run` from EnvironmentConfig (config)
- `kill_switch_active` from state file
- `confirm_token_required` = True (hardcoded)

`policy_state` inherits enabled/armed/dry_run/blocked/summary from guard_state. It does **not** include `kill_switch_active` and does **not** use it for `action` or `summary`.

### 1.3 OPS_SUITE_DASHBOARD_VNEXT_SPEC Expectations

Go / No-Go view (Section 2):
- policy outcome
- gating blockers
- readiness summary
- escalation signals

Policy / Governance view (Section 6):
- current policy action
- confirm-token requirement
- audit/evidence status

---

## 2. Gap Analysis

### 2.1 confirm_token_required

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `True` | No derivation from config |
| Real signal candidate | `EnvironmentConfig.require_confirm_token` | `environment.require_confirm_token` in config |

**Data source:** `get_environment_from_config()` already loads config; `require_confirm_token` is available.

**Recommendation:** Add `_config_confirm_token_required` to the config-load block (same as enabled/armed/dry_run). Set `guard_state["confirm_token_required"] = _config_confirm_token_required`. Fallback: `True` (safe default).

### 2.2 action

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `"NO_TRADE"` | No derivation from gating state |
| Spec | "current policy action" | Should reflect effective policy |

**Recommendation:** Derive `action` from blocked state:
- When `blocked` or `kill_switch_active`: `"NO_TRADE"`
- When `enabled` and `armed` and not `kill_switch_active`: `"TRADE_READY"` (or keep `"NO_TRADE"` in Phase 71; spec allows "policy outcome" semantics)

**Minimal option:** Keep `"NO_TRADE"` when blocked; add `"TRADE_READY"` only when enabled+armed+not kill_switch. Low risk; improves clarity.

### 2.3 summary / blocked — kill_switch not considered

| Aspect | Current | Gap |
|--------|---------|-----|
| blocked | `(not enabled) or (not armed)` | Does not include kill_switch_active |
| summary | blocked → "blocked", else "armed" | When enabled+armed but kill_switch_active, shows "armed" (misleading) |

**Observation:** When kill_switch is active, the effective policy is "no trade". `policy_state.summary = "armed"` would be incorrect.

**Recommendation:** Extend blocked logic:
- `blocked` = `(not enabled) or (not armed) or kill_switch_active`
- `summary` = "blocked" when blocked, else "armed"

This aligns with `incident_state` and `operator_state`, which already use `_kill_switch_active` for their blocked/attention logic.

### 2.4 Optional: kill_switch_active in policy_state

| Aspect | Current | Gap |
|--------|---------|-----|
| policy_state | No `kill_switch_active` field | Spec mentions "kill-switch posture" in Go/No-Go |

**Recommendation:** Optional. `incident_state` and `operator_state` already expose kill_switch_active. Adding it to policy_state would improve consistency. Defer if minimal scope preferred.

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Relevance |
|--------|----------|-----------|
| `get_environment_from_config` | `src&#47;core&#47;environment.py` | require_confirm_token |
| `guard_state` | ops_cockpit | kill_switch_active already present |
| Config load block | ops_cockpit | Already runs before guard_state |

### 3.2 Recommended Mapping (for future PR)

| policy_state field | Option | Real signal | Fallback |
|--------------------|--------|-------------|----------|
| confirm_token_required | Primary | `EnvironmentConfig.require_confirm_token` | True |
| blocked | Primary | `(not enabled) or (not armed) or kill_switch_active` | True |
| summary | Primary | "blocked" when blocked, else "armed" | "blocked" |
| action | Primary | "NO_TRADE" when blocked, "TRADE_READY" when armed | "NO_TRADE" |
| kill_switch_active | Optional | Add field, reuse `guard_state["kill_switch_active"]` | — |

### 3.3 Order of Operations

- Extend config-load block: add `_config_confirm_token_required = env_config.require_confirm_token` (default True).
- Set `guard_state["confirm_token_required"] = _config_confirm_token_required`.
- policy_state.blocked: add `or guard_state["kill_switch_active"]` to current expression.
- policy_state.summary: already uses blocked; will improve automatically.
- policy_state.action: derive from blocked (NO_TRADE when blocked, TRADE_READY when not).

### 3.4 Risk

- **Low:** Read-only addition; no execution authority.
- **Semantic change:** `blocked` including kill_switch may change behavior for consumers that assume blocked = only enabled/armed. Document as intentional alignment with incident_state.

---

## 4. Out of Scope (this review)

- confirm_token value (secret); only require_confirm_token boolean
- Execution authority changes
- New runtime dependencies

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| confirm_token_required | Hardcoded True | From `EnvironmentConfig.require_confirm_token` |
| blocked | enabled/armed only | Add `or kill_switch_active` |
| summary | — | Improves when blocked includes kill_switch |
| action | Hardcoded NO_TRADE | Derive: NO_TRADE when blocked, TRADE_READY when armed |
| kill_switch_active | — | Optional: add field for consistency |

**Next step:** Explicit approval for implementation PR when ready.
