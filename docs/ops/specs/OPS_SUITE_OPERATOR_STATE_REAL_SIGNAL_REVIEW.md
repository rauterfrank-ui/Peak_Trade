# OPS Suite — Operator State Real-Signal Review (Read-Only)

status: DRAFT
last_updated: 2026-03-12
owner: Peak_Trade
purpose: Read-only review of operator_state real-signal gaps and hardening options
docs_token: DOCS_TOKEN_OPS_SUITE_OPERATOR_STATE_REVIEW

## Scope
This document is a **read-only review** of `operator_state` in the Ops Cockpit. No code changes, no mutations. It identifies gaps and recommends real-signal mapping options for future implementation.

## Baseline
- **main@52a549f1**
- **Related:** OPS_SUITE_DASHBOARD_VNEXT_SPEC, incident_state (telemetry + kill_switch hardened), policy_state (same guard_state source)

---

## 1. Current operator_state Implementation

### 1.1 Schema (ops_cockpit.py ~418–425)

| Field | Current Source | Real Signal? |
|-------|----------------|--------------|
| `disabled` | `not guard_state["enabled"]` | **Placeholder** — guard_state hardcoded |
| `enabled` | `guard_state["enabled"]` | **Placeholder** — always False |
| `armed` | `guard_state["armed"]` | **Placeholder** — always False |
| `dry_run` | `guard_state["dry_run"]` | **Placeholder** — always True |
| `blocked` | `(not enabled) or (not armed)` | **Placeholder** — inputs hardcoded |
| `kill_switch_active` | `guard_state["kill_switch_active"]` | **Placeholder** — always False |

### 1.2 guard_state Source (ops_cockpit.py ~397–406)

`guard_state` is **hardcoded**:

```python
guard_state = {
    "no_trade_baseline": "reference",
    "deny_by_default": "active",
    "treasury_separation": "enforced",
    "enabled": False,
    "armed": False,
    "dry_run": True,
    "confirm_token_required": True,
    "kill_switch_active": False,
}
```

`operator_state` and `policy_state` are both derived from this dict. No config, no runtime, no persistence.

### 1.3 OPS_SUITE_DASHBOARD_VNEXT_SPEC Expectations

Operator States (Section "Operator States"):
- disabled
- enabled
- armed
- dry-run
- blocked
- kill-switch active

---

## 2. Gap Analysis

### 2.1 enabled / armed / dry_run

| Aspect | Current | Gap |
|--------|---------|-----|
| enabled | Always `False` | No derivation from config |
| armed | Always `False` | No derivation from config |
| dry_run | Always `True` | No derivation from config |

**Real signal candidate:** `EnvironmentConfig` from `get_environment_from_config(peak_config)`.

| operator_state field | EnvironmentConfig field | Config path | Default |
|----------------------|-------------------------|-------------|---------|
| enabled | `enable_live_trading` | `environment.enable_live_trading` | False |
| armed | `live_mode_armed` | `environment.live_mode_armed` | False |
| dry_run | `live_dry_run_mode` | `environment.live_dry_run_mode` | True |

**Data source:** `src&#47;core&#47;environment.py` — `EnvironmentConfig`, `get_environment_from_config()`. Config loaded via `PeakConfig` from `config&#47;config.toml` (or `config_path` param in `build_ops_cockpit_payload`).

**Recommendation:** When `config_path` exists (or `repo_root &#47; "config" &#47; "config.toml"`):

- Load config via `load_config(path)` → `PeakConfig`
- Call `get_environment_from_config(peak_config)` → `EnvironmentConfig`
- Map: `enabled` = env.enable_live_trading, `armed` = env.live_mode_armed, `dry_run` = env.live_dry_run_mode

**Fallback:** Current hardcoded values when config missing or parse error.

### 2.2 kill_switch_active

| Aspect | Current | Gap |
|--------|---------|-----|
| Value | Always `False` (from guard_state) | No derivation from runtime state |
| incident_state | Already hardened — reads from `data&#47;kill_switch&#47;state.json` | **Inconsistency** |

**Observation:** `incident_state` uses `_kill_switch_active` (from state file). `operator_state` still uses `guard_state["kill_switch_active"]` (hardcoded False). Same payload, different sources for the same semantic.

