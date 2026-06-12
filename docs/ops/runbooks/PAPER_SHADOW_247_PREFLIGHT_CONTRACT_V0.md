# Paper/Shadow 24/7 Preflight Contract v0

## 1. Purpose

This document defines the minimum preflight contract for any future Paper/Shadow 24/7 daemon or scheduler activation path.

It does **not** authorize activation. It does **not** start a daemon. It does **not** create a Paper, Shadow, Testnet, or Live runtime path.

Current status: **BLOCKED**.

### Related: Shadow-247 governance charter (non-authorizing)

For the **activation ladder**, operator-approval semantics, stop/evidence planning boundaries, and explicit **STOP_IDLE** posture, see **[SHADOW_247_GOVERNANCE_CHARTER_V0.md](SHADOW_247_GOVERNANCE_CHARTER_V0.md)**. That charter is governance-only and **does not** override this document’s **BLOCKED** status or constitute a runtime approval.

For **24h bounded Shadow dry-run candidate** documentary evidence semantics, see **Status and scope** in **[SHADOW_247_GOVERNANCE_CHARTER_V0.md](SHADOW_247_GOVERNANCE_CHARTER_V0.md)** (same charter file as the preceding governance link); that tier remains **documentary** and **non-authorizing**, **does not** change this contract’s **BLOCKED** status, and assists navigation only.

## 2. Canonical activation status

There is no approved one-command Paper/Shadow 24/7 activation path in the repository.

The only currently accepted scheduler command for this topic is diagnostics-only:

```bash
python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml --dry-run --once --verbose
```

That command is for planning and diagnostics. It must not be interpreted as daemon activation, Paper runtime activation, Shadow runtime activation, Testnet activation, or Live enablement.

Operator decision until a future reviewed slice completes all mandatory contract items: **STOP — do not activate Paper/Shadow 24/7.**

## 2a. Primary evidence retention invariant v0 (all run types)

`PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true`

Every governed run—**Paper**, **Shadow**, **Testnet**, **Live/Canary**, **Scheduler**, **Supervisor**, **Order-Capability offline**, **Daemon**, **Smoke**, **bounded trial**, and **runtime adapter** paths—must produce **durable primary evidence** before the run may be treated as complete.

A run is **not complete** until **archive verification passes**, including at minimum:

- durable archive outside `/tmp`
- `MANIFEST.sha256` present and verifiable (`shasum -a 256 -c` RC=0)
- required runtime artifacts present (for example account, fills, events, steps as applicable)
- config snapshot with secrets redacted when applicable
- stdout/stderr or scheduler logs present
- closeout present
- postrun/review present (for example `REVIEW_RESULT.json` with explicit verdict)
- archive copy verified against staging
- source path usable later for operator retrieval

The following are **forbidden as primary evidence** (supporting or documentary only):

- `/tmp`-only artifacts without durable archive
- transcript-only evidence
- Notion pointer-only evidence
- chat-summary-only evidence
- unverified archive copies

Future run selectors and adapters must **reject or block** a run plan when primary evidence retention cannot be guaranteed. **No gate clearance** may be inferred from degraded or documentary evidence alone. Completing one bounded Paper observation run (for example Paper120) does **not** impose an automatic **24h** or **72h** rerun requirement.

Reference implementation: `scripts/ops/run_paper_only_bounded_observation_adapter_v0.py` and shared manifest helpers in `scripts/ops/primary_evidence_retention_v0.py` (plan-only default; execute requires approval record; archive root outside `/tmp`; `MANIFEST.sha256` verified after durable copy).

**Gap-4 REQ-A bounded paper (non-authorizing):** profile `gap4_req_a_paper_bounded_v0` on the paper-only adapter wires RUN_ID-scoped scheduler HOLD runtime binding env (`PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_OUTROOT`, `PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_RUN_ID`) per Scheduler Boundary Hard-Block Contract §10a. Requires valid `HOLD_BINDING_OUTROOT` passing `build_scheduler_hold_runtime_binding_v0()`. Duration 300–900s. Static guard: `tests/ops/test_gap4_req_a_300s_hold_binding_profile_contract_v0.py`. **Does not** clear global Preflight **BLOCKED** or grant Testnet/Live/Shadow authority.

**Paper-L2 120min hold-binding (non-authorizing):** profile `paper_l2_120min_hold_binding_v0` on the paper-only adapter wires the same RUN_ID-scoped scheduler HOLD runtime binding env per Scheduler Boundary Hard-Block Contract §10b. Requires valid `HOLD_BINDING_OUTROOT` passing `build_scheduler_hold_runtime_binding_v0()`. Duration **7200** seconds (120min). Profile contract, adapter wiring, and static guards are **fully implemented** on `main`. Static guard: `tests/ops/test_paper_l2_120min_hold_binding_profile_contract_v0.py`. Reciprocal crosslink to Gap-4 REQ-A §10a profile above. **Does not** clear global Preflight **BLOCKED**, **does not** grant Testnet/Live/Shadow authority, **does not** authorize execute or preflight lift.

Combined daemon paper+shadow OUTROOTs are **composition/index** wrappers indexed in Generic Evidence Run Registry v1 `compositions[]` (taxonomy §6b); per-lane `MANIFEST.sha256` at `runs&#47;{paper,shadow,testnet}&#47;{run_id}&#47;` remains canonical primary evidence.

P67/P72 library paths (`run_shadow_session_scheduler_v1`, `run_shadowloop_pack_v1`) write partial evidence by default; opt-in `primary_evidence_enforce=True` calls shared `finalize_primary_evidence_root()` at library completion (non-authorizing; does not clear HOLD or grant Live/Testnet/broker authority; P67 CLI scheduler guard unchanged).

Scheduler launcher (`scripts/run_scheduler.py`) supports opt-in completion retention via `--evidence-dir` and `--primary-evidence-enforce`, writing `scheduler_completion_closeout_v0.json` and calling shared `finalize_primary_evidence_root()` when enforcement is enabled (default off; dry-run remains planning-only; start boundary guard unchanged).

Offline supervisor/daemon evidence pack: `scripts/ops/pack_online_readiness_supervisor_evidence_v0.py` copies an existing supervisor `OUT_DIR` and optional pid/log artifacts into a durable archive root, writes `supervisor_session_closeout_v0.json`, and may call shared `finalize_primary_evidence_root()` when `--primary-evidence-enforce` is set (operator-invoked after STOP; does not start/stop supervisor, daemon, or launchctl; non-authorizing).

**Post-closeout hook attach readiness (narrow vs full):** taxonomy §6a.0.8.1 records canonical attach surfaces for scheduler completion, Paper/Shadow/Testnet bounded adapters, and supervisor evidence pack. **Narrow durable-closeout attach hooks** are **implemented** on `main` (`DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true`; default-off; invoke [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) only; `DURABLE_CLOSEOUT_ATTACH_HOOK_V0_NON_AUTHORIZING=true`). **Full post-closeout automation** (phases 2–9 orchestration) remains **not implemented** (`POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false`; `FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false`). `hook_automation_owner_status=identified` is a Precheck label only. This contract remains **BLOCKED**; `PRE_FLIGHT_BLOCKED_LIFTED=false`; `READY_FOR_START=false`; no launchctl coupling, no Notion write, no Market global enablement, no AWS/S3/SSH/network, no scheduler/supervisor/runtime/Paper/Shadow/Testnet/Live authorization from attach hooks alone. See [Runtime Lane Taxonomy §6a.0.8.1](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md).

Post-stop pack wrapper: `scripts/ops/run_online_readiness_post_stop_pack_v0.sh` is the **operator-invoked** post-stop path after daemon/supervisor STOP; delegates to `pack_online_readiness_supervisor_evidence_v0.py`; optional `--p79-archive-verify` runs P79 `ARCHIVE_ROOT` verification only when explicitly set; does not start/stop supervisor, daemon, or launchctl; non-authorizing.

P79 offline archive manifest gate: `scripts/ops/p79_supervisor_health_gate_v1.sh` with `ARCHIVE_ROOT` (or `scripts/ops/p79_supervisor_evidence_manifest_verify_v0.py`) validates packed supervisor evidence (`supervisor_session_closeout_v0.json` + `MANIFEST.sha256` via shared `verify_manifest_sha256()`); mutually exclusive with runtime tick mode; non-authorizing; does not start/stop supervisor, daemon, or launchctl.

P101 post-stop operator hints: `scripts/ops/p101_stop_playbook_v1.sh` emits a non-executing hint block (`P101_POST_STOP_PRIMARY_EVIDENCE_OPERATOR_HINTS.txt`) after existing STOP semantics with copy-paste examples for `run_online_readiness_post_stop_pack_v0.sh` (optional `--p79-archive-verify`); P101 does not execute wrapper, pack, or P79 archive verify automatically—operator must invoke them explicitly after STOP (non-authorizing). P93 status dashboard and `scripts/ops/p91_audit_snapshot_runner_v1.sh` emit analogous non-executing post-stop hints referencing the same wrapper. In-process online-daemon automatic pack remains unimplemented; P91 runtime P79 tick `manifest.json` is not equivalent to §2a `MANIFEST.sha256` verification.

Bounded observation review scripts (`review_shadow_bounded_observation_evidence_v0.py`, `review_testnet_bounded_observation_evidence_v0.py`) support optional `--durable-run-root` (default off). When supplied after archive copy, review calls shared `validate_durable_primary_evidence_root()` to fail closed on `/tmp`-only roots, missing required durable files, invalid `MANIFEST.sha256`, or non-`PASS` durable `review&#47;REVIEW_RESULT.json`. Omitted flag preserves staging-only review. **Non-authorizing** — does not clear Preflight **BLOCKED** or grant runtime authority.

## 2a.1 Future-run primary evidence hard gate v0

```
RUN_PRIMARY_EVIDENCE_RETENTION_HARD_GATE_V0=true
FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
CLOSEOUT_REFERENCE_REQUIRED=true
RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
PE3_RUN_TYPE_APPLICABILITY_CONTRACT_V0=true
PE3_RUN_TYPE_MATRIX_DOCS_ANCHOR_V0=true
SLICE_PE2_COMPLETE=true
SLICE_PE3_DOCS_TESTS_ONLY=true
PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true
RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true
PREFLIGHT_REMAINS_BLOCKED=true
READY_FOR_OPERATOR_ARMING=false
GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false
PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true
SLICE_PE4_TESTS_ONLY=true
MANDATORY_DURABLE_CLOSEOUT_REQUIRED=true
CHECKSUM_VERIFY_REQUIRED=true
PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true
GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true
PE7_ORDER_CAPABILITY_OFFLINE_RUN_TYPE_APPLICABILITY_GUARD_V0=true
PRIMARY_EVIDENCE_ORDER_CAPABILITY_OFFLINE_APPLICABILITY_GUARD_IMPLEMENTED=true
ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_ROOT_HELPER_REFERENCED=true
ORDER_CAPABILITY_OFFLINE_ENFORCEMENT_OPT_IN_CONFIRMED=true
SLICE_PE7_DOCS_TESTS_ONLY=true
PE8_ORDER_CAPABILITY_FIXTURE_BINDING_OFFLINE_DURABLE_CLOSEOUT_WIRING_GUARD_V0=true
ORDER_CAPABILITY_FIXTURE_BINDING_PE_CLOSEOUT_WIRING_GUARD_IMPLEMENTED=true
FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_GUARDED=true
FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_COMPLETE=true
ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PE_WIRING_IMPLEMENTED=true
ADAPTER_PRIMARY_EVIDENCE_WIRING_REFERENCED=true
PRIMARY_EVIDENCE_RETENTION_V0_REFERENCED=true
PREFLIGHT_2A1_DURABLE_COMPLETION_DUTY_GUARDED=true
SLICE_PE8_DOCS_TESTS_ONLY=true
```

**Run-type applicability (run completion contract) v0:** The following lanes require durable primary evidence for **run completion** to be valid (docs/tests contract only; enforcement remains opt-in): **Paper**, **Shadow**, **Testnet**, **Live/Canary**, **bounded trial** (bounded observation/pilot adapters), **Scheduler** completion closeout, **Supervisor** evidence-pack closeout, **Order-Capability offline** (parked/read-only dry-validation adapter and fixture-binding runner lanes). Each lane: durable archive **outside `/tmp`**, `MANIFEST.sha256` verified (checksum manifest), closeout reference when applicable; **`/tmp`-only is insufficient**; **run completion is invalid** without durable primary evidence. Static guard matrix: `tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py` (`PE2_RUN_TYPE_GUARD_MATRIX`). Crosslink: `docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md` §2a.1. **Criteria-SSOT Repo-Internal Write/Lift §2a.1 reciprocal crosslink (A-04/C-04) v0:** bidirectional alignment with Owner Map §2a.1 Criteria-SSOT repo-internal write/lift applied reflection (`SECTION5_CRITERIA_SSOT_REPO_INTERNAL_WRITE_LIFT_GAP2A1_APPLIED_V0`); static guard: `tests/ops/test_gap2a1_primary_evidence_enforcement_drift_guard_contract_v0.py`. **Does not** activate enforcement. Criteria-SSOT repo-internal write/lift applied for §2a.1 slice (A-04/C-04). **Does not** lift Preflight **BLOCKED**, **does not** set `READY_FOR_OPERATOR_ARMING=true`.

Every future **Paper**, **Shadow**, **Testnet**, **Live/Canary**, **Scheduler**, **Supervisor**, **Order-Capability offline**, **Daemon**, **Smoke**, **bounded trial**, and **runtime adapter** path is **incomplete and invalid** for gate, readiness, or promotion decisions unless **all** of the following hold at run closeout:

