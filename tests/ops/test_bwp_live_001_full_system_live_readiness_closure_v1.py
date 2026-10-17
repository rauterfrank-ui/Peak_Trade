"""BWP-LIVE-001: capital-guard config strictness and runner/POST boundary locks.

Offline only. No network, no credentials, no venue POST, no productive state.
"""

from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1 import constants_v1 as live_constants
from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    load_full_core_capital_guard_config_v1,
    parse_full_core_capital_guard_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardError,
    load_canary_capital_guard_config_v1,
    parse_canary_capital_guard_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_CORE_CONFIG = REPO_ROOT / "config/ops/current_full_core_capital_guard_v1.json"
CANARY_CONFIG = REPO_ROOT / "config/ops/current_live_canary_capital_guard_v1.json"

NON_BOOL_FLAG_VALUES = ("false", "False", "0", "no", "true", 1, 0, "", [], {}, 0.0)
NON_FINITE_CAPS = ("Infinity", "-Infinity", "inf", "NaN", "sNaN")
NUMERIC_CAP_FIELDS = (
    "max_single_order_notional",
    "max_incremental_initial_margin",
    "max_aggregate_exposure",
    "max_leverage",
    "max_session_capital_commitment",
    "fee_buffer_usdc",
)

COMPOSITION_ROOT = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
RUNNER_SURFACES = (
    "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py",
    "scripts/ops/run_post_6948_productive_continuous_run_authority_live_c1_convergence_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1.py",
)
FORBIDDEN_RUNNER_CALLS = frozenset(
    {
        "post_trade_order",
        "FullCoreProductiveHttpTradeOrderTransportV1",
        "attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1",
        "execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
        "attempt_envelope_bound_external_effect_send_v1",
        "open_current_productive_k1_opaque_signing_handle_session_v1",
        "issue_external_effect_permit_v1",
    }
)


def _payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "guard.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# --- B2: canonical configs keep the Owner decision (unratified, disabled) ------------------


def test_b2_canonical_full_core_config_stays_unratified_and_disabled() -> None:
    cfg = load_full_core_capital_guard_config_v1(repo_root=REPO_ROOT)
    assert cfg.owner_caps_ratified is False
    assert cfg.full_core_guard_join_enabled is False
    assert cfg.max_single_order_notional is None
    assert cfg.max_existing_exposure is None


def test_b2_canonical_canary_config_stays_unratified_and_disallowed() -> None:
    cfg = load_canary_capital_guard_config_v1(repo_root=REPO_ROOT)
    assert cfg.owner_caps_ratified is False
    assert cfg.live_canary_allowed is False
    assert cfg.scale_in_forbidden is True
    assert cfg.automatic_retry_forbidden is True


# --- B2: manipulated authorization flags fail closed ---------------------------------------


@pytest.mark.parametrize("value", NON_BOOL_FLAG_VALUES)
@pytest.mark.parametrize("field", ("owner_caps_ratified", "full_core_guard_join_enabled"))
def test_b2_full_core_non_bool_authorization_flag_rejected(
    tmp_path: Path, field: str, value: object
) -> None:
    payload = _payload(FULL_CORE_CONFIG)
    payload[field] = value
    with pytest.raises(CanaryCapitalGuardError, match=f"INVALID_BOOL_FLAG:{field}"):
        load_full_core_capital_guard_config_v1(config_path=_write(tmp_path, payload))


@pytest.mark.parametrize("value", NON_BOOL_FLAG_VALUES)
@pytest.mark.parametrize(
    "field",
    (
        "owner_caps_ratified",
        "live_canary_allowed",
        "scale_in_forbidden",
        "automatic_retry_forbidden",
    ),
)
def test_b2_canary_non_bool_flag_rejected(tmp_path: Path, field: str, value: object) -> None:
    payload = _payload(CANARY_CONFIG)
    payload[field] = value
    with pytest.raises(CanaryCapitalGuardError, match=f"INVALID_BOOL_FLAG:{field}"):
        load_canary_capital_guard_config_v1(config_path=_write(tmp_path, payload))


def test_b2_string_false_never_ratifies_owner_caps() -> None:
    payload = _payload(FULL_CORE_CONFIG)
    payload["owner_caps_ratified"] = "false"
    payload["full_core_guard_join_enabled"] = "false"
    with pytest.raises(CanaryCapitalGuardError):
        parse_full_core_capital_guard_config_v1(payload, config_digest="d" * 64)


def test_b2_absent_flags_default_fail_closed() -> None:
    payload = _payload(FULL_CORE_CONFIG)
    for key in (
        "owner_caps_ratified",
        "full_core_guard_join_enabled",
        "scale_in_forbidden",
        "automatic_retry_forbidden",
    ):
        payload.pop(key)
    cfg = parse_full_core_capital_guard_config_v1(payload, config_digest="d" * 64)
    assert cfg.owner_caps_ratified is False
    assert cfg.full_core_guard_join_enabled is False
    assert cfg.scale_in_forbidden is True
    assert cfg.automatic_retry_forbidden is True


