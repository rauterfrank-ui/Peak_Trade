"""Deterministic offline MVR evidence harness. Injected/file replay only."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    ALLOWED_EVIDENCE_CLASSES,
    CALL_GRAPH,
    CHALLENGER_A_POLICY_ID,
    CHALLENGER_B_POLICY_ID,
    CHALLENGER_C_POLICY_ID,
    CHALLENGER_D_POLICY_ID,
    DEFAULT_EVIDENCE_CLASS,
    FORBIDDEN_EVIDENCE_CLASSES,
    HARNESS_ID,
    HARNESS_NETWORK_READ_REQUIRED,
    HARNESS_VERSION,
    NEGATIVE_CONTROL_POLICY_ID,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.evaluators_v1 import (
    assert_known_policy_id_v1,
    evaluate_challenger_a_v1,
    evaluate_challenger_b_v1,
    evaluate_challenger_c_v1,
    evaluate_challenger_d_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.features_v1 import (
    OfflineMvrFeatureError,
    OfflineMvrInstrumentFeaturesV1,
    compute_instrument_features_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.models_v1 import (
    CandidateUniverseMemberV1,
    OfflinePolicyRankingV1,
    authority_block,
    overlap_and_displacement_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.negative_control_v1 import (
    evaluate_negative_control_v1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.reason_codes_v1 import (
    OfflineMvrHarnessFailureCodeV1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.threshold_set_v1 import (
    InjectedPolicyBThresholdSetV1,
    PolicyBThresholdSetError,
    parse_injected_policy_b_threshold_set_v1,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.economic_md_input_producer_v1.universe_gate_v1 import (
    load_cap21_eligible_instruments_v1,
)


class OfflineMvrHarnessError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _fail(code: OfflineMvrHarnessFailureCodeV1, detail: str = "") -> None:
    raise OfflineMvrHarnessError(code.value, detail)


def _as_snapshot(
    payload: Mapping[str, Any] | EconomicMdInputSnapshotV1 | None,
) -> EconomicMdInputSnapshotV1:
    if payload is None:
        _fail(OfflineMvrHarnessFailureCodeV1.ECONOMIC_MD_SNAPSHOT_MISSING)
    if isinstance(payload, EconomicMdInputSnapshotV1):
        return payload
    return EconomicMdInputSnapshotV1.from_dict(payload)


def _validate_evidence_class(evidence_class: str) -> str:
    if evidence_class in FORBIDDEN_EVIDENCE_CLASSES:
        _fail(OfflineMvrHarnessFailureCodeV1.EVIDENCE_CLASS_FORBIDDEN, evidence_class)
    if evidence_class not in ALLOWED_EVIDENCE_CLASSES:
        _fail(OfflineMvrHarnessFailureCodeV1.EVIDENCE_CLASS_FORBIDDEN, evidence_class)
    return evidence_class


def _validate_digest(snapshot: EconomicMdInputSnapshotV1) -> None:
    recomputed = snapshot.compute_payload_digest()
    if not snapshot.payload_digest or snapshot.payload_digest != recomputed:
        _fail(
            OfflineMvrHarnessFailureCodeV1.SNAPSHOT_DIGEST_MISMATCH,
            f"{snapshot.payload_digest}!={recomputed}",
        )


def _validate_provenance(
    snapshot: EconomicMdInputSnapshotV1,
    expected_provenance: Mapping[str, Any] | None,
) -> None:
    actual = dict(snapshot.provenance or {})
    if actual.get("network_used") is True:
        _fail(
            OfflineMvrHarnessFailureCodeV1.NETWORK_READ_FORBIDDEN,
            "snapshot_provenance.network_used",
        )
    if expected_provenance is None:
        return
    for key, value in expected_provenance.items():
        if actual.get(key) != value:
            _fail(
                OfflineMvrHarnessFailureCodeV1.PROVENANCE_MISMATCH,
                f"{key}:{actual.get(key)!r}!={value!r}",
            )


def _bind_cap21(
    *,
    snapshot: EconomicMdInputSnapshotV1,
    universe_snapshot: Mapping[str, Any] | None,
) -> tuple[Mapping[str, Any], tuple[CandidateUniverseMemberV1, ...]]:
    if universe_snapshot is None:
        _fail(OfflineMvrHarnessFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING)
    gate = load_cap21_eligible_instruments_v1(universe_snapshot)
    if not gate.ok or gate.snapshot is None:
        _fail(
            OfflineMvrHarnessFailureCodeV1.CAP21_UNIVERSE_BINDING_MISMATCH,
            ",".join(gate.failure_codes),
        )
    reference = dict(snapshot.universe_snapshot_reference or {})
    expected_id = str(gate.universe_snapshot_reference.get("snapshot_id") or "")
    expected_digest = str(gate.universe_snapshot_reference.get("payload_digest") or "")
    if str(reference.get("snapshot_id") or "") != expected_id:
        _fail(
            OfflineMvrHarnessFailureCodeV1.CAP21_UNIVERSE_BINDING_MISMATCH,
            "snapshot_id",
        )
    if str(reference.get("payload_digest") or "") != expected_digest:
        _fail(
            OfflineMvrHarnessFailureCodeV1.CAP21_UNIVERSE_BINDING_MISMATCH,
            "payload_digest",
        )
    eligible = {(row.canonical_instrument_id, row.venue_native_id) for row in gate.eligible}
    candidates: list[CandidateUniverseMemberV1] = []
    for row in snapshot.instruments:
        identity = (row.canonical_instrument_id, row.venue_native_id)
        if identity not in eligible:
            _fail(
                OfflineMvrHarnessFailureCodeV1.INELIGIBLE_INSTRUMENT_INJECTION,
                row.canonical_instrument_id,
            )
        if not row.raw_input_eligible:
            _fail(
                OfflineMvrHarnessFailureCodeV1.RAW_INPUT_NOT_ELIGIBLE,
                row.canonical_instrument_id,
            )
        candidates.append(
            CandidateUniverseMemberV1(
                canonical_instrument_id=row.canonical_instrument_id,
                venue_native_id=row.venue_native_id,
            )
        )
    candidates.sort(key=lambda row: (row.canonical_instrument_id, row.venue_native_id))
    return universe_snapshot, tuple(candidates)


def _candidate_universe_digest(members: Sequence[CandidateUniverseMemberV1]) -> str:
    payload = {
        "members": [row.to_dict() for row in members],
    }
    return sha256_hex(canonical_json_dumps(payload))


def _raw_input_digest(snapshot: EconomicMdInputSnapshotV1) -> str:
    payload = {
        "economic_input_snapshot_id": snapshot.economic_input_snapshot_id,
        "instrument_raw_input_digests": [row.raw_input_digest for row in snapshot.instruments],
        "payload_digest": snapshot.payload_digest,
        "universe_snapshot_reference": dict(snapshot.universe_snapshot_reference),
    }
    return sha256_hex(canonical_json_dumps(payload))


def _feature_digest(features: Sequence[OfflineMvrInstrumentFeaturesV1]) -> str:
    payload = {
        "instruments": [row.to_dict() for row in features],
    }
    return sha256_hex(canonical_json_dumps(payload))


def _enforce_identical_universe(
    *,
    candidate_universe: Sequence[CandidateUniverseMemberV1],
    rankings: Sequence[OfflinePolicyRankingV1],
) -> None:
    expected = {(row.canonical_instrument_id, row.venue_native_id) for row in candidate_universe}
    for ranking in rankings:
        observed = {
            (row.canonical_instrument_id, row.venue_native_id) for row in ranking.ordered_ranking
        } | {(row.canonical_instrument_id, row.venue_native_id) for row in ranking.not_rankable}
        if observed != expected:
            _fail(
                OfflineMvrHarnessFailureCodeV1.CANDIDATE_UNIVERSE_MISMATCH,
                ranking.policy_id,
            )


def _harness_run_id(
    *,
    raw_input_digest: str,
    feature_digest: str,
    candidate_universe_digest: str,
    threshold_set_id: str | None,
    ranking_output_digests: Sequence[str],
    evidence_class: str,
) -> str:
    payload = {
        "candidate_universe_digest": candidate_universe_digest,
        "evidence_class": evidence_class,
        "feature_digest": feature_digest,
        "harness_id": HARNESS_ID,
        "harness_version": HARNESS_VERSION,
        "ranking_output_digests": list(ranking_output_digests),
        "raw_input_digest": raw_input_digest,
        "threshold_set_id": threshold_set_id,
    }
    return f"cap22_mvr_harness_{sha256_hex(canonical_json_dumps(payload))[:24]}"


def _coverage(
    candidate_universe: Sequence[CandidateUniverseMemberV1],
    ranking: OfflinePolicyRankingV1,
) -> dict[str, Any]:
    ranked = {row.canonical_instrument_id for row in ranking.ordered_ranking}
    return {
        "candidate_count": len(candidate_universe),
        "not_rankable_count": len(ranking.not_rankable),
        "policy_id": ranking.policy_id,
        "ranked_count": len(ranking.ordered_ranking),
        "ranked_fraction": format(
            (len(ranked) / len(candidate_universe)) if candidate_universe else 0,
            "f",
        ),
        "threshold_id": ranking.threshold_id,
    }


def run_offline_mvr_evidence_harness_v1(
    *,
    economic_md_snapshot: Mapping[str, Any] | EconomicMdInputSnapshotV1 | None,
    universe_snapshot: Mapping[str, Any] | None,
    policy_b_threshold_set: Mapping[str, Any] | InjectedPolicyBThresholdSetV1 | None,
    evidence_class: str = DEFAULT_EVIDENCE_CLASS,
    expected_provenance: Mapping[str, Any] | None = None,
    extra_policy_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Pure offline replay. Same input/config => same outputs/digests/run-id."""
    if HARNESS_NETWORK_READ_REQUIRED:
        _fail(OfflineMvrHarnessFailureCodeV1.NETWORK_READ_FORBIDDEN)
    classified = _validate_evidence_class(evidence_class)
    snapshot = _as_snapshot(economic_md_snapshot)
    _validate_digest(snapshot)
    _validate_provenance(snapshot, expected_provenance)
    bound_universe, candidate_universe = _bind_cap21(
        snapshot=snapshot, universe_snapshot=universe_snapshot
    )
    try:
        features = tuple(compute_instrument_features_v1(row) for row in snapshot.instruments)
    except OfflineMvrFeatureError as exc:
        raise OfflineMvrHarnessError(exc.failure_code, exc.detail) from exc
    features = tuple(
        sorted(
            features,
            key=lambda row: (row.canonical_instrument_id, row.venue_native_id),
        )
    )
    for policy_id in extra_policy_ids:
        try:
            assert_known_policy_id_v1(policy_id)
        except PolicyBThresholdSetError as exc:
            raise OfflineMvrHarnessError(exc.failure_code, exc.detail) from exc

    try:
        parsed_threshold_set = parse_injected_policy_b_threshold_set_v1(policy_b_threshold_set)
        ranking_a = evaluate_challenger_a_v1(features)
        ranking_b_members = evaluate_challenger_b_v1(features, threshold_set=parsed_threshold_set)
        ranking_c = evaluate_challenger_c_v1(features)
        ranking_d = evaluate_challenger_d_v1(features)
        ranking_neg = evaluate_negative_control_v1(
            universe_snapshot=bound_universe,
            candidate_universe=candidate_universe,
        )
    except PolicyBThresholdSetError as exc:
        raise OfflineMvrHarnessError(exc.failure_code, exc.detail) from exc

    all_rankings: tuple[OfflinePolicyRankingV1, ...] = (
        ranking_a,
        *ranking_b_members,
        ranking_c,
        ranking_d,
        ranking_neg,
    )
    _enforce_identical_universe(candidate_universe=candidate_universe, rankings=all_rankings)
    for ranking in all_rankings:
        recomputed = ranking.deterministic_payload_for_digest()
        if sha256_hex(canonical_json_dumps(recomputed)) != ranking.ranking_output_digest:
            _fail(OfflineMvrHarnessFailureCodeV1.NONDETERMINISTIC_OUTPUT, ranking.policy_id)
        if any(
            "inf" in str(value).lower()
            for row in ranking.ordered_ranking
            for value in row.sort_keys.values()
        ):
            _fail(
                OfflineMvrHarnessFailureCodeV1.POLICY_C_ZERO_SPREAD_INFINITY_FORBIDDEN,
                ranking.policy_id,
            )

    raw_digest = _raw_input_digest(snapshot)
    feature_digest = _feature_digest(features)
    universe_digest = _candidate_universe_digest(candidate_universe)
    ranking_digests = tuple(row.ranking_output_digest for row in all_rankings)
    run_id = _harness_run_id(
        raw_input_digest=raw_digest,
        feature_digest=feature_digest,
        candidate_universe_digest=universe_digest,
        threshold_set_id=parsed_threshold_set.threshold_set_id,
        ranking_output_digests=ranking_digests,
        evidence_class=classified,
    )
    comparisons = [
        overlap_and_displacement_v1(ranking_a, ranking_c),
        overlap_and_displacement_v1(ranking_a, ranking_d),
        overlap_and_displacement_v1(ranking_c, ranking_d),
        overlap_and_displacement_v1(ranking_a, ranking_neg),
    ]
    for member_ranking in ranking_b_members:
        comparisons.append(overlap_and_displacement_v1(ranking_a, member_ranking))
    payload = {
        "authority": authority_block(),
        "call_graph": list(CALL_GRAPH),
        "candidate_universe": [row.to_dict() for row in candidate_universe],
        "candidate_universe_digest": universe_digest,
        "challenger_rankings": [row.to_dict() for row in all_rankings],
        "coverage": [_coverage(candidate_universe, row) for row in all_rankings],
        "economic_input_snapshot_id": snapshot.economic_input_snapshot_id,
        "evidence_class": classified,
        "feature_digest": feature_digest,
        "features": [row.to_dict() for row in features],
        "harness_id": HARNESS_ID,
        "harness_network_read": False,
        "harness_run_id": run_id,
        "harness_version": HARNESS_VERSION,
        "ok": True,
        "policy_b_gate_pass_counts": [
            {
                "gate_pass_count": row.gate_pass_count,
                "threshold_id": row.threshold_id,
                "threshold_value": row.threshold_value,
            }
            for row in ranking_b_members
        ],
        "policy_b_threshold_set": parsed_threshold_set.to_dict(),
        "policy_c_exact_zero_not_rankable_count": ranking_c.exact_zero_not_rankable_count,
        "policy_ids": [
            CHALLENGER_A_POLICY_ID,
            CHALLENGER_B_POLICY_ID,
            CHALLENGER_C_POLICY_ID,
            CHALLENGER_D_POLICY_ID,
            NEGATIVE_CONTROL_POLICY_ID,
        ],
        "rank_comparison_diagnostics": comparisons,
        "raw_input_digest": raw_digest,
    }
    forbidden_keys = {
        "policy_winner",
        "policy_winner_id",
        "forward_abs_return",
        "forward_realized_vol",
        "friction_adjusted_forward_opportunity",
        "spearman",
        "pnl",
        "sharpe",
        "maxdd",
        "profit_factor",
        "active_set",
        "walk_forward",
    }
    leaked = forbidden_keys.intersection(payload)
    if leaked:
        _fail(
            OfflineMvrHarnessFailureCodeV1.FORWARD_LABEL_METRIC_FORBIDDEN,
            ",".join(sorted(leaked)),
        )
    return payload
