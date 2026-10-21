"""Ten prepared parents and thirty instrument identities. No invented evidence."""

from __future__ import annotations

import inspect
from pathlib import Path

from scripts.ops.generic_ghosv_kernel_v1.observe_v1 import run_generic_ghosv_v1
from scripts.ops.guardian_instrument_binding_v1 import bind_v1 as binding
from scripts.ops.guardian_instrument_binding_v1.bind_v1 import bind_domain_instrument_v1
from scripts.ops.guardian_parent_preparation_v1.prepare_v1 import prepare_parent_guardians_v1
from scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1 import run_scoped_causal_graph_v1
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1

_REPO = Path(__file__).resolve().parents[2]
_FORBIDDEN = (
    "execution_guardian_binding_verifier_v1",
    "ghosv_bounded_context_v1",
    "ghosv_master_v2_bounded_context_v1",
    "double_play_ghosv_observation_adapter_v1",
)


def test_ten_parents_and_thirty_instruments_are_prepared_and_disabled() -> None:
    prepared = prepare_parent_guardians_v1()

    assert prepared["status"] == "ACCEPTED"
    assert prepared["parent_count"] == 10
    assert prepared["instrument_count"] == 30
    assert prepared["sub_guardian_count"] == 0
    assert prepared["gcc_role"] == "COORDINATION_ONLY"
    assert prepared["trading_authority"] == "NONE"
    assert prepared["safety_authority"] == "NONE"
    assert prepared["post_authority"] == "NONE"
    identities: list[str] = []
    displays: list[str] = []
    for parent in prepared["parents"]:
        assert parent["activation"] == "DISABLED"
        assert parent["authority"] == "NONE"
        assert parent["guardian_ratified"] is False
        assert parent["technical_state"] == "TECHNICALLY_PREPARED"
        assert parent["domain_bound"] is False
        assert parent["domain_calibrated"] is False
        assert parent["current_validated"] is False
        assert parent["operationally_ready"] is False
        assert parent["domain_boundary"]
        types = {item["instrument_type"] for item in parent["instruments"]}
        assert types == {"DOMAIN_GHV", "DOMAIN_CURRENT_CAUSAL_GRAPH", "DOMAIN_GHOSV"}
        for item in parent["instruments"]:
            identities.append(item["instrument_id"])
            displays.append(item["display_name"])
            assert item["parent_id"] == parent["parent_id"]
            assert item["instrument_id"].startswith(parent["parent_id"])
            assert item["activation"] == "DISABLED"
            assert item["authority"] == "NONE"
            assert item["post_authority"] == "NONE"
            assert item["coverage"]["coverage_proof"] is False
            assert item["coverage"]["coverage_gap"] is True
            assert item["current_validated"] is False
            assert item["operationally_ready"] is False
            if parent["parent_id"] == "PARENT_OPTIMIZATION":
                assert item["evidence_status"] == "PROVISIONAL_SCOPE_PRESENT"
                assert item["scope"]["unresolved"] == [
                    "canonical_optimization_experiment_evidence_v1"
                ]
            else:
                assert item["evidence_status"] == "MISSING"
                assert item["coverage"]["reachability"] == "NOT_EVIDENCED"
                assert all(item["scope"][field] == [] for field in item["scope"])
    assert len(identities) == len(set(identities)) == 30
    assert len(displays) == len(set(displays)) == 30


def test_preparation_does_not_import_execution_or_double_play_observers() -> None:
    paths = [
        _REPO / "scripts/ops/guardian_parent_preparation_v1/prepare_v1.py",
        _REPO / "scripts/ops/guardian_instrument_contract_v1/contract_v1.py",
        _REPO / "scripts/ops/guardian_parent_slot_loader_v1/load_v1.py",
        _REPO / "scripts/ops/guardian_instrument_binding_v1/bind_v1.py",
    ]
    imports = [
        line
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("import ") or line.startswith("from ")
    ]
    for banned in _FORBIDDEN:
        assert all(banned not in line for line in imports)