1. **Durable archive root** — primary evidence bytes written under a path **outside `/tmp`** (operator `ARCHIVE_ROOT` or equivalent durable root; staging under `/tmp` alone does not qualify).
2. **Checksum manifest** — `MANIFEST.sha256` written over archived files and verified (`verify_manifest_sha256()` RC=0 or equivalent `shasum -a 256 -c` RC=0).
3. **Closeout reference** — a closeout artifact present and referencing the durable archive root (for example `scheduler_completion_closeout_v0.json`, `supervisor_session_closeout_v0.json`, or lane adapter closeout/review bundle per canonical owner).
4. **Postrun/review when applicable** — bounded observation adapters include review output (for example `REVIEW_RESULT.json`) with explicit verdict.

**Hard gate semantics (future runs):**

- Future run selectors, adapters, and opt-in enforcement paths **must reject or fail closed** when durable primary evidence retention cannot be guaranteed before `--execute` or non-dry-run start.
- A run that completes with `/tmp`-only artifacts is **`TMP_ONLY_EVIDENCE_INVALID`** — it must be treated as **not complete** regardless of exit code or operator narrative.
- **Evidence ≠ approval** — satisfying this hard gate does not clear Preflight **BLOCKED**, Shadow **STOP_IDLE**, HOLD, or grant Live/Testnet/broker authority.

**Mandatory durable closeout wiring (bounded Shadow/Testnet, future paths) v0:**

```
DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true
PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true
```

Future bounded **Shadow** and **Testnet** closeout paths that treat a run as **complete** for gate, readiness, or promotion **review input** must not claim completion when mandatory durable closeout wiring is unsatisfied: durable archive outside `/tmp`, `MANIFEST.sha256` verified (checksum), primary evidence present, and (when applicable) `durable_closeout_copy_verify_v0.py` invoked for material closeout copy — **contract/guard only**; enforcement remains opt-in. **Paper** bounded observation (`run_paper_only_bounded_observation_adapter_v0.py`) and **Scheduler** completion closeout (`scheduler_completion_closeout_v0.json`) follow the same §2a.1 hard-gate posture for run completion validity; `/tmp`-only remains insufficient.

**Gap4 output evidence ↔ Gap2a.1 dependency (PE-5 guard) v0:** Gap 4 output-evidence path completion **depends on** this §2a.1 primary-evidence lifecycle (`GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0`). Treating Gap 4 output paths as complete/valid without durable primary evidence, manifest/checksum verification, or while `/tmp`-only is **invalid** (`GAP4_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE`, `GAP4_COMPLETION_INVALID_WITHOUT_MANIFEST_VERIFY`). Crosslink: `docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md` (Gap 4 output/evidence paths criteria). Static guard: `tests/ops/test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py`. **Tests-only**; **does not** activate enforcement or arming.

**Order-Capability offline run-type applicability (PE-7 guard) v0:** Parked/read-only **Order-Capability offline** dry-validation lanes (`run_order_capability_dry_validation_adapter_v1.py`, `run_order_capability_fixture_binding_dry_validation_v1.py`) require durable primary evidence outside `/tmp`, `MANIFEST.sha256` verified, and shared `validate_order_capability_offline_durable_run_root()` when `--write-evidence` or equivalent operator-gated durable output is used — **run completion is invalid** without durable primary evidence. Canonical helper: `scripts/ops/primary_evidence_retention_v0.py` (`VALIDATE_ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_ROOT_V0=true`). Static guard: `tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py` (`PE2_RUN_TYPE_GUARD_MATRIX` row `order_capability_offline`). Crosslink: `docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md` §2a.1. **Parked/read-only** — does not authorize orderflow, cancel, execute, arming, Live, or Preflight lift; does not activate default enforcement (`ORDER_CAPABILITY_OFFLINE_ENFORCEMENT_OPT_IN_CONFIRMED=true`; `GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false`).

**Order-Capability fixture-binding offline durable closeout wiring (PE-8 guard) v0:**

```
ORDER_CAPABILITY_FIXTURE_BINDING_OFFLINE_DURABLE_CLOSEOUT_WIRING_V0=true
PE8_ORDER_CAPABILITY_FIXTURE_BINDING_OFFLINE_DURABLE_CLOSEOUT_WIRING_GUARD_V0=true
```

PE-7 establishes durable-completion applicability for both parked Order-Capability offline lanes. PE-8 closes the **adapter vs fixture-binding wiring asymmetry** (PE-4 analog): both offline owners import `scripts/ops/primary_evidence_retention_v0.py` (`require_durable_archive_root`, `write_manifest_sha256`, `validate_order_capability_offline_durable_run_root`) for operator-gated `--write-evidence`. `run_order_capability_dry_validation_adapter_v1.py` remains the **wired reference**; `run_order_capability_fixture_binding_dry_validation_v1.py` now mirrors adapter-parity wiring (`FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_COMPLETE=true`; `ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PE_WIRING_IMPLEMENTED=true`). Plan-only default unchanged; optional flat `--output` does not satisfy §2a.1 durable primary evidence. Operator-gated `--write-evidence` requires `GO_ORDER_CAPABILITY_FIXTURE_BINDING_RUNNER_PRIMARY_EVIDENCE_WIRING_IMPL_OPERATOR_GO_AUTOFILL_NO_RUN_V1`. Static guard: `tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py` (`PE8_ORDER_CAPABILITY_FIXTURE_BINDING_OFFLINE_CLOSEOUT_WIRING_LANE_MATRIX`; `test_pe8_order_capability_fixture_binding_offline_durable_closeout_wiring_guard_v0`); reciprocal tests in `tests/ops/test_run_order_capability_fixture_binding_dry_validation_v1.py`. Crosslink: `docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md` §2a.1. **Parked/read-only** — does not authorize orderflow, cancel, execute, arming, Live, runtime start, or Preflight lift; does not activate enforcement (`GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false`; `ORDER_CAPABILITY_OFFLINE_ENFORCEMENT_OPT_IN_CONFIRMED=true`).

Future bounded **Shadow** and **Testnet** closeout paths that treat a run as **complete** for gate, readiness, or promotion **review input** must retain a **durable primary evidence wiring contract**: after durable archive copy and `MANIFEST.sha256` verification on that copy, operators and closeout plans must invoke `review_shadow_bounded_observation_evidence_v0.py` or `review_testnet_bounded_observation_evidence_v0.py` with **`--durable-run-root`** pointing at the verified durable archive root (shared `validate_durable_primary_evidence_root()`). Review **`--durable-run-root` remains opt-in (default off)** in repository runtime at this stage — this anchor documents **mandatory closeout wiring for future paths**, not default-on review behavior, and **does not** modify adapter execute paths in this slice.

**Non-authorizing:** this wiring contract is **review/retention material only** — **Evidence ≠ approval**. It **does not** authorize runtime, scheduler, supervisor, daemon, Paper, Shadow, Testnet, Live, broker, exchange, or gate progression; **does not** clear Preflight **BLOCKED**, global **HOLD**, or GLB blockers.

### Tier-C + Shadow durable evidence archive anchors (non-authorizing) v0

```
TIER_C_SHADOW_DURABLE_EVIDENCE_REPO_STATIC_CROSSLINK_V0=true
EVIDENCE_ARCHIVE_ANCHOR_NOT_RUNTIME_AUTHORITY=true
TIER_C_POSITIVE_MANIFEST_FINALIZE_CONFIRMED=true
TIER_A_FAIL_CLOSED_CONFIRMED=true
TIER_B_PREFLIGHT_BLOCK_FAIL_CLOSED_CONFIRMED=true
SHADOW_DRYRUN_REHEARSAL_CONFIRMED=true
SHADOW_PRIMARY_EVIDENCE_DURABLE_CONFIRMED=true
SHADOW_HOLD_READINESS_HOLD=true
SHADOW_HOLD_LIFTED=false
PREFLIGHT_LIFT_DIRECTLY_ALLOWED=false
BL002_PATH_B_DIRECTLY_ALLOWED=false
PREFLIGHT_REMAINS_BLOCKED=true
READY_FOR_OPERATOR_ARMING=false
TESTNET_NOW_RECOMMENDED=false
TRADING_ACTION=false
ORDERS_CREATED=false
NETWORK_USED=false
PAPER_TEST_DATA_TOUCHED=false
```

`EXTERNAL_TIER_C_SHADOW_DURABLE_EVIDENCE_ARCHIVE_ROOT=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;`

Operator-verified durable archive bundles (2026-06-03 probe chain; read-only pointers):

- `EXTERNAL_REPO_WIDE_RANKING_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;planning&#47;repo_wide_next_system_step_ranking_after_class4_stop_idle_v0_20260603T175350Z&#47;`
- `EXTERNAL_TIER_C_EXECUTE_RETRY_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;runtime&#47;gap2a1_tier1_scheduler_tier_c_positive_manifest_execute_retry_v0_20260603T172211Z&#47;`
- `EXTERNAL_TIER_C_POST_EXECUTE_CLOSEOUT_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;closeout&#47;gap2a1_tier1_scheduler_tier_c_positive_manifest_post_execute_closeout_and_non_stop_ranking_v0_20260603T172509Z&#47;`
- `EXTERNAL_SHADOW_DRYRUN_EXECUTE_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;runtime&#47;shadow_bounded_dryrun_rehearsal_execute_v0_20260603T172859Z&#47;`
- `EXTERNAL_SHADOW_PRIMARY_EVIDENCE_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;runs&#47;shadow&#47;shadow_bounded_dryrun_rehearsal_20260603T172859Z&#47;` (durable primary evidence run root; `MANIFEST.sha256` present)
- `EXTERNAL_SHADOW_POST_EXECUTE_CLOSEOUT_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;closeout&#47;shadow_bounded_dryrun_rehearsal_post_execute_closeout_and_non_stop_ranking_v0_20260603T173011Z&#47;`
- `EXTERNAL_CLASS4_FINAL_MATRIX_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;closeout&#47;class4_external_final_decision_matrix_no_run_v0_20260603T174338Z&#47;`
- `EXTERNAL_SECTION5_FINAL_CLOSEOUT_POINTER=&#47;Users&#47;frnkhrz&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;closeout&#47;section5_no_lift_sequence_final_closeout_and_class4_decision_menu_v0_20260603T164910Z&#47;`

Crosslink: `docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md` — **Tier-C + Shadow durable evidence archive crosslink v0**. Static guard: `tests/ops/test_tier_c_shadow_durable_evidence_crosslink_contract_v0.py`. **Does not** activate §2a.1 default enforcement, **does not** lift preflight or Shadow-HOLD, **does not** authorize Testnet session execute (`TESTNET_NOW_RECOMMENDED=false`).

**Readiness ledger and gate snapshot (review-input-only):** offline outputs from `build_readiness_evidence_ledger_v0.py` and `report_readiness_gate_snapshot_v0.py` may report `READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE`, `READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE`, and `triple_lane_primary_evidence=true` when primary evidence manifests and reviews verify under durable archive roots. Those verdicts are **completeness and consistency signals only** — they **do not** authorize runtime, **do not** clear Preflight **BLOCKED**, **do not** lift **HOLD**, **do not** close GLB-014/GLB-015, and **do not** grant Paper/Shadow/Testnet/Live/broker/exchange activation. See GLB-015 clarification in [Master V2 Go-Live Blocker Register v0](../specs/MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md) §6.5.

**Scoped preflight exception (U3 pattern) v0:**

```
SCOPED_PREFLIGHT_EXCEPTION_U3_V0=true
ADAPTER_EXECUTE_EVIDENCE_ONLY=true
PREFLIGHT_MAY_REMAIN_BLOCKED_AFTER_RUN=true
SCOPED_EXCEPTION_NON_GENERALIZABLE=true
NO_AUTOMATIC_24H_72H_RERUN_REQUIRED=true
```

Under **BLOCKED** preflight and active global **HOLD**, a **bounded evidence-only adapter `--execute`** may be documented as a **scoped preflight exception (U3 pattern)** only when **all** of the following hold:

1. **Explicit operator archive record** — a durable, non-`/tmp` operator record outside the repository (for example `U3_SCOPED_PREFLIGHT_EXCEPTION_RECORD.md` under a planning slice) scopes the attempt as evidence-only; archive paths are **historical examples**, not mandatory runtime inputs.
2. **Stage-3 executing approval chain** — bounded adapters require `--approval-record` with executing approval fields; default plan-only mode remains unchanged.
3. **§2a.1 hard gate satisfied** — durable `ARCHIVE_ROOT`, `MANIFEST.sha256` verified, closeout and review present.
4. **Scope limits** — does **not** start scheduler, supervisor, daemon, launchctl, Paper, Testnet, Live, broker, exchange, P67/P72 workload, or WebUI server paths.

**U3 non-authorizing semantics:**

- Preflight **`status=BLOCKED`** and `activation_authorized=false` **may remain unchanged** after a successful scoped run.
- U3 **does not** clear global **HOLD**, **does not** close GLB-014/GLB-015, **does not** grant Live/Testnet/broker authority, and **does not** generalize to unbounded or recurring runs.
- One completed U3 exception **does not** authorize automatic **24h** or **72h** reruns or extensions.
- Executing approval records are **scoped and non-generalizable** — each future bounded attempt requires its own explicit operator record and approval chain.
- See GLB-015 §6.5 in [Master V2 Go-Live Blocker Register v0](../specs/MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md): evidence and closeouts remain **review inputs only**.

**Prior context (May 2026 testnet 240-min):** operator durable-copy check recorded `MISSING_SOURCE=true` for expired `/tmp` paths; reinforces that `/tmp`-only retention is insufficient for future governed runs.

**Implementation anchors (reuse-before-new):** shared helper `scripts/ops/primary_evidence_retention_v0.py` (`is_under_tmp`, `require_durable_archive_root`, `finalize_primary_evidence_root`, `verify_manifest_sha256`); bounded adapters (`run_*_bounded_observation_adapter_v0.py`); scheduler `--primary-evidence-enforce`; P67/P72 `primary_evidence_enforce=True`; offline supervisor pack + P79 archive verify; P101/P93 post-stop hints (operator-explicit). Default-off opt-in closeouts remain unchanged; this section states the **future-run invariant** operators and implementers must satisfy when treating a run as complete.

