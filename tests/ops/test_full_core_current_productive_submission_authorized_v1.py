"""CURRENT_PRODUCTIVE SUBMISSION_AUTHORIZED tests. Offline. No wire. No POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.cap72_host_join_to_live_execution_port_v1 import (
    join_cap72_host_to_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED,
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q,
    SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND,
    SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED,
    SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    gap_node_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    evaluate_submission_authorized_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_submission_authorized_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveSubmissionAuthorizedError,
    execute_current_productive_submission_authorized_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED as CANARY_LIVE_ARMED,
    LIVE_ORDER_AUTHORIZED as CANARY_LIVE_ORDER_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED as SECTION_11_14_LIVE_ARMED,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1 import (
    SimulatedExecutionPortV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DG_HEADING = "### 11.2.1.DG FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def test_standing_flags_close_without_wire() -> None:
    assert CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_ADAPTER_CREATED is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is True
    assert SUBMISSION_AUTHORIZED is True
    assert SUBMISSION_AUTHORIZED_STANDING_ADMISSION_SEAM_IMPLEMENTED is True
    assert SUBMISSION_AUTHORIZED_TRUE_IS_NOT_AUTOMATIC_SEND is True
    assert SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_WIRE_SEND is True
    assert SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_LIVE_AUTHORIZED is True
    assert SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_STEP_29Q is True
    assert SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_POST is True
    assert SUBMISSION_AUTHORIZED_DOES_NOT_IMPLY_PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is True
    assert LIVE_AUTHORIZED is True
    assert CANARY_LIVE_ARMED is False
    assert CANARY_LIVE_ORDER_AUTHORIZED is False
    assert SECTION_11_14_LIVE_ARMED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "7fa87e76c7755467528848a3ff52ac4d98f48bb6"
    assert current_productive_first_real_blocker_v1() == ("EXTERNAL_EFFECT_NOT_AUTHORIZED")
    assert gap_node_v1("SUBMISSION_AUTHORIZED").implementation_status == (
        "STANDING_TRUE_NOT_AUTOMATIC_WIRE"
    )
    assert gap_node_v1("LiveExecutionPort").implementation_status == (
        "SEND_CAPABLE_NOT_EXTERNAL_EFFECT"
    )


def test_default_and_missing_predicates_deny() -> None:
    denied = evaluate_submission_authorized_v1()
    assert denied.submission_authorized is False
    assert denied.fail_closed is True
    assert "HOST_NOT_JOINED" in denied.reason_codes
    assert "LIVE_PORT_MISSING" in denied.reason_codes
    assert "EXECUTION_ADMISSION_NOT_ADMITTED" in denied.reason_codes
    standing = evaluate_submission_authorized_v1(
        host_joined=True,
        admitted=True,
        standing_submission_authorized=False,
    )
    assert standing.submission_authorized is False
    assert "SUBMISSION_AUTHORIZED_STANDING_FALSE" in standing.reason_codes


def test_malformed_and_unknown_deny() -> None:
    malformed = evaluate_submission_authorized_v1(
        host_joined=True,
        admitted=True,
        standing_submission_authorized="UNKNOWN",  # type: ignore[arg-type]
        durable_kill_switch_evidence_status="UNKNOWN",
        durable_kill_switch_blocked=None,
    )
    assert malformed.submission_authorized is False
    assert "SUBMISSION_AUTHORIZED_STANDING_MALFORMED" in malformed.reason_codes
    assert "KILL_SWITCH_EVIDENCE_NOT_TRUSTED" in malformed.reason_codes
    assert "KILL_SWITCH_UNKNOWN" in malformed.reason_codes


def test_host_join_port_handle_and_wire_permit_alone_do_not_submit() -> None:
    host = HostActivationBindingV1()
    missing = join_cap72_host_to_live_execution_port_v1(host=host)
    assert missing.host_joined is False
    assert missing.submission_authorized is False
    assert isinstance(host.execution_port, SimulatedExecutionPortV1)
    construction = evaluate_live_execution_port_construction_admission_v1()
    assert construction.constructible is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    wire_only = evaluate_submission_authorized_v1(wire_send_permitted=True)
    assert wire_only.submission_authorized is False
    assert LIVE_AUTHORIZED is True


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveSubmissionAuthorizedError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_submission_authorized_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
        )
    with pytest.raises(
        CurrentProductiveSubmissionAuthorizedError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_submission_authorized_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
        )


def test_evaluate_closes_submission_without_wire(tmp_path: Path) -> None:
    result = execute_current_productive_submission_authorized_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
    )
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.live_enabled == "true"
    assert result.live_armed == "true"
    assert result.wire_send_permitted == "true"
    assert result.live_authorized == "true"
    assert result.admitted == "true"
    assert result.host_joined == "true"
    assert result.port_constructed == "true"
    assert result.submission_authorized == "true"
    assert result.submission_deny_absent == "true"
    assert result.step_29p_risk_admissible == "true"
    assert result.cap24_bound_instrument_id
    assert result.first_real_blocker == "EXTERNAL_EFFECT_NOT_AUTHORIZED"
    assert result.blocker_class == "E"
    assert result.post_count == "0"
    assert result.manifest_verify_rc == 0
    assert claims["SUBMISSION_AUTHORIZED"] == "true"
    assert claims["LIVE_AUTHORIZED"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["PRODUCTIVE_WIRE_SEND_REACHABLE"] == "true"
    assert claims["POST_COUNT"] == "0"
    assert claims["HOST_JOINED"] == "true"
    assert claims["CAP_7_2_HOST_JOINED_IS_NOT_SUBMISSION_AUTHORIZED"] == "true"
    assert claims["LIVE_EXECUTION_PORT_HANDLE_IS_NOT_SUBMISSION_AUTHORIZED"] == "true"
    assert claims["WIRE_SEND_PERMITTED_ALONE_IS_NOT_SUBMISSION_AUTHORIZED"] == "true"
    assert claims["PROTECTED_SURFACES_CHANGED"] == "false"
    assert claims["SAFETY_AUTHORITY_WEAKENED"] == "false"
    assert claims["CANARY_FULL_CORE_BOUNDARY_CHANGED"] == "false"
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    assert verify_manifest_sha256_v1(store_root=Path(result.store_root)) == 0


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
    assert DG_HEADING in runbook
    assert THIS_SLICE in runbook
    dg_section = runbook[
        runbook.index(
            "11.2.1.DG FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED"
        ) : runbook.index("## 11.3 Autonomy state model")
    ]
    assert "SUBMISSION_AUTHORIZED=true" in dg_section
    assert "WIRE_SEND_PERMITTED=true" in dg_section
    assert "LIVE_ENABLED=true" in dg_section
    assert "LIVE_ARMED=true" in dg_section
    assert "LIVE_AUTHORIZED=false" in dg_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in dg_section
    assert "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in dg_section
    assert "HOST_JOINED=true" in dg_section
    assert "FIRST_DEFINITIVE_BLOCK=PRODUCTIVE_WIRE_SEND_REACHABLE_REMAINS_FALSE" in dg_section
    df_section = runbook[
        runbook.index(
            "11.2.1.DF FULL_CORE_CURRENT_PRODUCTIVE_CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT"
        ) : runbook.index("11.2.1.DG FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED")
    ]
    assert "SUBMISSION_AUTHORIZED=false" in df_section
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1" in spec
    assert "11.2.1.DG" in atlas
    assert "current_productive_submission_authorized_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "true"
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["ADMITTED"] == "true"
    assert claims["HOST_JOINED"] == "true"
    assert claims["SUBMISSION_AUTHORIZED"] == "true"
    assert claims["FIRST_REAL_BLOCKER"] == "PRODUCTIVE_WIRE_SEND_REACHABLE_REMAINS_FALSE"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["PRODUCTIVE_WIRE_SEND_REACHABLE"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