def test_generic_adapters_have_no_instrument_identity_parameter() -> None:
    for adapter in (run_scoped_ghv_v1, run_scoped_causal_graph_v1, run_generic_ghosv_v1):
        assert "instrument_id" not in inspect.signature(adapter).parameters


def test_missing_domain_evidence_does_not_call_an_adapter(monkeypatch) -> None:
    def _forbidden(**_kwargs: object) -> dict[str, str]:
        raise AssertionError("adapter must not run without domain evidence")

    monkeypatch.setattr(binding, "run_scoped_ghv_v1", _forbidden)
    result = bind_domain_instrument_v1(
        instrument_id="PARENT_CAPITAL_GHV",
        requested_instrument_type="DOMAIN_GHV",
        adapter_kwargs={},
    )

    assert result["status"] == "MISSING_DOMAIN_EVIDENCE"
    assert result["adapter_invoked"] is False
    assert result["instrument_bound"] is False
    assert result["technical_state"] == "TECHNICALLY_PREPARED"
    assert result["domain_calibrated"] is False
    assert result["current_validated"] is False
    assert result["operationally_ready"] is False
    assert result["coverage_gap"] is True


def test_instrument_type_mismatch_does_not_substitute_another_adapter(monkeypatch) -> None:
    def _forbidden(**_kwargs: object) -> dict[str, str]:
        raise AssertionError("mismatched adapter must not run")

    monkeypatch.setattr(binding, "run_generic_ghosv_v1", _forbidden)
    result = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHV",
        requested_instrument_type="DOMAIN_GHOSV",
        adapter_kwargs={},
    )

    assert result["status"] == "INSTRUMENT_TYPE_MISMATCH"
    assert result["adapter_invoked"] is False
    assert result["instrument_bound"] is False


def test_activation_and_ratification_are_rejected_before_the_adapter(monkeypatch) -> None:
    def _forbidden(**_kwargs: object) -> dict[str, str]:
        raise AssertionError("rejected control must not call the adapter")

    monkeypatch.setattr(binding, "run_scoped_ghv_v1", _forbidden)
    active = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHV",
        requested_instrument_type="DOMAIN_GHV",
        adapter_kwargs={"activation": "ACTIVE"},
    )
    ratified = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHOSV",
        requested_instrument_type="DOMAIN_GHOSV",
        adapter_kwargs={"guardian_ratified": True},
    )

    assert active["status"] == "REJECTED"
    assert "activation_rejected" in active["reasons"]
    assert ratified["status"] == "REJECTED"
    assert "ratification_rejected" in ratified["reasons"]


def test_optimization_ghosv_id_binds_only_its_adapter(monkeypatch) -> None:
    def _ghosv(**_kwargs: object) -> dict[str, object]:
        return {"status": "ACCEPTED", "observation_proof": False, "authority": "NONE"}

    def _forbidden(**_kwargs: object) -> dict[str, str]:
        raise AssertionError("GHV adapter must not serve the GHOSV identity")

    monkeypatch.setattr(binding, "run_generic_ghosv_v1", _ghosv)
    monkeypatch.setattr(binding, "run_scoped_ghv_v1", _forbidden)
    result = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHOSV",
        requested_instrument_type="DOMAIN_GHOSV",
        adapter_kwargs={"findings": [], "evidence_refs": []},
    )

    assert result["status"] == "ACCEPTED"
    assert result["instrument_id"] == "PARENT_OPTIMIZATION_GHOSV"
    assert result["instrument_bound"] is True
    assert result["domain_bound"] is True
    assert result["technical_state"] == "DOMAIN_BOUND"
    assert result["domain_calibrated"] is False
    assert result["current_validated"] is False
    assert result["operationally_ready"] is False
    assert result["causal_closure_proven"] is False
