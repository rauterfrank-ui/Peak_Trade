# Runbook B — Execution Gates Quickstart (B5/B3/B2)

## Scope

This doc describes **how to enable and validate** the Runbook-B safety controls added in this branch:

- **B5**: Session Armed / Confirm Token gate (ArmedGate)
- **B3**: RiskGate (deterministic deny reasons)
- **B2**: Reconciliation hook (pure drift check via provider)

**All gates are OFF by default** and introduce **no behavior change** unless explicitly enabled.

---

## B5/B3 Guards (in `src/live/safety.py`)

### Enable (explicit)

```bash
export PEAK_EXEC_GUARDS_ENABLED=1
export PEAK_EXEC_GUARDS_SECRET='change-me-long-random'
# optional: arming token (issue via ArmedGate.issue_token(now_epoch))
export PEAK_EXEC_GUARDS_TOKEN=''
```

When enabled, **PEAK_EXEC_GUARDS_SECRET** is required; otherwise execution is blocked and an audit line is written.

### Risk limits (env, only when guards enabled)

All default to `0` (no enforcement). Set only if you want hard limits:

| Env | Description | Default |
|-----|-------------|--------|
| `PEAK_KILL_SWITCH` | `1` = deny all | `0` |
| `PEAK_MAX_NOTIONAL_USD` | Max order notional (USD) | `0` |
| `PEAK_MAX_ORDER_SIZE` | Max order size (base units) | `0` |
| `PEAK_MAX_POSITION` | Max position (base units) | `0` |
| `PEAK_MAX_SESSION_LOSS_USD` | Max session loss (USD) | `0` |
| `PEAK_MAX_DATA_AGE_SECONDS` | Max market data age (s) | `0` |

Context placeholders (for testing or when not wired from session):  
`PEAK_NOW_EPOCH`, `PEAK_MD_AGE_SECONDS`, `PEAK_SESSION_PNL_USD`, `PEAK_CURRENT_POSITION`, `PEAK_ORDER_SIZE`, `PEAK_ORDER_NOTIONAL_USD`.

### Safe usage

- **Default (no env set):** Guards are off; behavior unchanged.
- **Enable only in controlled sessions** with a strong secret and (when arming) a short-lived token.
- Audit lines: `place_order(runbook_b_guards)` with `allowed=True/False` and reason.

---

## B2 Reconciliation hook (in `src/live/safety.py`)

### Enable (explicit)

```bash
export PEAK_RECON_ENABLED=1
# optional tolerances (default 0 = strict match)
export PEAK_RECON_BALANCE_ABS=0
export PEAK_RECON_POSITION_ABS=0
```

When enabled, the hook uses a **provider** (default: `NullReconProvider` with empty snapshots, so no drift). Wire a real provider to supply expected/observed snapshots for meaningful drift checks.

### Safe usage

- **Default (no env set):** Recon is off; no reconciliation runs.
- Enable only when you have a provider (or accept the null provider’s no-op).

---

## Config examples (all OFF by default)

### Example: guards and recon disabled (default)

No env vars; no behavior change.

### Example: guards enabled for a test session (still safe: small limits)

```bash
export PEAK_EXEC_GUARDS_ENABLED=1
export PEAK_EXEC_GUARDS_SECRET='your-test-secret-min-16-chars'
export PEAK_EXEC_GUARDS_TOKEN=''   # optional; set if arming
export PEAK_MAX_NOTIONAL_USD=100
export PEAK_MAX_ORDER_SIZE=0.01
export PEAK_KILL_SWITCH=0
```

### Example: recon enabled with null provider (no drift)

```bash
export PEAK_RECON_ENABLED=1
# NullReconProvider is used by default → no drift
```

---

## Pointers

- **Implementation:** `src/ops/gates/` (ArmedGate, RiskGate), `src/ops/wiring/execution_guards.py`, `src/ops/recon/` (recon hook, providers), `src/live/safety.py` (wire-in).
- **Tests:** `tests/ops/test_armed_gate.py`, `test_risk_gate.py`, `test_execution_guards.py`, `test_recon_hook.py`, `test_recon_provider_wiring.py`, `tests/live/test_safety_exec_guards_wiring.py`.
- **Runbook B source:** See `out/ops/runbook_b/` (gap scan, integration map, tasks checklist) and the original Runbook B document (Shadow → Mini-Live).
