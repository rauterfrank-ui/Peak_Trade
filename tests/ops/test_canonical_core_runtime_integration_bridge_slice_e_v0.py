"""Contract tests for Canonical Core Runtime Integration Bridge Slice E v0.

Offline proofs that ops ``evaluate_double_play`` is ``LEGACY_NON_AUTHORITATIVE`` while
canonical offline Double-Play authority remains on the Master V2 composition matrix and
integrated replay chain. ``live_gates`` eligibility must not couple to ``dp_decision``.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from src.governance.runbook_progress_registry_v1 import (
    RegistryEntryClass,
    SLICE_D_HEADING,
    SLICE_E_HEADING,
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from src.live.live_gates import check_portfolio_live_eligibility, check_strategy_live_eligibility
from src.ops.double_play.specialists import DoublePlayDecision
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER,
    CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER,
    EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER,
    LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING,
    OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
    PACKAGE_MARKER,
    SLICE_E_STATUS,
    build_slice_e_status_fields_v0,
    classify_ops_evaluate_double_play_authority,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import SLICE_D_STATUS
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    load_registry,
    section_field_value,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE = (
    REPO_ROOT / "src" / "trading" / "master_v2" / "evaluate_double_play_authority_boundary_v0.py"
)
LIVE_GATES_MODULE = REPO_ROOT / "src" / "live" / "live_gates.py"
DECISION_AUTHORITY_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
)

TEST_PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_SLICE_E_BOUNDARY_V0=true"

DOUBLE_PLAY_AUTHORITY_KEYS = (
    "CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER",
    "CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER",
    "OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY",
    "EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER",
    "SLICE_E_STATUS",
    "CANONICAL_CORE_SINGLE_SSOT_CONFIRMED",
)


def test_package_marker_and_owner_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in BOUNDARY_MODULE.read_text(encoding="utf-8")
    assert EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER.endswith(
        "evaluate_double_play_authority_boundary_v0"
    )


def test_slice_e_status_fields() -> None:
    fields = build_slice_e_status_fields_v0()
    assert fields["SLICE_E_STATUS"] == SLICE_E_STATUS
    assert fields["OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY"] == OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY
    assert (
        fields["CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER"]
        == CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER
    )
    assert (
        fields["CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER"]
        == CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER
    )
    assert fields["LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING"] == "false"
    assert fields["MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED"] == "false"
    assert fields["EVALUATE_DOUBLE_PLAY_SLICE_E_RESIDUAL"] == "false"
    assert fields["CANONICAL_CORE_SINGLE_SSOT_CONFIRMED"] == "true"
    assert fields["ZERO_ORDER_RUNTIME_READY"] == "false"
    assert fields["RUNTIME_REWIRE_STATUS"] == "PARTIAL"


def test_classify_ops_evaluate_double_play_authority() -> None:
    assert classify_ops_evaluate_double_play_authority() == "LEGACY_NON_AUTHORITATIVE"


def test_registry_slice_e_authoritative_fields() -> None:
    assert authoritative_field_value("SLICE_E_STATUS") == SLICE_E_STATUS
    assert (
        authoritative_field_value("CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER")
        == CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER
    )
    assert authoritative_field_value("OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY") == (
        OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY
    )
    assert authoritative_field_value("EVALUATE_DOUBLE_PLAY_SLICE_E_RESIDUAL") == "false"
    assert authoritative_field_value("CANONICAL_CORE_SINGLE_SSOT_CONFIRMED") == "true"
    assert (
        section_field_value(SLICE_E_HEADING, "REGISTRY_ENTRY_CLASS")
        == RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY.value
    )


def test_slice_d_is_historical_snapshot_not_current_owner() -> None:
    registry = load_registry()
    slice_d = [
        occ
        for occ in registry.all_occurrences("SLICE_D_STATUS")
        if "SLICE_D_V0" in occ.section_heading
    ]
    assert slice_d
    assert all(
        occ.entry_class is RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT for occ in slice_d
    )
    assert authoritative_field_value("SLICE_D_STATUS") == SLICE_D_STATUS
    assert (
        section_field_value(SLICE_D_HEADING, "REGISTRY_ENTRY_CLASS")
        == RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT.value
    )


def test_no_duplicate_conflicting_authoritative_double_play_owners() -> None:
    registry = load_registry()
    ambiguous = duplicate_current_owner_fields(registry, fields=DOUBLE_PLAY_AUTHORITY_KEYS)
    assert ambiguous == {}


def test_live_gates_double_play_details_include_authority_boundary() -> None:
    result = check_strategy_live_eligibility("rsi_reversion", context={})
    dp = result.details["double_play"]
    assert dp["authority_boundary"]["authority_role"] == "LEGACY_NON_AUTHORITATIVE_ANNOTATION_ONLY"
    assert (
        dp["authority_boundary"]["canonical_offline_authority_owner"]
        == CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER
    )
    assert (
        dp["authority_boundary"]["eligibility_coupling"]
        == LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING
    )


@pytest.mark.parametrize(
    ("checker", "entity_id"),
    [
        (check_strategy_live_eligibility, "rsi_reversion"),
        (check_portfolio_live_eligibility, "core_balanced"),
    ],
)
def test_is_eligible_independent_of_evaluate_double_play(
    checker,
    entity_id: str,
) -> None:
    baseline = checker(entity_id, context={})
    flipped = DoublePlayDecision(
        enabled=True,
        active_specialist="bear",
        switch_state={"active": "bear"},
        reasons=("forced",),
        details={"forced": True},
    )
    with patch(
        "src.live.live_gates.evaluate_double_play",
        return_value=flipped,
    ):
        perturbed = checker(entity_id, context={"double_play_enabled": True})
    assert perturbed.is_eligible == baseline.is_eligible


def test_decision_authority_map_crosslink_present() -> None:
    text = DECISION_AUTHORITY_MAP.read_text(encoding="utf-8")
    assert "not a runtime mirror of `evaluate_double_play`" in text
    assert "evaluate_double_play_authority_boundary_v0" in text
    assert "LEGACY_NON_AUTHORITATIVE" in text


def test_boundary_module_has_no_runtime_network_or_credentials_imports() -> None:
    tree = ast.parse(BOUNDARY_MODULE.read_text(encoding="utf-8"))
    forbidden = {"credentials", "adapter", "requests", "httpx", "ccxt", "urllib3", "live_session"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(token in alias.name for token in forbidden)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(token in node.module for token in forbidden)


def test_live_gates_uses_boundary_annotation_helper() -> None:
    text = LIVE_GATES_MODULE.read_text(encoding="utf-8")
    assert "build_legacy_double_play_live_gates_annotation" in text
    assert "finalized above; evaluate_double_play must not affect it" in text
