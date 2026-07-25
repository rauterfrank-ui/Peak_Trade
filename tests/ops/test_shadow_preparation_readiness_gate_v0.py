"""Focused contract tests for ops.shadow_preparation_readiness_gate_v0."""

from __future__ import annotations

import ast
import inspect
import socket
from pathlib import Path

import pytest

from src.ops.shadow_preparation_readiness_gate_v0 import (
    ACTIVATION_FLAG_KEYS,
    AUTHORITY_EFFECT_NONE,
    DASHBOARD_BLOCKER_ID_CANONICAL,
    DASHBOARD_BLOCKER_STATE_OPEN,
    DETERMINISTIC_EVALUATED_AT_DEFAULT,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
    SCHEMA_ID,
    HistoricalSurfaceClassification,
    HistoricalSurfaceRecordV0,
    ShadowPreparationReadinessGateError,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCER = REPO_ROOT / "src" / "ops" / "shadow_preparation_readiness_gate_v0.py"
CONFIG = REPO_ROOT / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)

FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "src.orders",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.trading.master_v2",
)


def _default_result(**kwargs):
    return evaluate_shadow_preparation_readiness_gate_v0(repo_root=REPO_ROOT, **kwargs)


def test_package_marker_and_schema_identity() -> None:
    assert PACKAGE_MARKER == "SHADOW_PREPARATION_READINESS_GATE_V0=true"
    assert PRODUCER_FAMILY == "ops.shadow_preparation_readiness_gate_v0"
    assert SCHEMA_ID == PRODUCER_FAMILY


def test_default_contract_reports_canonical_shadow_mode_absent() -> None:
    result = _default_result()
    assert result.canonical_shadow_mode_exists is False
    assert result.shadow_preparation_complete is False


def test_step_29u_unbound() -> None:
    result = _default_result()
    assert result.canonical_step_29u_bound is False


def test_all_activation_and_order_flags_false() -> None:
    result = _default_result()
    assert result.shadow_activation_authorized is False
    assert result.paper_activation_authorized is False
    assert result.testnet_activation_authorized is False
    assert result.scheduler_activation_authorized is False
    assert result.runtime_activation_authorized is False
    assert result.live_authorized is False
    assert result.orders_authorized is False


def test_authority_effect_is_none() -> None:
    result = _default_result()
    assert result.authority_effect == AUTHORITY_EFFECT_NONE
    assert result.authority_effect == "NONE"


def test_runtime_bridge_bound_not_activated() -> None:
    result = _default_result()
    assert result.runtime_bridge_state == RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED


def test_economic_gate_remains_false_blocked() -> None:
    result = _default_result()
    assert result.economic_validity_offline_gate_pass is False
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL_BLOCKED" in result.blockers


def test_dashboard_blocker_remains_open_unresolved_unwaived() -> None:
    result = _default_result()
    assert result.dashboard_blocker_id == DASHBOARD_BLOCKER_ID_CANONICAL
    assert result.dashboard_blocker_id == "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY"
    assert result.dashboard_blocker_state == DASHBOARD_BLOCKER_STATE_OPEN
    assert result.dashboard_blocker_resolved is False
    assert result.dashboard_blocker_waived is False
    assert result.dashboard_blocker_accepted_as_done is False


def test_phase24_phase31_surfaces_non_canonical_step29u() -> None:
    result = _default_result()
    by_id = {s.surface_id: s for s in result.historical_surface_classifications}
    for surface_id in (
        "phase24_shadow_order_executor",
        "phase24_run_shadow_execution_script",
        "phase31_shadow_paper_session",
    ):
        assert surface_id in by_id
        assert by_id[surface_id].classification == (
            HistoricalSurfaceClassification.NON_CANONICAL_STEP29U
        )


def test_ambiguous_surfaces_fail_closed() -> None:
    ambiguous = (
        HistoricalSurfaceRecordV0(
            surface_id="ambiguous_surface",
            path="somewhere/unknown.py",
            classification=HistoricalSurfaceClassification.UNKNOWN_FAIL_CLOSED,
        ),
    )
    with pytest.raises(ShadowPreparationReadinessGateError, match="ambiguous_fail_closed"):
        _default_result(historical_surface_overrides=ambiguous)


