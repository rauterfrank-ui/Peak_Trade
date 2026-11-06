"""Fixtures for trading_logic_semantic_diff_evidence_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1 import (
    TradingLogicSemanticDiffEvidenceInputs,
    default_semantic_diff_evidence_request,
    produce_trading_logic_semantic_diff_evidence_v1,
    verify_trading_core_decision_attestation_bundle,
)
from tests.meta.trading_core_decision_attestation_v1_fixtures import (
    produce_trading_core_decision_attestation_fixture,
)


@dataclass(frozen=True)
class TradingLogicSemanticDiffEvidenceFixtureBundle:
    baseline_trading_core_decision_attestation_bundle_dir: Path
    candidate_trading_core_decision_attestation_bundle_dir: Path
    trading_logic_semantic_diff_evidence_bundle_dir: Path | None = None


def produce_trading_logic_semantic_diff_evidence_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    valid_from: str = "2026-06-29T00:00:00+00:00",
    valid_until: str = "2026-06-30T00:00:00+00:00",
    revocation_state: str = "NOT_REVOKED",
    produce_output: bool = True,
    baseline_name: str = "baseline_trading_core_decision_attestation",
    candidate_name: str = "candidate_trading_core_decision_attestation",
    semantic_diff_name: str = "trading_logic_semantic_diff_evidence",
    declared_change_class: str = "A",
    candidate_order_intent_digest: str | None = None,
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    correlation_id: str = "offline-semantic-diff-correlation-001",
) -> TradingLogicSemanticDiffEvidenceFixtureBundle:
    baseline_tmp = tmp_path / "baseline_chain"
    candidate_tmp = tmp_path / "candidate_chain"
    baseline_durable = durable_root / "baseline_durable"
    candidate_durable = durable_root / "candidate_durable"
    baseline_tmp.mkdir(parents=True, exist_ok=True)
    candidate_tmp.mkdir(parents=True, exist_ok=True)
    baseline_durable.mkdir(parents=True, exist_ok=True)
    candidate_durable.mkdir(parents=True, exist_ok=True)

    baseline_fixture = produce_trading_core_decision_attestation_fixture(
        baseline_tmp,
        baseline_durable,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
        produce_output=True,
        trading_session_name=f"{baseline_name}_session",
        lifecycle_name=f"{baseline_name}_lifecycle",
        idempotency_name=f"{baseline_name}_idempotency",
        attestation_name=baseline_name,
        instrument_type=instrument_type,
        instrument=instrument,
    )
    assert baseline_fixture.trading_core_decision_attestation_bundle_dir is not None

    if candidate_order_intent_digest is None:
        candidate_fixture = baseline_fixture
    else:
        candidate_kwargs: dict[str, object] = {
            "tmp_path": candidate_tmp,
            "durable_root": candidate_durable,
            "all_domains_pass": all_domains_pass,
            "use_candidate_lineage": use_candidate_lineage,
            "include_ai_assessment": include_ai_assessment,
            "evaluation_time": evaluation_time,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "revocation_state": revocation_state,
            "produce_output": True,
            "trading_session_name": f"{candidate_name}_session",
            "lifecycle_name": f"{candidate_name}_lifecycle",
            "idempotency_name": f"{candidate_name}_idempotency",
            "attestation_name": candidate_name,
            "instrument_type": instrument_type,
            "instrument": instrument,
            "order_intent_digest": candidate_order_intent_digest,
        }
        candidate_fixture = produce_trading_core_decision_attestation_fixture(**candidate_kwargs)
    assert candidate_fixture.trading_core_decision_attestation_bundle_dir is not None

    baseline = verify_trading_core_decision_attestation_bundle(
        baseline_fixture.trading_core_decision_attestation_bundle_dir
    )
    candidate = verify_trading_core_decision_attestation_bundle(
        candidate_fixture.trading_core_decision_attestation_bundle_dir
    )
    request = default_semantic_diff_evidence_request(
        baseline=baseline,
        candidate=candidate,
        declared_change_class=declared_change_class,
        correlation_id=correlation_id,
    )

    semantic_diff_dir: Path | None = None
    if produce_output:
        semantic_diff_dir = durable_root / semantic_diff_name
        produce_trading_logic_semantic_diff_evidence_v1(
            inputs=TradingLogicSemanticDiffEvidenceInputs(
                baseline_trading_core_decision_attestation_bundle_dir=baseline_fixture.trading_core_decision_attestation_bundle_dir,
                candidate_trading_core_decision_attestation_bundle_dir=candidate_fixture.trading_core_decision_attestation_bundle_dir,
                semantic_diff_request=request,
            ),
            output_dir=semantic_diff_dir,
        )

    return TradingLogicSemanticDiffEvidenceFixtureBundle(
        baseline_trading_core_decision_attestation_bundle_dir=baseline_fixture.trading_core_decision_attestation_bundle_dir,
        candidate_trading_core_decision_attestation_bundle_dir=candidate_fixture.trading_core_decision_attestation_bundle_dir,
        trading_logic_semantic_diff_evidence_bundle_dir=semantic_diff_dir,
    )
