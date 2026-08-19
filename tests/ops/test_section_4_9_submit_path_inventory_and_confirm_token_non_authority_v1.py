"""Docs/contract checks for Master Runbook §4.9 (FND-011) submit-path inventory.

Also binds existing confirm-token code symbols as not Owner execute-GO.
Read-only documentation and code contract. Does not authorize Live,
Testnet, Canary execute, funding, orders, or COVER_USDC instantiation.
Does not change token values or runtime gates.
"""

from __future__ import annotations

from pathlib import Path

from src.core.environment import LIVE_CONFIRM_TOKEN, PT_LIVE_CONFIRM_TOKEN_ENV
from src.execution.live_session import require_bounded_pilot_handoff_env
from src.live.safety import SafetyGuard
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    CONFIRM_TOKEN_ENV,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    latch_and_consume_confirm_digest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CONFIRM_TOKEN_CANONICAL,
    OWNER_GO_EXECUTE,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    FAMILY_LIVE_ARMED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"

SECTION_4_9_HEADING = "## 4.9 Canonical submit-path inventory and Owner-GO scope binding"

REQUIRED_PATH_IDS = (
    "SP-01-OKX-CANARY-HTTP-POST-TRADE-ORDER",
    "SP-02-OKX-CANARY-SUBMIT-TRANSPORT",
    "SP-03-OKX-CANARY-RUNNER-AND-CLI",
    "SP-04-OKX-TESTNET-PRODUCTIVE-PORT",
    "SP-05-OKX-TESTNET-CAMPAIGN-ORCHESTRATION",
    "SP-06-OKX-TESTNET-OPERATOR-EXECUTE-CLI",
    "SP-07-PIPELINE-SUBMIT-ORDER",
    "SP-08-PIPELINE-EXECUTE-WITH-SAFETY",
    "SP-09-EXCHANGE-ORDER-EXECUTOR",
    "SP-10-KRAKEN-LIVE-ADDORDER",
    "SP-11-KRAKEN-TESTNET-CREATE-ORDER",
    "SP-12-TESTNET-ORDER-EXECUTOR",
    "SP-13-LIVE-SESSION-BOUNDED-PILOT",
    "SP-14-EXECUTION-ROUTER-PLACE-ORDER",
    "SP-15-NETWORKED-ONRAMP-CLI",
)

REQUIRED_NON_EQUIVALENCE = (
    "DOCS_OR_CONTRACT_GO != EXECUTION_GO",
    "EVIDENCE_GET_GO != POST_OR_ORDER_GO",
    "FUNDING_EVALUATION_GO != FUNDING_AUTHORIZATION",
    "FUNDING_AUTHORIZATION != ORDER_SUBMIT_AUTHORIZATION",
    "TESTNET_GO != LIVE_GO",
    "HISTORICAL_DEMO_XPERP_AUTHORITY != CANARY_AUTHORITY",
    "CANARY_PREPARATION_GO != CANARY_EXECUTE_GO",
    "LIVE_ENABLED_ALONE != AUTHORITY",
    "LIVE_ARMED_ALONE != AUTHORITY",
    "CONFIG_REACHABILITY != OWNER_AUTHORIZATION",
    "EXISTENCE_OF_POST_TRANSPORT != PERMISSION_TO_CALL_IT",
    "MERGE_GO != SUBMIT_GO",
    "AUTHORING_GO != EXECUTE_GO",
    "CONSUMED_GO != REUSABLE_GO",
    "SECTION_11_12_8_CLOSED != LICENSE_TO_REOPEN_WITHOUT_NEW_GO",
    "CAPABILITY_11_9_FIXTURE_ONLY != SECTION_11_13_5_CANARY_EXECUTE",
    "KRAKEN_BOUNDED_PILOT != OKX_EEA_CANARY",
    "PIPELINE_SUBMIT != CANARY_OR_TESTNET_SUBMIT",
    "ONE_SUBMIT_PATH_GO != ANY_OTHER_SUBMIT_PATH_GO",
)

