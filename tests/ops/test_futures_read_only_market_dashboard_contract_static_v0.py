"""Static contract tests for Futures Read-only Market Dashboard Contract (v0).

Machine-anchors docs-only F5 read-only dashboard display boundary from
FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md (GAP-F5-STATIC-001). Protects
review legibility without importing runtime trading modules, WebUI apps, or
authorizing execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
WEBUI_DOCS = REPO_ROOT / "docs" / "webui"

F5_CONTRACT = SPECS / "FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md"
F1_CONTRACT = SPECS / "FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md"
F2_CONTRACT = SPECS / "FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md"
F3_CONTRACT = SPECS / "FUTURES_BACKTEST_REALISM_CONTRACT_V0.md"
F4_CONTRACT = SPECS / "FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md"
CAPABILITY_SPEC = SPECS / "FUTURES_CAPABILITY_SPEC_V0.md"
LANE_TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
MARKET_SURFACE = WEBUI_DOCS / "MARKET_SURFACE_V0.md"
ENV_NAME_CONTRACT = SPECS / "SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md"

TAXONOMY_CROSSREF_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_runtime_lane_taxonomy_authority_levels_contract_v0.py"
)

REQUIRED_STATUS_VALUES: tuple[str, ...] = (
    "spot_only",
    "generic_market",
    "metadata_label_only",
    "futures_metadata_missing",
    "futures_metadata_partial",
    "provenance_missing",
    "provenance_partial",
    "backtest_realism_incomplete",
    "risk_safety_incomplete",
    "testnet_candidate_only",
    "unsupported_for_live",
)

PROHIBITED_CONTROLS: tuple[str, ...] = (
    "placing orders",
    "cancelling orders",
    "starting sessions",
    "starting backtests",
    "refreshing market data through write-enabled paths",
    "enabling testnet",
    "enabling Live",
    "arming execution",
    "toggling RiskGate",
    "toggling SafetyGuard",
    "toggling KillSwitch",
    "changing leverage",
    "changing margin mode",
    "writing evidence",
    "writing archives",
    "uploading to S3",
    "changing configs",
)

VALIDATION_CHECKLIST_PHRASES: tuple[str, ...] = (
    "Dashboard futures surfaces are read-only",
    "No dashboard endpoint calls exchange clients",
    "No dashboard endpoint writes cache/evidence/archive/S3",
    "kraken_futures_testnet renders as metadata label only",
    "Unknown F1 metadata renders unsupported/partial",
    "Unknown F2 provenance renders unsupported/partial",
    "Unknown F3 realism renders incomplete",
    "Unknown F4 risk/safety renders incomplete",
    "No UI state implies Live authorization",
    "No UI control exists for orders, sessions, testnet, Live, RiskGate, SafetyGuard, or KillSwitch toggles",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def _lower(path: Path) -> str:
    return _plain(path).lower()


def test_f5_contract_exists_v0() -> None:
    assert F5_CONTRACT.is_file()
    text = _read(F5_CONTRACT)
    assert "Futures Read-only Market Dashboard Contract v0" in text
    assert "F5 Read-only Dashboard stage" in text


def test_f5_contract_docs_only_non_authority_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "docs-only dashboard contract" in lowered
    assert "does not implement a dashboard" in lowered
    assert "does not grant" in lowered
    assert "does not permit orders" in lowered
    assert "display semantics only" in lowered


def test_f5_contract_prohibited_controls_enumerated_v0() -> None:
    section = (
        _plain(F5_CONTRACT)
        .split("Explicitly prohibited controls", 1)[1]
        .split("API / endpoint boundary", 1)[0]
    )
    lowered = section.lower()
    for control in PROHIBITED_CONTROLS:
        assert control.lower() in lowered, f"missing prohibited control: {control!r}"


def test_f5_contract_required_status_model_twelve_values_v0() -> None:
    text = _read(F5_CONTRACT)
    for status in REQUIRED_STATUS_VALUES:
        assert f"`{status}`" in text, f"missing status value: {status!r}"
    assert "Dashboard copy must avoid green/ready styling for partial states" in text


def test_f5_contract_f1_f4_prerequisite_contracts_present_v0() -> None:
    text = _read(F5_CONTRACT)
    for contract in (F1_CONTRACT, F2_CONTRACT, F3_CONTRACT, F4_CONTRACT):
        assert contract.is_file()
        assert contract.name in text
    capability = _read(CAPABILITY_SPEC)
    assert F5_CONTRACT.name in capability
    assert "Read-only dashboard" in capability or "read-only dashboard" in capability.lower()


def test_f5_contract_missing_prerequisites_displayed_as_missing_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "display missing prerequisites as missing" in lowered
    assert "not infer support" in lowered
    assert "unknown or missing values must be visible" in lowered


def test_f5_contract_f1_missing_state_semantics_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "f1 instrument metadata" in lowered
    assert "futures_metadata_missing" in lowered
    assert "futures_metadata_partial" in lowered
    assert "missing metadata" in lowered and "unsupported/partial" in lowered


def test_f5_contract_f2_missing_state_semantics_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "f2 market data provenance" in lowered
    assert "provenance_missing" in lowered
    assert "provenance_partial" in lowered
    assert "missing provenance" in lowered and "unsupported/partial" in lowered


def test_f5_contract_f3_missing_state_semantics_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "f3 backtest realism" in lowered
    assert "backtest_realism_incomplete" in lowered
    assert "unknown f3 realism renders incomplete" in lowered
    assert "must not present a spot/cash backtest as futures-realistic" in lowered


def test_f5_contract_f4_missing_state_semantics_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "f4 risk / safety / killswitch" in lowered
    assert "risk_safety_incomplete" in lowered
    assert "missing killswitch status" in lowered
    assert "display is not enforcement" in lowered


def test_f5_contract_kraken_futures_testnet_metadata_label_only_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "kraken_futures_testnet" in lowered
    assert "metadata / label surface" in lowered or "metadata label only" in lowered
    assert "not a proven kraken futures adapter" in lowered
    assert "not futures trading capability" in lowered
    assert "metadata label only. no governed kraken futures adapter" in lowered


def test_f5_contract_env_name_not_execution_authority_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "env_name must never be displayed as execution authority" in lowered
    assert "mode and env_name must remain separate concepts" in lowered
    assert ENV_NAME_CONTRACT.is_file()
    assert ENV_NAME_CONTRACT.name in _read(F5_CONTRACT)


def test_f5_contract_validation_checklist_ten_points_v0() -> None:
    section = (
        _plain(F5_CONTRACT).split("Validation / future tests", 1)[1].split("## References", 1)[0]
    )
    for phrase in VALIDATION_CHECKLIST_PHRASES:
        assert phrase in section, f"missing validation checklist item: {phrase!r}"


def test_f5_contract_no_provider_or_dashboard_truth_v0() -> None:
    lowered = _lower(F5_CONTRACT)
    assert "does not authorize" in lowered
    assert "data fetching" in lowered
    assert "fail-closed display does not enforce trading" in lowered
    assert "dashboard ≠ freigabe" in lowered or "dashboard != freigabe" in lowered


def test_f5_contract_no_trading_readiness_or_selected_future_truth_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "first-live readiness" in lowered
    assert "production readiness" in lowered
    assert "testnet execution permission" in lowered
    assert "unsupported_for_live" in lowered
    assert "testnet_candidate_only" in lowered
    assert "not live-capable" in lowered


def test_f5_contract_no_execution_runtime_preflight_arming_authority_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "execution sessions" in lowered
    assert "arming execution" in lowered
    assert "scheduler" in lowered or "runtime execution" in lowered
    assert "broker" in lowered
    assert "workflow dispatch" in lowered
    assert "hidden background jobs" in lowered


def test_f5_contract_market_airport_excluded_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "market-airport" in lowered
    assert "out of scope" in lowered
    assert MARKET_SURFACE.is_file()
    assert MARKET_SURFACE.name in _read(F5_CONTRACT)
    assert "orthogonal" in lowered


def test_f5_contract_master_v2_double_play_protected_v0() -> None:
    text = _read(F5_CONTRACT)
    plain = _plain(F5_CONTRACT)
    lowered = plain.lower()
    assert "Master V2" in text
    assert "Double Play" in text
    assert "MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true" in text
    assert "does not grant Master V2 approval" in plain
    assert "double play authority" in lowered
    assert TAXONOMY_CROSSREF_TEST.is_file()


def test_f5_contract_read_only_observability_posture_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    assert "read-only" in lowered
    assert "review_input_only" in lowered
    assert "lane_id dashboard" in lowered or "`dashboard`" in _read(F5_CONTRACT)
    assert LANE_TAXONOMY.is_file()
    assert LANE_TAXONOMY.name in _read(F5_CONTRACT)
    assert (
        "futures dashboard is read-only. no orders, no sessions, no testnet activation, no live authorization"
        in lowered
    )


def test_f5_contract_fail_closed_display_semantics_v0() -> None:
    section = (
        _plain(F5_CONTRACT)
        .split("Fail-closed display semantics", 1)[1]
        .split("Lane taxonomy cross-reference", 1)[0]
    )
    lowered = section.lower()
    assert "missing metadata" in lowered
    assert "missing provenance" in lowered
    assert "missing funding" in lowered
    assert "missing liquidation model" in lowered
    assert "missing killswitch status" in lowered
    assert "unknown adapter binding" in lowered
    assert "stale data" in lowered


def test_f5_contract_api_read_only_boundary_no_network_runtime_v0() -> None:
    section = (
        _plain(F5_CONTRACT)
        .split("API / endpoint boundary", 1)[1]
        .split("UI copy / banner requirements", 1)[0]
    )
    lowered = section.lower()
    assert "dashboard apis must be read-only" in lowered
    assert "exchange calls" in lowered
    assert "cache writes" in lowered
    assert "evidence writes" in lowered
    assert "archive writes" in lowered
    assert "read-only dashboard v0 must not call write-enabled fetch/cache paths" in _lower(
        F5_CONTRACT
    )


def test_f5_contract_no_implicit_paper_shadow_testnet_live_activation_v0() -> None:
    text = _plain(F5_CONTRACT)
    lowered = text.lower()
    for path in ("paper", "shadow", "testnet", "live"):
        assert path in lowered
    assert "does not permit orders" in lowered
    assert "testnet activation" in lowered
    assert "live activation" in lowered
    assert "avoid labels such as ready" in lowered or "avoid labels such as `ready`" in _read(
        F5_CONTRACT
    )
