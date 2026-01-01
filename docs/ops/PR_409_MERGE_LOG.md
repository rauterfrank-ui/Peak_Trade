# PR #409 — Merge Log (Verified)

> **Note:** This is a historical merge log. File paths referenced may have been relocated or refactored since this PR was merged.

## Core Facts

* **Status:** MERGED
* **Merged at:** 2025-12-28 17:05:20 UTC
* **Main commit (squash):** `14d58ec`
* **CI:** 18/18 checks PASS
* **Tests on main:** 229/229 PASS (100%)

## Summary

This PR restores **Risk-Gate ↔ KillSwitch API compatibility** after the KillSwitch was upgraded to a **state-machine** implementation. A minimal, isolated **legacy adapter** brings back the historical evaluator surface (`evaluate/reset/_last_status`) expected by Risk-Gate, while keeping the KillSwitch core semantics intact.

## Why

Risk-Gate still relied on the legacy KillSwitchLayer "evaluator" API:

* `kill_switch.evaluate(risk_metrics) -> status.armed`
* `kill_switch.enabled`
* `kill_switch.reset(reason)`
* `kill_switch._last_status`

The new KillSwitch is a **state machine** (`state/is_killed` + recovery workflow), causing systematic failures:

* **47 failing tests** in `test_risk_gate.py`
* `AttributeError: 'KillSwitch' object has no attribute 'evaluate'`

## Changes

* **Added**

  * `src/risk_layer/kill_switch/adapter.py`

    * Legacy adapter implementing: `evaluate/reset/_last_status`, plus `enabled` passthrough
    * Marked **TEMPORARY** with deprecation target **Q1 2026**
* **Changed**

  * `src/risk_layer/kill_switch/core.py`

    * Added `enabled` compatibility property (getter/setter with override flag)
  * `src/risk_layer/kill_switch/__init__.py`

    * Factory produces a Risk-Gate compatible instance (adapter-wrapped)
  * `src/risk_layer/risk_gate.py`

    * **Exactly 3 LOC** change: wrap KillSwitch with adapter in constructor
  * Tests updated for `enabled` semantics and new integration shape
* **Removed**

  * Obsolete legacy test file(s) superseded by the new KillSwitch + adapter approach

## Verification

* Kill-Switch suite: **PASS**
* Risk-Gate suite: **PASS** (previously 47 failures resolved)
* Combined sanity (Kill-Switch + Risk-Gate): **PASS**
* Main branch verification: **229/229 PASS (100%)**
* CI verification: **18/18 checks PASS**

## Risk

**LOW**

* KillSwitch remains a state machine; no behavioral redesign in core logic.
* Risk-Gate change is minimal (adapter wrapping).
* Adapter is isolated and explicitly marked temporary.

## Operator How-To

No operational action required. No config migration required.

## Follow-up

* **Q1 2026:** Refactor Risk-Gate to the native KillSwitch state-machine API and remove the legacy adapter.
* **Tracking:** PR **#410** created for the migration TODO.

## References

* PR: **#409**
* Main commit: `14d58ec`
* Key paths:

  * `src/risk_layer/kill_switch/adapter.py`
  * `src/risk_layer/risk_gate.py`
  * `src/risk_layer/kill_switch/core.py`
* Documentation:

  * `docs/risk/KILL_SWITCH_ARCHITECTURE.md`
  * `docs/risk/KILL_SWITCH.md`
  * `docs/ops/KILL_SWITCH_RUNBOOK.md`
  * `docs/ops/KILL_SWITCH_TROUBLESHOOTING.md`
* Related PRs:

  * **#408:** Risk Layer v1.0 (introduced the new KillSwitch state-machine)
  * **#410:** Migration TODO for adapter removal (Q1 2026)

---

**Verified by:** CI + local test runs
**Merge method:** Squash
**Branch deleted:** ✅ Yes
