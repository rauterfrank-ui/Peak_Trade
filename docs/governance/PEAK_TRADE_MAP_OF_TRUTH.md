# Peak Trade — Map of Truth

```text
DOCUMENT_CLASS=CURRENT_NAVIGATION_ONLY
DOCUMENT_ROLE=NAVIGATION_ONLY
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
MAP_OF_TRUTH_AUTHORITY=NONE
MAP_OF_TRUTH_SEMANTIC_AUTHORITY_EFFECT=NONE
MAP_OF_TRUTH_INDEPENDENT_OPERATIONAL_TRUTH=NONE
THIS_DOCUMENT_DEFINES_NO_SEMANTICS=true
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
THIS_DOCUMENT_IS_NOT_A_SECOND_RUNBOOK=true
THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true
PARALLEL_SSOT_CREATED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

**Role:** discovery / path resolution only.  
**Authority:** none.

An autonomous agent may use this document to answer:

```text
WHERE is the authoritative CURRENT information?
```

An autonomous agent must NOT use this document to answer:

```text
WHAT is the authoritative operational decision?
WHAT is authorized / activated / next?
```

Operational semantics, safety policy, activation state, productive
boundary, and authority ownership live only in:

1. `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` (CURRENT operational SSOT)
2. CURRENT `origin/main` code / config / contracts / tests / sealed evidence

If this map and the Master Runbook appear to disagree: **Master Runbook +
CURRENT code win**. Do not invent a third interpretation here.

------------------------------------------------------------------------

## 1. Canonical CURRENT operational SSOT

| Role | Path |
| --- | --- |
| CURRENT operational SSOT | [`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) |
| Navigation only (this file) | [`docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md) |
| Python runtime contract | [`docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`](../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) |
| Agent entrypoint | [`AGENTS.md`](../../AGENTS.md) |

```text
CANONICAL_MASTER_RUNBOOK_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CANONICAL_WORKING_AUTHORITY=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true
NO_PARALLEL_SEMANTIC_MODEL=true
```

Master Runbook CURRENT section navigation (headings, not historical phase IDs):

| Question | Master Runbook section |
| --- | --- |
| What is the system now? | CURRENT System Identity |
| Who owns what? | CURRENT Architecture and Authority Graph |
| Trading core chain | CURRENT Trading Core |
| Inputs | CURRENT Data and Input Contracts |
| Persistence | CURRENT State and Persistence Contracts |
| Risk / capital | CURRENT Risk and Capital Admissibility |
| Intent / execution boundary | CURRENT Order-Intent and Execution Boundaries |
| Safety | CURRENT Safety Invariants |
| Autonomy limits | CURRENT Autonomy Boundaries |
| Operating / activation facts | CURRENT Operating and Activation State |
| Dashboard role | CURRENT Observability and Landscape Dashboard |
| Historical names still in code | CURRENT Compatibility Identifiers |
| Remaining productive boundary | CURRENT Productive Boundary |

------------------------------------------------------------------------

## 2. CURRENT semantic capability surfaces (code navigation)

These paths are location pointers only. Semantics and authorization remain
in the Master Runbook and the named packages.

| Semantic identity / domain | CURRENT surface |
| --- | --- |
| Full-Core live-path authority | `src/ops/full_core_live_path_composition_root_v1/` |
| `full_core_live_path_authority_v1` | `src/ops/full_core_live_path_composition_root_v1/constants_v1.py` |
| `capital_risk_admissibility_owner_v1` | `src/ops/full_core_live_path_composition_root_v1/` (risk admissibility modules) |
| `canonical_order_intent_owner_v1` | `src/ops/full_core_live_path_composition_root_v1/` |
| `stateful_no_order_host_join_v1` | `src/ops/full_core_live_path_composition_root_v1/` |
| `send_capable_adapter_v1` | `src/ops/governed_productive_account_equity_authority_producer_v1/` and Full-Core composition root |
| Exactly-one governed cycle | `src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py` |
| `governed_continuous_cycle_orchestrator_v1` | `src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py` |
| Single Selected Future policy | `src/ops/single_selected_future_policy_v1/` |
| Single Selected Future binding | `src/ops/single_selected_future_runtime_binding_v1/` |
| Governed universe | `src/ops/governed_futures_universe_producer_v1/` |
| Productive ranking | `src/ops/productive_futures_ranking_producer_v1/` |
| Master V2 / Double Play decision path | `trading` package / integrated offline trading-logic replay owners (see Master Runbook) |
| Canonical Python launcher | `scripts/pt` |
| Canonical interpreter | `.venv&#47;bin&#47;python` |

------------------------------------------------------------------------

## 3. Useful CURRENT related documents (non-SSOT)

These documents may help locate surfaces. They are **not** operational
authority and must not be read as activation or next-step instructions.

| Path | Navigation note |
| --- | --- |
| [`docs/governance/PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md`](PEAK_TRADE_CANONICAL_RUNTIME_TRUTH_MAP_V1.md) | Historical/runtime discovery aid; reconcile against Master Runbook + CURRENT code before use |
| [`docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) | Short navigation contract; not a second SSOT |
| [`docs/ops/registry/DOCS_TRUTH_MAP.md`](../ops/registry/DOCS_TRUTH_MAP.md) | Docs drift registry; not a runbook |
| [`docs/ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md`](../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md) | Local CI dedup navigation |
| [`docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md`](../ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md) | Landscape Dashboard consumer docs; read-only / non-authority |
| [`docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md`](../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) | Python launcher/interpreter contract |

------------------------------------------------------------------------

## 4. Compatibility-only name navigation

Some CURRENT files, claim keys, and evidence directories still use historical
names. Treat them as location compatibility only:

```text
CLASS=HISTORICAL_COMPATIBILITY_ONLY
AUTHORITY_EFFECT=NONE
```

Examples (non-exhaustive; authoritative list is in Master Runbook
**CURRENT Compatibility Identifiers**):

- `STEP_29P`, `STEP_29Q`, `PLAN_ONLY`
- `CAP_7_2`, `CAP_11_1`
- `SECTION_11_13_5_*`, `SECTION_11_14_*`
- `EH.S5` / `EH.S6`
- `CAPABILITY_2_3_*`, `CAPABILITY_2_4_*`
- Historically named module/evidence paths under `src/ops/` and `evidence/ops/`

Do not interpret these names as CURRENT phase, next action, or independent
authority.

------------------------------------------------------------------------

## 5. Explicit non-authority

This Map of Truth does **not** define or authorize:

- trading semantics
- authority ownership beyond pointing to owners
- activation / arming / wire-send / POST
- productive next action
- safety policy
- execution policy
- Live / Testnet / credential / capital movement
- Clean Trading Core status (read Master Runbook)
- standing LIVE_* predicate interpretation (read Master Runbook + CURRENT constants)

```text
LIVE_AUTHORIZED_BY_THIS_DOCUMENT=false
TESTNET_AUTHORIZED_BY_THIS_DOCUMENT=false
ORDERS_ALLOWED_BY_THIS_DOCUMENT=false
SCHEDULER_RUNTIME_ALLOWED_BY_THIS_DOCUMENT=false
DASHBOARD_AUTHORITY_EFFECT=NONE
```

Notion is not a Peak_Trade component and is not a navigation authority for
CURRENT operational truth.

------------------------------------------------------------------------

## 6. Guidance for new agents

1. Read [`PEAK_TRADE_MASTER_RUNBOOK.md`](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) fully before mutation.
2. Revalidate current `origin/main`.
3. Use this map only to find paths.
4. Prove runtime facts from code/config/persistence/tests/evidence.
5. Fail closed on drift or ambiguity.
6. Do not follow historical Cap/Phase/Step/Section/EH/Z2/Pxx/Dxx workflow
   pointers as CURRENT instructions.
