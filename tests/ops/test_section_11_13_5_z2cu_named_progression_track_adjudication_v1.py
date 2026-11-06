"""§11.13.5.Z2CU named progression-track adjudication. Offline only."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.post_z2ct_named_progression_track_adjudication_v1 import (
    ADJUDICATION,
    ALTERNATIVE_TRACKS,
    CANDIDATE_TRACK_COUNT,
    CANDIDATE_TRACKS,
    CLASS_D_CONSUMED,
    CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH,
    ELIGIBLE_NEXT_TRACK_IDS,
    EMPTY_DATA_IS_ZERO,
    EXECUTION_READY,
    IDENTICAL_UNFILTERED_GET_IS_PERMITTED_OBSERVATION_PATH_ONLY,
    LAST_CANONICALLY_CLOSED_11_13_5_SLICE,
    LiveCanaryPostZ2ctNamedProgressionTrackAdjudicationError,
    OFFLINE_PROGRESSION_AVAILABLE,
    OWNER_GO,
    P3_INTENTIONALLY_LEAVES_SUCCESSOR_SELECTION_TO_OWNER,
    PREREQUISITE_08_STATUS,
    RECOMMENDED_TRACK,
    RUNTIME_REOBSERVATION_IS_ONLY_VALID_NEXT_TRACK,
    THIS_GO_AUTHORIZES_FLATTEN,
    THIS_GO_AUTHORIZES_GET,
    THIS_GO_AUTHORIZES_POST,
    THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE,
    UNIQUE_CANONICAL_NEXT_TRACK,
    Z2AP_CONSUMED,
    adjudicate_post_z2ct_named_progression_tracks_v1,
    reject_automatic_08_reobservation_v1,
    reject_unique_canonical_next_invention_v1,
)


def test_adjudication_constants_are_fail_closed() -> None:
    assert ADJUDICATION == "MULTIPLE_OWNER_SELECTABLE_TRACKS"
    assert UNIQUE_CANONICAL_NEXT_TRACK == "NONE"
    assert RECOMMENDED_TRACK == "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"
    assert RECOMMENDED_TRACK not in ALTERNATIVE_TRACKS
    assert "P3_PREREQUISITE_08_UNFILTERED_POSITION_REOBSERVATION" in ALTERNATIVE_TRACKS
    assert EMPTY_DATA_IS_ZERO is False
    assert OFFLINE_PROGRESSION_AVAILABLE is True
    assert RUNTIME_REOBSERVATION_IS_ONLY_VALID_NEXT_TRACK is False
    assert IDENTICAL_UNFILTERED_GET_IS_PERMITTED_OBSERVATION_PATH_ONLY is True
    assert P3_INTENTIONALLY_LEAVES_SUCCESSOR_SELECTION_TO_OWNER is True
    assert THIS_GO_AUTHORIZES_GET is False
    assert THIS_GO_AUTHORIZES_POST is False
    assert THIS_GO_AUTHORIZES_FLATTEN is False
    assert CLASS_D_CONSUMED is False
    assert Z2AP_CONSUMED is False
    assert EXECUTION_READY is False
    assert LAST_CANONICALLY_CLOSED_11_13_5_SLICE == "SECTION_11_13_5_Z2CT"
    assert THIS_PERSIST_DOES_NOT_SUPERSEDE_Z2CT_AS_LAST_CANONICALLY_CLOSED_11_13_5_SLICE is True
    assert EARLIEST_UNRESOLVED_DEPENDENCY.endswith("TARGET_POSITION_NONZERO_PROVEN")
    assert PREREQUISITE_08_STATUS == "UNRESOLVED_TARGET_NOT_OBSERVED_THIS_WINDOW"
    assert CURRENT_UNCONSUMED_RUNTIME_GO_FOR_RESOLUTION_PATH == "NONE"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert CANDIDATE_TRACK_COUNT == len(CANDIDATE_TRACKS)
    assert CANDIDATE_TRACK_COUNT >= 16
    assert set(ELIGIBLE_NEXT_TRACK_IDS).issubset(set(CANDIDATE_TRACKS))


def test_census_does_not_silently_collapse_eligible_tracks() -> None:
    result = adjudicate_post_z2ct_named_progression_tracks_v1()
    assert result["ADJUDICATION"] == "MULTIPLE_OWNER_SELECTABLE_TRACKS"
    assert result["UNIQUE_CANONICAL_NEXT_TRACK"] == "NONE"
    assert result["eligible_track_count"] == len(ELIGIBLE_NEXT_TRACK_IDS)
    assert result["eligible_track_count"] > 1
    assert "P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF" in result["ELIGIBLE_TRACKS_INDEPENDENT_OF_08"]
    assert (
        "P3_EXECUTION_PREREQUISITE_09_TARGET_POSITION_QTY_NUMERIC"
        in result["TRACKS_REQUIRING_08_NONZERO_FIRST"]
    )
    assert "P3_CLASS_D_PRODUCTIVE_FLATTEN_MUTATION" in result["TRACKS_REQUIRING_08_NONZERO_FIRST"]
    dispositions = {row["TRACK_ID"]: row["DISPOSITION"] for row in result["census"]}
    assert dispositions["P3_Z2AR_REMAINING_UNRANKED_SUI_REPROOF"] == "ELIGIBLE_NEXT"
    assert dispositions["P3_PREREQUISITE_08_UNFILTERED_POSITION_REOBSERVATION"] == "ELIGIBLE_NEXT"
    assert dispositions["P3_CLASS_D_PRODUCTIVE_FLATTEN_MUTATION"] == "BLOCKED"
    assert dispositions["P3_Z2AP_PRODUCTIVE_LIVE_FLATTEN_PROOF"] == "BLOCKED"
    assert dispositions["P3_CLASS_C_AUTHENTICATED_SUI_RUNTIME_GET"] == "SUPERSEDED"
    assert dispositions["P3_CAP21_OPTION_C_DEFER_KEEP_UNPROVEN"] == "DEFERRED"
    assert dispositions["CAP_2_X_MASTER_V2_PARALLEL"] == "DEFERRED"


def test_unique_next_invention_and_automatic_get_fail_closed() -> None:
    assert (
        reject_unique_canonical_next_invention_v1(claimed_unique=None)
        == "UNIQUE_CANONICAL_NEXT_TRACK_NONE_BY_P3_POLICY"
    )
    assert (
        reject_unique_canonical_next_invention_v1(claimed_unique="NONE")
        == "UNIQUE_CANONICAL_NEXT_TRACK_NONE_BY_P3_POLICY"
    )
    with pytest.raises(LiveCanaryPostZ2ctNamedProgressionTrackAdjudicationError):
        reject_unique_canonical_next_invention_v1(
            claimed_unique="P3_PREREQUISITE_08_UNFILTERED_POSITION_REOBSERVATION"
        )
    assert (
        reject_automatic_08_reobservation_v1(claimed_next_is_identical_get=False)
        == "IDENTICAL_UNFILTERED_GET_IS_PERMITTED_OBSERVATION_PATH_ONLY"
    )
    with pytest.raises(LiveCanaryPostZ2ctNamedProgressionTrackAdjudicationError):
        reject_automatic_08_reobservation_v1(claimed_next_is_identical_get=True)
    with pytest.raises(LiveCanaryPostZ2ctNamedProgressionTrackAdjudicationError):
        adjudicate_post_z2ct_named_progression_tracks_v1(claimed_unique_next="P3_FLATTEN_EXECUTE")
    with pytest.raises(LiveCanaryPostZ2ctNamedProgressionTrackAdjudicationError):
        adjudicate_post_z2ct_named_progression_tracks_v1(claimed_next_is_identical_get=True)
