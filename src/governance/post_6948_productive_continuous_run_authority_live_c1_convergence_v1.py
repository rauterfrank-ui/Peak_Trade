"""Post-6948 productive continuous-run authority / Live-C1 convergence v1 (non-authorizing).

Navigation and fail-closed proof only. Does not start continuous runtime, GET, POST,
mint permits, or consume Owner-GO tokens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "POST_6948_PRODUCTIVE_CONTINUOUS_RUN_AUTHORITY_LIVE_C1_CONVERGENCE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/POST_6948_PRODUCTIVE_CONTINUOUS_RUN_AUTHORITY_LIVE_C1_CONVERGENCE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "post_6948_productive_continuous_run_authority_live_c1_convergence_v1_decision_v1.json"
)
BASELINE_ORIGIN_MAIN_SHA: Final[str] = "85581ee6ca095f8533e5f0b09299d8596d61cc81"

CANONICAL_CONTINUOUS_AUTHORITY_OWNER: Final[str] = "governance.current_continuous_run_policy_v1"
CONTINUOUS_ORCHESTRATION_OWNER: Final[str] = (
    "full_core_live_path_composition_root_v1."
    "current_productive_governed_continuous_cycle_orchestrator_v1"
)
PERSISTENT_OFFLINE_HARNESS_OWNER: Final[str] = (
    "full_core_live_path_composition_root_v1."
    "current_productive_persistent_natural_enter_convergence_v1"
)
RUNTIME_BINDING_OWNER: Final[str] = "governance.current_continuous_run_runtime_binding_v1"

RUNTIME_OWNER_GO_TOKEN: Final[str] = "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_V1"
POLICY_OWNER_GO_TOKEN: Final[str] = "OWNER_GO_CONTINUOUS_RUN_POLICY"
LIVE_C1_GET_OWNER_GO: Final[str] = "OWNER_GO_S4A_EH_EXACTLY_ONE_PUBLIC_READONLY_FRESH_C1_GET_V1"
LIVE_C1_ENTRY_MODULE: Final[str] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_scoped_one_shot_c1_observation_source_v1.py"
)


@dataclass(frozen=True)
class CausalPathStepV1:
    step_id: str
    layer: str
    owner: str
    epistemic_class: str
    runtime_effect: str
    notes: str

    def to_dict(self) -> dict[str, str]:
        return {
            "STEP_ID": self.step_id,
            "LAYER": self.layer,
            "OWNER": self.owner,
            "EPISTEMIC_CLASS": self.epistemic_class,
            "RUNTIME_EFFECT": self.runtime_effect,
            "NOTES": self.notes,
        }


def prove_continuous_module_pins_fail_closed_v1() -> dict[str, bool]:
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        CONTINUOUS_RUN_AUTHORIZED as F1_M9_CONTINUOUS_PIN,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        CONTINUOUS_RUN_AUTHORIZED as S6_CONTINUOUS_PIN,
        RUNTIME_OWNER_GO_STATUS,
        S6_V5_EXECUTE_NETWORK,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        assert_productive_execution_forbidden_v1,
    )

    assert_productive_execution_forbidden_v1()
    return {
        "S6_CONTINUOUS_RUN_AUTHORIZED_PIN_FALSE": S6_CONTINUOUS_PIN is False,
        "F1_M9_CONTINUOUS_RUN_AUTHORIZED_PIN_FALSE": F1_M9_CONTINUOUS_PIN is False,
        "S6_NETWORK_EXECUTE_FALSE": S6_V5_EXECUTE_NETWORK is False,
        "S6_RUNTIME_OWNER_GO_NOT_CONSUMED": RUNTIME_OWNER_GO_STATUS == "DEFINED_NOT_CONSUMED",
    }


def prove_continuous_policy_admission_layer_v1(*, repo_root: Path) -> dict[str, Any]:
    from src.governance.current_continuous_run_policy_v1 import (
        evaluate_continuous_runtime_admission_v1,
        standing_continuous_run_authorized_v1,
        validate_continuous_run_policy_record_v1,
    )
    from src.governance.current_productive_activation_policy_v1 import (
        RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    )

    policy = validate_continuous_run_policy_record_v1(repo_root=repo_root)
    admission = evaluate_continuous_runtime_admission_v1(
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
        repo_root=repo_root,
    )
    return {
        "policy_owner": CANONICAL_CONTINUOUS_AUTHORITY_OWNER,
        "policy_authorized": policy.policy_authorized is True,
        "standing_continuous_run_authorized": standing_continuous_run_authorized_v1(
            repo_root=repo_root
        ),
        "continuous_runtime_admission_granted": (
            admission.continuous_runtime_admission_granted is True
        ),
        "continuous_run_authorized_at_admission_evaluator": admission.continuous_run_authorized,
        "external_effect_authorized_by_policy": admission.external_effect_authorized,
        "post_allowed_by_policy": admission.post_allowed,
        "policy_reason_codes": list(policy.reason_codes),
        "admission_reason_codes": list(admission.reason_codes),
    }


def prove_live_c1_get_standing_v1() -> dict[str, str]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        S4A_FRESH_C1_GET_OWNER_GO,
        S4A_FRESH_C1_GET_OWNER_GO_STATUS,
    )

    return {
        "live_c1_get_entry_module": LIVE_C1_ENTRY_MODULE,
        "fresh_c1_get_owner_go": S4A_FRESH_C1_GET_OWNER_GO,
        "fresh_c1_get_owner_go_status": S4A_FRESH_C1_GET_OWNER_GO_STATUS,
        "s6_get_owner_go_aligned": S4A_FRESH_C1_GET_OWNER_GO == LIVE_C1_GET_OWNER_GO,
    }


def build_productive_continuous_causal_path_v1() -> tuple[CausalPathStepV1, ...]:
    return (
        CausalPathStepV1(
            step_id="S8_CAP24_PROVENANCE",
            layer="fixed_lane_binding",
            owner=PERSISTENT_OFFLINE_HARNESS_OWNER,
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="NONE_OFFLINE_READ",
            notes="Cap24 handoff + LANE_1 occupied pair; binding_epoch + repository_sha.",
        ),
        CausalPathStepV1(
            step_id="PRODUCTIVE_ACTIVATION_POLICY",
            layer="admission_prerequisite",
            owner="governance.current_productive_activation_policy_v1",
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="PRODUCTIVE_RUNTIME_ADMISSION_ONLY",
            notes="Required each cycle; does not imply continuous run.",
        ),
        CausalPathStepV1(
            step_id="CONTINUOUS_RUN_POLICY",
            layer="continuous_admission",
            owner=CANONICAL_CONTINUOUS_AUTHORITY_OWNER,
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="CONTINUOUS_RUNTIME_ADMISSION_ONLY",
            notes=(
                f"Record + {POLICY_OWNER_GO_TOKEN} consumed at policy layer; "
                "module pins stay false."
            ),
        ),
        CausalPathStepV1(
            step_id="CONTINUOUS_RUNTIME_BINDING",
            layer="orchestration_gate",
            owner=RUNTIME_BINDING_OWNER,
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="PER_CYCLE_REVALIDATION",
            notes="run_policy_governed_current_productive_continuous_cycle_run_v1.",
        ),
        CausalPathStepV1(
            step_id="S6_CONTINUOUS_ORCHESTRATOR",
            layer="sequencing",
            owner=CONTINUOUS_ORCHESTRATION_OWNER,
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="BOUNDED_PRE_EXTERNAL_CYCLES",
            notes=(
                f"Requires continuous_owner_go={RUNTIME_OWNER_GO_TOKEN} "
                f"({RUNTIME_OWNER_GO_TOKEN} status DEFINED_NOT_CONSUMED)."
            ),
        ),
        CausalPathStepV1(
            step_id="LIVE_C1_OBSERVATION",
            layer="progression_input",
            owner=LIVE_C1_ENTRY_MODULE,
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="NONE_UNTIL_GET_GO_CONSUMED",
            notes=(
                f"S6 poll path requires injected source today; live GET via "
                f"{LIVE_C1_GET_OWNER_GO} not consumed; S6 rejects perform_get=true."
            ),
        ),
        CausalPathStepV1(
            step_id="S5_GOVERNED_CYCLE",
            layer="per_cycle_trading",
            owner=(
                "full_core_live_path_composition_root_v1."
                "current_productive_governed_cycle_orchestrator_v1"
            ),
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="ONE_CYCLE_PRE_EXTERNAL",
            notes="N1 occupied-lane runner in persistent harness; five-token S5 auth.",
        ),
        CausalPathStepV1(
            step_id="S7_MV2_DP_CURSOR",
            layer="durable_state",
            owner=(
                "current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1"
            ),
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="CURSOR_PERSIST",
            notes="Authoritative C1 floor; S6 reconciles sequencing floor only.",
        ),
        CausalPathStepV1(
            step_id="PRE_EXTERNAL_TERMINAL",
            layer="boundary",
            owner="pre_external_to_external_effect_boundary_bounded_wp_v1",
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_effect="FAIL_CLOSED_BEFORE_POST",
            notes="Offline harness reaches here with injected C1 only.",
        ),
        CausalPathStepV1(
            step_id="PR6948_OFFLINE_HARNESS",
            layer="offline_proof",
            owner=PERSISTENT_OFFLINE_HARNESS_OWNER,
            epistemic_class="PARTIAL",
            runtime_effect="NONE",
            notes=(
                "Bypasses policy binding + live GET; CONTINUOUS_RUN_AUTHORIZED pin false; "
                "not productive continuous authorization."
            ),
        ),
    )


def build_owner_decision_schema_v1() -> dict[str, Any]:
    return {
        "decision_id": "OWNER_DECISION_PRODUCTIVE_CONTINUOUS_RUN_WITH_LIVE_C1_V1",
        "required": True,
        "scope": (
            "Bounded productive continuous run: repeated PRE_EXTERNAL cycles with "
            "live public readonly Fresh-C1 GET per S6 wait loop; no POST/permit/credentials."
        ),
        "must_not_imply": [
            "EXTERNAL_EFFECT_AUTHORIZATION",
            "VENUE_POST",
            "PERMIT_MINT",
            "CREDENTIAL_ACCESS",
            "CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN_TRUE",
            "CONSUME_EXISTING_ACTUAL_VENUE_POST_OWNER_GO",
        ],
        "tokens_to_scope_and_consume": [
            {
                "token": RUNTIME_OWNER_GO_TOKEN,
                "current_status": "DEFINED_NOT_CONSUMED",
                "effect": "S6 continuous_run authorization.continuous_owner_go binding",
            },
            {
                "token": LIVE_C1_GET_OWNER_GO,
                "current_status": "DEFINED_NOT_CONSUMED",
                "effect": "Exactly-one public readonly 1m candles GET for C1 progression",
            },
        ],
        "freshness_trust_bindings_required": [
            "repository_sha lineage on policy records",
            "binding_epoch + Cap24 selection/ranking integrity on S8 handoff",
            "F1/M9 600s threshold consumer per cycle via policy binding",
            "C1 venue_event_time monotonic floor vs S7 persisted cursor",
            "enter-live-29p injected GET only on ENTER decision path (not POST)",
        ],
        "fail_closed_default": True,
    }


def build_convergence_report_v1(*, repo_root: Path, baseline_sha: str) -> dict[str, Any]:
    pins = prove_continuous_module_pins_fail_closed_v1()
    policy_layer = prove_continuous_policy_admission_layer_v1(repo_root=repo_root)
    live_c1 = prove_live_c1_get_standing_v1()
    path = build_productive_continuous_causal_path_v1()
    owner_schema = build_owner_decision_schema_v1()

    runtime_go_open = pins.get("S6_RUNTIME_OWNER_GO_NOT_CONSUMED") is True
    get_go_open = live_c1.get("fresh_c1_get_owner_go_status") == "DEFINED_NOT_CONSUMED"

    earliest_gate = "UNKNOWN"
    if runtime_go_open:
        earliest_gate = RUNTIME_OWNER_GO_TOKEN
    if get_go_open and earliest_gate != "UNKNOWN":
        earliest_gate = f"{RUNTIME_OWNER_GO_TOKEN}+{LIVE_C1_GET_OWNER_GO}"

    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "CANONICAL_CONTINUOUS_AUTHORITY_OWNER": CANONICAL_CONTINUOUS_AUTHORITY_OWNER,
        "CONTINUOUS_AUTHORIZATION_MECHANISM": (
            "validate_continuous_run_policy_record_v1 + "
            "evaluate_continuous_runtime_admission_v1 (per cycle via runtime binding); "
            "S6 module pin CONTINUOUS_RUN_AUTHORIZED remains false census guard"
        ),
        "EXISTING_AUTHORITY_SUFFICIENT": False,
        "EXISTING_AUTHORITY_SUFFICIENT_RATIONALE": (
            "Policy-layer CONTINUOUS_RUNTIME_ADMISSION is valid on main, but productive "
            "continuous execution requires consumable RUNTIME_OWNER_GO and live Fresh-C1 "
            "GET Owner-GO; PR #6948 offline harness explicitly not productive authorization."
        ),
        "LIVE_C1_GET_ENTRYPOINT": LIVE_C1_ENTRY_MODULE,
        "LIVE_C1_REQUIRED_GATES": [
            LIVE_C1_GET_OWNER_GO,
            "S6 observation_source live poll wiring (today: injected-only fail-closed)",
            "C1 cursor floor monotonicity vs S7 persist",
        ],
        "EARLIEST_MISSING_JOIN_OR_GATE": earliest_gate,
        "OWNER_DECISION_REQUIRED": True,
        "MODULE_PINS": pins,
        "POLICY_ADMISSION_LAYER": policy_layer,
        "LIVE_C1_STANDING": live_c1,
        "PRODUCTIVE_CONTINUOUS_CAUSAL_PATH": [s.to_dict() for s in path],
        "OWNER_DECISION_SCHEMA": owner_schema,
        "CURRENT_PERSISTENT_NATURAL_ENTER_PATH_COMPLETE": True,
        "CURRENT_PERSISTENT_NATURAL_ENTER_PATH_NOTE": (
            "Offline injected-C1 path S8→S6→S7→PRE_EXTERNAL proven in "
            "tests/ops/test_current_productive_persistent_natural_enter_convergence_v1.py; "
            "productive continuous + live C1 not joined."
        ),
        "PRODUCTIVE_RUNTIME_EXECUTED": False,
        "CONTINUOUS_RUN_AUTHORIZED_CHANGED": False,
        "POST_OWNER_GO_CONSUMED": False,
        "PERMIT_MINTED": False,
        "VENUE_POST_COUNT": 0,
        "FIRST_GENUINE_REMAINING_BLOCKER": (
            "SCOPED_OWNER_GO_CONSUMPTION_FOR_PRODUCTIVE_CONTINUOUS_RUN_AND_LIVE_FRESH_C1_GET"
        ),
        "NEXT_CANONICAL_STEP": (
            "Owner issues scoped GO consuming RUNTIME_OWNER_GO and Fresh-C1 GET GO for "
            "bounded PRE_EXTERNAL-only continuous run; then mechanical wiring WP may bind "
            "policy-governed runtime binding + live observation source without POST."
        ),
    }


def load_decision_record_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    return json.loads((root / DECISION_CONFIG).read_text(encoding="utf-8"))


__all__ = [
    "BASELINE_ORIGIN_MAIN_SHA",
    "CANONICAL_CONTINUOUS_AUTHORITY_OWNER",
    "CausalPathStepV1",
    "DECISION_CONFIG",
    "LIVE_C1_GET_OWNER_GO",
    "NORMATIVE_SPEC",
    "RUNTIME_OWNER_GO_TOKEN",
    "WORKPACKAGE_ID",
    "build_convergence_report_v1",
    "build_owner_decision_schema_v1",
    "build_productive_continuous_causal_path_v1",
    "load_decision_record_v1",
    "prove_continuous_module_pins_fail_closed_v1",
    "prove_continuous_policy_admission_layer_v1",
    "prove_live_c1_get_standing_v1",
]
