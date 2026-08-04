"""Focused tests: CAPABILITY_PRESENTATION_PROJECTION_OCTET_ORCHESTRATOR_V1."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.ops.presentation_projection_octet_orchestrator_v1.constants_v1 import (
    ALLOWED_PROJECTION_RELATIVE_PATHS,
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ERROR_GENERATED_AT_REQUIRED,
    ERROR_SAFETY_CALLER_OBJECT_REQUIRED,
    ERROR_UNKNOWN_FAMILY,
    FAMILY_ORDER,
    ORCHESTRATOR_AUTHORITY_EFFECT,
    PROJECTION_PATH_BY_FAMILY,
    SIBLING_PATH_BY_FAMILY,
    STATUS_BLOCKED,
    STATUS_FAIL_CLOSED,
    STATUS_MISSING_SOURCE,
    STATUS_SKIPPED,
    STATUS_WRITTEN,
)
from src.ops.presentation_projection_octet_orchestrator_v1.orchestrator_v1 import (
    run_presentation_projection_octet_orchestrator_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1 import (
    SOURCE_STATE_RELATIVE_PATH,
)

REPO = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO / "src/ops/presentation_projection_octet_orchestrator_v1"
CLI_PATH = REPO / "scripts/ops/run_presentation_projection_octet_orchestrator_v1.py"
GENERATED_AT = "2026-07-24T17:30:00Z"


def _scope(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "scope_state": "scope_valid",
        "current_scope_ref": "scope-eth-1",
        "next_scope_ref": None,
        "reason_codes": ("SCOPE_INITIALIZED",),
        "semantic_digest": "c" * 64,
    }
    base.update(overrides)
    return base


def _regime(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "regime_id": "trending",
        "regime_status": "known",
        "side_state": "long_active",
        "previous_side_state": "long_armed",
        "next_side_state": "long_active",
        "scope_event_type": "upscope_confirmed",
        "transition_allowed": True,
        "transition_reason_code": "UPSCOPE_CONFIRMED",
        "reason_codes": ("STATE_SWITCH_OK",),
        "evidence_digest": "b" * 64,
    }
    base.update(overrides)
    return base


def _evidence(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "instrument_id": "ETH-USDT-SWAP",
        "decision_outcome": "observe",
        "next_direction_state": "neutral_observe",
        "decision_id": "decision-orchestrator-1",
        "evidence_schema_version": "canonical_trading_decision_evidence_v1",
        "reason_codes": ("WARMUP_ACTIVE", "NO_ENTRY"),
        "semantic_digest": "b" * 64,
    }
    base.update(overrides)
    return base


def _display(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "overall_status": "display_ready",
        "panel_summaries": (
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition: ELIGIBLE_MODEL_ONLY",
                "blockers": (),
            },
        ),
        "blockers": (),
        "display_only": True,
        "live_authorization": False,
        "evidence_digest": "d" * 64,
    }
    base.update(overrides)
    return base


def _safety(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "kill_switch_state": "KILLED",
        "veto_active": True,
        "reason_codes": ("killswitch_block_new",),
        "evidence_digest": "e" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _risk(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "risk_status": "PASS",
        "sizing_status": "PASS",
        "capital_status": "PASS",
        "quantity": 0.25,
        "reason_codes": ("PASS",),
        "evidence_digest": "r" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _execution(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "execution_status": "BOUND_OFFLINE",
        "reconciliation_status": "RECONCILED",
        "order_intent_ref": "intent://" + ("a" * 16),
        "reason_codes": ("PASS",),
        "evidence_digest": "e" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _metric(*, value: float | None = None, semantic: str = "COMPUTED") -> dict[str, object]:
    payload: dict[str, object] = {"semantic": semantic}
    if value is not None:
        payload["value"] = value
    return payload


def _economic(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "status": "ECONOMICALLY_VIABLE_OFFLINE",
        "economic_validity_proven": True,
        "profitability_claim_allowed": False,
        "policy_threshold_status": "PASS",
        "policy_version": "economic_validity_policy_v1",
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
        "reason_codes": ("SENTINEL_REASON_A",),
        "profit_factor": _metric(value=1.77),
        "net_return": _metric(value=0.123),
        "max_drawdown": _metric(value=-0.045),
        "sharpe": _metric(value=0.88),
        "trade_count": _metric(value=42.0),
        "funding_drag": _metric(value=-0.003),
        "contract_version": "v1",
        "owner": "backtest.economic_viability_evidence_v1",
        "strategy_id": "sentinel_strategy",
        "strategy_version": "sentinel_v9",
        "config_digest": "c" * 64,
        "implementation_digest": "i" * 64,
        "data_digest": "d" * 64,
        "manifest_digest": "m" * 64,
        "wiring_chain_digest": "w" * 64,
        "policy_digest": "p" * 64,
        "evidence_digest": "m" * 64,
        "schema_version": "v1",
    }
    base.update(overrides)
    return base


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_package_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8") for path in sorted(PACKAGE_DIR.glob("*.py"))
    }


def test_capability_and_authority_constants_are_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_PRESENTATION_PROJECTION_OCTET_ORCHESTRATOR_V1"
    assert AUTHORITY_EFFECT == "NONE"
    assert ORCHESTRATOR_AUTHORITY_EFFECT == "NONE"
    assert FAMILY_ORDER == (
        "dynamic_scope",
        "regime_bull_bear_switch",
        "canonical_decision",
        "double_play",
        "safety_authority",
        "risk_sizing_capital",
        "execution_reconciliation",
        "economic_summary",
    )
    assert SIBLING_PATH_BY_FAMILY["safety_authority"] is None
    assert PROJECTION_PATH_BY_FAMILY["safety_authority"] == "readmodels/safety_authority.v1.json"


def test_missing_inputs_write_no_files(tmp_path: Path) -> None:
    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
    )
    assert result.written_count == 0
    assert (tmp_path / "readmodels").exists() is False or not any(
        (tmp_path / "readmodels").rglob("*")
    )
    statuses = {item.family_id: item.status for item in result.family_results}
    assert statuses["safety_authority"] == STATUS_SKIPPED
    assert ERROR_SAFETY_CALLER_OBJECT_REQUIRED in next(
        item.errors for item in result.family_results if item.family_id == "safety_authority"
    )
    for family_id in FAMILY_ORDER:
        if family_id == "safety_authority":
            continue
        assert statuses[family_id] == STATUS_MISSING_SOURCE
    assert result.contract_ok is True


def test_missing_generated_at_fail_closed_writes_nothing(tmp_path: Path) -> None:
    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=None,
        dynamic_scope=_scope(),
        safety_authority=_safety(),
    )
    assert result.written_count == 0
    assert result.contract_ok is False
    assert all(item.status == STATUS_FAIL_CLOSED for item in result.family_results)
    assert all(ERROR_GENERATED_AT_REQUIRED in item.errors for item in result.family_results)
    assert not (tmp_path / "readmodels").exists()


def test_partial_success_and_allowed_projection_paths_only(tmp_path: Path) -> None:
    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        dynamic_scope=_scope(),
        safety_authority=_safety(),
        effective_at=GENERATED_AT,
        source_reference="presentation://unit-test",
    )
    by_id = {item.family_id: item for item in result.family_results}
    assert by_id["dynamic_scope"].status == STATUS_WRITTEN
    assert by_id["safety_authority"].status == STATUS_WRITTEN
    assert by_id["canonical_decision"].status == STATUS_MISSING_SOURCE
    assert result.written_count == 2
    assert result.contract_ok is True

    written_files = sorted(
        path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()
    )
    assert set(written_files) <= ALLOWED_PROJECTION_RELATIVE_PATHS
    assert "readmodels/dynamic_scope_presentation_projection.v1.json" in written_files
    assert "readmodels/safety_authority.v1.json" in written_files
    assert "readmodels/MANIFEST.sha256" not in written_files


def test_sibling_loading_uses_fixed_relative_path_only(tmp_path: Path) -> None:
    sibling = tmp_path / SOURCE_STATE_RELATIVE_PATH
    _write_json(sibling, _scope())
    # Decoy file that must never be selected via discovery.
    _write_json(tmp_path / "readmodels" / "latest_dynamic_scope.json", {"scope_state": "bogus"})

    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        families=("dynamic_scope",),
        source_reference="presentation://sibling-test",
    )
    assert len(result.family_results) == 1
    item = result.family_results[0]
    assert item.family_id == "dynamic_scope"
    assert item.sibling_relative_path == "readmodels/dynamic_scope_state_v1.json"
    assert item.caller_object_provided is False
    assert item.status == STATUS_WRITTEN
    assert (tmp_path / PROJECTION_PATH_BY_FAMILY["dynamic_scope"]).is_file()
    # Decoy path must not become a projection owner.
    assert item.source_path is not None
    assert item.source_path.endswith("dynamic_scope_state_v1.json")


def test_caller_objects_pass_through_and_idempotent_digests(tmp_path: Path) -> None:
    scope = _scope()
    safety = _safety()
    first = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        families=("dynamic_scope", "safety_authority"),
        dynamic_scope=scope,
        safety_authority=safety,
        effective_at=GENERATED_AT,
        source_reference="presentation://unit-test",
    )
    second = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        families=("dynamic_scope", "safety_authority"),
        dynamic_scope=scope,
        safety_authority=safety,
        effective_at=GENERATED_AT,
        source_reference="presentation://unit-test",
    )
    assert first.written_count == 2
    assert second.written_count == 2
    digests_first = {
        item.family_id: item.payload_digest for item in first.family_results if item.written
    }
    digests_second = {
        item.family_id: item.payload_digest for item in second.family_results if item.written
    }
    assert digests_first == digests_second
    assert digests_first["dynamic_scope"]
    assert digests_first["safety_authority"]
    # Caller-owned mappings remain untouched.
    assert scope["current_scope_ref"] == "scope-eth-1"
    assert safety["kill_switch_state"] == "KILLED"


def test_all_eight_families_with_explicit_caller_objects(tmp_path: Path) -> None:
    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        dynamic_scope=_scope(),
        regime_bull_bear_switch=_regime(),
        evidence=_evidence(),
        display=_display(),
        safety_authority=_safety(),
        risk_sizing_capital=_risk(),
        execution_reconciliation=_execution(),
        economic_summary=_economic(),
        effective_at=GENERATED_AT,
        source_reference="presentation://unit-test",
    )
    assert result.written_count == 8
    assert result.missing_source_count == 0
    assert result.skipped_count == 0
    assert result.blocked_count == 0
    assert result.contract_ok is True
    written = {
        path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*.json") if path.is_file()
    }
    assert written == set(ALLOWED_PROJECTION_RELATIVE_PATHS)


def test_unknown_family_is_blocked_fail_closed(tmp_path: Path) -> None:
    result = run_presentation_projection_octet_orchestrator_v1(
        archive_root=tmp_path,
        generated_at=GENERATED_AT,
        families=("dynamic_scope", "not_a_real_family"),
        dynamic_scope=_scope(),
    )
    assert result.contract_ok is False
    assert result.blocked_count == 1
    blocked = next(item for item in result.family_results if item.family_id == "not_a_real_family")
    assert blocked.status == STATUS_BLOCKED
    assert ERROR_UNKNOWN_FAMILY in blocked.errors
    written = next(item for item in result.family_results if item.family_id == "dynamic_scope")
    assert written.status == STATUS_WRITTEN


def test_source_has_no_implicit_time_latest_discovery_or_kill_switch_autoload() -> None:
    sources = _read_package_sources()
    joined = "\n".join(sources.values())
    cli_src = CLI_PATH.read_text(encoding="utf-8")
    combined = joined + "\n" + cli_src

    assert "datetime.now" not in combined
    assert "utcnow" not in combined
    assert "time.time(" not in combined
    assert "os.walk" not in combined
    assert "src.risk_layer.kill_switch" not in combined
    assert "data/kill_switch" not in combined
    for text in sources.values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"glob", "rglob", "walk"}
            if isinstance(node, ast.Attribute):
                assert node.attr not in {"utcnow"}
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                rendered = ast.unparse(node)
                assert "datetime" not in rendered
                assert "kill_switch" not in rendered
                assert "KillSwitch" not in rendered


def test_dispatch_table_targets_existing_materializers_only() -> None:
    orchestrator_src = (PACKAGE_DIR / "orchestrator_v1.py").read_text(encoding="utf-8")
    expected = [
        "materialize_dynamic_scope_presentation_projection_v1",
        "materialize_bull_bear_regime_presentation_projection_v1",
        "materialize_canonical_decision_presentation_projection_v1",
        "materialize_double_play_presentation_projection_v1",
        "materialize_safety_authority_presentation_projection_v1",
        "materialize_risk_sizing_capital_presentation_projection_v1",
        "materialize_execution_reconciliation_presentation_projection_v1",
        "materialize_economic_summary_presentation_projection_v1",
    ]
    for symbol in expected:
        assert symbol in orchestrator_src
    assert "export_dynamic_scope_state_to_archive_sibling_v1" not in orchestrator_src
    assert "LaunchAgent" not in orchestrator_src
    assert "supervisor" not in orchestrator_src.lower()
