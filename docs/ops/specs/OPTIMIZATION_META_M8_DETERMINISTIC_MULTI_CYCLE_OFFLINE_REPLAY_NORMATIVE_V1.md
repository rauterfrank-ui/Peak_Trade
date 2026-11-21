---
docs_token: DOCS_TOKEN_OPTIMIZATION_META_M8_DETERMINISTIC_MULTI_CYCLE_OFFLINE_REPLAY_NORMATIVE_V1
status: active
scope: M8 deterministic multi-cycle offline replay of M1-M7 evidence loop
capability: OPTIMIZATION_META_M8_DETERMINISTIC_MULTI_CYCLE_OFFLINE_REPLAY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# M8 — Deterministic Multi-Cycle Offline Replay V1

```text
WORKPACKAGE_ID=OPTIMIZATION_META_M8_DETERMINISTIC_MULTI_CYCLE_OFFLINE_REPLAY_V1
SEARCH_EXECUTION_AUTHORIZED=false
LEARNING_STATE_MUTATION_AUTHORIZED=false
M7_SEARCH_METHOD_FAIL_CLOSED_PRESERVED=true
```

Owner: `src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py`

Orchestrates M1→M7 per cycle; cycle N+1 binds M7 feedback lineage only.
Does not register capabilities, authorize surfaces, or mutate learning state.

## Non-goals

M9 surfaces, productive search, promotion, execution

## Prior-cycle content binding — 2026-11-21

An explicitly supplied prior feedback packet must equal the actual preceding
cycle's M7 output under the existing canonical JSON content hashing. An ID
match or a newly calculated transport digest alone does not establish that
relationship. Canonical comparison distinguishes booleans from numbers while
accepting an unchanged JSON round trip. Omitted prior feedback continues to
use the preceding output automatically. Existing IDs and digest formulas are
unchanged.

The carried dispositions remain lineage in the next cycle's evidence. They
do not rewrite its supplied experiment request, run a search on behalf of M7,
update a numerical model or create promotion/apply authority. The same check
applies at the MI-crossing and federated replay joins.
