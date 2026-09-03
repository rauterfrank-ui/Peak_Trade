"""Route-C create-path blocker census and adjudication tests."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_adjudicate_v1 import (
    adjudicate_route_c_create_path_blocker_census_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_census_v1 import (
    CREATE_PATH_BLOCKER_RECORDS_V1,
    census_summary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    G_POSMODE_STATUS,
    G_POSMODE_STATUS_CLOSED_AS,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)


def test_blocker_census_has_nine_frozen_records() -> None:
    assert len(CREATE_PATH_BLOCKER_RECORDS_V1) == 9
    summary = census_summary_v1()
    assert summary["BLOCKER_RECORD_COUNT"] == 9
    assert summary["OPEN_GAP_COUNT"] == 8
    assert summary["CLOSED_GAP_COUNT"] == 1
    assert summary["OFFLINE_CLOSABLE_GAP_COUNT"] == 0
    assert summary["UNADJUDICATED_BLOCKER_COUNT"] == 0


def test_g_posmode_is_closed_fail_closed() -> None:
    record = next(r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.gap_id == "G-POSMODE")
    assert record.status == "CLOSED_FAIL_CLOSED"
    assert record.can_be_closed_offline is False
    assert record.offline_only is True


def test_runtime_required_gaps_require_higher_authority() -> None:
    runtime = [r for r in CREATE_PATH_BLOCKER_RECORDS_V1 if r.runtime_fact_required]
    assert {r.gap_id for r in runtime} == {
        "G-PRETRADE-AVAILEQ",
        "G-CAPACITY",
        "G-P08",
        "G-FUNDING-EXPOSURE",
    }
    for record in runtime:
        assert record.higher_authority_required is True


def test_adjudication_proves_no_offline_bundle_remains() -> None:
    result = adjudicate_route_c_create_path_blocker_census_v1()
    assert result["OWNER_GO"] == OWNER_GO
    assert result["WORKPACKAGE_ID"] == WORKPACKAGE_ID
    assert result["THIS_SLICE"] == THIS_SLICE
    assert result["RESULT_CLASS"] == "CREATE_PATH_BLOCKER_CENSUS_EXHAUSTIVE_COMPLETE"
    assert result["CENSUS_EXHAUSTION_PROVEN"] is True
    assert result["G_POSMODE_STATUS"] == G_POSMODE_STATUS
    assert result["G_POSMODE_STATUS_CLOSED_AS"] == G_POSMODE_STATUS_CLOSED_AS
    assert result["OFFLINE_CLOSABLE_GAP_COUNT"] == 0
    assert result["MAX_SAFE_OFFLINE_BUNDLE_REMAINING"] == 0
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert result["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert result["PREREQUISITE_08_CLOSED"] is False
    assert "G-P08" in result["OPEN_GAP_IDS"]
