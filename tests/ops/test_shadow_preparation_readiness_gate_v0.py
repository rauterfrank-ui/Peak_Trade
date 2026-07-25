"""Focused contract tests for ops.shadow_preparation_readiness_gate_v0."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import socket
from pathlib import Path

import pytest

from src.ops.shadow_preparation_readiness_gate_v0 import (
    ACTIVATION_FLAG_KEYS,
    ALLOWED_PREPARATION_STATUSES,
    AUTHORITY_EFFECT_NONE,
    CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY,
    DASHBOARD_BLOCKER_ID_CANONICAL,
    DASHBOARD_BLOCKER_STATE_OPEN,
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    DETERMINISTIC_EVALUATED_AT_DEFAULT,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    PROJECTION_OUTPUT_PATH_CONFIG_KEY,
    PROJECTION_SCHEMA_ID,
    PROJECTION_SCHEMA_VERSION,
    REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS,
    RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
    SCHEMA_ID,
    HistoricalSurfaceClassification,
    HistoricalSurfaceRecordV0,
    PreparationStatusV0,
    ShadowPreparationReadinessGateError,
    build_shadow_preparation_readiness_projection_payload_v0,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
    serialize_shadow_preparation_readiness_projection_v0,
    write_shadow_preparation_readiness_projection_v0,
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


def test_mindestkontrakt_inventory_exact_set_and_stable_order() -> None:
    result = _default_result()
    ids = tuple(item.component_id for item in result.mindestkontrakt_inventory)
    assert ids == REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS
    assert len(ids) == len(set(ids))
    assert len(ids) == 20


def test_mindestkontrakt_statuses_are_closed_enum_only() -> None:
    result = _default_result()
    for item in result.mindestkontrakt_inventory:
        assert item.preparation_status.value in ALLOWED_PREPARATION_STATUSES
        assert isinstance(item.preparation_status, PreparationStatusV0)


def test_mindestkontrakt_missing_or_unbound_have_blockers() -> None:
    result = _default_result()
    for item in result.mindestkontrakt_inventory:
        if item.preparation_status in (
            PreparationStatusV0.MISSING,
            PreparationStatusV0.UNBOUND,
        ):
            assert item.blockers, item.component_id


def test_mindestkontrakt_no_canonical_executable_shadow_owners() -> None:
    result = _default_result()
    by_id = {item.component_id: item for item in result.mindestkontrakt_inventory}
    for component_id in (
        "lifecycle_owner",
        "session_state_machine",
        "canonical_decision_consumption",
        "fill_ownership",
        "fee_ownership",
        "slippage_ownership",
        "position_projection",
        "account_projection",
    ):
        item = by_id[component_id]
        assert item.preparation_status == PreparationStatusV0.MISSING
        assert item.implementation_path is None
        assert item.canonical_owner is None
    assert by_id["execution_simulation_boundary"].preparation_status == (
        PreparationStatusV0.LEGACY_NON_CANONICAL
    )
    assert by_id["execution_simulation_boundary"].implementation_path is None


def test_legacy_shadow_paper_remain_non_canonical() -> None:
    result = _default_result()
    by_hist = {s.surface_id: s for s in result.historical_surface_classifications}
    for surface_id in (
        "phase24_shadow_order_executor",
        "phase31_shadow_paper_session",
    ):
        assert by_hist[surface_id].classification == (
            HistoricalSurfaceClassification.NON_CANONICAL_STEP29U
        )
    legacy = next(
        item
        for item in result.mindestkontrakt_inventory
        if item.component_id == "legacy_surface_non_equivalence"
    )
    assert legacy.preparation_status == PreparationStatusV0.PRESENT
    assert "HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U" in legacy.blockers


def test_step29u_implementation_and_activation_locks_remain() -> None:
    result = _default_result()
    assert result.not_step_29u_implementation is True
    assert result.step_29u_implemented is False
    assert result.shadow_activatable is False
    assert result.shadow_mode_allowed is False
    assert result.separate_go_required_for_implementation is True
    assert result.separate_go_required_for_activation is True
    assert result.canonical_shadow_mode_exists is False
    assert result.canonical_step_29u_bound is False
    assert result.shadow_preparation_complete is False


def test_step_29v_remains_canonically_undefined() -> None:
    result = _default_result()
    assert result.canonical_step_29v_paper_mode_exists is False
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG)
    assert "runbook.STEP_29V.paper_absent" in cfg["known_canonical_authority_identifiers"]


def test_mindestkontrakt_output_deterministic_machine_readable() -> None:
    a = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    b = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    assert a.to_dict()["mindestkontrakt_inventory"] == b.to_dict()["mindestkontrakt_inventory"]
    assert isinstance(a.to_dict()["mindestkontrakt_inventory"], list)
    assert (
        a.to_dict()["mindestkontrakt_inventory"][0]["component_id"]
        == (REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS[0])
    )


def test_docs_declare_mindestkontrakt_inventory_non_activating() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    for token in (
        "MINDESTKONTRAKT_GAP_INVENTORY_V0=true",
        "NOT_STEP_29U_IMPLEMENTATION=true",
        "SHADOW_ACTIVATABLE=false",
        "CANONICAL_STEP_29V_PAPER_MODE_EXISTS=false",
        "LEGACY_NON_CANONICAL",
        "SEPARATE_GO_REQUIRED_FOR_IMPLEMENTATION=true",
        "SEPARATE_GO_REQUIRED_FOR_ACTIVATION=true",
    ):
        assert token in text, token


EXPECTED_DEFAULT_BLOCKERS = (
    "CANONICAL_STEP_29U_ABSENT",
    "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL_BLOCKED",
    "DASHBOARD_BLOCKER_OPEN:MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY",
    "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED",
    "HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U",
    "NO_ACTIVATION_AUTHORIZED",
)


def _collect_required_relative_paths(cfg: dict) -> set[str]:
    paths: set[str] = set()
    for surface in cfg["historical_surfaces"]:
        paths.add(str(surface["path"]).strip())
    for component in cfg["mindestkontrakt_components"]:
        for evidence_path in component.get("evidence_paths") or []:
            paths.add(str(evidence_path).strip())
    paths.add(str(cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).strip())
    return paths


def _materialize_temp_repo(tmp_path: Path) -> tuple[Path, dict]:
    """Build an isolated offline repo_root with stub files for all required refs."""
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    for relative in _collect_required_relative_paths(cfg):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# stub:{relative}\n", encoding="utf-8")
    config_dest = tmp_path / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
    config_dest.parent.mkdir(parents=True, exist_ok=True)
    config_dest.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path, cfg


def _assert_blocked_non_activating(result) -> None:
    assert result.shadow_preparation_complete is False
    assert result.shadow_activatable is False
    assert result.step_29u_implemented is False
    assert result.canonical_step_29u_bound is False
    assert result.shadow_activation_authorized is False
    assert result.paper_activation_authorized is False
    assert result.testnet_activation_authorized is False
    assert result.scheduler_activation_authorized is False
    assert result.runtime_activation_authorized is False
    assert result.live_authorized is False
    assert result.orders_authorized is False
    assert result.blockers == EXPECTED_DEFAULT_BLOCKERS


def test_default_canonical_config_reference_validation_still_blocked() -> None:
    result = _default_result()
    _assert_blocked_non_activating(result)
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    assert CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY in cfg
    assert (REPO_ROOT / cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).is_file()


def test_explicit_temporary_repo_root_works_deterministically(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    a = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=root, evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT
    )
    b = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=root, evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT
    )
    assert a.to_dict() == b.to_dict()
    _assert_blocked_non_activating(a)


def test_missing_historical_surface_file_fails_closed(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    surface_id = cfg["historical_surfaces"][0]["surface_id"]
    target = root / cfg["historical_surfaces"][0]["path"]
    target.unlink()
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match=f"HISTORICAL_SURFACE_PATH_MISSING:{surface_id}",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)


def test_historical_surface_directory_fails_closed(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    surface_id = cfg["historical_surfaces"][0]["surface_id"]
    target = root / cfg["historical_surfaces"][0]["path"]
    target.unlink()
    target.mkdir()
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match=f"HISTORICAL_SURFACE_PATH_NOT_FILE:{surface_id}",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)


def test_historical_surface_absolute_path_rejected(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    absolute = str((root / "src" / "orders" / "shadow.py").resolve())
    overrides = (
        HistoricalSurfaceRecordV0(
            surface_id="phase24_shadow_order_executor",
            path=absolute,
            classification=HistoricalSurfaceClassification.NON_CANONICAL_STEP29U,
        ),
    )
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match="HISTORICAL_SURFACE_PATH_ABSOLUTE:phase24_shadow_order_executor",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(
            repo_root=root, historical_surface_overrides=overrides
        )


def test_historical_surface_traversal_outside_repo_rejected(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    outside = tmp_path.parent / "outside_escape_probe.py"
    outside.write_text("# outside\n", encoding="utf-8")
    overrides = (
        HistoricalSurfaceRecordV0(
            surface_id="phase24_shadow_order_executor",
            path="../outside_escape_probe.py",
            classification=HistoricalSurfaceClassification.NON_CANONICAL_STEP29U,
        ),
    )
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match="HISTORICAL_SURFACE_PATH_OUTSIDE_REPO:phase24_shadow_order_executor",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(
            repo_root=root, historical_surface_overrides=overrides
        )


def test_missing_mindestkontrakt_evidence_file_fails_closed(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    component = next(c for c in cfg["mindestkontrakt_components"] if c.get("evidence_paths"))
    component_id = component["component_id"]
    evidence = component["evidence_paths"][0]
    (root / evidence).unlink()
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match=f"EVIDENCE_PATH_MISSING:{component_id}",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)


def test_evidence_path_directory_fails_closed(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    component = next(c for c in cfg["mindestkontrakt_components"] if c.get("evidence_paths"))
    component_id = component["component_id"]
    evidence = component["evidence_paths"][0]
    target = root / evidence
    target.unlink()
    target.mkdir()
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match=f"EVIDENCE_PATH_NOT_FILE:{component_id}",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)


def test_evidence_path_outside_repo_rejected(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    component = next(
        c
        for c in cfg["mindestkontrakt_components"]
        if c["component_id"] == "execution_simulation_boundary"
    )
    mutated = dict(cfg)
    components = []
    for item in cfg["mindestkontrakt_components"]:
        if item["component_id"] == component["component_id"]:
            replaced = dict(item)
            replaced["evidence_paths"] = ["../outside_escape_probe.py"]
            components.append(replaced)
        else:
            components.append(item)
    mutated["mindestkontrakt_components"] = components
    outside = tmp_path.parent / "outside_escape_probe.py"
    outside.write_text("# outside\n", encoding="utf-8")
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match="EVIDENCE_PATH_OUTSIDE_REPO:execution_simulation_boundary",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root, config=mutated)


def test_missing_canonical_step29u_semantics_reference_fails_closed(tmp_path: Path) -> None:
    root, cfg = _materialize_temp_repo(tmp_path)
    mutated = dict(cfg)
    mutated.pop(CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY, None)
    with pytest.raises(
        ShadowPreparationReadinessGateError,
        match="CANONICAL_STEP_29U_SEMANTICS_REFERENCE_MISSING",
    ):
        evaluate_shadow_preparation_readiness_gate_v0(repo_root=root, config=mutated)


def test_canonical_step29u_reference_does_not_mark_implemented_or_bound() -> None:
    result = _default_result()
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    assert (REPO_ROOT / cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).is_file()
    assert result.step_29u_implemented is False
    assert result.canonical_step_29u_bound is False
    assert result.shadow_preparation_complete is False


def test_valid_legacy_evidence_paths_remain_legacy_non_canonical() -> None:
    result = _default_result()
    by_id = {item.component_id: item for item in result.mindestkontrakt_inventory}
    assert by_id["execution_simulation_boundary"].preparation_status == (
        PreparationStatusV0.LEGACY_NON_CANONICAL
    )
    assert by_id["execution_simulation_boundary"].evidence_paths
    for path in by_id["execution_simulation_boundary"].evidence_paths:
        assert (REPO_ROOT / path).is_file()


def test_valid_references_preserve_blocker_order_and_readiness_semantics() -> None:
    result = _default_result()
    _assert_blocked_non_activating(result)
    assert list(result.blockers) == list(EXPECTED_DEFAULT_BLOCKERS)


def test_path_validation_performs_no_file_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    original_write_text = Path.write_text
    original_write_bytes = Path.write_bytes

    def _block_write_text(self: Path, *args, **kwargs):  # pragma: no cover
        raise AssertionError(f"unexpected write_text:{self}")

    def _block_write_bytes(self: Path, *args, **kwargs):  # pragma: no cover
        raise AssertionError(f"unexpected write_bytes:{self}")

    monkeypatch.setattr(Path, "write_text", _block_write_text)
    monkeypatch.setattr(Path, "write_bytes", _block_write_bytes)
    result = evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)
    _assert_blocked_non_activating(result)
    # Restore is automatic via monkeypatch teardown; keep originals referenced.
    assert original_write_text is not None
    assert original_write_bytes is not None


def test_docs_declare_path_reference_fail_closed_tokens() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    for token in (
        "HISTORICAL_SURFACE_PATH_MISSING",
        "EVIDENCE_PATH_MISSING",
        "CANONICAL_STEP_29U_SEMANTICS_REFERENCE",
        "ShadowPreparationReadinessGateError",
        "directories are rejected",
    ):
        assert token in text, token


# ---------------------------------------------------------------------------
# Durable readiness projection v0 (offline evidence projection only)
# ---------------------------------------------------------------------------


def _projection_out(tmp_path: Path, name: str = "projection.json") -> tuple[Path, str]:
    parent = tmp_path / "out" / "ops"
    parent.mkdir(parents=True, exist_ok=True)
    rel = f"out/ops/{name}"
    return tmp_path, rel


def test_projection_valid_evaluation_writes_expected_document(tmp_path: Path) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=REPO_ROOT, evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT
    )
    meta = write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    dest = root / rel
    assert dest.is_file()
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["schema_id"] == PROJECTION_SCHEMA_ID
    assert payload["schema_version"] == PROJECTION_SCHEMA_VERSION
    assert payload["evaluated_at"] == DETERMINISTIC_EVALUATED_AT_DEFAULT
    assert payload["evaluation"] == json.loads(json.dumps(evaluation.to_dict()))
    assert payload["blockers"] == list(EXPECTED_DEFAULT_BLOCKERS)
    assert meta.output_path == rel
    assert meta.schema_id == PROJECTION_SCHEMA_ID
    assert meta.schema_version == PROJECTION_SCHEMA_VERSION


def test_projection_fixed_inputs_byte_identical(tmp_path: Path) -> None:
    root, rel = _projection_out(tmp_path, "a.json")
    evaluation = evaluate_shadow_preparation_readiness_gate_v0(
        repo_root=REPO_ROOT, evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT
    )
    write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    first = (root / rel).read_bytes()
    write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    second = (root / rel).read_bytes()
    assert first == second


def test_projection_deterministic_json_ordering_and_trailing_newline(tmp_path: Path) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    raw = (root / rel).read_bytes()
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    text = raw.decode("utf-8")
    expected = (
        json.dumps(
            json.loads(text),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    assert text == expected


def test_projection_sha256_metadata_matches_exact_bytes(tmp_path: Path) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    meta = write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    raw = (root / rel).read_bytes()
    assert meta.byte_length == len(raw)
    assert meta.sha256 == hashlib.sha256(raw).hexdigest()


def test_projection_uses_existing_evaluation_without_recomputation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)

    def _blocked(*_a, **_k):  # pragma: no cover
        raise AssertionError("evaluate must not be called by writer")

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_gate_v0.evaluate_shadow_preparation_readiness_gate_v0",
        _blocked,
    )
    meta = write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    payload = json.loads((root / rel).read_text(encoding="utf-8"))
    assert payload["evaluation"] == json.loads(json.dumps(evaluation.to_dict()))
    assert meta.sha256


def test_projection_does_not_mutate_evaluation_object(tmp_path: Path) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    before = evaluation.to_dict()
    write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    assert evaluation.to_dict() == before


def test_projection_preserves_blocked_non_activating_readiness_semantics(
    tmp_path: Path,
) -> None:
    root, rel = _projection_out(tmp_path)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    _assert_blocked_non_activating(evaluation)
    write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    payload = json.loads((root / rel).read_text(encoding="utf-8"))
    assert payload["shadow_preparation_complete"] is False
    assert payload["shadow_activatable"] is False
    assert payload["step_29u_implemented"] is False
    assert payload["canonical_step_29u_bound"] is False
    for key in ACTIVATION_FLAG_KEYS:
        assert payload[key] is False
    assert payload["authority_effect"] == "NONE"
    assert payload["activation_authority"] is False
    assert payload["projection_only"] is True
    assert payload["blockers"] == list(EXPECTED_DEFAULT_BLOCKERS)
    _assert_blocked_non_activating(evaluation)


def test_projection_absolute_path_fails_closed(tmp_path: Path) -> None:
    evaluation = _default_result()
    with pytest.raises(
        ShadowPreparationReadinessGateError, match="PROJECTION_OUTPUT_PATH_ABSOLUTE"
    ):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=tmp_path,
            output_path=str(tmp_path / "out.json"),
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )


def test_projection_outside_repo_path_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "out" / "ops").mkdir(parents=True, exist_ok=True)
    evaluation = _default_result()
    with pytest.raises(
        ShadowPreparationReadinessGateError, match="PROJECTION_OUTPUT_PATH_OUTSIDE_REPO"
    ):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=tmp_path,
            output_path="../outside_projection.json",
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )


def test_projection_empty_path_fails_closed(tmp_path: Path) -> None:
    evaluation = _default_result()
    with pytest.raises(ShadowPreparationReadinessGateError, match="PROJECTION_OUTPUT_PATH_EMPTY"):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=tmp_path,
            output_path="   ",
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )


def test_projection_missing_parent_fails_closed(tmp_path: Path) -> None:
    evaluation = _default_result()
    with pytest.raises(
        ShadowPreparationReadinessGateError, match="PROJECTION_OUTPUT_PARENT_MISSING"
    ):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=tmp_path,
            output_path="missing_parent/projection.json",
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )


def test_projection_directory_target_fails_closed(tmp_path: Path) -> None:
    target_dir = tmp_path / "out" / "ops" / "projection_dir"
    target_dir.mkdir(parents=True, exist_ok=True)
    evaluation = _default_result()
    with pytest.raises(
        ShadowPreparationReadinessGateError, match="PROJECTION_OUTPUT_PATH_IS_DIRECTORY"
    ):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=tmp_path,
            output_path="out/ops/projection_dir",
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )


def test_projection_temp_write_failure_leaves_no_partial_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, rel = _projection_out(tmp_path)
    dest = root / rel
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)

    import src.ops.shadow_preparation_readiness_gate_v0 as mod

    def _fail_write(self, *_args, **_kwargs):
        raise OSError("simulated temp write failure")

    monkeypatch.setattr(mod.os, "write", _fail_write)  # unused safeguard

    # Fail at flush/fsync stage after temp creation by patching fsync.
    def _fail_fsync(_fd):
        raise OSError("simulated temp write failure")

    monkeypatch.setattr(mod.os, "fsync", _fail_fsync)
    with pytest.raises(ShadowPreparationReadinessGateError, match="PROJECTION_TEMP_WRITE_FAILED"):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=root,
            output_path=rel,
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )
    assert not dest.exists()
    leftovers = list((root / "out" / "ops").glob(".tmp_*"))
    assert leftovers == []


def test_projection_atomic_replace_failure_preserves_previous_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, rel = _projection_out(tmp_path)
    dest = root / rel
    previous = b'{"previous":true}\n'
    dest.write_bytes(previous)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)

    import src.ops.shadow_preparation_readiness_gate_v0 as mod

    def _fail_replace(src, dst):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(mod.os, "replace", _fail_replace)
    with pytest.raises(
        ShadowPreparationReadinessGateError, match="PROJECTION_ATOMIC_REPLACE_FAILED"
    ):
        write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=root,
            output_path=rel,
            evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
        )
    assert dest.read_bytes() == previous
    leftovers = list((root / "out" / "ops").glob(".tmp_*"))
    assert leftovers == []


def test_evaluation_alone_writes_no_projection_artifact(tmp_path: Path) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    before = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    result = evaluate_shadow_preparation_readiness_gate_v0(repo_root=root)
    after = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert after == before
    _assert_blocked_non_activating(result)
    assert not (root / DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH).exists()


def test_projection_writer_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, rel = _projection_out(tmp_path)
    other = tmp_path / "other_cwd"
    other.mkdir()
    monkeypatch.chdir(other)
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    meta = write_shadow_preparation_readiness_projection_v0(
        evaluation=evaluation,
        repo_root=root,
        output_path=rel,
        evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT,
    )
    assert (root / rel).is_file()
    assert not (other / rel).exists()
    assert meta.output_path == rel


def test_config_declares_default_projection_output_path() -> None:
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    assert cfg[PROJECTION_OUTPUT_PATH_CONFIG_KEY] == DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH
    assert not Path(DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH).is_absolute()


def test_docs_declare_durable_projection_contract_tokens() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    for token in (
        "PROJECTION_SCHEMA_ID=shadow_preparation_readiness_projection",
        "PROJECTION_SCHEMA_VERSION=v0",
        "PROJECTION_ONLY=true",
        "EXPLICIT_WRITE_CALL_REQUIRED=true",
        "NOT_READINESS_APPROVAL=true",
        "NOT_ACTIVATION_AUTHORITY=true",
        "NOT_SCHEDULER_INPUT=true",
        "NOT_RUNTIME_COMMAND=true",
        "NOT_DASHBOARD_AUTHORITY=true",
        "PROJECTION_OUTPUT_PATH_EMPTY",
        "write_shadow_preparation_readiness_projection_v0",
        "out&#47;ops&#47;shadow_preparation_readiness_projection_v0.json",
    ):
        assert token in text, token


def test_projection_payload_builder_uses_evaluation_to_dict() -> None:
    evaluation = _default_result(evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT)
    payload = build_shadow_preparation_readiness_projection_payload_v0(
        evaluation=evaluation, evaluated_at=DETERMINISTIC_EVALUATED_AT_DEFAULT
    )
    assert payload["evaluation"] == evaluation.to_dict()
    raw = serialize_shadow_preparation_readiness_projection_v0(payload)
    assert raw.endswith(b"\n")
