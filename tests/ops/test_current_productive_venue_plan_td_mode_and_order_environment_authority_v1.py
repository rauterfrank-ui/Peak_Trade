"""Contract for the new venue-plan tdMode and order-environment authority.

The productive venue-plan binder stays unwired. Standing pins stay unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED_BY_THIS_MODULE,
    HELPER_PINS_ARE_NOT_THIS_AUTHORITY,
    LIVE_CAPABILITY_COMPLETE_BY_THIS_MODULE,
    LIVE_TRADING_ADMITTED_BY_THIS_MODULE,
    NOT_A_HISTORICAL_PREEXISTING_FACT,
    ORDER_ENVIRONMENT_OWNER,
    ORDER_ENVIRONMENT_TRANSFORMATION,
    ORDER_ENVIRONMENT_VOCABULARY,
    TD_MODE_OWNER,
    TD_MODE_SOURCE_CLASS,
    TD_MODE_TOKEN,
    U01_ACCTLV_AUTHORITY_REMAINS_SEPARATE,
    VENUE_PLAN_BINDING_IMPLEMENTED,
    CurrentProductiveVenuePlanInputAuthorityError,
    resolve_current_productive_order_environment_v1,
    resolve_current_productive_venue_plan_td_mode_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

_REPO = Path(__file__).resolve().parents[2]
_AUTHORITY = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py"
)
_BINDER = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_venue_plan_v1.py"
)
_TRANSLATION = _REPO / "src/ops/full_core_live_path_composition_root_v1" / "venue_translation_v1.py"
_RUNBOOK = _REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
_ONE_SHOT = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
)


def test_new_owner_constants_are_labeled_as_new_authority() -> None:
    assert NOT_A_HISTORICAL_PREEXISTING_FACT is True
    assert TD_MODE_SOURCE_CLASS == "STATIC_VENUE_EXECUTION_POLICY"
    assert TD_MODE_OWNER == "CURRENT_PRODUCTIVE_VENUE_EXECUTION_POLICY"
    assert TD_MODE_TOKEN == "cross"
    assert ORDER_ENVIRONMENT_OWNER == "CURRENT_PRODUCTIVE_EXECUTION_MODE"
    assert ORDER_ENVIRONMENT_TRANSFORMATION == "IDENTITY"
    assert ORDER_ENVIRONMENT_VOCABULARY == (
        "SHADOW",
        "INTERNAL_SIMULATED_EXECUTION",
        "PAPER_EXCHANGE",
        "TESTNET",
        "LIVE",
    )
    assert U01_ACCTLV_AUTHORITY_REMAINS_SEPARATE is True
    assert HELPER_PINS_ARE_NOT_THIS_AUTHORITY is True
    assert VENUE_PLAN_BINDING_IMPLEMENTED is False
    assert EXTERNAL_EFFECT_AUTHORIZED_BY_THIS_MODULE is False
    assert LIVE_CAPABILITY_COMPLETE_BY_THIS_MODULE is False
    assert LIVE_TRADING_ADMITTED_BY_THIS_MODULE is False


def test_td_mode_returns_policy_token_without_copying_observation() -> None:
    assert (
        resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=False,
        )
        == "cross"
    )
    assert (
        resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=True,
            observed_td_mode="cross",
            observed_mgn_mode="cross",
        )
        == "cross"
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        (
            {"conformance_required": True},
            "TD_MODE_OBSERVATION_MISSING",
        ),
        (
            {
                "conformance_required": True,
                "observed_td_mode": "cross",
            },
            "MGN_MODE_OBSERVATION_MISSING",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "isolated",
            },
            "TD_MODE_OBSERVATION_MISMATCH",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "cross",
                "observed_mgn_mode": "isolated",
            },
            "TD_MODE_MGN_MODE_CONFLICT",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "  cross",
            },
            "TD_MODE_OBSERVATION_INVALID",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "",
            },
            "TD_MODE_OBSERVATION_MISSING",
        ),
    ],
)
def test_td_mode_conformance_fails_closed(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
        resolve_current_productive_venue_plan_td_mode_v1(**kwargs)  # type: ignore[arg-type]
    assert caught.value.reason_code == reason


@pytest.mark.parametrize("mode", ORDER_ENVIRONMENT_VOCABULARY)
def test_order_environment_is_identity_for_each_canonical_mode(mode: str) -> None:
    assert resolve_current_productive_order_environment_v1(execution_mode=mode) == mode


def test_live_environment_requires_exact_live_mode() -> None:
    assert resolve_current_productive_order_environment_v1(execution_mode="LIVE") == "LIVE"
    for folded in ("live", "prod", "production", "demo", "simulation", "LIVE "):
        with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
            resolve_current_productive_order_environment_v1(execution_mode=folded)
        assert caught.value.reason_code == "ORDER_ENVIRONMENT_MODE_UNKNOWN"


@pytest.mark.parametrize(
    "alias",
    ["prod", "demo", "simulation", "paper", "shadow", "testnet", "live"],
)
def test_aliases_do_not_collapse_canonical_modes(alias: str) -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
        resolve_current_productive_order_environment_v1(execution_mode=alias)
    assert caught.value.reason_code == "ORDER_ENVIRONMENT_MODE_UNKNOWN"
    assert alias not in ORDER_ENVIRONMENT_VOCABULARY


def test_missing_or_conflicting_mode_fails_closed() -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as missing:
        resolve_current_productive_order_environment_v1(execution_mode=None)
    assert missing.value.reason_code == "ORDER_ENVIRONMENT_MODE_MISSING"
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as conflict:
        resolve_current_productive_order_environment_v1(
            execution_mode="SHADOW",
            conflicting_mode="LIVE",
        )
    assert conflict.value.reason_code == "ORDER_ENVIRONMENT_CONFLICT"
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as requested:
        resolve_current_productive_order_environment_v1(
            execution_mode="TESTNET",
            requested_environment="LIVE",
        )
    assert requested.value.reason_code == "ORDER_ENVIRONMENT_CONFLICT"


def test_authority_module_does_not_import_helper_or_u01_owners() -> None:
    source = _AUTHORITY.read_text(encoding="utf-8")
    assert "import " in source
    assert "retroactively this authority" in source
    for forbidden in (
        "current_productive_available_for_sizing_producer_v1",
        "current_productive_u01_account_mode_adapter_v1",
        "environment_namespace",
        "try_bind_current_productive_venue_plan_v1",
    ):
        assert forbidden not in source


def test_productive_venue_plan_binding_is_not_implemented() -> None:
    module_name = "current_productive_venue_plan_td_mode_and_order_environment_authority_v1"
    binder = _BINDER.read_text(encoding="utf-8")
    translation = _TRANSLATION.read_text(encoding="utf-8")
    assert module_name not in binder
    assert module_name not in translation
    assert 'td_mode: str = "cross"' in binder
    assert 'environment="simulation"' in translation


def test_runbook_records_new_authority_without_repairing_header_sha() -> None:
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "BOUND_ORIGIN_MAIN_SHA=0ceb48d970b6d76df0aecd82eebee9570b5e453b" in text
    assert "EPISTEMIC_CLASS=NEW_OWNER_AUTHORITY" in text
    assert "NOT_A_HISTORICAL_PREEXISTING_FACT=true" in text
    assert "VENUE_PLAN_BINDING_IMPLEMENTED=false" in text
    assert "TOKEN=cross" in text
    assert "TRANSFORMATION=IDENTITY" in text


def test_standing_pins_and_post_go_remain_unconsumed() -> None:
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    one_shot = _ONE_SHOT.read_text(encoding="utf-8")
    assert 'POST_GO_STATUS = "UNCONSUMED"' in one_shot