STANDING_FLAGS = (
    "COVER_USDC=UNINSTANTIATED",
    "NUMERIC_FUNDING_AMOUNT=NONE",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
    "GENERAL_LIVE_UNLOCKED=false",
    "SUBMIT_UNLOCKED=false",
    "GENERAL_LIVE_SUBMIT_UNLOCKED=false",
    "ENABLE_LIVE_TRADING=false",
    "LIVE_ENABLED=false",
    "LIVE_ARMED=false",
    "LIVE_ORDER_AUTHORIZED=false",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _section_4_9(text: str) -> str:
    start = text.find(SECTION_4_9_HEADING)
    assert start >= 0, "missing §4.9 heading"
    end = text.find("\n## 4.10 ", start)
    assert end > start, "missing §4.10 boundary after §4.9"
    return text[start:end]


def _header(section: str) -> str:
    end = section.find("### 4.9.1 Binding definitions")
    assert end > 0, "missing §4.9.1 boundary"
    return section[:end]


def _scope_rule(section: str) -> str:
    start = section.find("### 4.9.2 Canonical Owner-GO scope rule")
    assert start >= 0, "missing §4.9.2 heading"
    end = section.find("### 4.9.3 Standing fail-closed binding", start)
    assert end > start, "missing §4.9.3 boundary after §4.9.2"
    return section[start:end]


def _standing(section: str) -> str:
    start = section.find("### 4.9.3 Standing fail-closed binding")
    assert start >= 0, "missing §4.9.3 heading"
    end = section.find("### 4.9.4 Inventoried real submit surfaces", start)
    assert end > start, "missing §4.9.4 boundary after §4.9.3"
    return section[start:end]


def _inventory(section: str) -> str:
    start = section.find("### 4.9.4 Inventoried real submit surfaces")
    assert start >= 0, "missing §4.9.4 heading"
    end = section.find("### 4.9.5 Classified non-productive paths", start)
    assert end > start, "missing §4.9.5 boundary after §4.9.4"
    return section[start:end]


def _sp13_block(inventory: str) -> str:
    start = inventory.find("#### SP-13 LiveSessionRunner bounded-pilot bridge")
    assert start >= 0, "missing SP-13 heading"
    end = inventory.find("#### SP-14 ", start)
    assert end > start, "missing SP-14 boundary after SP-13"
    return inventory[start:end]


def test_section_4_9_heading_and_fnd_011_docs_only_resolution() -> None:
    text = _read(MASTER_RUNBOOK)
    assert SECTION_4_9_HEADING in text
    header = _header(_section_4_9(text))
    assert "FND_011_STATUS=RESOLVED_DOCS_ONLY" in header
    assert "AUTHORITY_EXPANDED=false" in header
    assert "CAN_SUBMIT_ORDER_TODAY_ANY_PATH=false" in header
    assert "An Owner-GO authorizes only the explicitly named submit surface" in text


def test_section_4_9_standing_safety_flags_remain_fail_closed() -> None:
    standing = _standing(_section_4_9(_read(MASTER_RUNBOOK)))
    for flag in STANDING_FLAGS:
        assert flag in standing, flag
    assert "LIVE_AUTHORIZED=true" not in standing
    assert "TESTNET_AUTHORIZED=true" not in standing
    assert "ORDER_SUBMIT_AUTHORIZED=true" not in standing
    assert "CANARY_EXECUTE_AUTHORIZED=true" not in standing
    assert "COVER_USDC=INSTANTIATED" not in standing


def test_section_4_9_inventory_ids_and_counts() -> None:
    inventory = _inventory(_section_4_9(_read(MASTER_RUNBOOK)))
    assert "SUBMIT_PATH_COUNT=15" in inventory
    assert inventory.count("SUBMIT_PATH_ID=") == 15
    for path_id in REQUIRED_PATH_IDS:
        assert f"SUBMIT_PATH_ID={path_id}" in inventory, path_id
    assert inventory.count("CAN_SUBMIT_ORDER_TODAY=false") == 15
    assert "CAN_SUBMIT_ORDER_TODAY=true" not in inventory


def test_section_4_9_non_equivalence_rules() -> None:
    scope_rule = _scope_rule(_section_4_9(_read(MASTER_RUNBOOK)))
    for rule in REQUIRED_NON_EQUIVALENCE:
        assert rule in scope_rule, rule


def test_section_4_9_sp13_go_scope_must_not_authorize_okx_canary_paths() -> None:
    sp13 = _sp13_block(_inventory(_section_4_9(_read(MASTER_RUNBOOK))))
    assert "SUBMIT_PATH_ID=SP-13-LIVE-SESSION-BOUNDED-PILOT" in sp13
    assert "GO_SCOPE_MUST_NOT_AUTHORIZE=OKX Canary SP-01/SP-02/SP-03" in sp13
    assert "CAN_SUBMIT_ORDER_TODAY=false" in sp13


def test_confirm_token_literals_are_not_owner_go_execute() -> None:
    expected_confirm_token = "_".join(("I", "KNOW", "WHAT", "I", "AM", "DOING"))
    assert LIVE_CONFIRM_TOKEN == expected_confirm_token
    assert CONFIRM_TOKEN_CANONICAL == expected_confirm_token
    assert LIVE_CONFIRM_TOKEN != OWNER_GO_EXECUTE
    assert CONFIRM_TOKEN_CANONICAL != OWNER_GO_EXECUTE
    assert PT_LIVE_CONFIRM_TOKEN_ENV != OWNER_GO_EXECUTE


def test_existing_confirm_and_safety_surfaces_are_not_execute_authority() -> None:
    required_paths = (
        REPO_ROOT / "src" / "core" / "environment.py",
        REPO_ROOT / "src" / "execution" / "live_session.py",
        REPO_ROOT / "src" / "live" / "safety.py",
        REPO_ROOT
        / "src"
        / "ops"
        / "section_11_13_5_live_canary_minimum_exposure_v1"
        / "constants_v1.py",
        REPO_ROOT
        / "src"
        / "ops"
        / "section_11_12_8_actual_productive_testnet_campaign_run_start_v1"
        / "hidden_confirm_v1.py",
        REPO_ROOT / "src" / "ops" / "phase_9_2_public_md_session_preflight_v1",
        REPO_ROOT
        / "src"
        / "ops"
        / "secure_confirm_token_family_and_hidden_input_handoff_v1"
        / "family_matrix_v1.py",
    )
    for path in required_paths:
        assert path.exists(), f"missing confirm/safety surface: {path}"

    assert callable(require_bounded_pilot_handoff_env)
    assert callable(latch_and_consume_confirm_digest_v1)
    assert isinstance(SafetyGuard, type)

    confirm_symbols = (
        LIVE_CONFIRM_TOKEN,
        CONFIRM_TOKEN_CANONICAL,
        PT_LIVE_CONFIRM_TOKEN_ENV,
        FAMILY_LIVE_ARMED,
        CONFIRM_TOKEN_ENV,
    )
    for symbol in confirm_symbols:
        assert symbol != OWNER_GO_EXECUTE, symbol
