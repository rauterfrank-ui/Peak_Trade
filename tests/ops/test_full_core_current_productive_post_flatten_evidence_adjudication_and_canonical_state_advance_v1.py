"""Post-flatten evidence adjudication tests. Offline. No venue POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1 import (
    CANONICAL_PACK_RELPATH,
    CURRENT_PRODUCTIVE_FIRST_BLOCKER,
    EXPECTED_CL_ORD_ID,
    EXPECTED_ENVELOPE_ID,
    EXPECTED_ORD_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXPECTED_PERMIT_ID,
    OWNER_GO,
    STANDING_SEAM_REMAINDER,
    THIS_SLICE,
    CurrentProductivePostFlattenAdjudicationError,
    adjudicate_post_flatten_evidence_v1,
    execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_"
    "ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DM_HEADING = (
    "### 11.2.1.DM FULL_CORE_CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_"
    "ADJUDICATION_AND_CANONICAL_STATE_ADVANCE"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def _report() -> dict[str, str]:
    return {
        "POST_COUNT": "1",
        "SECOND_SUBMIT_PERFORMED": "false",
        "VENUE_ORDER_ID": EXPECTED_ORD_ID,
        "CLIENT_ORDER_ID": EXPECTED_CL_ORD_ID,
        "PERMIT_ID": EXPECTED_PERMIT_ID,
        "FINAL_ENVELOPE_ID": EXPECTED_ENVELOPE_ID,
        "RAW_VENUE_ACK_STATUS": "http=200;code=0;sCode=0",
    }


def _ack() -> dict[str, object]:
    return {
        "call_count": 1,
        "http_status": 200,
        "payload": {
            "code": "0",
            "data": [
                {
                    "clOrdId": EXPECTED_CL_ORD_ID,
                    "ordId": EXPECTED_ORD_ID,
                    "sCode": "0",
                    "sMsg": "Order placed",
                }
            ],
        },
    }


def _raw(*, fills: list | None = None, bills: list | None = None) -> dict[str, object]:
    default_bills = [
        {
            "clOrdId": EXPECTED_CL_ORD_ID,
            "ordId": EXPECTED_ORD_ID,
            "instId": "SUI-USD_UM_XPERP-310404",
            "fee": "-0.00033895",
            "sz": "1",
            "px": "0.6779",
            "type": "2",
        }
    ]
    return {
        "POSITIONS": {"code": "0", "data": []},
        "PENDING": {"code": "0", "data": []},
        "ORDERS_HISTORY": {"code": "0", "data": []},
        "FILLS": {"code": "0", "data": list(fills or [])},
        "BILLS": {"code": "0", "data": list(bills if bills is not None else default_bills)},
    }


def test_standing_flags_and_adjudication_go_cannot_post() -> None:
    assert (
        CURRENT_PRODUCTIVE_POST_FLATTEN_EVIDENCE_ADJUDICATION_AND_CANONICAL_STATE_ADVANCE_CREATED
        is True
    )
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert POST_ALLOWED is False
    assert OWNER_GO not in ONE_SHOT_REAL_POST_AUTHORITY_REFS
    assert current_productive_first_real_blocker_v1() == STANDING_SEAM_REMAINDER
    assert EXPECTED_ORIGIN_MAIN_SHA == "2105a0fdea633640fc0ffb810f55c4a46e74271e"


def test_bills_are_fee_not_fill() -> None:
    classified = adjudicate_post_flatten_evidence_v1(
        report=_report(),
        ack=_ack(),
        post_submit_raw=_raw(),
    )
    assert classified["SUBMIT_ACK_CLASS"] == "ACCEPTED_SUBMITTED_NOT_FILL"
    assert classified["FILL_OBSERVED"] == "false"
    assert classified["FEE_OBSERVED"] == "true"
    assert classified["ORDER_HISTORY_OBSERVED"] == "false"
    assert classified["POSITION_FLAT_OBSERVED"] == "true"
    assert classified["TARGET_OCCUPANCY_ABSENT"] == "true"
    assert classified["POST_SUBMIT_OPEN_ORDERS"] == "NONE_OBSERVED"
    assert classified["FLATTEN_RECONCILIATION_CLASS"] == (
        "OCCUPANCY_ABSENT_WITHOUT_FILL_ENDPOINT_PROOF"
    )
    assert classified["BILLS_NORMALIZED_TO_FILL"] == "false"
    assert classified["FRESH_FILL_OBSERVED"] == "false"
    assert classified["SECTION_11_14_REWRITTEN"] == "false"
    assert classified["FIRST_REAL_CURRENT_PRODUCTIVE_BLOCKER"] == CURRENT_PRODUCTIVE_FIRST_BLOCKER
    assert classified["STANDING_SEAM_REMAINDER_CLASS"] == (
        "LEGACY_NON_BLOCKING_FOR_POST_FLATTEN_OCCUPANCY_ABSENT"
    )


def test_fresh_fill_does_not_rewrite_sealed_fill_class() -> None:
    classified = adjudicate_post_flatten_evidence_v1(
        report=_report(),
        ack=_ack(),
        post_submit_raw=_raw(),
        fresh_recon={
            "POSITIONS": {"code": "0", "data": []},
            "PENDING": {"code": "0", "data": []},
            "FILLS": {
                "code": "0",
                "data": [
                    {
                        "clOrdId": EXPECTED_CL_ORD_ID,
                        "ordId": EXPECTED_ORD_ID,
                        "instId": "SUI-USD_UM_XPERP-310404",
                        "fillSz": "1",
                    }
                ],
            },
        },
    )
    assert classified["FILL_OBSERVED"] == "false"
    assert classified["FRESH_FILL_OBSERVED"] == "true"
    assert classified["FLATTEN_RECONCILIATION_CLASS"] == (
        "OCCUPANCY_ABSENT_WITHOUT_FILL_ENDPOINT_PROOF"
    )


def test_fill_endpoint_row_would_be_observed_but_execute_refuses_promotion(
    tmp_path: Path,
) -> None:
    fills = [
        {
            "clOrdId": EXPECTED_CL_ORD_ID,
            "ordId": EXPECTED_ORD_ID,
            "instId": "SUI-USD_UM_XPERP-310404",
            "fillSz": "1",
        }
    ]
    classified = adjudicate_post_flatten_evidence_v1(
        report=_report(),
        ack=_ack(),
        post_submit_raw=_raw(fills=fills),
    )
    assert classified["FILL_OBSERVED"] == "true"
    with pytest.raises(
        CurrentProductivePostFlattenAdjudicationError,
        match="FILL_MUST_REMAIN_UNOBSERVED",
    ):
        execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "must-not-write",
            report=_report(),
            ack=_ack(),
            post_submit_raw=_raw(fills=fills),
        )


def test_execute_persists_offline_pack(tmp_path: Path) -> None:
    result = execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        report=_report(),
        ack=_ack(),
        post_submit_raw=_raw(),
    )
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.submit_ack_class == "ACCEPTED_SUBMITTED_NOT_FILL"
    assert result.fill_observed == "false"
    assert result.fee_observed == "true"
    assert result.position_flat_observed == "true"
    assert result.target_occupancy_absent == "true"
    assert result.venue_mutation_performed == "false"
    assert result.post_count == "1"
    assert result.manifest_verify_rc == 0
    assert claims["CANONICAL_PHASE_AFTER"] == THIS_SLICE
    assert claims["SECTION_11_14_REWRITTEN"] == "false"
    assert claims["FLATTEN_POST_AUTHORIZED"] == "false"
    assert claims["POST_COUNT"] == "1"
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


def test_owner_go_and_sha_and_network_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductivePostFlattenAdjudicationError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
            report=_report(),
            ack=_ack(),
            post_submit_raw=_raw(),
        )
    with pytest.raises(
        CurrentProductivePostFlattenAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
            report=_report(),
            ack=_ack(),
            post_submit_raw=_raw(),
        )
    with pytest.raises(
        CurrentProductivePostFlattenAdjudicationError,
        match="NETWORK_FORBIDDEN_OFFLINE_ADJUDICATION",
    ):
        execute_current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "c",
            report=_report(),
            ack=_ack(),
            post_submit_raw=_raw(),
            execute_network=True,
        )


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert DM_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "FILL_OBSERVED=false" in runbook
    assert "FRESH_FILL_OBSERVED=true" in runbook
    assert "FEE_OBSERVED=true" in runbook
    assert "SECTION_11_14_REWRITTEN=false" in runbook
    assert "11.2.1.DM" in mot
    assert OWNER_GO in spec
    assert (
        "current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1.py"
        in atlas
    )
    assert CANONICAL_PACK_RELPATH in runbook or "20260916T001500Z" in runbook