def test_b2_explicit_json_true_still_parses_for_offline_fixture() -> None:
    payload = _payload(
        REPO_ROOT / "config/ops/current_full_core_capital_guard_offline_e2e_natural_enter_v1.json"
    )
    cfg = parse_full_core_capital_guard_config_v1(payload, config_digest="d" * 64)
    assert cfg.owner_caps_ratified is True
    assert cfg.full_core_guard_join_enabled is True


# --- B2: manipulated numeric caps fail closed -----------------------------------------------


@pytest.mark.parametrize("value", NON_FINITE_CAPS)
@pytest.mark.parametrize("field", NUMERIC_CAP_FIELDS)
def test_b2_non_finite_cap_rejected(field: str, value: str) -> None:
    payload = _payload(CANARY_CONFIG)
    payload[field] = value
    with pytest.raises(CanaryCapitalGuardError, match=f":{field}"):
        parse_canary_capital_guard_config_v1(payload, config_digest="d" * 64)


@pytest.mark.parametrize("value", NON_FINITE_CAPS)
def test_b2_full_core_non_finite_existing_exposure_rejected(value: str) -> None:
    payload = _payload(FULL_CORE_CONFIG)
    payload["max_existing_exposure"] = value
    with pytest.raises(CanaryCapitalGuardError, match="max_existing_exposure"):
        parse_full_core_capital_guard_config_v1(payload, config_digest="d" * 64)


@pytest.mark.parametrize("field", NUMERIC_CAP_FIELDS + ("max_existing_exposure",))
def test_b2_bool_numeric_cap_rejected(field: str) -> None:
    payload = _payload(FULL_CORE_CONFIG)
    payload[field] = True
    with pytest.raises(CanaryCapitalGuardError, match=f"INVALID_DECIMAL:{field}"):
        parse_full_core_capital_guard_config_v1(payload, config_digest="d" * 64)


@pytest.mark.parametrize("field", ("max_open_positions", "max_submitted_orders"))
@pytest.mark.parametrize("value", (True, -1, "abc", "-2"))
def test_b2_invalid_int_cap_rejected(field: str, value: object) -> None:
    payload = _payload(CANARY_CONFIG)
    payload[field] = value
    with pytest.raises(CanaryCapitalGuardError, match=f"_INT_CAP:{field}"):
        parse_canary_capital_guard_config_v1(payload, config_digest="d" * 64)


def test_b2_finite_caps_parse_unchanged() -> None:
    payload = _payload(CANARY_CONFIG)
    payload.update(
        {
            "max_single_order_notional": "100",
            "max_leverage": 20,
            "fee_buffer_usdc": "1.5",
            "max_open_positions": 1,
            "max_submitted_orders": "1",
        }
    )
    cfg = parse_canary_capital_guard_config_v1(payload, config_digest="d" * 64)
    assert cfg.max_single_order_notional == Decimal("100")
    assert cfg.max_leverage == Decimal("20")
    assert cfg.fee_buffer_usdc == Decimal("1.5")
    assert cfg.max_open_positions == 1
    assert cfg.max_submitted_orders == 1


# --- B4/B7: standing pins and runner-to-POST separation --------------------------------------


def test_b4_standing_external_effect_pins_remain_false() -> None:
    assert live_constants.EXTERNAL_EFFECT_AUTHORIZED is False
    assert live_constants.POST_ALLOWED is False
    assert live_constants.REAL_VENUE_POST_ALLOWED is False


def _called_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def _one_shot_true_keywords(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.keyword)
        and node.arg == "one_shot_real_post"
        and isinstance(node.value, ast.Constant)
        and node.value.value is True
    )


@pytest.mark.parametrize("rel", RUNNER_SURFACES)
def test_b7_runner_surface_never_calls_venue_post_seams(rel: str) -> None:
    path = REPO_ROOT / rel
    assert path.is_file(), rel
    hits = _called_names(path) & FORBIDDEN_RUNNER_CALLS
    assert hits == set(), f"{rel} calls POST seam(s): {sorted(hits)}"
    assert _one_shot_true_keywords(path) == 0


def test_b7_lifecycle_wiring_imports_only_post_result_type_from_transport() -> None:
    path = COMPOSITION_ROOT / "full_core_governed_cycle_host_post_submit_lifecycle_wiring_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and (node.module or "").endswith("full_core_productive_http_post_transport_v1")
        for alias in node.names
    ]
    assert imported == ["FullCoreTradeOrderPostResultV1"]


def test_b4_only_one_shot_join_builds_send_capable_transport_with_pre_send_gate() -> None:
    sites: list[str] = []
    for path in sorted((REPO_ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "FullCoreProductiveHttpTradeOrderTransportV1"
                and any(kw.arg == "pre_send_safety_gate" for kw in node.keywords)
            ):
                sites.append(str(path.relative_to(REPO_ROOT)))
    assert sites == [
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
    ]
