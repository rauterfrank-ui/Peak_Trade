# Post-Fix Canonical Chain Reevaluation v1

```text
SLICE=POST_FIX_CANONICAL_CHAIN_REEVALUATION_V1
BASE_SHA=00302a228e47d1cf74e43494a838123d2f803fb8
BRANCH=audit/post-fix-canonical-chain-reevaluation-v1
PRODUCTIVE_FILES_CHANGED=false
STATUS=PASS
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
ENTRY_SIDE=NONE
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

After PR #5338 (mark-relative BPS distances) and PR #5340 (ADVERSE_EXIT / DOWNSCOPE dual preserve),
the canonical offline research chain is **technically end-to-end reachable** on the PR #5338
1INCH fixture: ScopeEvents (including `DOWNSCOPE_*`), SideState transitions (including SHORT),
entry/exit intents, and at least one offline trade are observed. No productive value-loss,
second authority, or classic-engine bypass found.

## Scope

READ-ONLY / EVIDENCE-ONLY. No productive code changes. No parameter tuning. No live / orders /
runtime-bridge activation. Foreign untracked evidence dirs and stashes left untouched.

## Key counts (1INCH primary)

| Metric | Value |
|--------|------:|
| Bars hooked | 2953 |
| NOOP | 118 |
| Bull / Bear candidates | 2458 / 286 |
| Bull / Bear events | 284 / 2460 |
| ADVERSE_EXIT events | 31 |
| DOWNSCOPE events | 2460 |
| Adverse PolicySignal | 2491 |
| Entry intents (enter_*) | 9 |
| Exit/reduce intents | 2492 |
| Trades | 1 |
| Legacy absolute 120 distances | 0 |

## Artifacts

| File | Purpose |
|------|---------|
| `executive_summary.md` | Compact verdict |
| `canonical_chain_map.md` | Boundary map |
| `boundary_value_flow.tsv` | Per-boundary owner/value-loss |
| `instrument_matrix.tsv` | 1INCH / BONK / AVAX / SOL |
| `event_counts.tsv` | Generator + matched + mapped |
| `state_transition_counts.tsv` | SideState transitions |
| `policy_and_intent_counts.tsv` | Entry/exit policy |
| `execution_counts.tsv` | Offline execution / trades |
| `adverse_exit_downscope_traces.md` | Phase D traces |
| `first_blocking_boundary.md` | First blocker analysis |
| `classification.md` | A–L classification |
| `reevaluation_probe_v1.py` | Evidence-only probe |
| `probe_summary.json` | Machine summary |
| `test_results.txt` | Focused suite (146 passed) |

## Safety

`RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED`, `ENTRY_SIDE=NONE`, `LIVE_AUTHORIZED=false`, `ORDERS=false`.
