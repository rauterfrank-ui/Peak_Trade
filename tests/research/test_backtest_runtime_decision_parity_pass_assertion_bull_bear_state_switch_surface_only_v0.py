from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.research.bull_bear_state_switch_narrow_reuse_first_rewire_v0 import (
    evaluate_bull_bear_parity_fixtures_v0,
)
from src.research.owner_bindings.bull_bear_state_switch_owner_binding_v0 import (
    build_bull_bear_state_switch_owner_binding_v0,
)
from trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0 import (
    mirrored_side_states_parity_ok_v0,
    state_switch_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    evaluate_scenario_state_switch_for_fixture_v0,
    extract_state_switch_parity_envelope_v0,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "docs/research/backtest_runtime_decision_parity_pass_assertion_bull_bear_state_switch_surface_only_v0.json"
)
ASSESSMENT_CONTRACT = (
    ROOT
    / "docs/research/bull_bear_state_switch_backtest_parity_wiring_assessment_or_narrow_rewire_v0.json"
)
NO_REWIRE_CONTRACT = (
    ROOT / "docs/research/bull_bear_state_switch_backtest_parity_narrow_rewire_v0.json"
)
BACKTEST_CONSUMER = ROOT / "src/trading/master_v2/offline_double_play_scenario_replay_v0.py"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_contract_declares_surface_only_parity_pass() -> None:
    data = load_contract()
    assert (
        data["assertion_id"]
        == "BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_BULL_BEAR_STATE_SWITCH_SURFACE_ONLY_V0"
    )
    assert data["assertion_scope"] == "BULL_BEAR_STATE_SWITCH_SURFACE_ONLY"
    assert data["BULL_BEAR_STATE_SWITCH_BACKTEST_PARITY_PASS"] is True
    assert (
        data["BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_SCOPE"]
        == "BULL_BEAR_STATE_SWITCH_SURFACE_ONLY"
    )
    assert (
        data["verdict"]
        == "PASS_BACKTEST_RUNTIME_DECISION_PARITY_PASS_ASSERTION_BULL_BEAR_STATE_SWITCH_SURFACE_ONLY_V0"
    )