def test_true_activation_input_rejected() -> None:
    for key in ACTIVATION_FLAG_KEYS:
        with pytest.raises(ShadowPreparationReadinessGateError, match="activation_flag_true"):
            _default_result(activation_overrides={key: True})


def test_missing_invalid_config_fails_closed(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    with pytest.raises(ShadowPreparationReadinessGateError, match="missing_config"):
        load_shadow_preparation_readiness_gate_config_v0(missing)

    bad = tmp_path / "bad.toml"
    bad.write_text('schema_version = "wrong"\n', encoding="utf-8")
    with pytest.raises(ShadowPreparationReadinessGateError, match="invalid_config"):
        load_shadow_preparation_readiness_gate_config_v0(bad)


def test_output_deterministic_apart_from_timestamp_convention() -> None:
    a = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    b = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    assert a.to_dict() == b.to_dict()
    custom = _default_result(evaluated_at="2026-07-25T00:00:00Z")
    assert custom.evaluated_at == "2026-07-25T00:00:00Z"
    assert custom.canonical_shadow_mode_exists is False


def test_producer_performs_no_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_args, **_kwargs):  # pragma: no cover - fail if called
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    result = _default_result()
    assert result.schema_id == SCHEMA_ID


def test_producer_exposes_no_start_or_enable_methods() -> None:
    import src.ops.shadow_preparation_readiness_gate_v0 as mod

    # Forbid process-starting / enabling callables by exact action tokens in names.
    forbidden_callables = {
        "start",
        "enable",
        "activate",
        "schedule",
        "run_session",
        "submit_order",
        "start_shadow",
        "enable_runtime",
        "activate_shadow",
    }
    public_callables = {
        name
        for name in dir(mod)
        if not name.startswith("_")
        and callable(getattr(mod, name))
        and not inspect.isclass(getattr(mod, name))
    }
    assert not (public_callables & forbidden_callables)
    for name in public_callables:
        assert not name.lower().startswith(("start_", "enable_", "activate_", "schedule_"))
        assert not name.lower().endswith(("_start", "_enable", "_activate"))


def test_producer_imports_no_mutable_execution_order_runtime_or_webui() -> None:
    tree = ast.parse(PRODUCER.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    for module in imported:
        assert not any(
            module == prefix or module.startswith(prefix + ".")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        ), module


def test_config_contains_no_true_activation_flag() -> None:
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG)
    for key in ACTIVATION_FLAG_KEYS:
        assert cfg.get(key) is False
    text = CONFIG.read_text(encoding="utf-8")
    for key in ACTIVATION_FLAG_KEYS:
        assert f"{key} = true" not in text
        assert f"{key}=true" not in text


def test_docs_contain_mandatory_non_activation_and_non_equivalence_tokens() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    for token in (
        "Preparation and classification only",
        "not** STEP 29U implementation",
        "does **not** authorize Shadow",
        "Paper, Testnet, Scheduler, Runtime, Live, or Orders",
        "not** canonical by name",
        "Master V2",
        "Double Play",
        "Safety",
        "BOUND_NOT_ACTIVATED",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
        "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY",
        "Closing PR #5529",
        "separate operator GO",
        "NON_ACTIVATING=true",
        "AUTHORITY_EFFECT=NONE",
    ):
        assert token in text, token


def test_authority_effect_override_non_none_rejected() -> None:
    with pytest.raises(ShadowPreparationReadinessGateError, match="authority_effect_must_be_none"):
        _default_result(authority_effect_override="GRANT")


def test_dashboard_resolved_override_rejected() -> None:
    with pytest.raises(ShadowPreparationReadinessGateError, match="dashboard_blocker_resolved"):
        _default_result(dashboard_blocker_overrides={"dashboard_blocker_resolved": True})
