"""B11 operator-facing selected future profile and explainability projection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from src.ops.future_profile_snapshot_v1.constants_v1 import (
    AUTHORITY_PROFILE_ONLY,
    AUTHORITY_UNCLASSIFIED,
)
from src.ops.future_profile_snapshot_v1.models_v1 import (
    FutureProfileSnapshotV1,
    validate_future_profile_snapshot_v1,
)
from src.ops.future_profile_snapshot_v1.producer_v1 import get_selected_future_profile_v1
from src.ops.peak_trade_operator_profile_explainability_v1.constants_v1 import (
    B11_FEATURE_RECOMPUTE_COUNT,
    B11_RERANK_COUNT,
    B11_RESELECT_COUNT,
    B11_RESCORE_COUNT,
    PACKAGE_ID,
    PRODUCER_VERSION,
    REASON_AUTHORITY_INVARIANT_DRIFT,
    REASON_BINDING_NOT_OK,
    REASON_BOUND_IDENTITY_MISMATCH,
    REASON_EXPLAINABILITY_DIGEST_MISMATCH,
    REASON_MISSING_FUTURE_PROFILE,
    REASON_MISSING_RANKING_EXPLAINABILITY,
    REASON_MISSING_RANKING_SNAPSHOT,
    REASON_MISSING_RUNTIME_BINDING_EVIDENCE,
    REASON_MISSING_SELECTION,
    REASON_PROFILE_AUTHORITY_PROMOTION,
    REASON_PROFILE_DIGEST_MISMATCH,
    REASON_RANKING_DIGEST_MISMATCH,
    REASON_SELECTED_CANDIDATE_NOT_RANKED,
    REASON_SELECTED_EXPLAINABILITY_NOT_FOUND,
    REASON_SELECTED_IDENTITY_MISMATCH,
    REASON_SELECTED_PROFILE_NOT_FOUND,
    REASON_SELECTED_RANK_MISMATCH,
    REASON_SELECTION_DIGEST_MISMATCH,
    SCHEMA_VERSION,
    VIEW_STATE_AVAILABLE,
    VIEW_STATE_INCOMPLETE_REQUIRED_EVIDENCE,
    authority_block_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    RankingCandidateFeatureBundleV1,
    RankingFeatureExplainabilityWitnessV1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankedCandidateV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    RuntimeBindingEvidenceV1,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class OperatorProfileExplainabilityError(ValueError):
    """Fail-closed B11 view contract error."""


@dataclass(frozen=True)
class OperatorProfileExplainabilityViewV1:
    schema_version: str
    capability_id: str
    producer_version: str
    view_id: str
    repository_sha: str
    produced_at_wall_time: str
    view_state: str
    ok: bool
    hard_stop: bool
    reason_codes: tuple[str, ...]
    selected_future_identity: Mapping[str, Any]
    eligibility: Mapping[str, Any]
    rank: Optional[int]
    ranking_explanation: Mapping[str, Any]
    future_profile: Mapping[str, Any]
    timestamps: Mapping[str, Any]
    provenance: Mapping[str, Any]
    authority: Mapping[str, Any] = field(default_factory=dict)
    integrity_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": dict(sorted(self.authority.items())),
            "capability_id": self.capability_id,
            "eligibility": _sorted_mapping(self.eligibility),
            "future_profile": _sorted_mapping(self.future_profile),
            "hard_stop": bool(self.hard_stop),
            "integrity_digest": self.integrity_digest,
            "ok": bool(self.ok),
            "producer_version": self.producer_version,
            "produced_at_wall_time": self.produced_at_wall_time,
            "provenance": _sorted_mapping(self.provenance),
            "rank": None if self.rank is None else int(self.rank),
            "ranking_explanation": _sorted_mapping(self.ranking_explanation),
            "reason_codes": list(self.reason_codes),
            "repository_sha": self.repository_sha,
            "schema_version": self.schema_version,
            "selected_future_identity": _sorted_mapping(self.selected_future_identity),
            "timestamps": _sorted_mapping(self.timestamps),
            "view_id": self.view_id,
            "view_state": self.view_state,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        payload.pop("produced_at_wall_time", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_integrity_digest(self) -> "OperatorProfileExplainabilityViewV1":
        return OperatorProfileExplainabilityViewV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            view_id=self.view_id,
            repository_sha=self.repository_sha,
            produced_at_wall_time=self.produced_at_wall_time,
            view_state=self.view_state,
            ok=self.ok,
            hard_stop=self.hard_stop,
            reason_codes=self.reason_codes,
            selected_future_identity=dict(self.selected_future_identity),
            eligibility=dict(self.eligibility),
            rank=self.rank,
            ranking_explanation=dict(self.ranking_explanation),
            future_profile=dict(self.future_profile),
            timestamps=dict(self.timestamps),
            provenance=dict(self.provenance),
            authority=dict(self.authority),
            integrity_digest=self.compute_integrity_digest(),
        )


def _sorted_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): value[k] for k in sorted(value)}


def _coerce_selection(
    selection: Mapping[str, Any] | SingleSelectedFutureSelectionV1 | None,
) -> SingleSelectedFutureSelectionV1 | None:
    if selection is None:
        return None
    if isinstance(selection, SingleSelectedFutureSelectionV1):
        return selection
    return SingleSelectedFutureSelectionV1.from_dict(selection)


def _coerce_ranking(
    ranking: Mapping[str, Any] | ProductiveFuturesRankingSnapshotV1 | None,
) -> ProductiveFuturesRankingSnapshotV1 | None:
    if ranking is None:
        return None
    if isinstance(ranking, ProductiveFuturesRankingSnapshotV1):
        return ranking
    return ProductiveFuturesRankingSnapshotV1.from_dict(ranking)


def _coerce_explainability(
    witness: Mapping[str, Any] | RankingFeatureExplainabilityWitnessV1 | None,
) -> RankingFeatureExplainabilityWitnessV1 | None:
    if witness is None:
        return None
    if isinstance(witness, RankingFeatureExplainabilityWitnessV1):
        return witness
    return RankingFeatureExplainabilityWitnessV1.from_dict(witness)


def _coerce_profile(
    profile: Mapping[str, Any] | FutureProfileSnapshotV1 | None,
) -> FutureProfileSnapshotV1 | None:
    if profile is None:
        return None
    if isinstance(profile, FutureProfileSnapshotV1):
        return profile
    return FutureProfileSnapshotV1.from_dict(profile)


def _binding_to_dict(
    binding: Mapping[str, Any] | RuntimeBindingEvidenceV1 | None,
) -> dict[str, Any] | None:
    if binding is None:
        return None
    if isinstance(binding, RuntimeBindingEvidenceV1):
        return binding.to_dict()
    return dict(binding)


def _find_ranked_candidate(
    ranking: ProductiveFuturesRankingSnapshotV1 | None,
    instrument_id: str,
) -> RankedCandidateV1 | None:
    if ranking is None or not instrument_id:
        return None
    for candidate in ranking.ranked_candidates:
        if candidate.canonical_instrument_id == instrument_id:
            return candidate
    return None


def _find_explainability_candidate(
    witness: RankingFeatureExplainabilityWitnessV1 | None,
    instrument_id: str,
) -> RankingCandidateFeatureBundleV1 | None:
    if witness is None or not instrument_id:
        return None
    for candidate in witness.candidates:
        if candidate.canonical_instrument_id == instrument_id:
            return candidate
    return None


def _authority_effects_preserved(profile: FutureProfileSnapshotV1 | None) -> bool:
    if profile is None:
        return True
    for instrument in profile.instruments:
        for row in instrument.fields:
            if row.authority_class in {AUTHORITY_PROFILE_ONLY, AUTHORITY_UNCLASSIFIED}:
                if row.field_id in {"rank_position", "balanced_movement_score"}:
                    return False
    return True


def _compute_view_id(
    *,
    repository_sha: str,
    selection: SingleSelectedFutureSelectionV1 | None,
    ranking: ProductiveFuturesRankingSnapshotV1 | None,
    witness: RankingFeatureExplainabilityWitnessV1 | None,
    profile: FutureProfileSnapshotV1 | None,
    binding: Mapping[str, Any] | None,
) -> str:
    payload = {
        "binding_selection_id": "" if binding is None else str(binding.get("selection_id") or ""),
        "binding_selection_integrity_digest": ""
        if binding is None
        else str(binding.get("selection_integrity_digest") or ""),
        "capability_id": PACKAGE_ID,
        "profile_integrity_digest": "" if profile is None else profile.integrity_digest,
        "profile_snapshot_id": "" if profile is None else profile.profile_snapshot_id,
        "ranking_explainability_digest": "" if witness is None else witness.integrity_digest,
        "ranking_integrity_digest": "" if ranking is None else ranking.integrity_digest,
        "ranking_snapshot_id": "" if ranking is None else ranking.ranking_snapshot_id,
        "repository_sha": repository_sha,
        "schema_version": SCHEMA_VERSION,
        "selection_id": "" if selection is None else selection.selection_id,
        "selection_integrity_digest": "" if selection is None else selection.integrity_digest,
    }
    return f"b11_view_{sha256_hex(canonical_json_dumps(payload))[:24]}"


def build_operator_profile_explainability_view_v1(
    *,
    selection: Mapping[str, Any] | SingleSelectedFutureSelectionV1 | None,
    runtime_binding_evidence: Mapping[str, Any] | RuntimeBindingEvidenceV1 | None,
    ranking_snapshot: Mapping[str, Any] | ProductiveFuturesRankingSnapshotV1 | None,
    ranking_explainability: Mapping[str, Any] | RankingFeatureExplainabilityWitnessV1 | None,
    future_profile_snapshot: Mapping[str, Any] | FutureProfileSnapshotV1 | None,
    repository_sha: str,
    produced_at_wall_time: str,
) -> OperatorProfileExplainabilityViewV1:
    """Project authoritative upstream facts into an inert operator view."""

    selected = _coerce_selection(selection)
    ranking = _coerce_ranking(ranking_snapshot)
    witness = _coerce_explainability(ranking_explainability)
    profile = _coerce_profile(future_profile_snapshot)
    binding = _binding_to_dict(runtime_binding_evidence)

    reasons: list[str] = []
    if selected is None:
        reasons.append(REASON_MISSING_SELECTION)
    elif selected.integrity_digest != selected.compute_integrity_digest():
        reasons.append(REASON_SELECTION_DIGEST_MISMATCH)
    if binding is None:
        reasons.append(REASON_MISSING_RUNTIME_BINDING_EVIDENCE)
    if ranking is None:
        reasons.append(REASON_MISSING_RANKING_SNAPSHOT)
    elif ranking.integrity_digest != ranking.compute_integrity_digest():
        reasons.append(REASON_RANKING_DIGEST_MISMATCH)
    if witness is None:
        reasons.append(REASON_MISSING_RANKING_EXPLAINABILITY)
    elif witness.integrity_digest != witness.compute_integrity_digest():
        reasons.append(REASON_EXPLAINABILITY_DIGEST_MISMATCH)
    if profile is None:
        reasons.append(REASON_MISSING_FUTURE_PROFILE)
    else:
        try:
            validate_future_profile_snapshot_v1(profile)
        except Exception:  # noqa: BLE001
            reasons.append(REASON_PROFILE_DIGEST_MISMATCH)

    instrument_id = "" if selected is None else selected.instrument_id
    venue_native_id = "" if selected is None else selected.venue_native_id
    ranked_candidate = _find_ranked_candidate(ranking, instrument_id)
    explanation_candidate = _find_explainability_candidate(witness, instrument_id)
    selected_profile = get_selected_future_profile_v1(profile) if profile is not None else None

    if selected is not None and not instrument_id:
        reasons.append(REASON_SELECTED_IDENTITY_MISMATCH)
    if ranked_candidate is None and instrument_id:
        reasons.append(REASON_SELECTED_CANDIDATE_NOT_RANKED)
    if (
        selected is not None
        and ranked_candidate is not None
        and selected.selected_rank
        and selected.selected_rank != ranked_candidate.rank
    ):
        reasons.append(REASON_SELECTED_RANK_MISMATCH)
    if explanation_candidate is None and instrument_id:
        reasons.append(REASON_SELECTED_EXPLAINABILITY_NOT_FOUND)
    if selected_profile is None and instrument_id:
        reasons.append(REASON_SELECTED_PROFILE_NOT_FOUND)
    if (
        profile is not None
        and selected is not None
        and str(profile.selected_instrument_reference.get("instrument_id") or "")
        != selected.instrument_id
    ):
        reasons.append(REASON_SELECTED_IDENTITY_MISMATCH)
    if binding is not None and selected is not None:
        if not bool(binding.get("ok")):
            reasons.append(REASON_BINDING_NOT_OK)
        if str(binding.get("instrument_id") or "") != selected.instrument_id:
            reasons.append(REASON_BOUND_IDENTITY_MISMATCH)
        if str(binding.get("selection_id") or "") != selected.selection_id:
            reasons.append(REASON_BOUND_IDENTITY_MISMATCH)
    if not _authority_effects_preserved(profile):
        reasons.append(REASON_PROFILE_AUTHORITY_PROMOTION)

    authority = authority_block_v1()
    if (
        authority["B11_FEATURE_RECOMPUTE_COUNT"] != B11_FEATURE_RECOMPUTE_COUNT
        or authority["B11_RESCORE_COUNT"] != B11_RESCORE_COUNT
        or authority["B11_RERANK_COUNT"] != B11_RERANK_COUNT
        or authority["B11_RESELECT_COUNT"] != B11_RESELECT_COUNT
    ):
        reasons.append(REASON_AUTHORITY_INVARIANT_DRIFT)

    reason_codes = tuple(sorted(set(reasons)))
    ok = not reason_codes
    view_state = VIEW_STATE_AVAILABLE if ok else VIEW_STATE_INCOMPLETE_REQUIRED_EVIDENCE
    explanation = (
        {}
        if explanation_candidate is None or witness is None
        else {
            "balanced_movement_score": explanation_candidate.balanced_movement_score,
            "economic_rank_state": witness.economic_rank_state,
            "input2_provenance": witness.input2_provenance.to_dict(),
            "normalized_features": [
                row.to_dict() for row in explanation_candidate.normalized_features
            ],
            "order_primary": witness.order_primary,
            "order_secondary": witness.order_secondary,
            "order_tertiary": witness.order_tertiary,
            "policy_identity": witness.policy_identity.to_dict(),
            "rank_position": explanation_candidate.rank_position,
            "raw_features": [row.to_dict() for row in explanation_candidate.raw_features],
            "score_contributions": [
                row.to_dict() for row in explanation_candidate.score_contributions
            ],
            "tie_break_witness": [row.to_dict() for row in explanation_candidate.tie_break_witness],
        }
    )
    future_profile = {} if selected_profile is None else selected_profile.to_dict()
    rank = None if ranked_candidate is None else int(ranked_candidate.rank)

    view = OperatorProfileExplainabilityViewV1(
        schema_version=SCHEMA_VERSION,
        capability_id=PACKAGE_ID,
        producer_version=PRODUCER_VERSION,
        view_id=_compute_view_id(
            repository_sha=repository_sha,
            selection=selected,
            ranking=ranking,
            witness=witness,
            profile=profile,
            binding=binding,
        ),
        repository_sha=repository_sha,
        produced_at_wall_time=produced_at_wall_time,
        view_state=view_state,
        ok=ok,
        hard_stop=not ok,
        reason_codes=reason_codes,
        selected_future_identity={
            "binding_ok": False if binding is None else bool(binding.get("ok")),
            "bound_instrument_id": ""
            if binding is None
            else str(binding.get("instrument_id") or ""),
            "instrument_id": instrument_id,
            "selection_id": "" if selected is None else selected.selection_id,
            "selection_state": "" if selected is None else selected.state,
            "venue_native_id": venue_native_id,
        },
        eligibility={
            "binding_failure_codes": []
            if binding is None
            else list(binding.get("failure_codes") or ()),
            "ranking_eligibility_status": ""
            if ranked_candidate is None
            else ranked_candidate.eligibility_status,
            "ranking_exclusion_reason_codes": []
            if ranked_candidate is None
            else list(ranked_candidate.exclusion_reason_codes),
            "selection_reason_codes": [] if selected is None else list(selected.reason_codes),
            "selection_state": "" if selected is None else selected.state,
            "selected_active": False
            if selected is None
            else selected.state == STATE_SELECTED_ACTIVE,
        },
        rank=rank,
        ranking_explanation=explanation,
        future_profile=future_profile,
        timestamps={
            "profile_event_time": "" if profile is None else profile.profile_event_time,
            "ranking_event_time": "" if ranking is None else ranking.event_time,
            "selection_selected_at_event_time": ""
            if selected is None
            else selected.selected_at_event_time,
            "selection_valid_from": "" if selected is None else selected.valid_from,
            "selection_valid_until": "" if selected is None else selected.valid_until,
        },
        provenance={
            "binding_capability_id": ""
            if binding is None
            else str(binding.get("capability_id") or ""),
            "binding_config_digest": ""
            if binding is None
            else str(binding.get("config_digest") or ""),
            "feature_contract_digest": ""
            if witness is None
            else witness.policy_identity.feature_contract_digest,
            "future_profile_integrity_digest": "" if profile is None else profile.integrity_digest,
            "future_profile_snapshot_id": "" if profile is None else profile.profile_snapshot_id,
            "ranking_config_digest": "" if ranking is None else ranking.config_digest,
            "ranking_explainability_digest": "" if witness is None else witness.integrity_digest,
            "ranking_integrity_digest": "" if ranking is None else ranking.integrity_digest,
            "ranking_policy_digest": ""
            if witness is None
            else witness.policy_identity.ranking_policy_digest,
            "ranking_policy_id": "" if ranking is None else ranking.ranking_policy_id,
            "ranking_policy_version": "" if ranking is None else ranking.ranking_policy_version,
            "ranking_snapshot_id": "" if ranking is None else ranking.ranking_snapshot_id,
            "selection_config_digest": "" if selected is None else selected.config_digest,
            "selection_integrity_digest": "" if selected is None else selected.integrity_digest,
            "selection_policy_id": "" if selected is None else selected.policy_id,
            "selection_policy_version": "" if selected is None else selected.policy_version,
        },
        authority=authority,
    ).with_integrity_digest()
    validate_operator_profile_explainability_view_v1(view)
    return view


def validate_operator_profile_explainability_view_v1(
    view: OperatorProfileExplainabilityViewV1,
) -> None:
    if view.schema_version != SCHEMA_VERSION:
        raise OperatorProfileExplainabilityError("SCHEMA_VERSION_MISMATCH")
    if view.capability_id != PACKAGE_ID:
        raise OperatorProfileExplainabilityError("CAPABILITY_ID_MISMATCH")
    if view.integrity_digest != view.compute_integrity_digest():
        raise OperatorProfileExplainabilityError("INTEGRITY_DIGEST_MISMATCH")
    auth = dict(view.authority)
    if auth.get("B11_FEATURE_RECOMPUTE_COUNT") != 0:
        raise OperatorProfileExplainabilityError("FEATURE_RECOMPUTE_FORBIDDEN")
    if auth.get("B11_RESCORE_COUNT") != 0:
        raise OperatorProfileExplainabilityError("RESCORE_FORBIDDEN")
    if auth.get("B11_RERANK_COUNT") != 0:
        raise OperatorProfileExplainabilityError("RERANK_FORBIDDEN")
    if auth.get("B11_RESELECT_COUNT") != 0:
        raise OperatorProfileExplainabilityError("RESELECT_FORBIDDEN")
    if auth.get("PROFILE_ONLY_RANKING_EFFECT") != "NONE":
        raise OperatorProfileExplainabilityError("PROFILE_ONLY_RANKING_EFFECT_FORBIDDEN")
    if auth.get("PROFILE_ONLY_SELECTION_EFFECT") != "NONE":
        raise OperatorProfileExplainabilityError("PROFILE_ONLY_SELECTION_EFFECT_FORBIDDEN")
    if auth.get("UNCLASSIFIED_RANKING_EFFECT") != "NONE":
        raise OperatorProfileExplainabilityError("UNCLASSIFIED_RANKING_EFFECT_FORBIDDEN")
    if auth.get("UNCLASSIFIED_SELECTION_EFFECT") != "NONE":
        raise OperatorProfileExplainabilityError("UNCLASSIFIED_SELECTION_EFFECT_FORBIDDEN")
    if auth.get("MAX_POSITIONS_EFFECTIVE") != 1:
        raise OperatorProfileExplainabilityError("MAX_POSITIONS_EFFECTIVE_DRIFT")
    if auth.get("MULTI_FUTURE_RUNTIME_AUTHORIZED") is not False:
        raise OperatorProfileExplainabilityError("MULTI_FUTURE_AUTHORITY_FORBIDDEN")
    if auth.get("LIVE_EXTERNAL_EFFECT_AUTHORIZED") is not False:
        raise OperatorProfileExplainabilityError("LIVE_EXTERNAL_EFFECT_FORBIDDEN")
