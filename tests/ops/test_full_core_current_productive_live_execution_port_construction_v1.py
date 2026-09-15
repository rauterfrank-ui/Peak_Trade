"""CURRENT_PRODUCTIVE LiveExecutionPort construction tests. Offline. No wire. No POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_LIVE_AUTHORIZED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_POST,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_STEP_29Q,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_SUBMISSION_AUTHORIZED,
    LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_WIRE_SEND,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN,
    gap_node_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_ADAPTER_CREATED,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_execution_port_construction_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveLiveExecutionPortConstructionError,
    execute_current_productive_live_execution_port_construction_v1,
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

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DE_HEADING = "### 11.2.1.DE FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def test_standing_flags_construct_without_activation() -> None:
    assert CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_ADAPTER_CREATED is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTIBLE is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN is False
    assert LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_SUBMISSION_AUTHORIZED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_WIRE_SEND is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_LIVE_AUTHORIZED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_STEP_29Q is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTED_IS_NOT_POST is True
    assert CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT is False
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is False
    assert LIVE_AUTHORIZED is False
    assert CANARY_LIVE_ARMED is False
    assert CANARY_LIVE_ORDER_AUTHORIZED is False
    assert SECTION_11_14_LIVE_ARMED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "fec53461fe1a6c8b3000b57d8f0ce842a5bdc7ea"
    assert gap_node_v1("LiveExecutionPort").implementation_status == (
        "CONSTRUCTIBLE_NOT_HOST_JOINED_NOT_WIRE"
    )


def test_construction_fail_closed_without_prerequisites() -> None:
    denied = evaluate_live_execution_port_construction_admission_v1()
    assert denied.constructible is False
    assert denied.constructed is False
    assert "EXECUTION_ADMISSION_NOT_ADMITTED" in denied.reason_codes
    with pytest.raises(
        ExecutionPortConstructionForbiddenError,
        match="LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN_IN_CAPABILITY_11_1",
    ):
        construct_live_execution_port_v1(construction_admission=denied)
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveLiveExecutionPortConstructionError, match="OWNER_GO_MISMATCH"
    ):
        execute_current_productive_live_execution_port_construction_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
        )
    with pytest.raises(
        CurrentProductiveLiveExecutionPortConstructionError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_current_productive_live_execution_port_construction_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
        )


def test_evaluate_constructs_fail_closed_port_without_wire(tmp_path: Path) -> None:
    result = execute_current_productive_live_execution_port_construction_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
    )
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert result.live_enabled == "true"
    assert result.live_armed == "true"
    assert result.wire_send_permitted == "true"
    assert result.live_authorized == "false"
    assert result.admitted == "true"
    assert result.admission_deny_absent == "true"
    assert result.port_constructible == "true"
    assert result.port_constructed == "true"
    assert result.port_construction_side_effect_free == "true"
    assert result.step_29p_risk_admissible == "true"
    assert result.cap24_bound_instrument_id
    assert result.first_real_blocker == "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_REMAINS_FALSE"
    assert result.blocker_class == "E"
    assert result.post_count == "0"
    assert result.manifest_verify_rc == 0
    assert claims["ADMISSION_REASON_CODES"] == []
    assert claims["CONSTRUCTION_REASON_CODES"] == []
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["ADMITTED"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["SUBMISSION_AUTHORIZED"] == "false"
    assert claims["POST_COUNT"] == "0"
    assert claims["PRODUCTIVE_WIRE_SEND_REACHABLE"] == "false"
    assert claims["LIVE_EXECUTION_PORT_CONSTRUCTIBLE"] == "true"
    assert claims["LIVE_EXECUTION_PORT_CONSTRUCTED"] == "true"
    assert claims["PORT_CONSTRUCTION_SIDE_EFFECT_FREE"] == "true"
    assert claims["CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT"] == "false"
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
    assert DE_HEADING in runbook
    assert THIS_SLICE in runbook
    de_section = runbook[
        runbook.index(
            "11.2.1.DE FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION"
        ) : runbook.index("## 11.3 Autonomy state model")
    ]
    assert "WIRE_SEND_PERMITTED=true" in de_section
    assert "LIVE_ENABLED=true" in de_section
    assert "LIVE_ARMED=true" in de_section
    assert "LIVE_AUTHORIZED=false" in de_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in de_section
    assert "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in de_section
    assert "ADMITTED=true" in de_section
    assert "LIVE_EXECUTION_PORT_CONSTRUCTIBLE=true" in de_section
    assert "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT=false" in de_section
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_V1" in spec
    assert "11.2.1.DE" in atlas
    assert "current_productive_live_execution_port_construction_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "true"
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["ADMITTED"] == "true"
    assert claims["LIVE_EXECUTION_PORT_CONSTRUCTED"] == "true"
    assert claims["FIRST_REAL_BLOCKER"] == (
        "CAP_7_2_HOST_JOIN_TO_LIVE_EXECUTION_PORT_REMAINS_FALSE"
    )
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