## 2b. Planning artifact durable retention v0

`PLANNING_ARTIFACT_DURABLE_RETENTION_REQUIRED=true`

`/tmp` may be used for scratch, staging, and short-lived working outputs. It is **not** durable storage for **material** planning, gate, closeout, or operator-decision artifacts that operators will rely on in later slices.

When an artifact is **material** to future decisions (for example merge closeouts, scoped HOLD operator records, GLB authority packets, Testnet readiness selectors, durable-copy results), it must **not** remain `/tmp`-only. Operators must copy it to a durable archive **outside `/tmp`**, preferably:

`/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_<id>/planning/<slice_or_context>/`

Each durable copy should include at minimum:

- the source report(s) or equivalent decision record
- a context file (for example `DURABLE_COPY_README.md`) stating source, meaning, and non-authorizing scope
- `MANIFEST.sha256` over the copied files (excluding the manifest line list itself)
- checksum verification evidence (for example `shasum -a 256 -c MANIFEST.sha256` with **RC=0**)

**Scope:** material decision artifacts only—not every scratch file, log fragment, or transient prompt under `/tmp`.

**Not primary runtime evidence:** planning, gate, and closeout copies under `planning&#47;` assist review and traceability; they do **not** by themselves satisfy §2a primary runtime evidence for Paper, Shadow, Testnet, or Live runs.

**Forbidden as durable artifact storage:**

- Notion pointer-only rows (index/navigation; not the archive of record)
- chat-summary-only evidence
- transcript-only evidence without durable archive copy

Repo docs state **policy**; durable artifact bytes remain in external archive paths. This section does **not** authorize scheduler execution, daemon activation, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order paths.

## 2b.1 Mandatory Durable Closeout Contract v0

```
MANDATORY_DURABLE_CLOSEOUT_CONTRACT_V0=true
MANDATORY_DURABLE_CLOSEOUT_DOCS_TESTS_ONLY=true
TMP_ONLY_CLOSEOUT_INCOMPLETE=true
MATERIAL_CLOSEOUT_REQUIRES_DURABLE_COPY=true
DURABLE_COPY_README_REQUIRED=true
MANIFEST_SHA256_REQUIRED=true
MANIFEST_VERIFY_RC_ZERO_REQUIRED=true
DURABLE_INDEX_OR_POINTER_REQUIRED=true
MERGE_POST_PR_CLOSEOUTS_INCLUDED=true
S3_NOT_CLOSEOUT_COMPLETION=true
NOTION_NOT_AUTHORITY=true
MARKET_DASHBOARD_NOT_AUTHORITY=true
SOURCE_TMP_NOT_CANONICAL=true
CLOSEOUT_DOES_NOT_AUTHORIZE_RUNTIME=true
```

**Purpose:** Define when a **material** closeout (planning, merge/post-PR, operator-decision, or evidence-chain record) is **complete** vs **incomplete** — **without** executing copy/verify in this contract slice and **without** duplicating §2a runtime primary evidence rules.

**Normative rule:** A material closeout that exists **only** under `/tmp` is **`TMP_ONLY_CLOSEOUT_INCOMPLETE`** and must not be treated as the canonical audit record, gate input, or promotion evidence — regardless of narrative, chat summary, or CI pass status.

### Incomplete vs complete (material closeouts)

A **material** closeout is **incomplete** unless **all** of the following hold on a durable destination **outside `/tmp`**:

1. Durable destination root exists (operator archive under `Peak_Trade_runtime_evidence_archive_<id>&#47;`, not `/tmp`).
2. Durable closeout directory exists at that root (for example `{archive_root}&#47;closeout&#47;{context}/` or `{archive_root}&#47;planning&#47;{slice}/` per §2b).
3. `DURABLE_COPY_README.md` exists in the durable closeout directory (`DURABLE_COPY_README_REQUIRED=true`).
4. `MANIFEST.sha256` exists over the durable closeout files (`MANIFEST_SHA256_REQUIRED=true`).
5. Manifest verify passes with **RC=0** (`MANIFEST_VERIFY_RC_ZERO_REQUIRED=true`; `shasum -a 256 -c MANIFEST.sha256` or shared `verify_manifest_sha256()` semantics).
6. A durable **index or pointer** exists (for example batch backfill index markdown, `archive_closeout_index` entry, or cross-reference in durable archive context) (`DURABLE_INDEX_OR_POINTER_REQUIRED=true`).

**Source `/tmp` may remain** as a non-deleted working copy, but **`SOURCE_TMP_NOT_CANONICAL=true`** — `/tmp` must not be the sole owner of a material closeout used for audit or downstream slices.

### Merge / post-PR closeouts explicitly included

`MERGE_POST_PR_CLOSEOUTS_INCLUDED=true`

Post-merge and post-PR operator closeout reports (for example `AFTER_*_MERGE_CLOSEOUT.md`) are **material** when used as evidence of merged slice state, canonical chain continuity, or operator handoff. They are **incomplete** if `/tmp`-only.

**Canonical durable merge-closeout owner pattern (observed, not exclusive timestamp):**

- `{operator_home}&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_<id>&#47;closeout&#47;`
- Observed owner example: `Peak_Trade_runtime_evidence_archive_20260520T161443Z&#47;closeout&#47;`
- Do **not** hardcode a single `<id>` as the only allowed archive; any durable `Peak_Trade_runtime_evidence_archive_*` root outside `/tmp` may qualify when index/pointer semantics are satisfied.

Planning-only closeouts under `{archive}&#47;planning&#47;` remain valid per §2b when the same manifest/readme/verify requirements are met.

### Relationship to §2a runtime primary evidence

§2a governs **runtime primary evidence** for Paper, Shadow, Testnet, Live, scheduler, supervisor, and adapter paths. This §2b.1 governs **material planning/merge/operator closeout completeness** only. Satisfying §2b.1 does **not** satisfy §2a and vice versa.

### Non-authorizing boundaries

- `S3_NOT_CLOSEOUT_COMPLETION=true` — S3 upload, object prefix, or export success does **not** complete a material closeout unless a local durable copy + manifest verify RC=0 + index/pointer exist (align with taxonomy §6a.3 download+verify acceptance).
- `NOTION_NOT_AUTHORITY=true` — Notion sync or projection rows do **not** complete or authorize closeouts.
- `MARKET_DASHBOARD_NOT_AUTHORITY=true` — Dashboard projection/status does **not** complete or authorize closeouts.
- `CLOSEOUT_DOES_NOT_AUTHORIZE_RUNTIME=true` — durable closeout completeness does **not** authorize runtime, scheduler clearance, testnet, live, broker, or Double Play decisions.

**Implementation note:** This contract is **normative/static only** (`MANDATORY_DURABLE_CLOSEOUT_DOCS_TESTS_ONLY=true`). Future operator scripts may enforce copy+verify; this slice does **not** execute copy, verify, or archive mutation.

Cross-reference: [Runtime Lane Taxonomy + Authority Levels Contract v0](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) §2 index; shared manifest helper [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) (reuse semantics only).

### Evidence Durable Closeout Retention RC v0 — index v0

**Release:** `EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0` · **Status:** **CORE COMPLETE** (SLICE-ER-1 + SLICE-ER-2; ER-3 optional deferred) · **UTC:** 2026-06-02 · **Recommended next larger release candidate** after `CYBERSECURITY_VISIBILITY_RELEASE_RC_V0` (CORE COMPLETE on `main` @ `f4be4e4848c1205d1f88d54bc76fe26ad0eff84d`). **Canonical repo owners (reuse — no parallel index):**

| Concern | Owner |
|---------|-------|
| §2a primary evidence retention invariant + §2a.1 future-run hard gate | this document (§2a / §2a.1) |
| §2b planning artifact durable retention + §2b.1 mandatory durable closeout | this document (§2b / §2b.1) |
| Primary evidence manifest/finalize helper | [primary_evidence_retention_v0.py](../../../scripts/ops/primary_evidence_retention_v0.py) |
| Durable closeout copy/verify helper (local-only; operator-invoked) | [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) |
| Primary evidence retention invariant guard | `tests&#47;ops&#47;test_primary_evidence_retention_invariant_contract_v0.py` |
| Primary evidence hard gate guard | `tests&#47;ops&#47;test_run_primary_evidence_retention_hard_gate_v0.py` |
| Durable closeout copy/verify guard | `tests&#47;ops&#47;test_durable_closeout_copy_verify_v0.py` |
| Mandatory durable closeout contract guard | `tests&#47;ops&#47;test_mandatory_durable_closeout_contract_v0.py` |
| CI audit reciprocal retention crosslink (PE-6 guard; read-only) | `docs&#47;ops&#47;CI_AUDIT_KNOWN_ISSUES.md` — `artifact_retention_or_evidence_gap` histogram linked to §2a.1 durable primary evidence / ER retention (`PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0`); defensive/derived/static only; **no ER SSOT duplication**; static guard: `tests&#47;ci&#47;test_cybersecurity_visibility_repo_static_histogram_artifact_retention_or_evidence_gap_crosslink_v0.py` |

**Release scope (complete):** **2 PRs** merged (**docs/tests/tooling-only**) — primary evidence retention (§2a/§2a.1), mandatory durable closeout (§2b.1), and existing helper/guard ownership consolidated without runtime, S3/rclone, or new parallel evidence surfaces.

**Prior releases complete (reference):**

