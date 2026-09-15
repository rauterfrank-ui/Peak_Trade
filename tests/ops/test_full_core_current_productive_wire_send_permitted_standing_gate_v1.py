"""CURRENT_PRODUCTIVE WIRE_SEND_PERMITTED standing-gate tests. Offline. No wire. No POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    WIRE_SEND_PERMITTED,
    WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_ADMISSION,
    WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_POST,
    WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_STEP_29Q,
    WIRE_SEND_PERMITTED_STANDING_GATE_CLOSED,
    WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_ADMISSION,
    WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_SEND,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_wire_send_permitted_standing_gate_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveWireSendPermittedStandingGateError,
    execute_current_productive_wire_send_permitted_standing_gate_v1,
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
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DC_HEADING = "### 11.2.1.DC FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def test_standing_flags_close_wire_send_without_activation() -> None:
    assert CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_ADAPTER_CREATED is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert WIRE_SEND_PERMITTED_STANDING_GATE_CLOSED is True
    assert WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_SEND is True
    assert WIRE_SEND_PERMITTED_TRUE_IS_NOT_AUTOMATIC_ADMISSION is True
    assert WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_ADMISSION is True
    assert WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    assert WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_LIVE_AUTHORIZED is True
    assert WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_STEP_29Q is True
    assert WIRE_SEND_PERMITTED_DOES_NOT_IMPLY_POST is True
    assert PRODUCTIVE_WIRE_SEND_REACHABLE is False
    assert LIVE_AUTHORIZED is False
    assert CANARY_LIVE_ARMED is False
    assert CANARY_LIVE_ORDER_AUTHORIZED is False
    assert SECTION_11_14_LIVE_ARMED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "12653267f48ad91bfd2a167303bf0c43870822a1"


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveWireSendPermittedStandingGateError, match="OWNER_GO_MISMATCH"
    ):
        execute_current_productive_wire_send_permitted_standing_gate_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
        )
    with pytest.raises(
        CurrentProductiveWireSendPermittedStandingGateError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_current_productive_wire_send_permitted_standing_gate_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
        )


def test_evaluate_closes_wire_send_and_halts_on_admission(tmp_path: Path) -> None:
    result = execute_current_productive_wire_send_permitted_standing_gate_v1(
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
    assert result.wire_send_deny_absent == "true"
    assert result.step_29p_risk_admissible == "true"
    assert result.cap24_bound_instrument_id
    assert result.first_real_blocker == "PRODUCTIVE_WIRE_SEND_REACHABLE_REMAINS_FALSE"
    assert result.blocker_class == "E"
    assert result.post_count == "0"
    assert result.manifest_verify_rc == 0
    assert "LIVE_ENABLED_FALSE" not in claims["ADMISSION_REASON_CODES"]
    assert "LIVE_ARMED_FALSE" not in claims["ADMISSION_REASON_CODES"]
    assert "WIRE_SEND_NOT_PERMITTED" not in claims["ADMISSION_REASON_CODES"]
    assert "EXECUTION_ADMISSION_FAIL_CLOSED" not in claims["ADMISSION_REASON_CODES"]
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "true"
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["ADMITTED"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["POST_COUNT"] == "0"
    assert claims["PRODUCTIVE_WIRE_SEND_REACHABLE"] == "false"
    assert claims["PROTECTED_SURFACES_CHANGED"] == "false"
    assert claims["SAFETY_AUTHORITY_WEAKENED"] == "false"
    assert claims["CANARY_FULL_CORE_BOUNDARY_CHANGED"] == "false"
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
    assert DC_HEADING in runbook
    assert THIS_SLICE in runbook
    dc_section = runbook[
        runbook.index(
            "11.2.1.DC FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE"
        ) : runbook.index("11.2.1.DD FULL_CORE_CURRENT_PRODUCTIVE_EXECUTION_ADMISSION_REMAINDER")
    ]
    assert "WIRE_SEND_PERMITTED=true" in dc_section
    assert "LIVE_ENABLED=true" in dc_section
    assert "LIVE_ARMED=true" in dc_section
    assert "LIVE_AUTHORIZED=false" in dc_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in dc_section
    assert "PRODUCTIVE_WIRE_SEND_REACHABLE=false" in dc_section
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_V1" in spec
    assert "11.2.1.DC" in atlas
    assert "current_productive_wire_send_permitted_standing_gate_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "true"
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["FIRST_REAL_BLOCKER"] == "EXECUTION_ADMISSION_REMAINS_FAIL_CLOSED"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["ADMITTED"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
