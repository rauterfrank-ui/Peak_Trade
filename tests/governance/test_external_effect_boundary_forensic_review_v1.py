"""External Effect boundary forensic review v1 tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.current_continuous_run_policy_v1 import (
    standing_continuous_run_authorized_v1,
)
from src.governance.current_productive_activation_policy_v1 import (
    standing_productive_activation_authorized_v1,
)
from src.governance.external_effect_boundary_forensic_review_v1 import (
    EXTERNAL_EFFECT_ADJUDICATION_CLASS,
    EXTERNAL_EFFECT_BOUNDARY_REVIEW_COMPLETE,
    prove_external_effect_boundary_forensic_review_v1,
)
from src.governance.external_effect_boundary_forensic_review_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CONTINUOUS_RUN_ADJUDICATION_CLASS,
    CREDENTIAL_ADJUDICATION_CLASS,
    DECISION_CONFIG,
    PERMIT_ADJUDICATION_CLASS,
    POST_SINK_ADJUDICATION_CLASS,
    PRE_EXTERNAL_ADJUDICATION_CLASS,
    VENUE_POST_SINK_OWNER,
)
from src.governance.governed_current_productive_chain_pre_external_to_external_effect_boundary_closure_v1 import (
    CANONICAL_EXTERNAL_EFFECT_BOUNDARY,
    prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1,
)
from src.governance.governed_external_effect_boundary_forensic_review_closure_v1 import (
    prove_governed_external_effect_boundary_forensic_review_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    invoke_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    CONTINUOUS_RUN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    evaluate_external_effect_v1,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_census_verdict_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "7330b6cb8a3cfccca9163028cbdf13e13910088c"
    assert EXTERNAL_EFFECT_BOUNDARY_REVIEW_COMPLETE is True
    assert CONTINUOUS_RUN_ADJUDICATION_CLASS == "POLICY_AUTHORIZED_ORCHESTRATOR_MODULE_PIN_FALSE"
    assert EXTERNAL_EFFECT_ADJUDICATION_CLASS == "STANDING_FALSE_FAIL_CLOSED"
    assert PRE_EXTERNAL_ADJUDICATION_CLASS == "PROVEN_STATIC_CENSUS"
    assert PERMIT_ADJUDICATION_CLASS == "INTENTIONALLY_ISOLATED_OWNER_GO"
    assert CREDENTIAL_ADJUDICATION_CLASS == "CAPABILITY_WITHOUT_ACCESS_AUTHORIZATION"
    assert POST_SINK_ADJUDICATION_CLASS == "IDENTIFIED_NOT_REACHABLE_WITH_CURRENT_AUTHORITY"
    assert "post_trade_order" in VENUE_POST_SINK_OWNER


def test_forensic_proof_and_closure() -> None:
    result = prove_external_effect_boundary_forensic_review_v1(repo_root=REPO_ROOT)
    assert result.ok is True, (
        f"guard={result.guard_failures} decision={result.decision_failures} "
        f"chain={result.chain_failures} simulated={result.simulated_failures} "
        f"upstream={result.upstream_closure_failures}"
    )
    assert prove_governed_external_effect_boundary_forensic_review_v1(repo_root=REPO_ROOT)


def test_end_to_end_chain_closure() -> None:
    assert prove_governed_current_productive_chain_pre_external_to_external_effect_boundary_v1(
        repo_root=REPO_ROOT
    )
    assert prove_pre_external_to_external_effect_boundary_v1().ok is True


def test_standing_authority_pins_and_non_implications() -> None:
    assert standing_productive_activation_authorized_v1(repo_root=REPO_ROOT) is True
    assert standing_continuous_run_authorized_v1(repo_root=REPO_ROOT) is True
    assert CONTINUOUS_RUN_AUTHORIZED is False
    decision = evaluate_external_effect_v1()
    assert decision.external_effect_authorized is False
    assert decision.fail_closed is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False


def test_decision_records_fail_closed() -> None:
    payload = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert payload["external_effect_authorized"] is False
    assert payload["post_allowed"] is False
    assert payload["continuous_run_authorized"] is True
    assert payload["productive_activation_authorized"] is True
    assert payload["continuous_run_module_pin_authorized"] is False
    assert payload["earliest_unclosed_boundary"] == "EXTERNAL_EFFECT_AUTHORIZATION"
    assert payload["next_genuine_blocker"] == "EXTERNAL_EFFECT_POLICY_OWNER_GO"


def test_invoke_external_effect_sink_raises_fail_closed() -> None:
    try:
        invoke_external_effect_v1(attempt_post=True)
    except FullCoreExternalEffectNotAuthorizedError:
        pass
    else:
        raise AssertionError("invoke_external_effect_v1 must fail closed")


def test_canonical_boundary_constant() -> None:
    assert CANONICAL_EXTERNAL_EFFECT_BOUNDARY == (
        "STANDING_EXTERNAL_EFFECT_GATE_AND_ENVELOPE_SEAM_FAIL_CLOSED"
    )
