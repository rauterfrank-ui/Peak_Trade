"""PR #6252 merge-closeout offline contract tests. No GET. No POST."""

from __future__ import annotations

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.adjudicate_v1 import (
    Pr6252MergeCloseoutAdjudicationError,
    adjudicate_pr_6252_merge_closeout_v1,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    G12_STATUS_VALUE,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    SECTION_11_14_AUTHORIZED_VALUE,
    TARGET_POSITION_ZERO_PROVEN_VALUE,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.contract_v1 import (
    Pr6252MergeCloseoutContractError,
    assert_preserved_flatten_residuals_v1,
)


def test_standing_flags_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert GET_ALLOWED is False
    assert POST_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert THIS_GO_GET_COUNT == 0
    assert SECTION_11_14_AUTHORIZED_VALUE is False
    assert TARGET_POSITION_ZERO_PROVEN_VALUE is False
    assert G12_STATUS_VALUE == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_adjudication_binds_merged_sha_and_preserves_g12() -> None:
    verdict = adjudicate_pr_6252_merge_closeout_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert verdict["THIS_SLICE"] == THIS_SLICE
    assert verdict["LAST_CANONICALLY_CLOSED_STEP"] == LAST_CANONICALLY_CLOSED_STEP
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert verdict["PR_6252_STATUS"] == "SQUASH_MERGED"
    assert verdict["G12_STATUS"] == G12_STATUS_VALUE
    assert verdict["TARGET_POSITION_ZERO_PROVEN"] is False
    assert verdict["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert verdict["RECOVERY_POSITION_SEMANTICS"] == "CASE_C_EMPTY_DATA_NOT_ZERO"
    assert verdict["SECTION_11_14_AUTHORIZED"] is False
    assert verdict["GET_PERFORMED_THIS_PERSIST"] is False
    assert verdict["POST_PERFORMED"] is False
    assert verdict["MERGE_AUTHORIZED_BY_THIS_PERSIST"] is False


def test_wrong_sha_fail_closed() -> None:
    with pytest.raises(Pr6252MergeCloseoutAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_pr_6252_merge_closeout_v1(origin_main_sha="deadbeef")


def test_residual_promotion_fail_closed() -> None:
    with pytest.raises(Pr6252MergeCloseoutContractError, match="G12_MUST_REMAIN_OPEN"):
        assert_preserved_flatten_residuals_v1(
            {
                "G12_STATUS": "CLOSED",
                "TARGET_POSITION_ZERO_PROVEN": False,
                "LIVE_FLATTEN_PROVABILITY_PROVEN": False,
                "RECOVERY_POSITION_SEMANTICS": "CASE_C_EMPTY_DATA_NOT_ZERO",
                "EMPTY_DATA_IS_ZERO": False,
                "SECTION_11_14_AUTHORIZED": False,
                "RETRY_ALLOWED": False,
            }
        )
