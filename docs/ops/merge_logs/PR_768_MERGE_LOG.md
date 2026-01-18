# PR #768 — Merge Log

## Summary
Watch-only Observability Hardening: `shadow_mvs_local_verify.sh` ist jetzt **deterministisch PASS/FAIL** nach Stack-Up durch **bounded retries** (Targets/Grafana) und **Warmup-handling** für rate-/histogram-Queries. Dazu Contract/Failure-Map/Runbook Einstieg + ein Stub-HTTP Test für Retries/Warmup.

## Why
Direkt nach `up` waren lokale Snapshot-Verifikationen flakey:
- Prometheus ist “ready”, aber `/api/v1/targets` ist kurz leer (Target refresh race)
- Grafana health ist kurz nicht ready nach Container-Start
- `rate(...[5m])`/`histogram_quantile(...)` liefern kurz empty/NaN, bis genug Samples im Window sind

Ziel: **governance-safe** (NO-LIVE), snapshot-only, keine unbounded loops, aber dennoch reproduzierbares `RESULT=PASS`.

## Changes
- `scripts/obs/shadow_mvs_local_verify.sh`
  - bounded retries für Targets + `INFO|targets_retry=...` Evidence
  - bounded Grafana health warmup
  - bounded warmup retry für Golden Queries inkl. NaN/empty handling
  - formatstabile Evidence-Lines (Pipe-delimited)
- `docs/webui/observability/SHADOW_MVS_CONTRACT.md`
  - “Retries & Warmup Semantics” inkl. Defaults + ENV overrides
- `docs/webui/observability/SHADOW_MVS_FAILURE_MAP_PHASE_F.md`
  - F-0X/F-0Y/F-0Z Failure-Classes (Targets race / Grafana warmup / rate warmup)
- `docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md`
  - Einstieg: “Verify PASS Evidence (Deterministic, Snapshot-only)” inkl. Log + `rg` Extract
- `tests/obs/test_shadow_mvs_verify_retries.py`
  - Stub-HTTP Test (kein Docker/Netz), validiert bounded retries + warmup retries

## Verification
- PR #768 war mergeStateStatus=CLEAN, mergeable=MERGEABLE, 0 failing/pending.
- Lokaler Quick Verify (snapshot-only, operator-freundlich):
  - `bash -n scripts/obs/shadow_mvs_local_verify.sh`
  - `python3 -m pytest -q tests&#47;obs&#47;test_shadow_mvs_verify_retries.py`
  - Deterministic evidence log:
    - `LOG="&#47;tmp&#47;pt_shadow_mvs_verify.log"; rm -f "$LOG"; bash scripts&#47;obs&#47;shadow_mvs_local_down.sh 2>&1 | tee -a "$LOG"; bash scripts&#47;obs&#47;shadow_mvs_local_up.sh 2>&1 | tee -a "$LOG"; bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh 2>&1 | tee -a "$LOG"; bash scripts&#47;obs&#47;shadow_mvs_local_down.sh 2>&1 | tee -a "$LOG"`
    - `rg -n "^RESULT=PASS$" &#47;tmp&#47;pt_shadow_mvs_verify.log`
    - `rg -n "^(INFO\\|targets_retry=|EVIDENCE\\||RESULT=|INFO\\|See Contract:)" &#47;tmp&#47;pt_shadow_mvs_verify.log`

## Risk
Niedrig: Änderungen betreffen nur Verify/Docs/Tests (watch-only). Retries sind bounded (kein “ewiges Grünlügen”), Fail bleibt deterministisch bei Exhaustion.

## Operator How-To
- Env overrides sind im Contract dokumentiert:
  - `docs&#47;webui&#47;observability&#47;SHADOW_MVS_CONTRACT.md`
- Bei FAIL: `/tmp/pt_shadow_mvs_verify.log` prüfen und auf F-0X/F-0Y/F-0Z mappen:
  - `docs&#47;webui&#47;observability&#47;SHADOW_MVS_FAILURE_MAP_PHASE_F.md`

## References
- PR: `https://github.com/rauterfrank-ui/Peak_Trade/pull/768`
- Merge commit: `a1bd7b84212661b404a80c1ff483fe7274b53c69`