- `OPERATOR_EXPERIENCE_RELEASE_RC_V0` — CORE COMPLETE
- `CYBERSECURITY_VISIBILITY_RELEASE_RC_V0` — CORE COMPLETE (CV-1 + CV-2 + CV-3 merged; CV3+ train after SLICE-CV-3 #4164)

**Durable operator pointers (archive only — not repo-ingested):**

| Token | Durable path |
|-------|--------------|
| Release planning bundle | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/evidence_durable_closeout_retention_rc_v0_planning_20260602T180921Z/` |
| SLICE-ER-1 docs-only start | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/evidence_durable_closeout_retention_rc_v0_slice_er1_docs_only_20260602T181115Z/` |
| ER final release closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/closeout/evidence_durable_closeout_retention_rc_v0_final_closeout_handoff_20260602T182534Z/` |
| Cyber final release closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/closeout/cybersecurity_visibility_release_rc_v0_final_closeout_handoff_20260602T180735Z/` |
| OE final release closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/closeout/operator_experience_release_rc_v0_final_release_closeout_handoff_20260602T174916Z/` |

**Slice decomposition (historical reference + status):**

| Order | Slice ID | Scope | Status |
|-------|----------|-------|--------|
| 1 | **SLICE-ER-1** | Docs-only: this release index in Preflight §2a/§2b.1 owner | **complete** (#3906) |
| 2 | **SLICE-ER-2** | Tests-only: extend existing `tests&#47;ops&#47;test_*retention*` and `tests&#47;ops&#47;test_*closeout*` guards only | **complete** (#3907) |
| 3 | **SLICE-ER-3** (optional) | Docs/tests: lightweight CI audit crosslink pointer only if ER-2 proves Preflight↔CI drift | **deferred** |

**Operational rules:**

- **No runtime** — no paper/shadow/testnet/live, no scheduler/daemon, no workflow dispatch from automation.
- **No retention enforcement activation** — ER-1 + ER-2 merged; this release index does **not** enable default-on primary evidence enforcement, does **not** activate closeout copy/verify, and does **not** claim retention is fully enforced repo-wide.
- **No AWS/S3/rclone/Notion** — no archive export, no Notion write, no external cloud mutation.
- **No trading authority** — no Master V2 / Double Play / execution / risk / governance / live gate changes.
- **Preflight remains BLOCKED** — `PRE_FLIGHT_BLOCKED_LIFTED=false`; `PREFLIGHT_REMAINS_BLOCKED=true`; this release index does **not** authorize future runs, does **not** set `READY_FOR_OPERATOR_ARMING`, and does **not** clear **STOP_IDLE**.
- **Reuse-before-new** — extend this Preflight owner and existing helper/guard modules; **no** parallel evidence index, readiness map, or handoff surface.
- **Canonical remains repo + durable Evidence Archive** — external archive paths are operator pointers only.
- **Do not start SLICE-ER-3** without proven Preflight↔CI histogram drift; CI audit carries reciprocal crosslinks by design (PE-6 strengthens Cyber↔ER artifact-retention guard; still non-authorizing).

**Cyber ↔ ER artifact-retention crosslink (PE-6 guard) v0:** CI audit `artifact_retention_or_evidence_gap` visibility is linked to §2a.1 durable primary evidence and ER closeout retention posture — defensive/derived/static only; `/tmp`-only insufficient; manifest/checksum verify required for valid completion semantics; no definitive R-001/R-002/R-007 mapping without authoritative INPUT_JSONL. Static guard: `tests/ci/test_cybersecurity_visibility_repo_static_histogram_artifact_retention_or_evidence_gap_crosslink_v0.py`. **Does not** activate enforcement or arming.

```text
EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0=true
PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0=true
CYBER_VISIBILITY_ARTIFACTS_RETENTION_LINKED_TO_PRIMARY_EVIDENCE_V0=true
ER_ARTIFACT_RETENTION_LINKED_TO_CYBER_VISIBILITY_V0=true
SLICE_ER1_COMPLETE=true
SLICE_ER2_COMPLETE=true
SLICE_ER3_DEFERRED=true
RETENTION_ENFORCEMENT_ACTIVATED=false
CLOSEOUT_ENFORCEMENT_ACTIVATED=false
PRE_FLIGHT_BLOCKED_LIFTED=false
PREFLIGHT_REMAINS_BLOCKED=true
READY_FOR_OPERATOR_ARMING=false
READY_FOR_START=false
NO_PREFLIGHT_LIFT=true
NO_ENFORCEMENT_ACTIVATION=true
NO_RUNTIME=true
NO_PAPER_SHADOW_TESTNET_LIVE=true
NO_AWS_S3_RCLONE=true
NOTION_WRITES=false
WORKFLOW_DISPATCH_EXECUTED=false
NO_TRADING_AUTHORITY_CHANGE=true
MASTER_V2_LOGIC_CHANGED=false
PARALLEL_EVIDENCE_INDEX_CREATED=false
REUSE_BEFORE_NEW_PASS=true
STOP_IDLE_VALID=true
```

## 2b.2 Closeout Enforcement Planning Contract v0

```
CLOSEOUT_ENFORCEMENT_PLANNING_CONTRACT_V0=true
CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true
CLOSEOUT_ENFORCEMENT_HELPER_IMPLEMENTED=true
CLOSEOUT_ENFORCEMENT_HELPER_NON_AUTHORIZING=true
CLOSEOUT_ENFORCEMENT_HELPER_DOES_NOT_AUTHORIZE_RUNTIME=true
CLOSEOUT_ENFORCEMENT_HELPER_DOES_NOT_AUTHORIZE_REMOTE_RUNNER_START=true
CLOSEOUT_ENFORCEMENT_NO_ARCHIVE_MUTATION=true
CLOSEOUT_ENFORCEMENT_NO_TMP_DELETE=true
CLOSEOUT_ENFORCEMENT_TMP_ONLY_INCOMPLETE=true
CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_DESTINATION_OUTSIDE_TMP=true
CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_COPY_README=true
CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_SHA256=true
CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true
CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_INDEX_OR_POINTER=true
CLOSEOUT_ENFORCEMENT_SOURCE_TMP_NOT_CANONICAL=true
CLOSEOUT_ENFORCEMENT_S3_NOT_COMPLETION=true
CLOSEOUT_ENFORCEMENT_NOTION_NOT_COMPLETION=true
CLOSEOUT_ENFORCEMENT_DASHBOARD_NOT_COMPLETION=true
CLOSEOUT_ENFORCEMENT_POST_MERGE_CLOSEOUT_SH_NOT_COMPLETION=true
CLOSEOUT_ENFORCEMENT_APPEND_CLOSEOUT_INDEX_NOT_CANONICAL_ARCHIVE_INDEX=true
CLOSEOUT_ENFORCEMENT_REQUIRED_BEFORE_REMOTE_IMPLEMENTATION_CHARTER=true
CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true
CLOSEOUT_ENFORCEMENT_DOES_NOT_AUTHORIZE_RUNTIME=true
PRE_FLIGHT_BLOCKED_LIFTED=false
READY_FOR_START=false
```

**Purpose:** Define the **enforcement plan** so material/post-merge closeouts cannot silently remain **`/tmp`-only** — classify helpers, record the **implemented** local durable closeout copy/verify helper, and state normative enforcement requirements — **without** duplicating §2b.1 completeness rules and **without** lifting Preflight **BLOCKED**, `READY_FOR_START`, remote runner start, or remote implementation-charter gates.

**Planning + helper posture:** `CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true` — this section remains the normative enforcement **contract** (static + tests). `CLOSEOUT_ENFORCEMENT_HELPER_IMPLEMENTED=true` — [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) ships on `main` under charter **OP-CLOSEOUT-HELPER-IMPL-V0** (local filesystem only; operator-invoked). `CLOSEOUT_ENFORCEMENT_HELPER_NON_AUTHORIZING=true` — helper **PASS** does **not** complete §2b.1, lift gates, or authorize runtime. `CLOSEOUT_ENFORCEMENT_NO_ARCHIVE_MUTATION=true` — this **contract slice** does **not** auto-write operator archives; the helper mutates durable destinations **only** when an operator explicitly runs it. `CLOSEOUT_ENFORCEMENT_NO_TMP_DELETE=true` — enforcement must not delete `/tmp` sources before verify passes; source artifacts may remain non-canonical per §2b.1.

### Relationship to §2b.1

§2b.1 defines **when** a material closeout is complete vs incomplete. This §2b.2 defines **how tooling must enforce** those rules and **classifies helpers** (including the implemented copy/verify helper). Satisfying §2b.2 planning review or running the helper does **not** replace §2b.1, does **not** by itself complete any closeout, and does **not** auto-index the archive — operators remain responsible for durable index/pointer under `{archive_root}&#47;closeout&#47;`.

### Current tooling classification (observed; not completion)

| Tool / surface | Role today | Closeout completion? |
|---|---|---|
| [post_merge_closeout.sh](../../../scripts/governance/post_merge_closeout.sh) | Git sync to `origin&#47;main`, optional PR branch cleanup, `safe_delete_merged_branches` dry-run | **`CLOSEOUT_ENFORCEMENT_POST_MERGE_CLOSEOUT_SH_NOT_COMPLETION=true`** — **not** §2b.1 durable copy/verify/index |
| [append_closeout_index.py](../../../scripts/ops/append_closeout_index.py) | Appends JSONL under repo-local `out/ops/index_post_merge_closeouts.jsonl` (or `PT_CLOSEOUT_INDEX` override) | **`CLOSEOUT_ENFORCEMENT_APPEND_CLOSEOUT_INDEX_NOT_CANONICAL_ARCHIVE_INDEX=true`** — navigation aid only; **not** canonical durable archive index |
| [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) | Operator-invoked local copy + `DURABLE_COPY_README.md` + `MANIFEST.sha256` + verify RC=0 (`OP-CLOSEOUT-HELPER-IMPL-V0`) | **`CLOSEOUT_ENFORCEMENT_HELPER_NON_AUTHORIZING=true`** — supports §2b.1 copy/readme/manifest/verify; **does not** auto-index archive `closeout&#47;`, authorize runtime, or lift gates |
| `{operator_home}&#47;Documents&#47;Peak_Trade_runtime_evidence_archive_*&#47;closeout&#47;` | Observed canonical durable closeout owner pattern (example archive id `20260520T161443Z`) | **Target owner** for material closeout bytes + manifest + durable index/pointer when §2b.1 complete |

**Gap (acknowledged):** Merge/post-PR slices through PR #3679–#3687 relied on **manual** operator durable copy/verify/index under the archive pattern above. The implemented helper reduces copy/verify friction but **does not** auto-write durable archive index/pointers or prevent tmp-only recurrence when operators skip it.

### Normative enforcement requirements (helper partially implements; full enforcement not granted)

Future material closeout enforcement must treat closeout as **incomplete** unless **all** of the following hold (align with §2b.1; additive enforcement semantics only):

1. **`CLOSEOUT_ENFORCEMENT_TMP_ONLY_INCOMPLETE=true`** — evidence existing **only** under `/tmp` is incomplete; must not be promoted to canonical audit input.
2. **`CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_DESTINATION_OUTSIDE_TMP=true`** — durable destination root outside `/tmp` (for example `Peak_Trade_runtime_evidence_archive_*`).
3. **`CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_COPY_README=true`** — `DURABLE_COPY_README.md` in durable closeout directory.
4. **`CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_SHA256=true`** — `MANIFEST.sha256` over durable closeout files.
5. **`CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true`** — manifest verify **RC=0** on durable tree (reuse `verify_manifest_sha256()` / `shasum -a 256 -c` semantics).
6. **`CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_INDEX_OR_POINTER=true`** — durable index markdown or pointer under archive `closeout&#47;` root (not repo-local JSONL alone).
7. **`CLOSEOUT_ENFORCEMENT_SOURCE_TMP_NOT_CANONICAL=true`** — `/tmp` source may remain until operator deletes; it is **not** canonical and must not be deleted before verify passes.

**Non-completion substitutes (explicit):**

- `CLOSEOUT_ENFORCEMENT_S3_NOT_COMPLETION=true` — S3 export/upload/prefix success does **not** complete enforcement (align §6a.3 / §6a.3.1 download+verify acceptance).
- `CLOSEOUT_ENFORCEMENT_NOTION_NOT_COMPLETION=true` — Notion projection/sync does **not** complete enforcement.
- `CLOSEOUT_ENFORCEMENT_DASHBOARD_NOT_COMPLETION=true` — Market Dashboard projection does **not** complete enforcement.

### Implemented durable closeout helper (non-authorizing)

Charter **OP-CLOSEOUT-HELPER-IMPL-V0** — [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py):

- **Local / operator-invoked** — copy into durable destination outside `/tmp`; preserve source `/tmp` until verify passes (`CLOSEOUT_ENFORCEMENT_NO_TMP_DELETE=true`).
- Writes `DURABLE_COPY_README.md`, generates `MANIFEST.sha256`, verifies durable tree **RC=0** (reuse `verify_manifest_sha256()` semantics).
- **Fail closed** on: missing source, verify RC≠0, destination under `/tmp` (without explicit flag), non-empty destination without `--force`.
- **Does not** write or update a **durable index/pointer** under `{archive_root}&#47;closeout&#47;` — operators remain responsible for archive index/pointer per §2b.1 item 6.
- **`CLOSEOUT_ENFORCEMENT_HELPER_DOES_NOT_AUTHORIZE_RUNTIME=true`** — no scheduler, daemon, Paper, Shadow, Testnet, Live, broker, or exchange authority.
- **`CLOSEOUT_ENFORCEMENT_HELPER_DOES_NOT_AUTHORIZE_REMOTE_RUNNER_START=true`** — no remote runner implementation or start.
- **`PRE_FLIGHT_BLOCKED_LIFTED=false`** and **`READY_FOR_START=false`** — helper does **not** clear Preflight **BLOCKED** or set start readiness.

This §2b.2 contract slice **does not** modify [post_merge_closeout.sh](../../../scripts/governance/post_merge_closeout.sh) to copy files and **does not** modify [append_closeout_index.py](../../../scripts/ops/append_closeout_index.py) to mutate archive roots.

### Bindings to existing contracts

- **§2b.1 Mandatory Durable Closeout Contract v0** — completeness rules owner; §2b.2 enforcement plan subordinate.
- **§2a Primary evidence retention invariant v0** — runtime primary evidence; orthogonal unless closeout references runtime runs.
- **Remote planning §6a.0–§6a.0.5** — remote Paper planning chain; merge closeouts for those slices remain §2b.1 material closeouts; `CLOSEOUT_ENFORCEMENT_REQUIRED_BEFORE_REMOTE_IMPLEMENTATION_CHARTER=true`.
- **S3 finalized evidence export §6a.3 / §6a.3.1** — transport planning only; S3 does not substitute for local durable closeout enforcement.

### Gates and non-authority

- `CLOSEOUT_ENFORCEMENT_REQUIRED_BEFORE_REMOTE_IMPLEMENTATION_CHARTER=true` — remote runner/host implementation charter must not proceed until closeout enforcement planning is reviewed **and** the copy/verify helper is chartered (**OP-CLOSEOUT-HELPER-IMPL-V0**); the helper alone does **not** unlock full enforcement or implementation charter.
- `CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true` — remote dry command template slices (taxonomy §6a.0.5 gate) require this §2b.2 contract; dry templates must **not** invoke the closeout helper (taxonomy §6a.0.7).
- `CLOSEOUT_ENFORCEMENT_DOES_NOT_AUTHORIZE_RUNTIME=true` — enforcement planning and helper **PASS** do **not** authorize scheduler, daemon, Paper, Shadow, Testnet, Live, broker, exchange, remote runner start, or gate clearance.

Cross-reference: [Runtime Lane Taxonomy + Authority Levels Contract v0](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) §2 index; §6a.0.5 dry-template gate; §6a.0.7 dry-template non-invocation of helper; [test_closeout_enforcement_planning_contract_v0.py](../../../tests/ops/test_closeout_enforcement_planning_contract_v0.py); [test_durable_closeout_copy_verify_v0.py](../../../tests/ops/test_durable_closeout_copy_verify_v0.py).

### Evidence Durable Enforcement Readiness Review RC v0 — EER1 crosslink v0

**Release:** `EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0` · **Slice:** `SLICE-EER-1` · **Operator-GO:** `GO_SLICE_EER1_EVIDENCE_ENFORCEMENT_READINESS_REVIEW_INDEX_V0` · **Readiness review index only** — binds this §2b.2 closeout enforcement planning posture with §2a.1 durable primary evidence / manifest verification, SECTION5 §2a.1 Gap-2a.1 contract, and completed prerequisite RCs (PE run-completion **CORE COMPLETE** after PE-6; ER **CORE COMPLETE**; CV3+ **CORE COMPLETE** after SLICE-CV-3 #4164). Meta-index: `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **§ Evidence Durable Enforcement Readiness Review RC v0 — index v0**. Static guards: `tests/ops/test_paper_shadow_247_preflight_contract_v0.py`, `tests/ops/test_primary_evidence_retention_invariant_contract_v0.py`. **Does not** activate enforcement, **does not** lift Preflight **BLOCKED**, **does not** set `READY_FOR_OPERATOR_ARMING=true`.

```text
EVIDENCE_DURABLE_ENFORCEMENT_READINESS_REVIEW_RC_V0_STARTED=true
EER1_READINESS_REVIEW_INDEX_COMPLETE=true
PRIMARY_EVIDENCE_RUN_COMPLETION_CONTRACT_RC_V0_STATUS=CORE_COMPLETE_AFTER_PE6
CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STATUS=CORE_COMPLETE_AFTER_CV3
CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true
CLOSEOUT_ENFORCEMENT_ACTIVATED=false
GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false
RETENTION_ENFORCEMENT_ACTIVATED=false
ENFORCEMENT_ACTIVATED=false
MANIFEST_VERIFY_REQUIRED=true
PREFLIGHT_REMAINS_BLOCKED=true
READY_FOR_OPERATOR_ARMING=false
```

## 2b.3 Durable closeout adapter validation operator SSOT v0

```
PREFLIGHT_DURABLE_CLOSEOUT_ADAPTER_VALIDATION_SSOT_V0=true
PREFLIGHT_DURABLE_CLOSEOUT_ADAPTER_VALIDATION_DOCS_TESTS_ONLY=true
DURABLE_CLOSEOUT_IDENTICAL_SOURCE_DEST_REJECTED=true
DURABLE_CLOSEOUT_ADAPTER_PRE_INVOKE_VALIDATION=true
SCHEDULER_SUPERVISOR_DURABLE_CLOSEOUT_PRE_INVOKE_VALIDATION=true
VALIDATE_DURABLE_CLOSEOUT_PATHS_REUSED=true
HELPER_PARALLEL_LOGIC_CREATED=false
BOUNDED_ADAPTER_OBSERVATION_CLOSEOUT_DECOUPLED=true
DURABLE_CLOSEOUT_FORCE_REQUIRES_DISTINCT_PATHS=true
BLOCKER_HINT_MACHINE_READABLE=true
AUTHORITATIVE_STATUS_HIERARCHY_V0=true
HISTORICAL_PRE_RECOVERY_FAIL_NOT_CURRENT_STATUS=true
PREFLIGHT_REMAINS_BLOCKED=true
PRE_FLIGHT_BLOCKED_LIFTED=false
READY_FOR_OPERATOR_ARMING=false
CLOSEOUT_DOES_NOT_AUTHORIZE_RUNTIME=true
```

**Purpose:** Operator/SSOT sync after PR **#4127** (helper identical/equivalent source-dest guard) and PR **#4128** (bounded observation adapter closeout pre-invoke validation). This section documents runtime guard semantics already on `main`; it **does not** re-implement helpers, **does not** lift Preflight **BLOCKED**, and **does not** authorize Paper/Shadow/Testnet/Live/scheduler/daemon execution.

### PR #4127 — helper source/dest guard (reuse; no parallel logic)

[durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) fail-closed rejects **identical or equivalent** `--source-dir` and `--dest-dir` paths (`_validate_source_dest_distinct`). Resolved paths that are the same directory are **rejected** regardless of narrative or observation PASS. Operators must use a **separate snapshot source directory** with a **distinct** durable destination, or satisfy helper `--force` **only when source and dest actually differ** (not as a bypass for identical paths).

Static guard: [test_durable_closeout_copy_verify_v0.py](../../../tests/ops/test_durable_closeout_copy_verify_v0.py).

### PR #4128 — bounded adapter closeout validation (decoupled from observation PASS)

Paper, Shadow, and Testnet bounded observation adapters ([run_paper_only_bounded_observation_adapter_v0.py](../../../scripts/ops/run_paper_only_bounded_observation_adapter_v0.py), [run_shadow_bounded_observation_adapter_v0.py](../../../scripts/ops/run_shadow_bounded_observation_adapter_v0.py), [run_testnet_bounded_observation_adapter_v0.py](../../../scripts/ops/run_testnet_bounded_observation_adapter_v0.py)) call `validate_durable_closeout_invoke_paths()` **before** invoking the helper when `--invoke-durable-closeout-v0` is set. The adapter **reuses** `_validate_source_dest_distinct` and `_dest_has_content` from the helper module — **no parallel guard logic**.

When validation blocks closeout copy:

- `BOUNDED_ADAPTER_DURABLE_CLOSEOUT_VALIDATION_BLOCKED=true`
- `BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS=blocked`
- `BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC=not_run`
- `BOUNDED_ADAPTER_OBSERVATION_CLOSEOUT_DECOUPLED=true` — observation/review **PASS** does **not** imply closeout copy **PASS**; operators must treat closeout status separately.

Static guard: [test_bounded_adapter_invoke_durable_closeout_v0.py](../../../tests/ops/test_bounded_adapter_invoke_durable_closeout_v0.py).

### Scheduler and supervisor attach-hook closeout pre-invoke validation (taxonomy §6a.0.8.1)

Scheduler completion ([run_scheduler.py](../../../scripts/run_scheduler.py) with `--invoke-durable-closeout-after-completion-v0`) and supervisor evidence pack ([pack_online_readiness_supervisor_evidence_v0.py](../../../scripts/ops/pack_online_readiness_supervisor_evidence_v0.py) with `--invoke-durable-closeout-after-pack-v0`) call the same shared `validate_durable_closeout_invoke_paths()` **before** invoking [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) — **reuse only**; **no parallel guard logic** (`SCHEDULER_SUPERVISOR_DURABLE_CLOSEOUT_PRE_INVOKE_VALIDATION=true`; `VALIDATE_DURABLE_CLOSEOUT_PATHS_REUSED=true`; `HELPER_PARALLEL_LOGIC_CREATED=false`).

When validation blocks closeout copy:

- `SCHEDULER_DURABLE_CLOSEOUT_VALIDATION_BLOCKED=true` or `SUPERVISOR_PACK_DURABLE_CLOSEOUT_VALIDATION_BLOCKED=true`
- `SCHEDULER_DURABLE_CLOSEOUT_STATUS=blocked` or `SUPERVISOR_PACK_DURABLE_CLOSEOUT_STATUS=blocked`
- `SCHEDULER_DURABLE_CLOSEOUT_HELPER_RC=not_run` or `SUPERVISOR_PACK_DURABLE_CLOSEOUT_HELPER_RC=not_run`

Static guards: [test_scheduler_durable_closeout_hook_pass_through_v0.py](../../../tests/ops/test_scheduler_durable_closeout_hook_pass_through_v0.py); [test_supervisor_pack_durable_closeout_hook_pass_through_v0.py](../../../tests/ops/test_supervisor_pack_durable_closeout_hook_pass_through_v0.py).

Cross-surface validate-paths parity matrix static guard: [test_post_closeout_hook_attach_readiness_bridge_v0.py](../../../tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py) (`VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true`; all five §6a.0.8.1 attach surfaces including Testnet; Shadow/Testnet Paper import delegation; Scheduler/Supervisor invoke-time import; `NEW_PARALLEL_VALIDATION_LOGIC_CREATED=false`).

Cross-surface post-invoke result-classification parity matrix static guard: [test_post_closeout_hook_attach_readiness_bridge_v0.py](../../../tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py) (`POST_INVOKE_RESULT_CLASSIFICATION_MATRIX_GUARD_V0=true`; `ALL_FIVE_ATTACH_HOOK_SURFACES_RESULT_CLASSIFICATION_COVERED=true`; Paper canonical `STATUS`/`HELPER_RC`/`NON_AUTHORIZING` emit; Shadow/Testnet Paper import delegation; Scheduler/Supervisor prefix-scoped emit with blocked-path classification and invoked-path `EXIT_CODE` fail-closed surrogate; `SCHEDULER_RESULT_CLASSIFICATION_SURFACE_GUARDED=true`; `SUPERVISOR_RESULT_CLASSIFICATION_SURFACE_GUARDED=true`; `STATUS_CLASSIFICATION_GUARDED=true`; `HELPER_RC_CLASSIFICATION_GUARDED=true`; `NON_AUTHORIZING_CLASSIFICATION_GUARDED=true`; `NEW_PARALLEL_CLASSIFICATION_LOGIC_CREATED=false`).

Cross-surface bounded-adapter CLI-args parity matrix static guard: [test_post_closeout_hook_attach_readiness_bridge_v0.py](../../../tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py) (`VALIDATE_CLI_ARGS_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true`; `ALL_BOUNDED_ADAPTER_ATTACH_SURFACES_CLI_ARGS_MATRIX_COVERED=true`; Paper canonical `validate_durable_closeout_invoke_cli_args()` + `add_bounded_adapter_durable_closeout_cli_args()`; Shadow/Testnet Paper import delegation; invoke-flag coupling and dest-outside-`/tmp` fail-closed rules; `--durable-closeout-force` force-scope registration; `PAPER_CLI_ARGS_SURFACE_GUARDED=true`; `SHADOW_CLI_ARGS_IMPORT_CHAIN_GUARDED=true`; `TESTNET_CLI_ARGS_SURFACE_GUARDED=true`; `VALIDATE_DURABLE_CLOSEOUT_INVOKE_CLI_ARGS_GUARDED=true`; `DURABLE_CLOSEOUT_INVOKE_FLAG_CLI_ARGS_GUARDED=true`; `FORCE_SCOPE_BLOCKER_HINT_CLI_ARGS_GUARDED=true`; `NEW_PARALLEL_CLI_ARGS_VALIDATION_LOGIC_CREATED=false`). Scheduler/Supervisor out of scope (distinct attach-hook CLI shapes).

Cross-surface post-invoke dest manifest-verify RC parity matrix static guard: [test_post_closeout_hook_attach_readiness_bridge_v0.py](../../../tests/ops/test_post_closeout_hook_attach_readiness_bridge_v0.py) (`DEST_MANIFEST_VERIFY_RC_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true`; `ALL_FIVE_ATTACH_HOOK_SURFACES_DEST_MANIFEST_VERIFY_RC_COVERED=true`; canonical helper `durable_closeout_copy_verify_v0.py` emits `DURABLE_CLOSEOUT_DEST_MANIFEST_VERIFY_RC`; Paper canonical helper invoke chain with `BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC` surrogate; Shadow/Testnet Paper import delegation without parallel dest manifest RC emit; Scheduler/Supervisor prefix-scoped helper invoke with `EXIT_CODE` surrogate; `PAPER_DEST_MANIFEST_VERIFY_RC_SURFACE_GUARDED=true`; `SHADOW_DEST_MANIFEST_VERIFY_RC_IMPORT_CHAIN_GUARDED=true`; `TESTNET_DEST_MANIFEST_VERIFY_RC_SURFACE_GUARDED=true`; `SCHEDULER_DEST_MANIFEST_VERIFY_RC_SURFACE_GUARDED=true`; `SUPERVISOR_DEST_MANIFEST_VERIFY_RC_SURFACE_GUARDED=true`; `HOOK_ATTACH_AFTER_MANIFEST_VERIFY_RC_ZERO_ONLY_GUARDED=true`; `NEW_PARALLEL_MANIFEST_RC_CLASSIFICATION_LOGIC_CREATED=false`).

**Force-scope note:** bounded adapters expose `--durable-closeout-force`; scheduler and supervisor attach hooks do **not** expose a separate force flag in this slice — non-empty dest without force remains blocked (same as bounded adapters without force).

### `--durable-closeout-force` (adapter) vs `--force` (helper)

| Flag | Surface | Safe use |
|------|---------|----------|
| `--durable-closeout-force` | bounded adapter (`--invoke-durable-closeout-v0`) | Only when `--durable-closeout-dest-dir` is **non-empty** and source/dest are **distinct** paths (for example overwrite of an existing durable tree from a separate snapshot source). **Not** a bypass for identical/equivalent source==dest. |
| `--force` | [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) | Same rule: distinct source/dest required; permits overwrite when destination already has content. |

Unsafe pattern (blocked): same resolved path for archive source and durable closeout destination with or without force flags.

### `BLOCKER_HINT` (machine-readable operator recovery)

When closeout copy is blocked, adapters emit machine-readable hints for operator recovery:

| Token | Meaning | Operator recovery |
|-------|---------|-------------------|
| `durable_closeout_identical_source_dest` | Source and dest resolve to the same path | Copy from a **separate snapshot source directory**; ensure dest is a **distinct** durable path outside `/tmp`. |
| `durable_closeout_dest_non_empty_without_force` | Destination exists and is non-empty without `--durable-closeout-force` | Use a fresh dest, or `--durable-closeout-force` only with **distinct** source/dest (or separate snapshot source). |

Machine line shapes (non-authorizing):

- `BOUNDED_ADAPTER_DURABLE_CLOSEOUT_BLOCKER_HINT=<token>`
- `SCHEDULER_DURABLE_CLOSEOUT_BLOCKER_HINT=<token>`
- `SUPERVISOR_PACK_DURABLE_CLOSEOUT_BLOCKER_HINT=<token>`
- `BLOCKER_HINT=<token>` in adapter `START_RETURN_CODE` artifact when execute returns blocked closeout

Hints point to **snapshot-source recovery** or appropriate force scope; they **do not** authorize runtime, lift Preflight **BLOCKED**, or clear **HOLD**.

### Authoritative status hierarchy (post-recovery vs historical pre-recovery FAIL)

When durable run/closeout bundles contain **divergent** status fields — for example historical `RUN_CLOSEOUT.md` or `RESULT_SUMMARY.env` recording a **pre-recovery FAIL** (identical source/dest, missing force, or `/tmp`-only closeout) while later **snapshot-recovery** artifacts show **PASS**:

**Authoritative current status** (when `MANIFEST_VERIFY_RC=0` on the recovery/analysis bundle):

1. **`MACHINE_SUMMARY.env`** in the recovery or post-run analysis bundle
2. **Recovery artifacts** (for example snapshot-source re-copy, durable closeout verify RC=0, analysis bundle verdict)
3. **Post-run analysis bundle** with verified manifest

**Subordinate / historical only:**

- Pre-recovery `RUN_CLOSEOUT.md` / `RESULT_SUMMARY.env` FAIL lines — **traceability only**; must **not** be promoted as the current run FAIL when recovery PASS + analysis PASS + `MANIFEST_VERIFY_RC=0` are present.

**Paper-L2 120min hold-binding context (observed):** bounded observation may **PASS** while closeout copy was **blocked** until snapshot-source recovery; `NEXT_TEST_NECESSITY=false` after analysis PASS does **not** imply Preflight lift.

This hierarchy is **operator SSOT for status interpretation** only — **Evidence ≠ approval**; Preflight remains **BLOCKED** (`PREFLIGHT_REMAINS_BLOCKED=true`; `PRE_FLIGHT_BLOCKED_LIFTED=false`).

Cross-reference: §2b.2 helper fail-closed rules; §2a.1 primary evidence hard gate; §2b.1 material closeout completeness; [Runtime Lane Taxonomy + Authority Levels Contract v0](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) **§6a.0.8.1** post-closeout automation hook owner precheck (canonical bounded-adapter attach surfaces; narrow durable-closeout hooks default-off; **non-authorizing**).

## 2c. Preflight Gate Repo-Internal Write/Lift Applied Reflection v0

PREFLIGHT_GATE_REPO_INTERNAL_WRITE_LIFT_V0=true
PREFLIGHT_GATE_REPO_INTERNAL_WRITE_LIFT_APPLIED_V0=true
PREFLIGHT_GATE_DECISION_ACCEPTED=true
PREFLIGHT_EVIDENCE_SATISFIED=true
DOCS_ONLY_EXECUTE_SLICE=true
PREFLIGHT_GATE_LIFTED=false
PREFLIGHT_GATE_LIFT_AUTHORIZED=false
PRE_FLIGHT_BLOCKED_LIFTED=false
PREFLIGHT_REMAINS_BLOCKED=true
PILOT_CHECKLIST_VERDICT=CONDITIONAL
PILOT_CHECKLIST_GO_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
LIVE_AUTHORIZED=false
ALL_AUTHORITY_FLAGS_REMAIN_FALSE=true

This criteria-reflection block records the bounded Preflight Umbrella Gate repo-internal write/lift applied posture for evidence-satisfied and decision-accepted reflection only. Contract [§2](#2-canonical-activation-status) canonical activation status and [§4](#4-status-model) status model remain **BLOCKED**; this slice **does not** set `PREFLIGHT_REMAINS_BLOCKED=false`, **does not** set `PREFLIGHT_GATE_LIFTED=true`, **does not** authorize Paper/Shadow 24/7 activation, scheduler execute, pilot GO, arming, or live, and **does not** authorize runtime, broker, exchange, or order activity.

Evidence-satisfied classification reflected here is **not** Preflight lift. §4 status discipline and §5 mandatory preflight dimensions remain binding.

**Durable archive chain (read-only pointers; non-authorizing):**

- Prep: `preflight_gate_repo_internal_write_lift_prep_no_run_v1_20260607T054243Z`
- Operator decision: `preflight_gate_repo_internal_write_lift_operator_decision_record_no_run_v1_20260607T054506Z`
- Execute plan: `preflight_gate_repo_internal_write_lift_execute_plan_no_run_v1_20260607T054710Z`
- Execute confirmation: `preflight_gate_repo_internal_write_lift_execute_operator_confirmation_no_run_v1_20260607T054854Z`

Archive root: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/runtime/` (external durable evidence; not a runtime input).

## 3. Non-authority

The following are **not** trading authority, readiness approval, evidence approval, promotion, Master V2 / Double Play approval, or Live/Testnet approval:

- this contract and its status fields;
- scheduler dry-run output;
- WebUI Paper/Shadow summary or other read models;
- CI shadow/paper smoke artifacts;
- any future read-only preflight JSON emitted from this contract.

Normative **lane IDs** and **authority levels** for all runtime/evidence surfaces are indexed in **[Runtime Lane Taxonomy + Authority Levels Contract v0](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md)**. That spec is **non-authorizing**; this contract remains the owner of §2a/§2b/§2b.1 retention and preflight **BLOCKED** status.

**Runtime Lane Taxonomy CI_AUDIT ↔ Preflight reciprocal crosslink (reference-only — docs/tests guard):** Reciprocal crosslink guard: `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **§ Runtime Lane Taxonomy CI_AUDIT ↔ Preflight reciprocal crosslink — docs/tests-only guard v1**; CI_AUDIT / DOCS_TRUTH_MAP reciprocal guard: `tests/ops/test_remote_runtime_contract_docs_guard_v0.py`. Static guards: `tests/ops/test_runtime_lane_taxonomy_authority_levels_contract_v0.py`, `tests/ops/test_paper_shadow_247_preflight_readiness_peer_static_crosslink_contract_v0.py`. **Docs/tests-only**; **does not** lift Preflight **BLOCKED**; **does not** set `READY_FOR_OPERATOR_ARMING=true`. `RUNTIME_LANE_TAXONOMY_CI_AUDIT_PREFLIGHT_RECIPROCAL_CROSSLINK_GUARD_V1=true`; `PREFLIGHT_REMAINS_BLOCKED=true`; `READY_FOR_OPERATOR_ARMING=false`.

**Scheduler Boundary Hard Block CI_AUDIT ↔ Preflight reciprocal crosslink (reference-only — docs/tests guard):** Reciprocal crosslink guard: `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **§ Scheduler Boundary Hard Block CI_AUDIT ↔ Preflight reciprocal crosslink — docs/tests-only guard v1**; CI_AUDIT / DOCS_TRUTH_MAP reciprocal guard: `tests/ops/test_remote_runtime_contract_docs_guard_v0.py`. Static guards: `tests/ops/test_scheduler_boundary_hard_block_contract_v0.py`, `tests/ops/test_gap4_req_a_300s_hold_binding_profile_contract_v0.py`, `tests/ops/test_paper_l2_120min_hold_binding_profile_contract_v0.py`. **Docs/tests-only**; **does not** lift Preflight **BLOCKED**; **does not** set `READY_FOR_OPERATOR_ARMING=true`. `SCHEDULER_BOUNDARY_HARD_BLOCK_CI_AUDIT_PREFLIGHT_RECIPROCAL_CROSSLINK_GUARD_V1=true`; `PREFLIGHT_REMAINS_BLOCKED=true`; `READY_FOR_OPERATOR_ARMING=false`.

Future **remote Paper-only** command/metadata/gate shape (non-executing; no runtime unlock): taxonomy **§6a.0 Remote Runtime Command Contract v0** in the same spec — backend-not-lane; reuses §2a/§2a.1/§2b.1, scheduler boundary guard, and HOLD binding; **does not** authorize remote execution in this repository slice.

Future **remote Paper-only** non-executable approval/command packet (binds §6a.0.1 preflight JSON + guard/HOLD/approval/Registry/§2a/§2b.1 pointers; no runner/start unlock): taxonomy **§6a.0.2 Remote paper approval/command packet contract v0** — `REMOTE_PAPER_PACKET_READY_FOR_START=false`; extends bounded adapter approval chain only; **does not** authorize remote runner implementation or start.

Future **remote host inventory** planning-only fields (non-provisioning; no connect/network/AWS/SSH/systemd/GHA; no runtime unlock): taxonomy **§6a.0.3 Remote host inventory planning contract v0** — `REMOTE_HOST_INVENTORY_PLANNING_ONLY=true`; `REMOTE_HOST_INVENTORY_READY_FOR_IMPLEMENTATION_CHARTER=false`; binds §6a.0–§6a.0.2 + Registry + §2a/§2b.1; **does not** provision, inspect, or authorize hosts.

Future **remote cost/kill/orphan safety** planning-only requirements (no kill/terminate/process-control/network/AWS/SSH/systemd/GHA; no runtime unlock): taxonomy **§6a.0.4 Remote cost/kill/orphan safety contract v0** — `REMOTE_COST_KILL_ORPHAN_PLANNING_ONLY=true`; `REMOTE_COST_KILL_ORPHAN_READY_FOR_IMPLEMENTATION_CHARTER=false`; binds §6a.0–§6a.0.3 + §2a/§2b.1; implementation charter blocked without declared safety fields; **does not** stop, kill, or terminate hosts.

Future **remote paper packet assembly validator** planning-only cross-check contract (offline artifact consistency; no CLI/runner/dry-template unlock): taxonomy **§6a.0.5 Remote paper packet assembly validator planning contract v0** — `REMOTE_PAPER_PACKET_VALIDATOR_PLANNING_ONLY=true`; `REMOTE_PAPER_PACKET_VALIDATOR_READY_FOR_DRY_COMMAND_TEMPLATE=false`; binds §6a.0.1–§6a.0.4 fixtures + Registry v1; dry-template blocked until **§2b.2 Closeout Enforcement Planning Contract v0** review; **does not** approve implementation or start.

**Remote paper validator CLI** contract + implemented offline CLI (local JSON validation only; no runner/dry-template/start unlock): taxonomy **§6a.0.6 Remote paper validator CLI contract v0** — `REMOTE_PAPER_VALIDATOR_CLI_IMPLEMENTED=true`; `validate_remote_paper_packet_v0.py`; `REMOTE_PAPER_VALIDATOR_CLI_PASS_DOES_NOT_AUTHORIZE_RUNTIME=true`; `REMOTE_PAPER_VALIDATOR_CLI_READY_FOR_START=false`; `REMOTE_PAPER_VALIDATOR_CLI_PREFLIGHT_BLOCKED_LIFTED=false`; `REMOTE_RUNNER_START_PERMITTED=false`; **does not** authorize runtime, remote runner start, live, testnet, or Stage-3 start charter.

Future **remote paper dry command template** planning-only contract (non-executable illustrative review steps; no runnable shell; not in approval packet; not emitted by Validator CLI): taxonomy **§6a.0.7 Remote paper dry command template planning contract v0** — `DRY_COMMAND_TEMPLATE_PLANNING_ONLY=true`; `DRY_COMMAND_TEMPLATE_DOES_NOT_INVOKE_CLOSEOUT_HELPER=true`; `DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false`; `DRY_COMMAND_TEMPLATE_READY_FOR_START=false`; Preflight **BLOCKED** unchanged; **does not** authorize runtime, remote runner, or invoke [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py); live/testnet forbidden.

**Closeout enforcement planning** + implemented non-authorizing helper: **§2b.2 Closeout Enforcement Planning Contract v0** — `CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true`; `CLOSEOUT_ENFORCEMENT_HELPER_IMPLEMENTED=true`; [durable_closeout_copy_verify_v0.py](../../../scripts/ops/durable_closeout_copy_verify_v0.py) (`OP-CLOSEOUT-HELPER-IMPL-V0`); classifies `post_merge_closeout.sh` and `append_closeout_index.py` as non-completion; `CLOSEOUT_ENFORCEMENT_HELPER_NON_AUTHORIZING=true`; binds §2b.1 + §2a + remote §6a.0–§6a.0.5 + S3 §6a.3; `PRE_FLIGHT_BLOCKED_LIFTED=false`; `READY_FOR_START=false`; **does not** authorize runtime or remote runner start.

**S3 finalized evidence export dry preflight CLI** (local-only transport planning; no upload/download/network): taxonomy **§6a.3 / §6a.3.1** — `S3_EXPORT_PREFLIGHT_CLI_IMPLEMENTED=true`; [preflight_s3_finalized_evidence_export_v0.py](../../../scripts/ops/preflight_s3_finalized_evidence_export_v0.py); `--dry-run` + `--no-network` required; non-executing `--export-prefix-plan`; `S3_EXPORT_PREFLIGHT_CLI_NON_AUTHORIZING=true`; `S3_UPLOAD_AUTHORITY=false`; `PRE_FLIGHT_BLOCKED_LIFTED=false`; `READY_FOR_START=false`; **does not** authorize runtime, remote runner start, or Stage-3 start charter.

## 3a. Futures / perpetual planning boundary (BTC/USD proxy evidence)

Symbols and surfaces such as **BTC/USD**, **BTC-USD**, **Bitcoin USD**, or **BTCUSDT** may appear in this repository as WebUI defaults, spot-style fixtures, Class-A smoke paths, or **public REST market-data captures**. Treat that evidence as **technical proxy / spot-smoke instrumentation only**.

Proxy-style BTC evidence may still help validate scheduler wiring, logging discipline, evidence roots, path hygiene, and other **non-trading-authority** mechanics. It must **not** be interpreted as:

- Futures or perpetual (**perp**) readiness,
- Futures Shadow 24/7 readiness,
- approval of continuous daemon operation,
- clearance for no-active-run preflight “done” by itself,
- Testnet approval, Live approval, broker/exchange connectivity, or order submission.

Futures / perpetual Shadow 24/7 readiness requires explicit Futures scope and command-contract coverage **before** any run-readiness claim, including at minimum: exchange-native Futures/perp instrument notation (for example a venue-specific **BTCUSDT perpetual** if that is the governed candidate), explicit **market type**, **venue/adapter** binding, **margin/leverage/contract metadata**, **position mode** and **long/short** behavior under derivatives semantics, **reduce-only / close-only / no-order-submission** constraints as applicable, **funding / liquidation / fees / slippage** assumptions, and mapped boundaries for **Risk / KillSwitch / Scope / Capital / Master V2 / Double Play**, plus Futures-specific **evidence collection and abort criteria** aligned to the canonical Futures specs.

Acceptance of a Futures scope command contract is **preparation only** and remains **non-authorizing** for scheduler execution, daemon execution, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, REST/WebSocket trading paths, credentials, or orders. **No-active-run preflight** (read-only, separate gate) and **explicit operator run approval** remain mandatory before any future authorized start.

Canonical Futures planning surfaces (read alongside this contract; **not** approval sources):

- [Futures Trading Readiness Runbook v0](futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md)
- [Futures Capability Spec v0](../specs/FUTURES_CAPABILITY_SPEC_V0.md)
- [Futures Candidate Evidence Package Contract v0](../specs/FUTURES_CANDIDATE_EVIDENCE_PACKAGE_CONTRACT_V0.md)
- [Master V2 Futures Class A Capability Contract v0](../specs/MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md)

## 3b. Shadow 24/7 Futures executable command template boundary

> **WARNUNG:** Dieser Abschnitt ist ein **Kommando-/Argumentvertrag zur späteren Überprüfung** („executable command template boundary“). Er ist **keine Ausführungsfreigabe**, kein Scheduling-/Daemon-Approval, keine Notion-/KG-Zustimmung und **keine** Aussage, dass Shadow-24/7-Futures jetzt bereit sei oder ohne weiteres Gate gestartet werden darf.

> **Nicht kopieren und nicht ausführen**, bis eine **spätere, explizite Operator-Review** alle Platzhalter, Tag-Listen, Scheduler-Configs und Kill-/Abort-Kriterien **gegen das aktuelle Repository** nachgewiesen hat.

### Aktueller Repo-Realismus (Pflicht beim Gate)

Aus `config/scheduler/jobs.toml` sind heute **`paper_shadow_247`**-/Diagnostics- sowie **Paper-runtime**-Jobs sichtbar; ein **Governance-definierter Job-Satz für „Futures / perpetual Shadow 24/7 Daemon“** ist **nicht** als ausführbares Ziel dokumentiert.

Vor einem realen Versuch sind mindestens verifiziert:

- Hilfe-Ausgabe: `python scripts/run_scheduler.py --help`
- Hilfe-Ausgabe: `python scripts/ops/run_with_timeout.py --help`
- Relevante Repo-Pfade nur lesend (z.B. Abgleich `config/scheduler/jobs.toml`; optional Planungspfad für **temporäre** Scheduler-Configs: `scripts/ops/make_scheduler_temp_config.py` beschreibt keinen Aktivierungsauthority und **ändert keine** Canonical-`jobs.toml`).

Siehe **„Futures / perpetual planning boundary“** weiter oben: **BTC-/USD-/Spot-/Proxy-/Public-REST-Evidenz allein sind keine Futures-/Perp-Shadow-Readiness.**

### Constraints (bei jeder zukünftigen Ausarbeitung dieser Linie gelten weiter)

Die folgenden Punkte sind **explizite Leitplanke** bis ein separates Governance-Gate andere Vorgaben beschließt:

- **Kein Live**; **kein Testnet**, außer künftig **separat** und schriftlich freigegeben und erneut gegated.
- **Kein Broker**, **keine private Exchange-/REST-/WebSocket-Endpunkte** für Konten-/Order-/Trading-Pfade.
- **Keine Order-Submission**, **keine Credentials**, **keine** privaten Daten zu Orders/Fills/Kontoständen/Positionen.
- **Keine Notion-/KG-Schreibfreigabe** aus diesem Dokument.
- Evidence **immer** unter einem neuen **`/tmp/peak_trade_<…>`** Root; keine sensiblen Pfade unter dem Repo-Root ohne separates Risk-/Retention-Gate.

### Bounded duration und Supervisor-Anforderung

Jede künftige, explizit erlaubte Ausführung muss einen **hart begrenzten Wall-Clock**. Im Repo liegt dafür **nur** ein generischer Wrapper:

- `scripts&#47;ops&#47;run_with_timeout.py --timeout-seconds <positive_float> -- <child argv…>`

**Timeout-Verhalten:** Abbruch mit Exit-Code **124** bei Überschreitung (Konvention wie GNU `timeout`). Der Template-Wrapper unten soll **jeden** vorgeschlagenen Child-Prozess in diesen Supervisor einbetten — **Ausnahmen nur** nach dokumentiertem Operator-Governance.

### Abort / STOP-Kriterien (nicht exhaustiv)

Sofort **STOP ohne Fortführungsannahme**, wenn eines zutrifft:

- Aktivierung eines Live-/Testnet-/Broker-/Exchange-Order-/private-Account-Pflugs ist erkennbar oder nicht zweifelsfrei ausgeschlossen.
- Evidence-Root ist nicht frisch/neu angelegt oder liegt außerhalb `/tmp/peak_trade_*` ohne Governance.
- Abweichungen von dokumentiertem Futures-/Perp-Instruments-/Venue-Vertrag, Kill-/Risk-State unklar, oder Proxy-/Spot-/BTCUSDT-Daten werden fälschlich als Futures-Readiness verkauft.
- `run_scheduler`/Job-Menge weicht ohne Review von erwarteten Tag-Gates / Dry-Run-Proof ab oder umgeht dokumentierte Guards.

Der folgende Block ist **`DO_NOT_RUN_YET`** markiert:

```DO_NOT_RUN_YET
#!/usr/bin/env bash
#
# PLANNING SURFACE ONLY — NOT EXECUTABLE AS-IS.
#
# Prerequisites before ANY future operator execution gate copies this skeleton:
#
# - Replace EVERY <PLACEHOLDER> after verifying against repo + governance.
# - Prove a governed Futures/perpetual Shadow-247 job EXISTS in scheduler inventory
#   matching this scope OR obtain a governance PR that introduces it BEFORE treating
#   include/exclude tag lists as real.
#
# Repo-verified tooling shape (CLI surface may evolve — re-run --help each time):
#   uv run python scripts/ops/run_with_timeout.py --timeout-seconds <N> -- \
#       uv run python scripts/run_scheduler.py --config … --poll-interval … [tag filters …]
#

set -euo pipefail

export PT_TRADING_SCOPE="${PT_TRADING_SCOPE:-<PLACEHOLDER_SHADOW_FUTURES_PERP_REVIEW_REQUIRED>}"
export PT_MARKET_TYPE="${PT_MARKET_TYPE:-<PLACEHOLDER_MARKET_TYPE_FUTURES_PERP_REVIEW_REQUIRED>}"
export PT_SYMBOL_NATIVE="${PT_SYMBOL_NATIVE:-<PLACEHOLDER_FOR_EXCHANGE_NATIVE_PERP_INSTRUMENT_STRING_REVIEW_REQUIRED>}"
export PT_SYMBOL_CCXT_UNIFIED="${PT_SYMBOL_CCXT_UNIFIED:-<PLACEHOLDER/ccxt:LINEAR_PERP_PAIR_REVIEW_REQUIRED>}"
export PT_VENUE_ADAPTER_REF="${PT_VENUE_ADAPTER_REF:-<PLACEHOLDER_READONLY_NO_ORDER_OBSERVATION_ADAPTER_REVIEW_REQUIRED>}"
export PT_EVIDENCE_ROOT="${PT_EVIDENCE_ROOT:-/tmp/peak_trade_shadow_247_futures_<UTC_TIMESTAMP_REPLACE_ME>}"
export PT_MAX_RUNTIME_SECONDS="${PT_MAX_RUNTIME_SECONDS:-7200}"
export PT_SCHEDULER_CONFIG_PATH="${PT_SCHEDULER_CONFIG_PATH:-<ABSOLUTE_PATH_TO_OPERATOR_REVIEWED_SCHEDULER_CONFIG_TOML_REQUIRED_MAY_INCLUDE_TEMP_HELPER_OUTPUT>}"

PT_LIVE_ENABLED="${PT_LIVE_ENABLED:-false}"
PT_TESTNET_ENABLED="${PT_TESTNET_ENABLED:-false}"
PT_BROKER_ENABLED="${PT_BROKER_ENABLED:-false}"
PT_ORDER_SUBMISSION_ENABLED="${PT_ORDER_SUBMISSION_ENABLED:-false}"
PT_PRIVATE_EXCHANGE_ENDPOINTS_ENABLED="${PT_PRIVATE_EXCHANGE_ENDPOINTS_ENABLED:-false}"
PT_CREDENTIAL_REQUIRED="${PT_CREDENTIAL_REQUIRED:-false}"

if [[ "${PT_LIVE_ENABLED}" != "false" ]]; then echo "STOP: PT_LIVE_ENABLED must remain false"; exit 64; fi
if [[ "${PT_TESTNET_ENABLED}" != "false" ]]; then echo "STOP: PT_TESTNET_ENABLED must remain false unless separately approved gate"; exit 64; fi
if [[ "${PT_BROKER_ENABLED}" != "false" ]]; then echo "STOP: broker paths blocked"; exit 64; fi
if [[ "${PT_ORDER_SUBMISSION_ENABLED}" != "false" ]]; then echo "STOP: order submission blocked"; exit 64; fi
if [[ "${PT_PRIVATE_EXCHANGE_ENDPOINTS_ENABLED}" != "false" ]]; then echo "STOP: private endpoints blocked"; exit 64; fi
if [[ "${PT_CREDENTIAL_REQUIRED}" != "false" ]]; then echo "STOP: credentials required — blocked"; exit 64; fi

mkdir -p "${PT_EVIDENCE_ROOT}"

echo "$(date -uIs) DO_NOT_RUN_YET scaffold — execution intentionally blocked until governance resolves placeholders/governed scheduler jobs." \
  > "${PT_EVIDENCE_ROOT}/DO_NOT_RUN_YET_PLACEHOLDER.log"

exit 64
```
## 4. Status model

Conservative states (future materializations must use one of these):

| Status | Meaning |
|--------|---------|
| **BLOCKED** | Mandatory preflight fields are missing, risk flags are present, or stop/emergency-stop semantics are undefined. Default for the repository today. |
| **DRY_RUN_ONLY** | Enough fields exist for offline diagnosis; operator arming or runtime activation is still **not** authorized. |
| **READY_FOR_OPERATOR_ARMING** | Owner, job set, commands, output paths, stop commands, dry-run proof, and no-Live/no-Testnet/no-broker/no-exchange/no-order boundaries are fully documented and reviewed. This is still **not** automatic activation—only permission to proceed with an explicit, governed arming step defined elsewhere. |

As of v0, the only valid status for this contract is **BLOCKED**.

## 5. Mandatory preflight dimensions (future)

Before **READY_FOR_OPERATOR_ARMING** may be claimed, a future runbook or implementation must name all of:

1. **Single owner entrypoint** — the one ops-approved path for Paper/Shadow 24/7 (not a grab-bag of scripts).
2. **Canonical job set** — exact scheduler or runner jobs for Paper and Shadow; `config/scheduler/jobs.toml` alone is inventory, not the canonical 24/7 set until explicitly declared.
3. **Commands** — resolved argv per job, with no ambiguous “run everything” defaults.
4. **Output paths** — directories, state files, logs, retention; no accidental overwrite of existing paper/shadow runs.
5. **Stop and emergency-stop** — explicit operator commands or procedures.
6. **Dry-run proof** — evidence that unexpected jobs do not run (e.g. scheduler `--dry-run` behavior documented and gated in process).
7. **Risk boundaries** — documented no-Live, no-Testnet, no-broker, no-exchange, no-order guarantees for the proposed path.

Until each dimension is satisfied, status remains **BLOCKED**.

**Future-run operator decision worksheet (review-only):** For a compact STOP_IDLE worksheet that maps these seven dimensions plus §2a.1 primary-evidence posture to existing canonical owners (no new evidence/readiness/map surface), see [SHADOW_247_GOVERNANCE_CHARTER_V0.md](SHADOW_247_GOVERNANCE_CHARTER_V0.md) — **Future-run operator decision worksheet v0**. That worksheet is **non-authorizing**; it does **not** change this contract’s **BLOCKED** status or grant `READY_FOR_OPERATOR_ARMING`.

## 6. Expected JSON shape (informative only)

No emitter is required by this document. A future read-only tool **may** emit JSON shaped like:

```json
{
  "schema_version": "paper_shadow_247_preflight_contract.v0",
  "generated_at_utc": "<iso8601>",
  "source_owner": "ops_scheduler_boundary",
  "source_files": [
    "docs/SCHEDULER_DAEMON.md",
    "config/scheduler/jobs.toml",
    "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
  ],
  "status": "BLOCKED",
  "status_reasons": [
    "paper_shadow_247_owner_entrypoint_missing",
    "paper_shadow_247_canonical_job_set_missing",
    "paper_shadow_247_output_paths_missing",
    "paper_shadow_247_stop_commands_missing"
  ],
  "canonical_candidate_jobs": [],
  "candidate_commands": [],
  "output_paths": [],
  "risk_flags": {
    "live": false,
    "testnet": false,
    "broker": false,
    "exchange": false,
    "orders": false
  },
  "risk_evidence": [],
  "stop_commands": [],
  "emergency_stop_commands": [],
  "activation_authorized": false
}
```

Field names and enums may be refined in a later contract version; v0 only fixes semantics and authority boundaries.

## 7. Related documents

- [Runtime Lane Taxonomy + Authority Levels Contract v0](../specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) — normative lane IDs, authority levels, forbidden cross-lane promotions (non-authorizing index; §2a/§2b retention remain here).
- [SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md) — scheduler boundary and dry-run-only diagnostics.
- Shadow session runbook: [runbook_shadow_session.md](../p6/runbook_shadow_session.md) (single-run, no daemon).
- Paper trading runbook: [runbook_paper_trading.md](../p7/runbook_paper_trading.md).
- Futures planning (non-authorizing pointers): [Futures Trading Readiness Runbook v0](futures/FUTURES_TRADING_READINESS_RUNBOOK_V0.md), [Futures Capability Spec v0](../specs/FUTURES_CAPABILITY_SPEC_V0.md), [Futures Candidate Evidence Package Contract v0](../specs/FUTURES_CANDIDATE_EVIDENCE_PACKAGE_CONTRACT_V0.md), [Master V2 Futures Class A Capability Contract v0](../specs/MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md).

## Paper/Shadow 24/7 Preflight Metadata v0

The read-only metadata source for this preflight is `config/ops/paper_shadow_247_preflight.toml`.

This metadata may populate canonical owner, paper/shadow job identifiers, output path declarations, and stop-command declarations for the preflight reporter. It does **not** authorize daemon execution, scheduler execution, Testnet, Live, broker, exchange, or order submission paths. Runtime activation remains blocked unless separate explicit governance gates authorize it.

## Controlled Paper-only Dry Activation Readiness v0

The preflight reporter exposes a nested `dry_activation_readiness` object with schema version `paper_shadow_247_dry_activation_readiness.v0`.

This object is **non-authorizing**. It may confirm that metadata, output-path declarations, stop controls, and paper/shadow job declarations are present, but it must keep `ready=false` until a separate explicit governance step authorizes a manual paper-only dry activation. The top-level daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remain `false`.

The operator command in this object is a readiness reference only. It is not executed by the reporter and does not start a daemon, scheduler, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order path.

## Unknown operator classification / HOLD context v0

The read-only preflight reporter includes a nested `hold_context_v0` object with schema version `unknown_hold_context.v0`.

This object is **non-authorizing**. It records the conservative operating posture when `OPERATOR_CLASSIFICATION=unknown`: `current_state=HOLD_NO_PAPER_RUN`, `go_live_next_step=blocked`, and all listed progression authorization flags remain `false`. Canonical references are documentation pointers only (`docs/ops/runbooks/incident_stop_freeze_rollback.md`, `docs/SCHEDULER_DAEMON.md`, and this contract). It does not clear incident stops, authorize daemon or scheduler execution, or activate Paper, Shadow, Testnet, Live, broker, exchange, or order paths.

**Live projection (conservative by design):**

```
HOLD_CONTEXT_V0_CONSERVATIVE_PROJECTION=true
ARCHIVE_OPERATOR_RECORD_TRACEABILITY_ONLY=true
SCOPED_EXCEPTION_DOES_NOT_CLOSE_GLOBAL_HOLD=true
PASS_BLOCKED_SAFE_DOES_NOT_CLEAR_HOLD=true
```

`hold_context_v0` is the **canonical live Preflight reporter projection**. Default reporter output **always** uses schema `unknown_hold_context.v0` with `operator_classification=unknown` and blocking progression flags — even when durable archive operator records exist (for example `OPERATOR_CLASSIFICATION=scoped_hold_with_exceptions`, completed U3 scoped preflight exceptions, or merge closeouts). Archive records **do not mutate, override, or clear** `hold_context_v0`. Global **HOLD** remains active unless a separate explicit gate-clearance slice authorizes otherwise.

Offline readiness outputs (`READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE`, `READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE`, `triple_lane_primary_evidence=true`) **do not** clear HOLD. See §2a.1 U3 scoped preflight exception and GLB-015 §6.5 in [Master V2 Go-Live Blocker Register v0](../specs/MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md).

## Operator decision record context v0 (optional)

The read-only preflight reporter (`scripts/ops/report_paper_shadow_247_preflight_status.py`) and stop-signal snapshot (`scripts/ops/snapshot_operator_stop_signals.py`) accept an optional `--operator-decision-record <path>` argument. When supplied, JSON includes `operator_decision_context_v0` (schema `operator_decision_context.v0`). This object is **non-authorizing**: it records parsed `OPERATOR_CLASSIFICATION`, `CURRENT_STATE`, and `GO_LIVE_NEXT_STEP` lines from the file for operator traceability only. It does not remove, move, overwrite, or reinterpret incident-stop artifacts; it does not change `hold_context_v0` (which remains the conservative unknown-HOLD projection); and it does not authorize scheduler, daemon, paper-validation, Testnet, Live, broker, exchange, or order paths.

When `--operator-decision-record` points to a durable archive file (for example `OPERATOR_HOLD_CLASSIFICATION_RECORD.txt` with `OPERATOR_CLASSIFICATION=scoped_hold_with_exceptions`), parsed fields appear in `operator_decision_context_v0` for **traceability only** — they **do not** lift global HOLD, **do not** clear Preflight **BLOCKED**, and **do not** authorize Paper/Shadow/Testnet/Live/broker/exchange paths. A completed U3 scoped exception record is **not** global HOLD closure and **does not** generalize to unbounded runtime activation.

## Governance OUTROOT clearance evidence v0 (optional)

The read-only preflight reporter accepts optional paired CLI arguments:

- `--durable-run-outroot <path>`
- `--expected-run-id <RUN_ID>`

When both are supplied, JSON includes `governance_outroot_clearance_v0` (schema `governance_outroot_clearance.v0`). This object is **non-authorizing**: it validates scoped durable OUTROOT governance/staging/bridge allowlisted files for the requested `RUN_ID` only and sets `valid=true` only when fail-closed checks pass. It **does not** change `status` (which remains **BLOCKED**), **does not** mutate or clear `hold_context_v0`, **does not** set `dry_activation_readiness.ready=true`, and **does not** authorize scheduler, daemon, Paper, Shadow, Testnet, Live, broker, exchange, or order paths.

When the paired arguments are omitted, reporter output is unchanged and `governance_outroot_clearance_v0` is absent.

```
GOVERNANCE_OUTROOT_CLEARANCE_TRACEABILITY_ONLY=true
GOVERNANCE_OUTROOT_CLEARANCE_DOES_NOT_CLEAR_HOLD=true
GOVERNANCE_OUTROOT_CLEARANCE_DOES_NOT_CHANGE_STATUS=true
DRY_ACTIVATION_READY_UNCHANGED_BY_GOVERNANCE_OUTROOT_BINDING=true
```

## Activation authorization evidence v0 (optional)

When paired `--durable-run-outroot` and `--expected-run-id` arguments are supplied and `governance_outroot_clearance_v0.valid=true`, JSON may also include `activation_authorization_v0` (schema `activation_authorization.v0`). This object is **non-authorizing**: it validates scoped durable OUTROOT activation authorization records for the requested `RUN_ID` only and sets `valid=true` only when fail-closed checks pass **and** governance clearance is valid. It **does not** change `status` (which remains **BLOCKED**), **does not** mutate or clear `hold_context_v0`, **does not** set top-level activation or scheduler authorization flags to `true`, **does not** set `dry_activation_readiness.ready=true`, and **does not** authorize scheduler, daemon, Paper, Shadow, Testnet, Live, broker, exchange, or order paths.

If governance clearance is invalid or activation records are missing/mismatched, `activation_authorization_v0.valid=false`.

```
ACTIVATION_AUTHORIZATION_TRACEABILITY_ONLY=true
ACTIVATION_AUTHORIZATION_REQUIRES_GOVERNANCE_OUTROOT_CLEARANCE_VALID=true
ACTIVATION_AUTHORIZATION_DOES_NOT_CHANGE_STATUS=true
ACTIVATION_AUTHORIZATION_DOES_NOT_CLEAR_HOLD=true
DRY_ACTIVATION_READY_UNCHANGED_BY_ACTIVATION_AUTHORIZATION_BINDING=true
```

## Execution prep readiness evidence v0 (optional)

When paired `--durable-run-outroot` and `--expected-run-id` arguments are supplied and both `governance_outroot_clearance_v0.valid=true` and `activation_authorization_v0.valid=true`, JSON may also include `execution_prep_readiness_v0` (schema `execution_prep_readiness.v0`). This object is **non-authorizing**: it validates scoped durable OUTROOT execution-prep operator records for the requested `RUN_ID` only and sets `valid=true` only when fail-closed checks pass **and** governance clearance and activation authorization are valid. It **does not** change `status` (which remains **BLOCKED**), **does not** mutate or clear `hold_context_v0`, **does not** set top-level activation or scheduler authorization flags to `true`, **does not** set `dry_activation_readiness.ready=true`, and **does not** authorize scheduler, daemon, Paper, Shadow, Testnet, Live, broker, exchange, or order paths.

If governance clearance, activation authorization, or execution-prep records are missing/mismatched, `execution_prep_readiness_v0.valid=false`.

```
EXECUTION_PREP_READINESS_TRACEABILITY_ONLY=true
EXECUTION_PREP_READINESS_REQUIRES_GOVERNANCE_OUTROOT_CLEARANCE_VALID=true
EXECUTION_PREP_READINESS_REQUIRES_ACTIVATION_AUTHORIZATION_VALID=true
EXECUTION_PREP_READINESS_DOES_NOT_CHANGE_STATUS=true
EXECUTION_PREP_READINESS_DOES_NOT_CLEAR_HOLD=true
DRY_ACTIVATION_READY_UNCHANGED_BY_EXECUTION_PREP_READINESS_BINDING=true
```

## 8. Revision

- **v0** — Initial contract: BLOCKED default, status model, non-authority, informative JSON shape.

## Post-PR3376 operator readiness closeout v0

After PRs **#3371** through **#3376**, the repository completed a focused **tests and reporting-contract** slice for Paper/Shadow 24/7 **read-only diagnostics** (prometheus declaration contract, preflight command inventory, safety classification, runtime-min timeout, high-vol inventory parity, runtime `outdir` placeholders in reporter inventory). This section is an operator-facing closeout. It does **not** authorize scheduler execution, daemon execution, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order submission.

### Canonical surfaces (reuse only)

Treat these as the coordinated sources for this topic—**do not** add parallel readiness maps, handoffs, or evidence indexes:

- `config/ops/paper_shadow_247_preflight.toml` — canonical owner `ops-paper-shadow-247-readiness`, job identifiers, output paths, stop commands; metadata only, not execution authority.
- `config/scheduler/jobs.toml` — scheduler-visible job shapes; Paper runtime jobs remain **disabled by default** unless a future gate explicitly enables them.
- `scripts/ops/make_scheduler_temp_config.py` — helper from PR **#3394** that writes a **temporary** scheduler TOML derived from `config/scheduler/jobs.toml`, enabling exactly one operator-selected job key and replacing Paper-runtime dry-run `outdir` placeholders with an operator-provided **absolute** path. It **does not** execute the scheduler or daemon, does not start Paper/Shadow/Testnet/Live/broker/exchange/order paths, and does not modify the canonical `jobs.toml` or evidence bundles; generated files are planning/diagnostics material only (not a new readiness, authority, or evidence surface).
- `scripts/ops/report_paper_shadow_247_preflight_status.py` — read-only JSON reporter (`status` remains **BLOCKED** in normal operation); command inventory and safety classification are diagnostic.
- `tests/ops/test_report_paper_shadow_247_preflight_status_cli_v0.py` — contract tests for reporter output, including runtime job inventory fields.

### Read-only diagnostics (examples)

Manual inspection only; they do not start daemons, schedulers in non-dry modes, or external trading paths:

```bash
python3 scripts/ops/report_paper_shadow_247_preflight_status.py --json --repo-root .
python3 scripts/ops/snapshot_operator_stop_signals.py --json --repo-root .
```

Prefer `uv run python` for interpreter parity (see **Operator Python Environment Note v0**).

### Evidence sections above

The tag-gated daemon and Paper-only runtime evidence sections in this contract remain **non-authorizing**: they describe bounded historical runs and flat/no-fill or roundtrip artifacts only. They do **not** approve continuous 24/7 operation, Shadow runtime, broker/exchange connectivity, Testnet, or Live.

### Operator decision

- Contract status stays **BLOCKED**; reporter `dry_activation_readiness.ready` remains **false** until a **separate explicit governance** step authorizes otherwise.
- **STOP — do not activate Paper/Shadow 24/7** based on this closeout alone.
- The next gate should be an explicit reviewed readiness or arming process—not implicit activation and not another single-field micro-contract unless a concrete safety defect requires it.

## Paper-only Tag-Gated Scheduler Daemon Stability Evidence v0

A controlled Paper-only, tag-gated scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/PAPER_ONLY_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/PREFLIGHT_AFTER.json`

Observed result:

- tag gate: `paper_shadow_247`
- target job: `paper_shadow_247_paper_only_preflight_status_v0`
- bounded runtime: 7200 seconds
- scheduler iterations: 240
- executed jobs: 1
- no-due-job observations: 239
- error mentions: 0
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

This evidence is non-authorizing. It proves only that the tag-gated scheduler daemon can run for the bounded window while executing the Paper/Shadow 24/7 preflight-status job once and then remaining idle. It does not prove Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: add or select a Paper-only runtime job and prove it first under explicit tag gating and bounded execution. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Paper-only Runtime Daemon 120-Minute Stability Evidence v0

A controlled Paper-only runtime scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/PAPER_ONLY_RUNTIME_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/PREFLIGHT_AFTER.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/account.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/fills.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/evidence_manifest.json`

Observed result:

- tag gate: `paper_runtime`
- target job: `paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0`
- runtime fixture: `tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json`
- bounded runtime: 7200 seconds
- runtime job mentions: 3
- no-due-job observations: 239
- error mentions: 0
- fills count: 0
- account cash: 1000.0
- positions shape: `{}`
- flat positions accepted: `true`
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

The empty positions object `{}` is accepted as the flat position representation for this evidence because there were no fills and the account remained flat. This is equivalent to no open BTC exposure for the high-vol no-trade fixture, even though the fixture-level expectation may name `BTC: 0.0`.

This evidence is non-authorizing. It proves only that the tag-gated Paper-only runtime scheduler daemon can run for the bounded window, execute the high-vol no-trade Paper runtime job once, produce flat/no-fill runtime artifacts, and then remain idle. It does not prove multi-run Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: either repeat the Paper-only runtime daemon with a longer bound or introduce a second Paper-only runtime fixture type under explicit tag gating and bounded execution. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Paper-only Runtime-Min Daemon 120-Minute Stability Evidence v0

A controlled Paper-only runtime-min scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/PAPER_ONLY_RUNTIME_MIN_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/PREFLIGHT_AFTER.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/account.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/fills.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/evidence_manifest.json`

Observed result:

- tag gate: `paper_runtime_min`
- target job: `paper_shadow_247_paper_only_runtime_min_v0`
- runtime fixture: `tests/fixtures/p7/paper_run_min_v0.json`
- bounded runtime: 7200 seconds
- scheduler checks: 240
- runtime-min job mentions: 3
- no-due-job observations: 239
- error mentions: 0
- fills count: 2
- fill sides: `BUY`, `SELL`
- fill prices: `100.1`, `99.9`
- fill fees: `0.1001`, `0.0999`
- account cash: 999.6
- positions shape: `{'BTC': 0.0}`
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

This evidence is non-authorizing. It proves only that the tag-gated Paper-only runtime-min scheduler daemon can run for the bounded window, execute the min Paper runtime job once, produce the expected BUY/SELL roundtrip artifacts, and then remain idle. It does not prove multi-symbol Paper runtime stability, longer-horizon Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: either repeat with a longer bound, add another Paper-only runtime fixture class, or promote a strictly bounded Paper-only runtime job only through an explicit non-live governance gate. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Operator Python Environment Note v0

Bounded Paper-only scheduler and runtime daemon runs should be launched with the project environment, preferably through `uv run python`, not a system Python such as `/usr/bin/python3`.

Reason: `prometheus_client` is available in the project-managed environment, while Apple Command Line Tools Python may not include it. If the scheduler is started with system Python, stderr may show the optional warning `prometheus_client not installed`. This warning is non-fatal for the current Paper-only evidence gates, but it reduces observability quality and can confuse operator triage.

This note does **not** change runtime authorization. It does not authorize daemon execution, scheduler execution, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order submission paths. It only documents the preferred interpreter boundary for future bounded Paper-only operator runs.
