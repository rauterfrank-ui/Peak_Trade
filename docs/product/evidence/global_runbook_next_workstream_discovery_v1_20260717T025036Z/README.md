# Global Runbook Next Workstream Discovery v1

**UTC:** 20260717T025036Z  
**Base main HEAD:** `12d7e2ba6cad611e6c0d530ab29ea1f3b97cc35b`  
**Mode:** DISCOVERY_ONLY — no implementation, no runtime activation, no dashboard mutation.

## Verdict

`SELECTED_NEXT_SLICE=DRIFT_B02_RD_STRATEGY_STATUS_GRAMMAR_V0`

Reproduzierbarer Docs-Truth-Gap: kanonisches `docs&#47;features&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` behauptet weiterhin TODO&#47;NotImplementedError bzw. Null-Placeholder für R&amp;D-Strategien (Ehlers, López de Prado&#47;Meta-Labeling, Bouchaud, Gatheral), während die produktiven Strategy-Module auf aktuellem main bereits Klassen ohne `NotImplementedError` liefern und Meta-Labeling an Research-Labeling&#47;Vol-Features delegiert.

Dieser Slice ist **docs-only**, behavior-preserving und braucht ein **separates Implementation-GO** (Drift Plan Section B Regel). Kein Runtime-&#47;Live-&#47;Capital-GO.

## Exclusions (not selected)

- Dashboard composition &#47; cosmetic polish — workstream closed after PR #5266
- Canonical-chain rewire &#47; replay-input builder — closed; prior discovery `SELECTED_NEXT_SLICE=NONE` (PR #5268)
- Runtime bridge activation — `BOUND_NOT_ACTIVATED` (INTENTIONAL_POLICY_STATE)
- Live &#47; Orders &#47; Shadow &#47; Paper &#47; Testnet
- Economic unchanged retries — terminal fail &#47; retry forbidden in autonomy registry
- AUTH-ECM-01 code&#47;config resolution — BLOCKED until separate authority GO
- Master-V2 &#47; Double-Play &#47; Risk &#47; Sizing semantic changes

## Separate Implementation GO?

**YES** — sinnvoll, aber nur als docs-only Operator-GO für Drift B-02 (optional gebündelt mit B-01&#47;B-03). Dieses Discovery-Paket autorisiert **keine** Mutation der Owner-Docs.
