"""Tests for CAPABILITY_PRESENTATION_PROJECTION_OPERATIONAL_MATERIALIZER_INVOCATION_V1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from src.ops.double_play_archive_sibling_exporter_v1.exporter_v1 import (
    export_double_play_display_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    FAMILY_DOUBLE_PLAY,
    FAMILY_REGIME_BULL_BEAR_SWITCH,
    STATUS_MISSING_SOURCE,
    STATUS_WRITTEN,
)
from src.ops.presentation_projection_operational_materializer_invocation_v1 import (
    CAPABILITY_ID,
    OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES,
    run_operational_presentation_materializer_invocation_v1,
)
from src.ops.presentation_projection_operational_materializer_invocation_v1.constants_v1 import (
    ERROR_GENERATED_AT_REQUIRED,
    ERROR_OWNER_GO_REQUIRED,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.exporter_v1 import (
    export_regime_bull_bear_switch_to_archive_sibling_v1,
)
from src.trading.master_v2.double_play_state import TransitionDecision
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    StateSwitchEvidenceV1,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as REGIME_PROJECTION_PATH,
    try_load_bull_bear_regime_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as DP_PROJECTION_PATH,
    try_load_double_play_presentation_projection_v1,
)
from tests.ops.test_double_play_dashboard_display_archive_sibling_exporter_v1 import (
    _intermediate_with_bundle,
)

REPO = Path(__file__).resolve().parents[2]
CLI_PATH = REPO / "scripts/ops/run_operational_presentation_materializer_invocation_v1.py"
GENERATED_AT = "2026-09-21T12:00:00Z"


def test_capability_id_stable() -> None:
    assert CAPABILITY_ID == (
        "CAPABILITY_PRESENTATION_PROJECTION_OPERATIONAL_MATERIALIZER_INVOCATION_V1"
    )
    assert FAMILY_REGIME_BULL_BEAR_SWITCH in OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES
    assert FAMILY_DOUBLE_PLAY in OPERATIONAL_SIBLING_MATERIALIZER_FAMILIES


def test_owner_go_required() -> None:
    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=REPO / "var",
        generated_at=GENERATED_AT,
        owner_go=False,
    )
    assert result.ok is False
    assert ERROR_OWNER_GO_REQUIRED in result.errors


def test_generated_at_required(tmp_path: Path) -> None:
    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=tmp_path,
        generated_at=None,
        owner_go=True,
    )
    assert result.ok is False
    assert ERROR_GENERATED_AT_REQUIRED in result.errors


def test_regime_sibling_materializes_projection(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    intermediate = type(
        "Inter",
        (),
        {
            "state_switch": StateSwitchEvidenceV1(
                state_switch_id="sw-1",
                instrument_id="BTC-USDT-SWAP",
                trading_epoch=1,
                previous_side_state="long_armed",
                next_side_state="long_active",
                scope_event_type="upscope_confirmed",
                transition_allowed=True,
                transition_reason_code="UPSCOPE_CONFIRMED",
                semantic_digest="a" * 64,
            ),
            "transition_decision": TransitionDecision(True, "UPSCOPE_CONFIRMED", False),
        },
    )()
    export_regime_bull_bear_switch_to_archive_sibling_v1(
        archive_root=archive,
        regime_id="trending",
        regime_status="known",
        replay_intermediate=intermediate,
    )

    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=archive,
        generated_at=GENERATED_AT,
        owner_go=True,
        families=(FAMILY_REGIME_BULL_BEAR_SWITCH,),
        effective_at=GENERATED_AT,
    )
    assert result.ok is True
    assert result.orchestrator is not None
    item = result.orchestrator.family_results[0]
    assert item.status == STATUS_WRITTEN
    loaded = try_load_bull_bear_regime_presentation_projection_v1(archive)
    assert loaded.loaded is True
    assert (archive / REGIME_PROJECTION_PATH).is_file()


def test_double_play_sibling_materializes_projection(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    export_double_play_display_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=_intermediate_with_bundle(),
    )
    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=archive,
        generated_at=GENERATED_AT,
        owner_go=True,
        families=(FAMILY_DOUBLE_PLAY,),
        effective_at=GENERATED_AT,
    )
    assert result.ok is True
    item = result.orchestrator.family_results[0]
    assert item.status == STATUS_WRITTEN
    loaded = try_load_double_play_presentation_projection_v1(archive)
    assert loaded.loaded is True
    assert (archive / DP_PROJECTION_PATH).is_file()


def test_double_play_missing_sibling_fail_closed(tmp_path: Path) -> None:
    result = run_operational_presentation_materializer_invocation_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        owner_go=True,
        families=(FAMILY_DOUBLE_PLAY,),
    )
    assert result.ok is True
    item = result.orchestrator.family_results[0]
    assert item.status == STATUS_MISSING_SOURCE
    assert not (tmp_path / DP_PROJECTION_PATH).exists()


def test_idempotent_second_invocation(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    export_regime_bull_bear_switch_to_archive_sibling_v1(
        archive_root=archive,
        regime_id="trending",
        regime_status="known",
        replay_intermediate=type(
            "Inter",
            (),
            {
                "state_switch": StateSwitchEvidenceV1(
                    state_switch_id="sw-2",
                    instrument_id="BTC-USDT-SWAP",
                    trading_epoch=2,
                    previous_side_state="long_armed",
                    next_side_state="long_active",
                    scope_event_type="upscope_confirmed",
                    transition_allowed=True,
                    transition_reason_code="UPSCOPE_CONFIRMED",
                    semantic_digest="b" * 64,
                ),
                "transition_decision": TransitionDecision(True, "UPSCOPE_CONFIRMED", False),
            },
        )(),
    )
    kwargs = dict(
        archive_root=archive,
        generated_at=GENERATED_AT,
        owner_go=True,
        families=(FAMILY_REGIME_BULL_BEAR_SWITCH,),
        effective_at=GENERATED_AT,
    )
    first = run_operational_presentation_materializer_invocation_v1(**kwargs)
    second = run_operational_presentation_materializer_invocation_v1(**kwargs)
    assert first.ok and second.ok
    d1 = first.orchestrator.family_results[0].payload_digest
    d2 = second.orchestrator.family_results[0].payload_digest
    assert d1 and d1 == d2


def test_module_has_no_trading_execution_imports() -> None:
    forbidden = (
        "integrated_offline_trading_logic_replay",
        "compose_double_play",
        "execution",
        "kill_switch",
        "order_intent",
    )
    module_path = (
        REPO
        / "src/ops/presentation_projection_operational_materializer_invocation_v1/invocation_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_cli_json_contract(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "--archive-root",
            str(tmp_path),
            "--generated-at",
            GENERATED_AT,
            "--owner-go",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO),
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["capability_id"] == CAPABILITY_ID
    assert payload["ok"] is True
