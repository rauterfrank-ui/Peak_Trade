"""Bounded Master V2 testnet completion path wiring v0.

Static admission contract binding the offline-proven Master-V2 replay → six-node
validation graph → completion → primary-evidence-retention chain into the canonical
bounded testnet observation completion path.

Non-authorizing. Does not execute testnet runtime, network, credentials, or orders.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    CONTRACT_VERSION as COMPLETION_INTEGRATION_CONTRACT_VERSION,
    DurableRunPrimaryEvidenceCompletionIntegrationInput,
    evaluate_durable_run_primary_evidence_completion_integration,
)
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER,
    PROOF_CLASSIFICATION_FULL_E2E_BOUND,
    PROOF_CLASSIFICATION_GRAPH_FAIL_CLOSED,
    PROOF_CLASSIFICATION_INTEGRATION_FAIL_CLOSED,
    PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
    PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
    OfflineReplaySixNodeValidationGraphBindingResultV0,
    build_completion_integration_input_from_offline_replay_result,
    build_validation_context_from_completion_integration_input,
    prove_offline_replay_six_node_validation_graph_binding_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    OfflineDoublePlayScenarioTickV0,
    run_offline_double_play_scenario_replay_v0,
)

BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_LAYER_VERSION = "v0"
BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER = (
    "ops.bounded_master_v2_testnet_completion_path_wiring_v0"
)
PACKAGE_MARKER = "BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_V0=true"

CANONICAL_TESTNET_RUNNER = "scripts/ops/run_testnet_bounded_observation_adapter_v0.py"
CANONICAL_TESTNET_ADAPTER = CANONICAL_TESTNET_RUNNER
CANONICAL_TESTNET_STAGING_OWNER = "scripts/ops/run_testnet_bounded_evidence_staging_v0.sh"
CANONICAL_TESTNET_COMPLETION_OWNER = "src/ops/bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0.py"
CANONICAL_MASTER_V2_REPLAY_OWNER = "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"
CANONICAL_SIX_NODE_GRAPH_OWNER = (
    "src/ops/offline_master_v2_replay_six_node_validation_graph_binding_v0.py"
)
CANONICAL_DIGEST_BINDING_OWNER = CANONICAL_TESTNET_COMPLETION_OWNER
CANONICAL_RETENTION_OWNER = "scripts/ops/primary_evidence_retention_v0.py"
CANONICAL_RETENTION_VERIFY_OWNER = "scripts.ops.primary_evidence_retention_v0"

_BTC_SPOT_RE = re.compile(r"(?i)(btc|xbt|bitcoin|/usd|/eur|spot)")

_FORBIDDEN_TESTNET_CLAIMS = frozenset(
    {
        "TESTNET_EXECUTES_CANONICAL_MASTER_V2",
        "TESTNET_DOUBLE_PLAY_DECISION_PATH_OBSERVED",
        "TESTNET_DECISION_DIGESTS_PERSISTED",
        "TESTNET_SIX_NODE_VALIDATION_GRAPH_PROVEN",
        "TESTNET_PRIMARY_EVIDENCE_RETENTION_PROVEN",
        "TESTNET_ZERO_ORDER_BOUNDARY_PROVEN_BY_RUN",
    }
)

_KNOWN_PROOF_CLASSIFICATIONS = frozenset(
    {
        PROOF_CLASSIFICATION_FULL_E2E_BOUND,
        PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
        PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
        PROOF_CLASSIFICATION_INTEGRATION_FAIL_CLOSED,
        PROOF_CLASSIFICATION_GRAPH_FAIL_CLOSED,
    }
)


@dataclass(frozen=True)
class TestnetCompletionPathMarketInputV0:
    """Typed admission for real testnet-observed market ticks."""

    selected_future_id: str
    ticks: tuple[OfflineDoublePlayScenarioTickV0, ...]
    source_run_id: str
    source_lane: str = "testnet_bounded_observation"
    synthetic_offline_fixture: bool = False


@dataclass(frozen=True)
class TestnetCompletionPathRetentionVerificationResultV0:
    """Canonical retention manifest verification result bound into completion wiring."""

    verify_pass: bool
    verify_message: str
    verify_owner: str
    archive_root: str | None = None


@dataclass(frozen=True)
class BoundedMasterV2TestnetCompletionPathWiringResultV0:
    layer_version: str
    wiring_pass: bool
    admission_pass: bool
    fail_reasons: tuple[str, ...]
    orders_total: int
    cancels_total: int
    fills_total: int
    positions_opened_total: int
    bounded_testnet_completion_path_master_v2_wiring_present: bool
    bounded_testnet_completion_path_six_node_graph_wiring_present: bool
    bounded_testnet_completion_path_decision_digest_wiring_present: bool
    bounded_testnet_completion_path_retention_wiring_present: bool
    bounded_testnet_zero_order_admission_boundary_present: bool
    missing_testnet_market_input_fails_closed: bool
    testnet_runner_reuses_canonical_completion_path: bool
    dashboard_display_projection_digest: str | None = None
    replay_proof_classification: str | None = None
    replay_proof_classification_bound: bool = False
    replay_proof_event_stream_non_authorizing: bool = True

    def to_machine_lines(self) -> dict[str, str | bool | int]:
        return {
            "BOUNDED_TESTNET_COMPLETION_PATH_MASTER_V2_WIRING_PRESENT": (
                self.bounded_testnet_completion_path_master_v2_wiring_present
            ),
            "BOUNDED_TESTNET_COMPLETION_PATH_SIX_NODE_GRAPH_WIRING_PRESENT": (
                self.bounded_testnet_completion_path_six_node_graph_wiring_present
            ),
            "BOUNDED_TESTNET_COMPLETION_PATH_DECISION_DIGEST_WIRING_PRESENT": (
                self.bounded_testnet_completion_path_decision_digest_wiring_present
            ),
            "BOUNDED_TESTNET_COMPLETION_PATH_RETENTION_WIRING_PRESENT": (
                self.bounded_testnet_completion_path_retention_wiring_present
            ),
            "BOUNDED_TESTNET_ZERO_ORDER_ADMISSION_BOUNDARY_PRESENT": (
                self.bounded_testnet_zero_order_admission_boundary_present
            ),
            "MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED": self.missing_testnet_market_input_fails_closed,
            "TESTNET_RUNNER_REUSES_CANONICAL_COMPLETION_PATH": (
                self.testnet_runner_reuses_canonical_completion_path
            ),
            "TESTNET_EXECUTES_CANONICAL_MASTER_V2": False,
            "TESTNET_DOUBLE_PLAY_DECISION_PATH_OBSERVED": False,
            "TESTNET_DECISION_DIGESTS_PERSISTED": False,
            "TESTNET_SIX_NODE_VALIDATION_GRAPH_PROVEN": False,
            "TESTNET_PRIMARY_EVIDENCE_RETENTION_PROVEN": False,
            "TESTNET_ZERO_ORDER_BOUNDARY_PROVEN_BY_RUN": False,
            "ORDERS_TOTAL": self.orders_total,
            "CANCELS_TOTAL": self.cancels_total,
            "FILLS_TOTAL": self.fills_total,
            "POSITIONS_OPENED_TOTAL": self.positions_opened_total,
            "DASHBOARD_DISPLAY_PROJECTION_DIGEST": self.dashboard_display_projection_digest or "",
            "OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION": self.replay_proof_classification
            or "",
            "REPLAY_PROOF_CLASSIFICATION_BOUND": self.replay_proof_classification_bound,
            "OFFLINE_END_TO_END_EVENT_STREAM_NON_AUTHORIZING": (
                self.replay_proof_event_stream_non_authorizing
            ),
        }


def run_canonical_retention_manifest_verification(
    archive_root: Path,
) -> TestnetCompletionPathRetentionVerificationResultV0:
    """Execute canonical verify_manifest_sha256 once; do not recompute digests elsewhere."""
    ok, msg = verify_manifest_sha256(archive_root)
    return TestnetCompletionPathRetentionVerificationResultV0(
        verify_pass=ok,
        verify_message=msg,
        verify_owner=CANONICAL_RETENTION_VERIFY_OWNER,
        archive_root=str(archive_root.resolve()),
    )


def verify_testnet_completion_path_retention_wiring(
    retention_verification: TestnetCompletionPathRetentionVerificationResultV0 | None,
    *,
    expected_archive_root: str | None = None,
) -> list[str]:
    """Fail-closed retention wiring guard; requires an executed canonical verify result."""
    reasons: list[str] = []
    if retention_verification is None:
        reasons.append("retention verification result required")
        return reasons
    if retention_verification.verify_owner != CANONICAL_RETENTION_VERIFY_OWNER:
        reasons.append(f"retention verify owner drift: {retention_verification.verify_owner!r}")
    if not retention_verification.verify_pass:
        detail = retention_verification.verify_message or "retention verification failed"
        reasons.append(f"retention verification failed: {detail}")
    if expected_archive_root is not None and retention_verification.archive_root is not None:
        expected = str(Path(expected_archive_root).resolve())
        if retention_verification.archive_root != expected:
            reasons.append("retention verification stale: archive_root mismatch")
    return reasons


def _retention_wiring_present(
    retention_verification: TestnetCompletionPathRetentionVerificationResultV0 | None,
) -> bool:
    if retention_verification is None:
        return False
    return (
        retention_verification.verify_pass
        and retention_verification.verify_owner == CANONICAL_RETENTION_VERIFY_OWNER
    )


def _static_wiring_flags(
    retention_verification: TestnetCompletionPathRetentionVerificationResultV0 | None = None,
) -> dict[str, bool]:
    return {
        "bounded_testnet_completion_path_master_v2_wiring_present": (
            OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER
            == "trading.master_v2.offline_double_play_scenario_replay_v0"
        ),
        "bounded_testnet_completion_path_six_node_graph_wiring_present": (
            OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER
            == "ops.offline_master_v2_replay_six_node_validation_graph_binding_v0"
        ),
        "bounded_testnet_completion_path_decision_digest_wiring_present": bool(
            COMPLETION_INTEGRATION_CONTRACT_VERSION
        ),
        "bounded_testnet_completion_path_retention_wiring_present": _retention_wiring_present(
            retention_verification
        ),
        "bounded_testnet_zero_order_admission_boundary_present": True,
        "testnet_runner_reuses_canonical_completion_path": True,
    }


def validate_testnet_completion_path_market_input(
    market_input: TestnetCompletionPathMarketInputV0,
) -> list[str]:
    """Fail-closed validation for real testnet market input admission."""
    reasons: list[str] = []
    if market_input.synthetic_offline_fixture:
        reasons.append("synthetic_offline_fixture must be false for testnet market input")
    if market_input.source_lane != "testnet_bounded_observation":
        reasons.append("source_lane must be testnet_bounded_observation")
    if not market_input.source_run_id.strip():
        reasons.append("source_run_id required")
    if not market_input.selected_future_id.strip():
        reasons.append("selected_future_id required")
    if _BTC_SPOT_RE.search(market_input.selected_future_id):
        reasons.append("selected_future_id must be futures-only (no BTC/XBT/spot)")
    if not market_input.ticks:
        reasons.append("testnet market ticks required")
    for tick in market_input.ticks:
        if tick.price <= 0:
            reasons.append(f"tick_index={tick.tick_index}: price must be positive")
    return reasons


def build_replay_input_from_testnet_market_input(
    market_input: TestnetCompletionPathMarketInputV0,
) -> OfflineDoublePlayScenarioReplayInputV0:
    """Map admitted testnet market input into the canonical offline replay input contract."""
    reasons = validate_testnet_completion_path_market_input(market_input)
    if reasons:
        raise ValueError("; ".join(reasons))
    return OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=market_input.selected_future_id,
        ticks=market_input.ticks,
        source_revision=(f"testnet-completion-path-wiring-v0:{market_input.source_run_id}"),
    )


def verify_dashboard_display_projection_digest_wiring(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
) -> tuple[str | None, list[str]]:
    """Fail-closed verification that replay, binding, six-node, and completion chain share one digest."""
    fail_reasons: list[str] = []
    prefix = "dashboard_display_projection_digest"
    replay_digest = replay_result.dashboard_display_projection_digest
    binding = replay_result.master_v2_decision_state_digest_binding
    chain = integration_input.completion_proof_chain
    six_node_digest = six_node_binding.dashboard_display_projection_digest

    if not replay_digest:
        fail_reasons.append(f"{prefix} missing from replay result")
        return None, fail_reasons

    binding_digest = binding.dashboard_display_projection_digest if binding else None
    chain_digest = (
        chain.completion_referenced_dashboard_display_projection_digest if chain else None
    )

    if not binding_digest:
        fail_reasons.append(f"{prefix} missing from decision state binding")
    if not chain_digest:
        fail_reasons.append(f"{prefix} missing from completion proof chain")
    if not six_node_digest:
        fail_reasons.append(f"{prefix} missing from six-node binding result")
    if binding_digest and replay_digest != binding_digest:
        fail_reasons.append(f"{prefix} drift: replay vs decision state binding")
    if chain_digest and binding_digest and chain_digest != binding_digest:
        fail_reasons.append(f"{prefix} drift: completion proof chain vs decision state binding")
    if chain_digest and replay_digest != chain_digest:
        fail_reasons.append(f"{prefix} drift: replay vs completion proof chain")
    if six_node_digest and replay_digest != six_node_digest:
        fail_reasons.append(f"{prefix} drift: replay vs six-node binding result")
    if six_node_digest and binding_digest and six_node_digest != binding_digest:
        fail_reasons.append(f"{prefix} drift: six-node binding result vs decision state binding")
    if six_node_digest and chain_digest and six_node_digest != chain_digest:
        fail_reasons.append(f"{prefix} drift: six-node binding result vs completion proof chain")

    return replay_digest, fail_reasons


def verify_replay_proof_classification_wiring(
    six_node_binding: OfflineReplaySixNodeValidationGraphBindingResultV0,
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> tuple[str | None, list[str]]:
    """Fail-closed verification that Stage-4 replay proof classification is FULL_E2E_BOUND."""
    fail_reasons: list[str] = []
    prefix = "replay_proof_classification"
    classification = six_node_binding.proof_classification

    if not classification or not classification.strip():
        fail_reasons.append(f"{prefix}: classification required")
        return None, fail_reasons

    if classification not in _KNOWN_PROOF_CLASSIFICATIONS:
        fail_reasons.append(f"{prefix}: unknown classification {classification!r}")
        return classification, fail_reasons

    if classification != PROOF_CLASSIFICATION_FULL_E2E_BOUND:
        fail_reasons.append(f"{prefix}: incomplete binding classification={classification!r}")
        return classification, fail_reasons

    if not six_node_binding.binding_pass:
        fail_reasons.append(f"{prefix}: six-node binding_pass required for FULL_E2E_BOUND")

    if not six_node_binding.state_event_projection_digest:
        fail_reasons.append(f"{prefix}: state_event_projection_digest required for FULL_E2E_BOUND")
    if not six_node_binding.master_v2_state_event_stream_identity:
        fail_reasons.append(
            f"{prefix}: master_v2_state_event_stream_identity required for FULL_E2E_BOUND"
        )

    mv2_proof = integration_input.master_v2_state_event_stream_proof
    mv2_input = integration_input.master_v2_state_event_stream_validation_input
    if (
        six_node_binding.master_v2_state_event_stream_identity
        and mv2_proof.state_event_stream_identity
        != six_node_binding.master_v2_state_event_stream_identity
    ):
        fail_reasons.append(
            f"{prefix}: master_v2_state_event_stream_identity drift: six-node vs integration proof"
        )
    if (
        six_node_binding.evidence_chain_profile is not None
        and mv2_input.evidence_chain_profile != six_node_binding.evidence_chain_profile
    ):
        fail_reasons.append(
            f"{prefix}: evidence_chain_profile drift: six-node vs integration input"
        )

    if not six_node_binding.event_stream_non_authorizing:
        fail_reasons.append(f"{prefix}: event_stream_non_authorizing must be true")

    return classification, fail_reasons


def evaluate_bounded_master_v2_testnet_completion_path_wiring(
    market_input: TestnetCompletionPathMarketInputV0 | None,
    *,
    retention_verification: TestnetCompletionPathRetentionVerificationResultV0 | None = None,
    expected_archive_root: str | None = None,
) -> BoundedMasterV2TestnetCompletionPathWiringResultV0:
    """Evaluate wiring admission. Fail-closed without real testnet market input."""
    static_flags = _static_wiring_flags(retention_verification)
    if market_input is None:
        return _result(
            wiring_pass=False,
            admission_pass=False,
            fail_reasons=("testnet market input required before Master-V2 completion path",),
            orders_total=0,
            cancels_total=0,
            fills_total=0,
            positions_opened_total=0,
            missing_testnet_market_input_fails_closed=True,
            **static_flags,
        )

    reasons = validate_testnet_completion_path_market_input(market_input)
    if reasons:
        return _result(
            wiring_pass=False,
            admission_pass=False,
            fail_reasons=tuple(reasons),
            orders_total=0,
            cancels_total=0,
            fills_total=0,
            positions_opened_total=0,
            missing_testnet_market_input_fails_closed=True,
            **static_flags,
        )

    replay_input = build_replay_input_from_testnet_market_input(market_input)
    replay_result = run_offline_double_play_scenario_replay_v0(replay_input)
    if not replay_result.replay_pass:
        return _result(
            wiring_pass=False,
            admission_pass=False,
            fail_reasons=tuple(replay_result.fail_reasons),
            orders_total=replay_result.summary.orders_total,
            cancels_total=replay_result.summary.cancels_total,
            fills_total=replay_result.summary.fills_total,
            positions_opened_total=replay_result.summary.positions_opened_total,
            missing_testnet_market_input_fails_closed=False,
            **static_flags,
        )

    binding = prove_offline_replay_six_node_validation_graph_binding_v0(replay_input)
    integration_input = build_completion_integration_input_from_offline_replay_result(replay_result)
    integration_result = evaluate_durable_run_primary_evidence_completion_integration(
        integration_input
    )
    _ = build_validation_context_from_completion_integration_input(integration_input)

    display_digest, display_digest_reasons = verify_dashboard_display_projection_digest_wiring(
        replay_result,
        integration_input,
        binding,
    )
    proof_classification, proof_classification_reasons = verify_replay_proof_classification_wiring(
        binding,
        integration_input,
    )

    fail_reasons = list(binding.fail_reasons)
    fail_reasons.extend(display_digest_reasons)
    fail_reasons.extend(proof_classification_reasons)
    if not integration_result.get("integration_pass"):
        fail_reasons.extend(integration_result.get("fail_reasons", ()))

    zero_order_ok = (
        binding.orders_total == 0
        and binding.cancels_total == 0
        and binding.fills_total == 0
        and binding.positions_opened_total == 0
    )
    if not zero_order_ok:
        fail_reasons.append("zero-order admission boundary violated")

    retention_reasons = verify_testnet_completion_path_retention_wiring(
        retention_verification,
        expected_archive_root=expected_archive_root,
    )
    fail_reasons.extend(retention_reasons)

    wiring_pass = binding.binding_pass and bool(integration_result.get("integration_pass"))
    wiring_pass = wiring_pass and zero_order_ok and not fail_reasons
    classification_bound = (
        proof_classification == PROOF_CLASSIFICATION_FULL_E2E_BOUND
        and not proof_classification_reasons
    )

    return _result(
        wiring_pass=wiring_pass,
        admission_pass=wiring_pass,
        fail_reasons=tuple(fail_reasons),
        orders_total=binding.orders_total,
        cancels_total=binding.cancels_total,
        fills_total=binding.fills_total,
        positions_opened_total=binding.positions_opened_total,
        missing_testnet_market_input_fails_closed=False,
        dashboard_display_projection_digest=display_digest,
        replay_proof_classification=proof_classification,
        replay_proof_classification_bound=classification_bound,
        replay_proof_event_stream_non_authorizing=binding.event_stream_non_authorizing,
        **static_flags,
    )


def build_testnet_bounded_adapter_completion_path_wiring_section(
    *,
    run_id: str,
    mode: str,
    market_input: TestnetCompletionPathMarketInputV0 | None = None,
    market_input_producer_fail_reasons: tuple[str, ...] | None = None,
    retention_verification: TestnetCompletionPathRetentionVerificationResultV0 | None = None,
    expected_archive_root: str | None = None,
) -> dict[str, Any]:
    """Static completion-path wiring metadata for the bounded testnet adapter plan."""
    admission = evaluate_bounded_master_v2_testnet_completion_path_wiring(
        market_input,
        retention_verification=retention_verification,
        expected_archive_root=expected_archive_root,
    )
    machine = admission.to_machine_lines()
    producer_fail_reasons = list(market_input_producer_fail_reasons or ())
    if market_input is None and not producer_fail_reasons:
        producer_fail_reasons = list(admission.fail_reasons)
    return {
        "layer_version": BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_LAYER_VERSION,
        "owner": BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_OWNER,
        "run_id": run_id,
        "mode": mode,
        "canonical_testnet_runner": CANONICAL_TESTNET_RUNNER,
        "canonical_testnet_completion_owner": CANONICAL_TESTNET_COMPLETION_OWNER,
        "canonical_master_v2_replay_owner": CANONICAL_MASTER_V2_REPLAY_OWNER,
        "canonical_six_node_graph_owner": CANONICAL_SIX_NODE_GRAPH_OWNER,
        "canonical_digest_binding_owner": CANONICAL_DIGEST_BINDING_OWNER,
        "canonical_retention_owner": CANONICAL_RETENTION_OWNER,
        "market_input_bound": market_input is not None,
        "market_input_producer_fail_reasons": producer_fail_reasons,
        "admission_pass": admission.admission_pass,
        "wiring_pass": admission.wiring_pass,
        "fail_reasons": list(admission.fail_reasons),
        "dashboard_display_projection_digest": admission.dashboard_display_projection_digest,
        "machine_summary": machine,
        "retention_verify_owner": CANONICAL_RETENTION_VERIFY_OWNER,
        "retention_verification": (
            {
                "verify_pass": retention_verification.verify_pass,
                "verify_message": retention_verification.verify_message,
                "verify_owner": retention_verification.verify_owner,
                "archive_root": retention_verification.archive_root,
            }
            if retention_verification is not None
            else None
        ),
    }


def assert_forbidden_testnet_execution_claims_absent(claims: Mapping[str, Any]) -> list[str]:
    """Reject any claim that static wiring constitutes executed testnet proof."""
    violations: list[str] = []
    for key in _FORBIDDEN_TESTNET_CLAIMS:
        if claims.get(key) is True:
            violations.append(f"forbidden testnet execution claim present: {key}=true")
    return violations


def _result(
    *,
    wiring_pass: bool,
    admission_pass: bool,
    fail_reasons: tuple[str, ...],
    orders_total: int,
    cancels_total: int,
    fills_total: int,
    positions_opened_total: int,
    missing_testnet_market_input_fails_closed: bool,
    bounded_testnet_completion_path_master_v2_wiring_present: bool,
    bounded_testnet_completion_path_six_node_graph_wiring_present: bool,
    bounded_testnet_completion_path_decision_digest_wiring_present: bool,
    bounded_testnet_completion_path_retention_wiring_present: bool,
    bounded_testnet_zero_order_admission_boundary_present: bool,
    testnet_runner_reuses_canonical_completion_path: bool,
    dashboard_display_projection_digest: str | None = None,
    replay_proof_classification: str | None = None,
    replay_proof_classification_bound: bool = False,
    replay_proof_event_stream_non_authorizing: bool = True,
) -> BoundedMasterV2TestnetCompletionPathWiringResultV0:
    return BoundedMasterV2TestnetCompletionPathWiringResultV0(
        layer_version=BOUNDED_MASTER_V2_TESTNET_COMPLETION_PATH_WIRING_LAYER_VERSION,
        wiring_pass=wiring_pass,
        admission_pass=admission_pass,
        fail_reasons=fail_reasons,
        orders_total=orders_total,
        cancels_total=cancels_total,
        fills_total=fills_total,
        positions_opened_total=positions_opened_total,
        bounded_testnet_completion_path_master_v2_wiring_present=(
            bounded_testnet_completion_path_master_v2_wiring_present
        ),
        bounded_testnet_completion_path_six_node_graph_wiring_present=(
            bounded_testnet_completion_path_six_node_graph_wiring_present
        ),
        bounded_testnet_completion_path_decision_digest_wiring_present=(
            bounded_testnet_completion_path_decision_digest_wiring_present
        ),
        bounded_testnet_completion_path_retention_wiring_present=(
            bounded_testnet_completion_path_retention_wiring_present
        ),
        bounded_testnet_zero_order_admission_boundary_present=(
            bounded_testnet_zero_order_admission_boundary_present
        ),
        missing_testnet_market_input_fails_closed=missing_testnet_market_input_fails_closed,
        testnet_runner_reuses_canonical_completion_path=testnet_runner_reuses_canonical_completion_path,
        dashboard_display_projection_digest=dashboard_display_projection_digest,
        replay_proof_classification=replay_proof_classification,
        replay_proof_classification_bound=replay_proof_classification_bound,
        replay_proof_event_stream_non_authorizing=replay_proof_event_stream_non_authorizing,
    )
