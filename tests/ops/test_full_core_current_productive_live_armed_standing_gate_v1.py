"""CURRENT_PRODUCTIVE LIVE_ARMED standing-gate tests. Offline. No wire. No POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ARMED_DOES_NOT_IMPLY_LIVE_AUTHORIZED,
    LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION,
    LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE,
    LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND,
    LIVE_ARMED_STANDING_GATE_CLOSED,
    LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_ADAPTER_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_live_armed_standing_gate_v1 import (
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    CurrentProductiveLiveArmedStandingGateError,
    execute_current_productive_live_armed_standing_gate_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED as CANARY_LIVE_ARMED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED as SECTION_11_14_LIVE_ARMED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_V1.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DB_HEADING = "### 11.2.1.DB FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
)


def test_standing_flags_close_live_armed_without_activation() -> None:
    assert CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_ADAPTER_CREATED is True
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert LIVE_ARMED_STANDING_GATE_CLOSED is True
    assert LIVE_ARMED_TRUE_IS_NOT_AUTOMATIC_ADMISSION is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_WIRE_SEND is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_PORT_CONSTRUCTION is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_LIVE_AUTHORIZED is True
    assert LIVE_ARMED_DOES_NOT_IMPLY_RISK_ADMISSIBLE is True
    assert WIRE_SEND_PERMITTED is True
    assert LIVE_AUTHORIZED is True
    assert CANARY_LIVE_ARMED is False
    assert SECTION_11_14_LIVE_ARMED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "5895fcb495a00f71ffa1fff643da8e4a701b95bf"


def test_owner_go_and_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(CurrentProductiveLiveArmedStandingGateError, match="OWNER_GO_MISMATCH"):
        execute_current_productive_live_armed_standing_gate_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "a",
        )
    with pytest.raises(
        CurrentProductiveLiveArmedStandingGateError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_current_productive_live_armed_standing_gate_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "b",
        )


def test_evaluate_closes_live_armed_and_halts_on_wire_send(tmp_path: Path) -> None:
    result = execute_current_productive_live_armed_standing_gate_v1(
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
    assert result.live_armed_deny_absent == "true"
    assert result.step_29p_risk_admissible == "true"
    assert result.cap24_bound_instrument_id
    assert result.first_real_blocker == "EXTERNAL_EFFECT_NOT_AUTHORIZED"
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
    assert claims["LIVE_AUTHORIZED"] == "true"
    assert claims["ADMITTED"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert claims["POST_COUNT"] == "0"
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
    assert DB_HEADING in runbook
    assert THIS_SLICE in runbook
    db_section = runbook[
        runbook.index(
            "11.2.1.DB FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE"
        ) : runbook.index(
            "11.2.1.DC FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE"
        )
    ]
    assert "LIVE_ARMED=true" in db_section
    assert "WIRE_SEND_PERMITTED=false" in db_section
    assert "LIVE_AUTHORIZED=false" in db_section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in db_section
    assert SPEC_PATH.name in mot
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_V1" in spec
    assert "11.2.1.DB" in atlas
    assert "current_productive_live_armed_standing_gate_v1.py" in atlas
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_ENABLED"] == "true"
    assert claims["LIVE_ARMED"] == "true"
    assert claims["WIRE_SEND_PERMITTED"] == "false"
    assert claims["LIVE_AUTHORIZED"] == "false"
    assert claims["FIRST_REAL_BLOCKER"] == "WIRE_SEND_PERMITTED_STANDING_GATE_REMAINS_FALSE"
    assert claims["POST_COUNT"] == "0"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "true"
    assert claims["STEP_29Q_STATUS"] == "PLAN_ONLY"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
