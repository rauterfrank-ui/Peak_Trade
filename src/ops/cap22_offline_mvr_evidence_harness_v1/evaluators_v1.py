"""Pure offline challenger evaluators A/B/C/D. No Policy A. No Active Set."""

from __future__ import annotations

from typing import Sequence

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    CHALLENGER_A_CLASS,
    CHALLENGER_A_POLICY_ID,
    CHALLENGER_B_CLASS,
    CHALLENGER_B_POLICY_ID,
    CHALLENGER_C_CLASS,
    CHALLENGER_C_POLICY_ID,
    CHALLENGER_D_CLASS,
    CHALLENGER_D_POLICY_ID,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.features_v1 import (
    OfflineMvrInstrumentFeaturesV1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.models_v1 import (
    NotRankableCandidateV1,
    OfflinePolicyRankingV1,
    make_policy_ranking,
    ranked_from_sorted,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.reason_codes_v1 import (
    OfflineMvrHarnessFailureCodeV1,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.threshold_set_v1 import (
    InjectedPolicyBThresholdSetV1,
    PolicyBThresholdMemberV1,
    PolicyBThresholdSetError,
)
from src.ops.cap22_offline_mvr_spread_challenger_order_contract_v1 import (
    POLICY_C_ZERO_SPREAD_RESULT,
)


def evaluate_challenger_a_v1(
    features: Sequence[OfflineMvrInstrumentFeaturesV1],
) -> OfflinePolicyRankingV1:
    rows = [
        (
            (-row.volatility, row.venue_native_id, row.canonical_instrument_id),
            row.venue_native_id,
            row.canonical_instrument_id,
            {
                "primary": "volatility_desc",
                "volatility": format(row.volatility, ".16e"),
            },
        )
        for row in features
    ]
    rows.sort(key=lambda item: item[0])
    return make_policy_ranking(
        policy_id=CHALLENGER_A_POLICY_ID,
        policy_class=CHALLENGER_A_CLASS,
        ordered=ranked_from_sorted(rows),
    )


def evaluate_challenger_b_member_v1(
    features: Sequence[OfflineMvrInstrumentFeaturesV1],
    *,
    threshold_set: InjectedPolicyBThresholdSetV1,
    member: PolicyBThresholdMemberV1,
) -> OfflinePolicyRankingV1:
    eligible: list[OfflineMvrInstrumentFeaturesV1] = []
    gated: list[NotRankableCandidateV1] = []
    for row in features:
        if row.relative_spread <= member.relative_spread_threshold:
            eligible.append(row)
        else:
            gated.append(
                NotRankableCandidateV1(
                    canonical_instrument_id=row.canonical_instrument_id,
                    venue_native_id=row.venue_native_id,
                    reason_code="POLICY_B_HARD_SPREAD_GATE_FAILED",
                )
            )
    rows = [
        (
            (-row.volatility, row.venue_native_id, row.canonical_instrument_id),
            row.venue_native_id,
            row.canonical_instrument_id,
            {
                "primary": "volatility_desc_after_spread_gate",
                "relative_spread": format(row.relative_spread, "f"),
                "threshold": format(member.relative_spread_threshold, "f"),
                "volatility": format(row.volatility, ".16e"),
            },
        )
        for row in eligible
    ]
    rows.sort(key=lambda item: item[0])
    gated_sorted = tuple(
        sorted(gated, key=lambda item: (item.venue_native_id, item.canonical_instrument_id))
    )
    return make_policy_ranking(
        policy_id=CHALLENGER_B_POLICY_ID,
        policy_class=CHALLENGER_B_CLASS,
        ordered=ranked_from_sorted(rows),
        not_rankable=gated_sorted,
        threshold_set_id=threshold_set.threshold_set_id,
        threshold_id=member.threshold_id,
        threshold_value=format(member.relative_spread_threshold, "f"),
        gate_pass_count=len(eligible),
    )


def evaluate_challenger_b_v1(
    features: Sequence[OfflineMvrInstrumentFeaturesV1],
    *,
    threshold_set: InjectedPolicyBThresholdSetV1 | None,
) -> tuple[OfflinePolicyRankingV1, ...]:
    if threshold_set is None:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.POLICY_B_THRESHOLD_SET_MISSING.value
        )
    return tuple(
        evaluate_challenger_b_member_v1(features, threshold_set=threshold_set, member=member)
        for member in threshold_set.members
    )


def evaluate_challenger_c_v1(
    features: Sequence[OfflineMvrInstrumentFeaturesV1],
) -> OfflinePolicyRankingV1:
    rankable: list[tuple[tuple[object, ...], str, str, dict[str, str]]] = []
    not_rankable: list[NotRankableCandidateV1] = []
    for row in features:
        if row.relative_spread == 0 or row.exact_zero_spread:
            not_rankable.append(
                NotRankableCandidateV1(
                    canonical_instrument_id=row.canonical_instrument_id,
                    venue_native_id=row.venue_native_id,
                    reason_code=POLICY_C_ZERO_SPREAD_RESULT,
                )
            )
            continue
        if row.relative_spread < 0:
            raise PolicyBThresholdSetError(OfflineMvrHarnessFailureCodeV1.INVALID_BID_ASK.value)
        ratio = row.volatility / row.relative_spread
        if ratio.is_infinite() or ratio != ratio:
            raise PolicyBThresholdSetError(
                OfflineMvrHarnessFailureCodeV1.POLICY_C_ZERO_SPREAD_INFINITY_FORBIDDEN.value
            )
        rankable.append(
            (
                (-ratio, row.venue_native_id, row.canonical_instrument_id),
                row.venue_native_id,
                row.canonical_instrument_id,
                {
                    "primary": "volatility_divided_by_relative_spread_desc",
                    "ratio": format(ratio, ".16e"),
                    "relative_spread": format(row.relative_spread, "f"),
                    "volatility": format(row.volatility, ".16e"),
                },
            )
        )
    rankable.sort(key=lambda item: item[0])
    not_rankable_sorted = tuple(
        sorted(
            not_rankable,
            key=lambda item: (item.venue_native_id, item.canonical_instrument_id),
        )
    )
    return make_policy_ranking(
        policy_id=CHALLENGER_C_POLICY_ID,
        policy_class=CHALLENGER_C_CLASS,
        ordered=ranked_from_sorted(rankable),
        not_rankable=not_rankable_sorted,
        exact_zero_not_rankable_count=len(not_rankable_sorted),
    )


def evaluate_challenger_d_v1(
    features: Sequence[OfflineMvrInstrumentFeaturesV1],
) -> OfflinePolicyRankingV1:
    rows = [
        (
            (
                row.relative_spread,
                -row.volatility,
                row.venue_native_id,
                row.canonical_instrument_id,
            ),
            row.venue_native_id,
            row.canonical_instrument_id,
            {
                "primary": "relative_spread_asc",
                "relative_spread": format(row.relative_spread, "f"),
                "secondary": "volatility_desc",
                "volatility": format(row.volatility, ".16e"),
            },
        )
        for row in features
    ]
    rows.sort(key=lambda item: item[0])
    return make_policy_ranking(
        policy_id=CHALLENGER_D_POLICY_ID,
        policy_class=CHALLENGER_D_CLASS,
        ordered=ranked_from_sorted(rows),
    )


KNOWN_POLICY_IDS: frozenset[str] = frozenset(
    {
        CHALLENGER_A_POLICY_ID,
        CHALLENGER_B_POLICY_ID,
        CHALLENGER_C_POLICY_ID,
        CHALLENGER_D_POLICY_ID,
        "CAP22_MVR_STRUCTURAL_NEGATIVE_CONTROL_V1",
    }
)


def assert_known_policy_id_v1(policy_id: str) -> None:
    if policy_id not in KNOWN_POLICY_IDS:
        raise PolicyBThresholdSetError(
            OfflineMvrHarnessFailureCodeV1.UNKNOWN_POLICY_ID.value, policy_id
        )
