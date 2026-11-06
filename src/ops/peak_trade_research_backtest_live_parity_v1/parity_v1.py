"""B09 parity runner over the authoritative B05/B06 Peak_Trade economics.

This module intentionally contains no economic formula implementation. It is
an adapter/proof surface that routes equivalent mode inputs through the same
authoritative B05 feature producer and B06 economic ranking runtime.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1 import (
    classify_and_rank_economic_candidates_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    validate_explainability_witness_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
    validate_ranking_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)

from src.ops.peak_trade_research_backtest_live_parity_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    B10_STARTED,
    CAP23_RERANK_COUNT,
    CAP23_RESCORE_COUNT,
    CAP23_SOLE_SELECTION_OWNER,
    CURRENT_PATH_CLASSIFICATION_V1,
    CROSS_UNIVERSE_AUTHORITY,
    FEATURE_FORMULA_CHANGED,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PACKAGE_MARKER,
    PARITY_MODES,
    PARITY_PACKAGE_ID,
    PARITY_SSOT,
    PARITY_VERSION,
    PRODUCTIVE_MODE,
    RANKING_POLICY_CHANGED,
    REQUIRED_POLICY_IDENTITY,
    RESEARCH_BACKTEST_SHADOW_PRODUCTIVE_AUTHORITY_CREATED,
    RUNTIME_AUTHORIZATION_EFFECT,
)
from src.ops.peak_trade_research_backtest_live_parity_v1.models_v1 import (
    ModeParityWitnessV1,
    ParityProofV1,
)


class PeakTradeParityError(ValueError):
    """Fail-closed parity proof error."""


def authority_block_v1() -> dict[str, Any]:
    return {
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "B10_STARTED": B10_STARTED,
        "CAP23_RERANK_COUNT": CAP23_RERANK_COUNT,
        "CAP23_RESCORE_COUNT": CAP23_RESCORE_COUNT,
        "CAP23_SOLE_SELECTION_OWNER": CAP23_SOLE_SELECTION_OWNER,
        "CROSS_UNIVERSE_AUTHORITY": CROSS_UNIVERSE_AUTHORITY,
        "FEATURE_FORMULA_CHANGED": FEATURE_FORMULA_CHANGED,
        "LIVE_EXTERNAL_EFFECT_AUTHORIZED": LIVE_EXTERNAL_EFFECT_AUTHORIZED,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "PACKAGE_MARKER": PACKAGE_MARKER,
        "PARITY_SSOT": PARITY_SSOT,
        "RANKING_POLICY_CHANGED": RANKING_POLICY_CHANGED,
        "RESEARCH_BACKTEST_SHADOW_PRODUCTIVE_AUTHORITY_CREATED": (
            RESEARCH_BACKTEST_SHADOW_PRODUCTIVE_AUTHORITY_CREATED
        ),
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
    }


def _universe_payload(
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1,
) -> dict[str, Any]:
    if isinstance(universe_snapshot, GovernedFuturesUniverseSnapshotV1):
        return universe_snapshot.to_dict()
    if not isinstance(universe_snapshot, Mapping):
        raise PeakTradeParityError("UNIVERSE_SNAPSHOT_REQUIRED")
    return dict(universe_snapshot)


def _economic_md_snapshot(
    economic_md_snapshot: Mapping[str, Any] | EconomicMdInputSnapshotV1,
) -> EconomicMdInputSnapshotV1:
    if isinstance(economic_md_snapshot, EconomicMdInputSnapshotV1):
        snapshot = economic_md_snapshot
    elif isinstance(economic_md_snapshot, Mapping):
        snapshot = EconomicMdInputSnapshotV1.from_dict(economic_md_snapshot)
    else:
        raise PeakTradeParityError("ECONOMIC_MD_SNAPSHOT_REQUIRED")
    if snapshot.payload_digest != snapshot.compute_payload_digest():
        raise PeakTradeParityError("ECONOMIC_MD_DIGEST_MISMATCH")
    return snapshot


def _feature_witness_rows(snapshot: Any) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    for instrument in snapshot.instruments:
        raw_by_id = {
            row.feature_policy_id: {
                "state": row.state.value,
                "raw_value": row.raw_value,
                "units": row.units,
                "direction": row.direction,
                "raw_feature_normalization": row.raw_feature_normalization,
                "reason_code": row.reason_code,
            }
            for row in instrument.raw_features
        }
        rows.append(
            {
                "canonical_instrument_id": instrument.canonical_instrument_id,
                "venue_native_id": instrument.venue_native_id,
                "feature_production_ready": instrument.feature_production_ready,
                "raw_features": raw_by_id,
            }
        )
    return tuple(sorted(rows, key=lambda row: str(row["canonical_instrument_id"])))


def _rank_witness_rows(economic_result: Any) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    by_id = {row.canonical_instrument_id: row for row in economic_result.explainability.candidates}
    for candidate in economic_result.ranked:
        explain = by_id[candidate.canonical_instrument_id]
        rows.append(
            {
                "rank": candidate.rank,
                "canonical_instrument_id": candidate.canonical_instrument_id,
                "venue_native_id": candidate.venue_native_id,
                "total_score": candidate.total_score,
                "tie_break_values": dict(candidate.tie_break_values),
                "normalized_features": [row.to_dict() for row in explain.normalized_features],
                "score_contributions": [row.to_dict() for row in explain.score_contributions],
            }
        )
    return tuple(rows)


def _temporal_witness_rows(snapshot: Any) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    for instrument in snapshot.instruments:
        provenance = instrument.mark_window_provenance
        if provenance is None:
            rows.append(
                {
                    "canonical_instrument_id": instrument.canonical_instrument_id,
                    "ready": False,
                    "no_lookahead_proven": False,
                    "reason": "NO_READY_MARK_WINDOW",
                }
            )
            continue
        event_timestamps = tuple(str(ts) for ts in provenance.event_timestamps)
        as_of = str(provenance.as_of_event_time)
        rows.append(
            {
                "canonical_instrument_id": instrument.canonical_instrument_id,
                "ready": True,
                "as_of_event_time": as_of,
                "event_timestamps": list(event_timestamps),
                "mark_count": provenance.mark_count,
                "no_lookahead_proven": bool(event_timestamps and max(event_timestamps) == as_of),
            }
        )
    return tuple(sorted(rows, key=lambda row: str(row["canonical_instrument_id"])))


def _config_identity(snapshot: Any, ranking_snapshot: Any) -> dict[str, Any]:
    return {
        **REQUIRED_POLICY_IDENTITY,
        "feature_production_schema_version": snapshot.schema_version,
        "feature_production_version": snapshot.production_version,
        "feature_production_digest": snapshot.production_digest,
        "ranking_config_digest": ranking_snapshot.config_digest,
        "ranking_policy_id": ranking_snapshot.ranking_policy_id,
        "ranking_policy_version": ranking_snapshot.ranking_policy_version,
        "ranking_policy_provenance": ranking_snapshot.ranking_policy_provenance,
    }


def produce_mode_parity_witness_v1(
    *,
    mode: str,
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1,
    economic_md_snapshot: Mapping[str, Any] | EconomicMdInputSnapshotV1,
    repository_sha: str,
    producer_observed_at_unix: float,
) -> ModeParityWitnessV1:
    if mode not in PARITY_MODES:
        raise PeakTradeParityError("UNKNOWN_PARITY_MODE", mode)
    universe = _universe_payload(universe_snapshot)
    economic_md = _economic_md_snapshot(economic_md_snapshot)
    features = produce_ranking_feature_production_snapshot_v1(economic_md)
    validate_ranking_feature_production_snapshot_v1(features)
    economic_result = classify_and_rank_economic_candidates_v1(
        universe_snapshot=universe,
        feature_production_snapshot=features,
    )
    validate_explainability_witness_v1(economic_result.explainability)
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=universe,
        feature_production_snapshot=features,
        repository_sha=repository_sha,
        producer_observed_at_unix=producer_observed_at_unix,
    )
    return ModeParityWitnessV1(
        mode=mode,
        ok=bool(ranking.ok),
        feature_witness=_feature_witness_rows(features),
        rank_witness=_rank_witness_rows(economic_result),
        config_identity=_config_identity(features, ranking.snapshot),
        temporal_witness=_temporal_witness_rows(features),
        failure_codes=tuple(ranking.failure_codes),
    )


def _all_equal_to_productive(modes: Sequence[ModeParityWitnessV1], key: str) -> bool:
    productive = next((mode for mode in modes if mode.mode == PRODUCTIVE_MODE), None)
    if productive is None:
        return False
    expected = productive.comparable_payload()[key]
    return all(mode.comparable_payload()[key] == expected for mode in modes)


def _temporal_no_lookahead(modes: Sequence[ModeParityWitnessV1]) -> bool:
    for mode in modes:
        for row in mode.temporal_witness:
            if row.get("ready") is True and row.get("no_lookahead_proven") is not True:
                return False
    return True


def prove_peak_trade_research_backtest_live_parity_v1(
    *,
    universe_snapshot: Mapping[str, Any] | GovernedFuturesUniverseSnapshotV1,
    economic_md_snapshot: Mapping[str, Any] | EconomicMdInputSnapshotV1,
    repository_sha: str,
    producer_observed_at_unix: float,
    modes: Sequence[str] = PARITY_MODES,
) -> ParityProofV1:
    witnesses = tuple(
        produce_mode_parity_witness_v1(
            mode=mode,
            universe_snapshot=universe_snapshot,
            economic_md_snapshot=economic_md_snapshot,
            repository_sha=repository_sha,
            producer_observed_at_unix=producer_observed_at_unix,
        )
        for mode in modes
    )
    feature_ok = _all_equal_to_productive(witnesses, "feature_witness")
    rank_ok = _all_equal_to_productive(witnesses, "rank_witness")
    config_ok = _all_equal_to_productive(witnesses, "config_identity")
    temporal_ok = _all_equal_to_productive(witnesses, "temporal_witness")
    temporal_ok = temporal_ok and _temporal_no_lookahead(witnesses)
    failures: list[str] = []
    if not feature_ok:
        failures.append("FEATURE_FORMULA_PARITY_MISMATCH")
    if not rank_ok:
        failures.append("RANK_ORDER_PARITY_MISMATCH")
    if not config_ok:
        failures.append("CONFIG_VERSION_PARITY_MISMATCH")
    if not temporal_ok:
        failures.append("TEMPORAL_NO_LOOKAHEAD_PARITY_MISMATCH")
    if not all(witness.ok for witness in witnesses):
        failures.append("PARITY_MODE_NOT_OK")
    if any(not witness.rank_witness for witness in witnesses):
        failures.append("PARITY_RANK_WITNESS_MISSING")
    if any(
        any(row.get("feature_production_ready") is not True for row in witness.feature_witness)
        for witness in witnesses
    ):
        failures.append("PARITY_FEATURE_WITNESS_NOT_READY")
    counts: dict[str, int] = {}
    for row in CURRENT_PATH_CLASSIFICATION_V1:
        cls = row["classification"]
        counts[cls] = counts.get(cls, 0) + 1
    proof = ParityProofV1(
        package_id=PARITY_PACKAGE_ID,
        parity_version=PARITY_VERSION,
        repository_sha=repository_sha,
        modes=witnesses,
        authority=authority_block_v1(),
        path_classification=CURRENT_PATH_CLASSIFICATION_V1,
        feature_formula_parity_proven=feature_ok,
        rank_order_parity_proven=rank_ok,
        config_version_parity_proven=config_ok,
        temporal_no_lookahead_proven=temporal_ok,
        productive_only_economic_formula_count=0,
        duplicated_equivalent_path_count=counts.get("DUPLICATED_EQUIVALENT", 0),
        divergent_current_path_count=counts.get("DIVERGENT", 0),
        legacy_not_current_path_count=counts.get("LEGACY_NOT_CURRENT", 0),
        not_applicable_path_count=counts.get("NOT_APPLICABLE", 0),
        failure_codes=tuple(failures),
    ).with_integrity_digest()
    return proof


def validate_parity_proof_v1(proof: ParityProofV1) -> None:
    if proof.package_id != PARITY_PACKAGE_ID:
        raise PeakTradeParityError("PARITY_PACKAGE_ID_MISMATCH")
    if proof.parity_version != PARITY_VERSION:
        raise PeakTradeParityError("PARITY_VERSION_MISMATCH")
    if proof.integrity_digest != proof.compute_integrity_digest():
        raise PeakTradeParityError("PARITY_PROOF_DIGEST_MISMATCH")
    if not proof.feature_formula_parity_proven:
        raise PeakTradeParityError("FEATURE_FORMULA_PARITY_NOT_PROVEN")
    if not proof.rank_order_parity_proven:
        raise PeakTradeParityError("RANK_ORDER_PARITY_NOT_PROVEN")
    if not proof.config_version_parity_proven:
        raise PeakTradeParityError("CONFIG_VERSION_PARITY_NOT_PROVEN")
    if not proof.temporal_no_lookahead_proven:
        raise PeakTradeParityError("TEMPORAL_NO_LOOKAHEAD_NOT_PROVEN")
    if proof.divergent_current_path_count != 0:
        raise PeakTradeParityError("DIVERGENT_CURRENT_PATH_PRESENT")
    if proof.failure_codes:
        raise PeakTradeParityError("PARITY_PROOF_FAILURE_CODES_PRESENT", proof.failure_codes)
    auth = dict(proof.authority)
    if auth.get("RESEARCH_BACKTEST_SHADOW_PRODUCTIVE_AUTHORITY_CREATED") is not False:
        raise PeakTradeParityError("PARITY_AUTHORITY_MIGRATION_FORBIDDEN")
    if auth.get("RANKING_POLICY_CHANGED") is not False:
        raise PeakTradeParityError("RANKING_POLICY_CHANGE_FORBIDDEN")
    if auth.get("FEATURE_FORMULA_CHANGED") is not False:
        raise PeakTradeParityError("FEATURE_FORMULA_CHANGE_FORBIDDEN")
