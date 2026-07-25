"""Focused contract tests for ops.shadow_preparation_readiness_gate_v0."""

from __future__ import annotations

import ast
import inspect
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
    DETERMINISTIC_EVALUATED_AT_DEFAULT,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS,
    RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
    SCHEMA_ID,
    HistoricalSurfaceClassification,
    HistoricalSurfaceRecordV0,
    PreparationStatusV0,
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