**Recommendation:** Reuse `_kill_switch_active` (already computed before incident_state) for `operator_state["kill_switch_active"]`. No new read; align with incident_state.

### 2.3 blocked / disabled

| Aspect | Current | Gap |
|--------|---------|-----|
| Derivation | `(not enabled) or (not armed)` | Correct logic; inputs are placeholders |
| disabled | `not enabled` | Same |

Once `enabled` and `armed` are hardened from config, `blocked` and `disabled` improve automatically.

### 2.4 policy_state Alignment

`policy_state` is built from the same `guard_state`. Hardening `guard_state` (or deriving operator_state from config) would affect both. Consider:

- **Option A:** Harden `guard_state` first (load config, populate enabled/armed/dry_run; kill_switch from state file). Then policy_state and operator_state inherit.
- **Option B:** Harden only `operator_state` (read config for operator_state block; reuse _kill_switch_active). Leave guard_state/policy_state as-is for now.

**Recommendation:** Option A — single source of truth. Derive guard_state.enabled/armed/dry_run from config; guard_state.kill_switch_active from state file. Both policy_state and operator_state then reflect real signals.

---

## 3. Real-Signal Mapping Options

### 3.1 Existing Real Signals

| Source | Location | Relevance |
|--------|----------|-----------|
| `get_environment_from_config` | `src&#47;core&#47;environment.py` | enable_live_trading, live_mode_armed, live_dry_run_mode |
| `load_config` | `src&#47;core&#47;peak_config.py` | Config loading from path |
| State file | `data&#47;kill_switch&#47;state.json` | kill_switch_active (already read for incident_state) |

### 3.2 Recommended Mapping (for future PR)

| operator_state field | Option | Real signal | Fallback |
|----------------------|--------|-------------|----------|
| enabled | Primary | `EnvironmentConfig.enable_live_trading` | False |
| armed | Primary | `EnvironmentConfig.live_mode_armed` | False |
| dry_run | Primary | `EnvironmentConfig.live_dry_run_mode` | True |
| kill_switch_active | Primary | Reuse `_kill_switch_active` from incident_state block | False |
| blocked | Derived | `(not enabled) or (not armed)` | True |
| disabled | Derived | `not enabled` | True |

### 3.3 Order of Operations

- `build_ops_cockpit_payload` already receives `config_path` (or derives from repo_root).
- Add config-load block **before** guard_state: load config → get EnvironmentConfig → populate guard_state.enabled/armed/dry_run.
- Move kill_switch read **before** guard_state (or keep current order; _kill_switch_active is already before incident_state). Set `guard_state["kill_switch_active"] = _kill_switch_active` after kill_switch block.
- Then guard_state → policy_state, operator_state unchanged in structure.

### 3.4 Risk

- **Low:** Read-only addition; no execution authority. Ops Cockpit is observability only.
- **Config coupling:** If config is missing or invalid, fallback to safe defaults (enabled=False, armed=False, dry_run=True).
- **Policy critic:** Config may contain `enable_live_trading=true` or `live_mode_armed=true` in test fixtures. Ops Cockpit **displays** these values; it does not change execution. Displaying actual config state is correct for operator visibility.

---

## 4. Out of Scope (this review)

- `OperatorState` (alerting) — ACK/SNOOZE state; different concept from operator_state (guard posture).
- PEAK_EXEC_GUARDS_* env vars — runtime guards; not yet surfaced in Ops Cockpit.
- ArmedGate / ArmedState persistence — session-scoped; config is the source of truth for Ops Cockpit read-model.

---

## 5. Summary

| Field | Current | Recommended Hardening |
|-------|---------|------------------------|
| enabled | Hardcoded False | From `EnvironmentConfig.enable_live_trading` |
| armed | Hardcoded False | From `EnvironmentConfig.live_mode_armed` |
| dry_run | Hardcoded True | From `EnvironmentConfig.live_dry_run_mode` |
| kill_switch_active | Hardcoded False | Reuse `_kill_switch_active` (state file) |
| blocked / disabled | Derived | Improve automatically when inputs hardened |

**Next step:** Explicit approval for implementation PR (read-model contract + code changes) when ready.