def test_contract_preserves_whole_system_fail_closed_flags() -> None:
    data = load_contract()
    assert data["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert data["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert data["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert data["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert data["authority_effect"] == "NONE"
    assert data["runtime_effect"] == "NONE"
    assert data["futures_only"] is True
    assert data["bitcoin_direction_allowed"] is False


def test_contract_binds_required_evidence_references() -> None:
    data = load_contract()
    assessment = json.loads(ASSESSMENT_CONTRACT.read_text(encoding="utf-8"))
    no_rewire = json.loads(NO_REWIRE_CONTRACT.read_text(encoding="utf-8"))

    assert data["canonical_owner"] == "src/trading/master_v2"
    assert data["direct_reference_count"] == 20
    assert data["direct_reference_count"] == assessment["backtest_direct_reference_count"]
    assert data["assessment_source_pr"] == 5057
    assert data["no_rewire_review_source_pr"] == 5058
    assert data["no_rewire_classification"] == "REVIEW_NO_REWIRE_REQUIRED"
    assert data["no_rewire_classification"] == no_rewire["narrow_rewire_decision"]["classification"]
    assert (ROOT / data["owner_binding_contract_ref"]).is_file()
    assert (ROOT / data["assessment_contract_ref"]).is_file()
    assert (ROOT / data["no_rewire_review_contract_ref"]).is_file()
    assert all((ROOT / path).is_file() for path in data["backtest_consumer_paths"])
    assert all((ROOT / ref).is_file() for ref in data["deterministic_test_refs"])


def test_source_evidence_review_metadata_recorded_without_ci_archive_dependency() -> None:
    data = load_contract()
    no_rewire = json.loads(NO_REWIRE_CONTRACT.read_text(encoding="utf-8"))

    assert data["source_manifest_verify_rc"] == 0
    assert no_rewire["source_evidence_manifest_verify_rc"] == 0
    assert data["source_evidence_provenance_mode"] == "OPERATOR_DURABLE_ARCHIVE_REVIEW_TIME_ONLY"
    assert len(data["source_evidence_dirs"]) == 2
    assert set(data["source_manifest_digests"]) == {
        Path(evidence_dir).name for evidence_dir in data["source_evidence_dirs"]
    }
    for contract_ref in data["source_evidence_contract_refs"]:
        assert (ROOT / contract_ref).is_file()
    assert data["assessment_contract_ref"] in data["source_evidence_contract_refs"]
    assert data["no_rewire_review_contract_ref"] in data["source_evidence_contract_refs"]


def test_implementation_digests_match_origin_main_baseline() -> None:
    data = load_contract()
    for rel_path, expected_digest in data["implementation_digests"].items():
        actual = _sha256_file(ROOT / rel_path)
        assert actual == expected_digest, f"digest drift for {rel_path}"


def test_source_manifest_digests_are_stable_review_metadata() -> None:
    data = load_contract()
    for bundle_key, digest in data["source_manifest_digests"].items():
        assert bundle_key.endswith("Z")
        assert len(digest) == 64
        assert all(char in "0123456789abcdef" for char in digest)
        matching_dir = next(
            evidence_dir
            for evidence_dir in data["source_evidence_dirs"]
            if bundle_key in evidence_dir
        )
        assert matching_dir.endswith(bundle_key)


def test_owner_binding_aligns_with_canonical_owner() -> None:
    data = load_contract()
    binding = build_bull_bear_state_switch_owner_binding_v0()
    contract = binding.as_contract()

    assert contract["canonical_owner"] == data["canonical_owner"]
    assert "NO_PARALLEL_STATE_SWITCH_OWNER" in contract["required_parity_assertions"]


def test_backtest_consumer_routes_through_canonical_adapter() -> None:
    data = load_contract()
    replay_text = BACKTEST_CONSUMER.read_text(encoding="utf-8")

    assert "evaluate_scenario_state_switch_v0" in replay_text
    assert data["backtest_consumer_paths"][0].endswith("offline_double_play_scenario_replay_v0.py")
    for forbidden in ("def _bull_layer_state", "def _bear_layer_state", "def transition_state"):
        assert forbidden not in replay_text


def test_mirrored_bull_bear_behavior_and_bypass_exclusion() -> None:
    data = load_contract()
    bull_binding, bear_binding = evaluate_bull_bear_parity_fixtures_v0()

    assert bull_binding.side_state_after == SideState.LONG_ARMED
    assert bear_binding.side_state_after == SideState.SHORT_ARMED
    assert mirrored_side_states_parity_ok_v0(
        bull_binding.side_state_after,
        bear_binding.side_state_after,
    )
    for binding in (bull_binding, bear_binding):
        env = extract_state_switch_parity_envelope_v0(binding)
        assert env.state_switch_ref
        assert state_switch_binding_non_authority_boundary_ok_v0(binding)

    harness_binding = evaluate_scenario_state_switch_for_fixture_v0(
        side_state=SideState.NEUTRAL_OBSERVE,
        scope_event=ScopeEvent.UPSCOPE_CONFIRMED,
        instrument_id="SYNTH_FUTURES_BTCUSDT_PERP",
        trading_epoch=48,
        context_reference="surface-only-parity-assertion-v0",
    )
    assert harness_binding.side_state_after == SideState.LONG_ARMED
    assert state_switch_binding_non_authority_boundary_ok_v0(harness_binding)
    assert data["mirrored_behavior_verified"] is True
    assert data["bypass_authority_excluded"] is True


def test_next_parity_surface_is_scope_adverse_exit_assessment() -> None:
    data = load_contract()
    assert (
        data["next_parity_surface"]
        == "SCOPE_ADVERSE_EXIT_AND_REVERSAL_PREPARATION_BACKTEST_PARITY_WIRING_ASSESSMENT_OR_NARROW_REWIRE_V0"
    )


def test_limitations_and_non_claims_documented() -> None:
    data = load_contract()
    limitations = data["limitations_and_non_claims"]
    assert any("whole-system" in item for item in limitations)
    assert any("FULL_CANONICAL_CHAIN_WIRED" in item for item in limitations)
    assert any("reference count" in item for item in limitations)
