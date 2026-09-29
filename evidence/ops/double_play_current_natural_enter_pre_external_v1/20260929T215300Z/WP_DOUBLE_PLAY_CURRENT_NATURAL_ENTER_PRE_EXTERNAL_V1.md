# WP Double-Play CURRENT Natural-Enter PRE_EXTERNAL Liveness Proof V1

## A. Pre-existing WP-3 facts (input only)

Consumed from `evidence&#47;ops&#47;double_play_compatibility_boundary_patch_v1&#47;20260929T214800Z&#47;` and uncommitted worktree diff on branch `wp3&#47;double-play-compatibility-boundary-v1` @ `8475ebb`:

- `WP3_STATUS=PASS`, `BEHAVIORAL_ROOT_DIVERGENCES_AFTER=0`, `CORE_FILES_CHANGED=0`
- Compatibility targets: F1/M9 boundary alpha, G17 produced-only bind, layered CMC-mark init
- No commit; production diff vs HEAD: 4 modified + 2 new modules + 1 governance decision JSON

## B. Productive attachment proof (runtime-nah, pre-cycle)

Verified via `./scripts/pt -c` on this worktree (no harness substitute for config load):

| Check | Result |
|-------|--------|
| `old_effective_host_contract_enabled_v1` | true |
| `integrated_replay_presence_alpha_at_dp_boundary_v1` | true |
| `g17_cmc_bind_produced_only_v1` | true |
| `layered_core_cmc_mark_observation_init_v1` | true |
| `run_integrated_offline_trading_logic_replay_v1` uses `resolve_alpha_scope_entry_for_integrated_replay_v1` | true |
| `run_current_productive_master_v2_runtime_cycle_v1` → integrated replay | true |
| Bounded continuous Owner-GO @ `8475ebb` | valid |
| Canonical price provenance module | unchanged; fail-closed preserved |

**WP3_PRODUCTIVE_ATTACHMENT=PROVEN_CURRENT** for decision consumption and code path presence. Full MV2 cycle path was **not reached** in this run (see H).

## C. Runtime observations

**Entrypoint:** `scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`  
**Flags:** `--wp-branch-evidence-run` (WP-3 uncommitted on HEAD; protected 29P chain surfaces clean vs `origin&#47;main`)

**Bounds (canonical S6 hard caps):**

- `HARD_CAP_MAX_CYCLES_PER_RUN=4`
- `HARD_CAP_MAX_RUN_DURATION_SECONDS=180`

**Window 1** (`2026-09-29T19:54:30Z` binding epoch):

1. EEA universe GET → Cap24 canonical write → SSF selection **PROVEN_CURRENT** (real GET ranking input).
2. Selected instrument: `okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap` / venue native `0G-USDT-SWAP` (Cap24 policy; not agent-chosen).
3. G17 mark-history GET performed for hot-path producer prep (`get_request_count` includes mark history).
4. Fresh-C1 candles GET performed (`fresh_c1_get_owner_go_consumptions_v1.jsonl`, `get_performed=true`, endpoint `/api/v5/market/candles`).
5. **Fail-closed before S6 cycles:** `PersistentNaturalEnterConvergenceError: BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED`.

**PRODUCTIVE_CYCLES=0** — no S5/S7/MV2 cycle executed.

## D. Natural market conditions

Not adjudicated for ENTER admissibility: the productive stack **never reached** Double-Play decision cycles. This is **not** `MARKET_CONDITION_NOT_ADMISSIBLE`.

## E. DP decision/state progression

No C1 acceptance, scope, C3, composition, or entry/exit outcomes recorded — bootstrap blocked prior to sidestate cursor persist and continuous loop.

## F. Persistence / duplicate invariants

**UNKNOWN_CURRENT** for this run (no DISTINCT/DUPLICATE C1 processed in productive host). WP-3 unit/harness proofs remain separate; not re-run here per WP scope.

## G. PRE_EXTERNAL boundary

| Field | Value |
|-------|-------|
| PRE_EXTERNAL_REACHED | false |
| POST_COUNT | 0 |
| EXTERNAL_EFFECT_COUNT | 0 |
| LIVE_PUBLIC_C1_GET | true (candles) |

## H. Blocker adjudication

| Field | Value |
|-------|-------|
| FIRST_BLOCKING_GATE | `BOOTSTRAP_CMC_MARK_PAYLOAD_REQUIRED` |
| BLOCKER_CLASS | `PRODUCTIVE_ATTACHMENT_BLOCKER` |
| CODE_DEFECT_PROVEN | true |
| WP3_INVOLVED_IN_BLOCKER | false |

**Root cause (minimal causal):**

- `run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1` cold-lane bootstrap calls `observation_source.poll()` and requires `first_obs.mark_price_payload` (`current_productive_persistent_natural_enter_convergence_v1.py`).
- `LiveFreshC1ContinuousObservationSourceV1.poll` returns `InjectedContinuousObservationV1` with **candles only** — never sets `mark_price_payload` (`current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py` L118–121).
- Each S5 cycle also passes `observation.mark_price_payload` into N1 runner, which raises `CMC_MARK_PRICE_PAYLOAD_REQUIRED` if null (`make_n1_occupied_lane_s5_runner_v1`).

The entry script performs a separate G17 mark-history GET but does **not** attach that payload to bootstrap observation.

**Producer/consumer/owner:**

- Observation producer: `LiveFreshC1ContinuousObservationSourceV1` (S6 poll)
- Bootstrap consumer: `bootstrap_s8_lane_via_s7_compose_v1` / `run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1`
- Owner: Full-Core persistent natural-enter convergence + live C1 source wiring

## I. Next minimal action

**Bounded wiring only (not in WP-4):** On cold lane, provide CMC mark payload (scoped public GET mark-price and index if required) into bootstrap observation—either extend `LiveFreshC1ContinuousObservationSourceV1` or pass `bootstrap_observation` from the entry script using the already-fetched G17/mark GET result. Re-run WP-4 bounded window with same Owner-GO and `--wp-branch-evidence-run`.

---

## Git / delivery

- No commit, push, PR, or production/test edits in WP-4.
- Runtime evidence: this directory + `runtime&#47;wp4_natural_enter_pre_external_v1&#47;20260929T215300Z&#47;productivity&#47;` (Cap24 selection state from real GET; not used for fixture ENTER).
