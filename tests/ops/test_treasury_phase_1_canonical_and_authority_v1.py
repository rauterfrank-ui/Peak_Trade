"""Treasury Phase-1 canonical persist, authority isolation, and capital regression."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAPITAL_ADMISSION_IMPLEMENTED,
    FULL_CORE_OFFLINE_E2E_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    LIVE_ARMED as FULL_CORE_LIVE_ARMED,
    LIVE_ENABLED as FULL_CORE_LIVE_ENABLED,
    RISK_SIZING_OWNER,
    WIRE_SEND_PERMITTED as FULL_CORE_WIRE_SEND,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
)
from src.ops.treasury_phase_1_offline_contracts_v1.authority_v1 import (
    phase_1_no_authority_proof_v1,
    trading_authority_cannot_mint_treasury_authority_v1,
    treasury_authorization_cannot_mint_wire_or_live_v1,
    treasury_observer_cannot_authorize_mutation_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CAPITAL_ADMISSION_AUTHORITY,
    FORBIDDEN_IMPORT_TOKENS,
    PL_TF_002_STATUS,
    TREASURY_PHASE_1_STATUS,
    TREASURY_MUTATION_REACHABLE_FROM_TRADING,
    TREASURY_SEPARATION_GATE_WIRED,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.constants_v1 import (
    TREASURY_PHASE_2_STATUS,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    TREASURY_MUTATION_REACHABLE,
    TREASURY_PHASE_3_STATUS,
    TREASURY_SEPARATION_GATE_WIRED as PHASE_3_SEPARATION_GATE_WIRED,
)
from src.ops.treasury_separation_gate import TREASURY_ONLY_OPERATIONS, evaluate_treasury_policy
from src.trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
)
from tests.ops._current_frozen_document_navigation_v1 import (
    assert_current_frozen_document_navigation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src/ops/treasury_phase_1_offline_contracts_v1"
FULL_CORE_DIR = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1.md"
PHASE_3_SPEC = REPO_ROOT / "docs/ops/specs/TREASURY_PHASE_3_SHADOW_ENFORCEMENT_V1.md"


def test_at07_trading_authority_cannot_mint_treasury() -> None:
    assert trading_authority_cannot_mint_treasury_authority_v1() is True
    for payload in (
        {"live_enabled": True},
        {"live_armed": True},
        {"wire_send_permitted": True},
        {"trading_owner_permit": "OWNER_GO_TRADE"},
        {"strategy_decision": "ENTER"},
        {"double_play_state": "ACTIVE"},
        {"planner_result": "PLAN"},
        {"learner_output": "SCORE"},
        {"scheduler": "TICK"},
        {"generic_execution_token": "exec-1"},
        {"canonical_order_intent": "coi-1"},
    ):
        try:
            trading_authority_cannot_mint_treasury_authority_v1(payload)
        except Exception as exc:
            assert "TREASURY" in str(exc) or "LIVE" in str(exc)
        else:
            raise AssertionError(f"expected deny for {payload}")
    assert (
        treasury_authorization_cannot_mint_wire_or_live_v1("MUTATION_PERMIT_TYPED_OFFLINE") is False
    )
    assert treasury_observer_cannot_authorize_mutation_v1("OBSERVER_CONTRACT") is True
    assert TREASURY_SEPARATION_GATE_WIRED is False
    bot = evaluate_treasury_policy("withdraw", role="bot")
    assert bot.allowed is False
    assert "withdraw" in TREASURY_ONLY_OPERATIONS


def test_package_has_no_network_or_canary_imports() -> None:
    texts = [
        path.read_text(encoding="utf-8")
        for path in PACKAGE_DIR.glob("*.py")
        if path.name != "constants_v1.py"
    ]
    joined = "\n".join(texts)
    for token in FORBIDDEN_IMPORT_TOKENS:
        assert token not in joined
    assert "urllib.request" not in joined
    assert "http.client" not in joined
    full_core = "\n".join(
        path.read_text(encoding="utf-8")
        for path in FULL_CORE_DIR.glob("*.py")
        if path.name != "treasury_interference_proof_v1.py"
    )
    assert "treasury_phase_1_offline_contracts_v1" not in full_core
    assert "treasury_separation_gate" not in full_core


def test_capital_admission_authority_reused_not_replaced() -> None:
    assert CAPITAL_ADMISSION_IMPLEMENTED is True
    assert CAPITAL_ADMISSION_AUTHORITY == "capital_admission_contract_v1"
    assert CAPITAL_AUTHORITY_RISK_ADMISSIBLE == "RISK_ADMISSIBLE"
    assert FULL_CORE_LIVE_ENABLED is True
    assert FULL_CORE_LIVE_ARMED is True
    assert FULL_CORE_WIRE_SEND is True
    assert FULL_CORE_OFFLINE_E2E_PROVEN is True
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
    assert CAPITAL_RISK_MODE_OFFLINE_ALGEBRA == "OFFLINE_ALGEBRA"
    proof = phase_1_no_authority_proof_v1()
    assert proof["TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL"] is False


def test_runbook_spec_and_mot_bind_without_live_or_phase2() -> None:
    assert_current_frozen_document_navigation(
        REPO_ROOT,
        spec=SPEC_PATH,
        owners=(
            PACKAGE_DIR / "constants_v1.py",
            REPO_ROOT / "src/ops/treasury_phase_2_read_only_reconciliation_v1/constants_v1.py",
            REPO_ROOT / "src/ops/treasury_phase_3_shadow_enforcement_v1/constants_v1.py",
            PHASE_3_SPEC,
        ),
    )
    spec = SPEC_PATH.read_text(encoding="utf-8")
    shadow = PHASE_3_SPEC.read_text(encoding="utf-8")
    assert TREASURY_PHASE_1_STATUS == "CLOSED_OFFLINE_CONTRACTS"
    assert TREASURY_PHASE_2_STATUS == "READ_ONLY_FOUNDATION_BOUND"
    assert TREASURY_PHASE_3_STATUS == "SHADOW_ENFORCEMENT_BOUND"
    assert PL_TF_002_STATUS == "CLOSED_TRADING_KEY_TREASURY_CAPABILITY_VENUE_PROVEN"
    assert TREASURY_MUTATION_REACHABLE_FROM_TRADING is False
    assert TREASURY_MUTATION_REACHABLE is False
    assert TREASURY_SEPARATION_GATE_WIRED is False
    assert PHASE_3_SEPARATION_GATE_WIRED is True
    for pin in (
        "docs_token: DOCS_TOKEN_TREASURY_PHASE_1_OFFLINE_CONTRACTS_V1",
        f"TREASURY_PHASE_1_STATUS={TREASURY_PHASE_1_STATUS}",
        f"TREASURY_PHASE_2_STATUS={TREASURY_PHASE_2_STATUS}",
        f"PL_TF_002_STATUS={PL_TF_002_STATUS}",
        "TREASURY_MUTATION_REACHABLE_FROM_TRADING=false",
        "TREASURY_SEPARATION_GATE_WIRED=false",
    ):
        assert pin in spec
    assert f"TREASURY_PHASE_3_STATUS={TREASURY_PHASE_3_STATUS}" in shadow
    assert "TREASURY_MUTATION_REACHABLE=false" in shadow
    assert "TREASURY_SEPARATION_GATE_WIRED=true" in shadow


def test_capital_admission_runbook_slice_excludes_phase1() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    risk_section = runbook.split("### Risiko, Budget, Intent und Ausführung\n", 1)[1].split(
        "\n## ", 1
    )[0]
    assert RISK_SIZING_OWNER == "capital_risk_admissibility_owner_v1"
    assert "../../../src/governance/capital_risk_sizing_v1.py" in risk_section
    assert "../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py" in risk_section
    assert "treasury_phase_1_offline_contracts_v1" not in risk_section.lower()
    assert (
        phase_1_no_authority_proof_v1()["TREASURY_PHASE_1_CAN_MINT_RISK_ADMISSIBLE_CAPITAL"]
        is False
    )
