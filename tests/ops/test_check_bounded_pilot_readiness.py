"""Tests for scripts/ops/check_bounded_pilot_readiness.py — canonical bounded-pilot preflight."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def _passing_readiness_report() -> object:
    from scripts.check_live_readiness import CheckResult, ReadinessReport

    return ReadinessReport(
        stage="live",
        checks=[CheckResult("stub", True, "ok")],
        warnings=[],
    )


def test_run_bounded_pilot_readiness_green(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {"repo_root": str(ROOT)},
    )

    def _go(payload: dict) -> dict:
        return {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [{"row": 1, "area": "Safety Gates", "status": "PASS"}],
        }

    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        _go,
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is True
    assert bundle["contract"] == mod.CONTRACT_ID
    assert bundle["go_no_go"]["verdict"] == "GO_FOR_NEXT_PHASE_ONLY"
    assert bundle["live_readiness"]["all_passed"] is True


def test_run_bounded_pilot_readiness_blocks_on_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod
    from scripts.check_live_readiness import CheckResult, ReadinessReport

    bad = ReadinessReport(
        stage="live",
        checks=[
            CheckResult("API-Credentials", False, "Live-API-Keys fehlen"),
        ],
        warnings=[],
    )
    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: bad,
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["blocked_at"] == "live_readiness"
    assert "go_no_go" not in bundle


def test_run_bounded_pilot_readiness_blocks_on_go_no_go(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "NO_GO",
            "rows": [{"row": 6, "area": "Treasury Separation", "status": "FAIL"}],
        },
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["blocked_at"] == "go_no_go"
    assert bundle["go_no_go"]["verdict"] == "NO_GO"


def test_run_bounded_pilot_readiness_readiness_check_exception_is_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    def _boom(**kw: object) -> object:
        raise RuntimeError("readiness boom")

    monkeypatch.setattr("scripts.check_live_readiness.run_readiness_checks", _boom)

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["contract"] == mod.CONTRACT_ID
    assert bundle.get("ok") is False
    assert bundle["blocked_at"] == "live_readiness"
    assert "readiness evaluation error" in (bundle.get("message") or "")
    assert "readiness boom" in (bundle.get("message") or "")
    assert "go_no_go" not in bundle


def test_run_bounded_pilot_readiness_blocks_on_cockpit_payload_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )

    def _no_cockpit(**kw: object) -> object:
        raise OSError("cockpit down")

    monkeypatch.setattr("src.webui.ops_cockpit.build_ops_cockpit_payload", _no_cockpit)
    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["contract"] == mod.CONTRACT_ID
    assert bundle.get("ok") is False
    assert bundle["blocked_at"] == "cockpit_payload"
    assert "failed to build ops cockpit payload" in (bundle.get("message") or "")
    assert "cockpit down" in (bundle.get("message") or "")
    assert "go_no_go" not in bundle
    assert "live_readiness" in bundle  # partial summary for diagnostics


def test_main_json_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_bounded_pilot_readiness", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    )

    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(ROOT)])
    assert mod.main() == 0
    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["ok"] is True

    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "CONDITIONAL",
            "rows": [{"row": 1, "area": "Safety Gates", "status": "UNKNOWN"}],
        },
    )
    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(ROOT)])
    assert mod.main() == 1


def test_main_json_exit_2_on_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_bounded_pilot_readiness", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    def _boom(*a, **k):
        raise RuntimeError("orchestrated preflight failure")

    monkeypatch.setattr(mod, "run_bounded_pilot_readiness", _boom)
    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(ROOT)])
    assert mod.main() == 2
    data = json.loads(capsys.readouterr().out.strip())
    assert data["contract"] == mod.CONTRACT_ID
    assert data["ok"] is False
    assert "orchestrated preflight failure" in str(data.get("error", ""))


VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
SHARED_STATE_DIGEST = "a" * 64


def _coherent_lifecycle_proof_fixtures() -> tuple[object, object, object, object, dict, dict]:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
        evaluate_operator_closure_lifecycle_integration,
    )
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        CONTRACT_VERSION as PE26_CONTRACT_VERSION,
        Pe25OperatorClosureProofBinding as Pe26Pe25ProofBinding,
        compute_lifecycle_matrix_digest,
        default_minimal_assembly_input,
        evaluate_preflight_execution_readiness_assembly_lifecycle_integration,
    )
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        CONTRACT_VERSION as PE32_CONTRACT_VERSION,
        default_minimal_integration_input,
        evaluate_readiness_decision_lifecycle_integration,
    )

    adapter_id = "offline_bounded_futures_testnet_adapter_v0"
    matrix_digest = compute_lifecycle_matrix_digest()

    pe32_input = default_minimal_integration_input(
        source_revision=VALID_COMMIT_SHA,
        adapter_id=adapter_id,
        lifecycle_state_digest=SHARED_STATE_DIGEST,
    )
    pe25_input = pe32_input.pe25_operator_closure_integration_input
    pe25_result = evaluate_operator_closure_lifecycle_integration(pe25_input)
    pe25_closure_input_digest = pe25_result["closure_input_digest"]
    pe25_closure_result_digest = pe25_result["closure_result_digest"]

    pe26_input = default_minimal_assembly_input(
        source_revision=VALID_COMMIT_SHA,
        adapter_id=adapter_id,
        lifecycle_state_digest=SHARED_STATE_DIGEST,
    )
    pe26_pe25 = Pe26Pe25ProofBinding(
        closure_input_digest=pe25_closure_input_digest,
        closure_result_digest=pe25_closure_result_digest,
        pe25_integration_pass=True,
        operator_closure_static_complete=True,
        lifecycle_matrix_digest=matrix_digest,
    )
    pe26_input = replace(pe26_input, pe25_operator_closure_proof=pe26_pe25)

    pe32_result = evaluate_readiness_decision_lifecycle_integration(pe32_input)
    pe26_result = evaluate_preflight_execution_readiness_assembly_lifecycle_integration(pe26_input)

    binding = mod.LifecycleStaticProofCompositionBinding(
        source_revision=VALID_COMMIT_SHA,
        pe32_canonical_owner=PE32_CONTRACT_VERSION,
        pe32_proof_identity=pe32_input.integration_id,
        pe32_proof_digest=pe32_result["integration_proof_digest"],
        pe32_lifecycle_chain_identity=SHARED_STATE_DIGEST,
        pe32_blocker_state=mod.CANONICAL_BLOCKER_STATE,
        pe26_canonical_owner=PE26_CONTRACT_VERSION,
        pe26_assembly_identity=pe26_input.assembly_id,
        pe26_assembly_digest=pe26_result["assembly_result_digest"],
        pe26_source_revision=VALID_COMMIT_SHA,
        pe26_traceability_identity=pe26_input.pe37_traceability_proof.traceability_identity,
    )
    composition_input = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=pe32_input,
        pe26_assembly_input=pe26_input,
        binding=binding,
    )
    return composition_input, pe32_input, pe26_input, binding, pe32_result, pe26_result


def test_valid_pe32_pe26_composition_passes() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, _, _, _ = _coherent_lifecycle_proof_fixtures()
    result = mod.evaluate_lifecycle_static_proof_composition(composition_input)
    assert result["composition_pass"] is True
    assert result["static_readiness_proof_coherent"] is True
    assert result["preflight_remains_blocked"] is True
    assert result["authority_lift"] is False
    assert result["pilot_readiness_operationally_granted"] is False
    assert result["fail_reasons"] == []


def test_missing_pe32_proof_fails() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=None,
        pe26_assembly_input=pe26_input,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_integration_input required" in r for r in result["fail_reasons"])


def test_missing_pe26_proof_fails() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, pe32_input, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=pe32_input,
        pe26_assembly_input=None,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe26_assembly_input required" in r for r in result["fail_reasons"])


def test_missing_pe32_proof_identity_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, pe32_input, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_proof_identity="")
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_proof_identity required" in r for r in result["fail_reasons"])


def test_missing_pe26_assembly_identity_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe26_assembly_identity="")
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe26_assembly_identity required" in r for r in result["fail_reasons"])


def test_empty_proof_identity_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, pe32_input, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_pe32 = replace(pe32_input, integration_id="")
    bad_binding = replace(binding, pe32_proof_identity="")
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=bad_pe32,
        pe26_assembly_input=composition_input.pe26_assembly_input,
        binding=bad_binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False


def test_malformed_proof_digest_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_proof_digest="not-a-digest")
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_proof_digest must be 64-char" in r for r in result["fail_reasons"])


def test_pe32_proof_digest_mismatch_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_proof_digest="0" * 64)
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_proof_digest mismatch" in r for r in result["fail_reasons"])


def test_pe26_assembly_digest_mismatch_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe26_assembly_digest="1" * 64)
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe26_assembly_digest mismatch" in r for r in result["fail_reasons"])


def test_source_revision_mismatch_between_pe32_and_pe26_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, pe32_input, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    other_sha = "1234567890abcdef1234567890abcdef12345678"
    bad_pe26 = replace(pe26_input, source_revision=other_sha)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=pe32_input,
        pe26_assembly_input=bad_pe26,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("source_revision mismatch" in r for r in result["fail_reasons"])


def test_wrong_pe32_canonical_owner_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_canonical_owner="wrong.owner.v0")
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_canonical_owner mismatch" in r for r in result["fail_reasons"])


def test_wrong_pe26_canonical_owner_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe26_canonical_owner="wrong.owner.v0")
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe26_canonical_owner mismatch" in r for r in result["fail_reasons"])


def test_wrong_lifecycle_chain_binding_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_lifecycle_chain_identity="b" * 64)
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe32_lifecycle_chain_identity mismatch" in r for r in result["fail_reasons"])


def test_incomplete_pe32_lifecycle_chain_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, pe32_input, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_matrix = replace(
        pe32_input.lifecycle_matrix_proof,
        lifecycle_state_digest="c" * 64,
    )
    bad_pe32 = replace(pe32_input, lifecycle_matrix_proof=bad_matrix)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=bad_pe32,
        pe26_assembly_input=composition_input.pe26_assembly_input,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False


def test_missing_pe37_traceability_identity_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        Pe37TraceabilityProofBinding,
    )

    composition_input, _, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_pe37 = replace(pe26_input.pe37_traceability_proof, traceability_identity="")
    bad_pe26 = replace(pe26_input, pe37_traceability_proof=bad_pe37)
    bad_binding = replace(binding, pe26_traceability_identity="")
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=bad_pe26,
        binding=bad_binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("traceability_identity required" in r for r in result["fail_reasons"])


def test_pe37_traceability_mismatch_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe26_traceability_identity="d" * 64)
    bad = replace(composition_input, binding=bad_binding)
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("pe26_traceability_identity mismatch" in r for r in result["fail_reasons"])


def test_blocker_state_not_canonically_blocked_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        BlockerSnapshotEntry,
    )

    composition_input, pe32_input, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    snapshot = pe32_input.blocker_register_snapshot
    lifted_entry = replace(snapshot.entries[0], blocker_state="LIFTED")
    bad_snapshot = replace(snapshot, entries=(lifted_entry,) + snapshot.entries[1:])
    bad_pe32 = replace(pe32_input, blocker_register_snapshot=bad_snapshot)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=bad_pe32,
        pe26_assembly_input=composition_input.pe26_assembly_input,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("must be BLOCKED" in r for r in result["fail_reasons"])


def test_stale_pe37_traceability_proof_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        HANDOFF_STATE_STALE,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        default_minimal_pe35_proof_binding,
    )

    composition_input, _, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    broken_pe35 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_STALE,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    bad_boundary = replace(
        pe26_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    bad_pe26 = replace(pe26_input, pe37_traceability_boundary_input=bad_boundary)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=bad_pe26,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False


def test_revoked_pe37_traceability_proof_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        HANDOFF_STATE_REVOKED,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        default_minimal_pe35_proof_binding,
    )

    composition_input, _, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    broken_pe35 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_REVOKED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    bad_boundary = replace(
        pe26_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    bad_pe26 = replace(pe26_input, pe37_traceability_boundary_input=bad_boundary)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=bad_pe26,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False


def test_superseded_pe37_traceability_proof_fails() -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
        HANDOFF_STATE_SUPERSEDED,
    )
    from src.ops.bounded_futures_testnet_operator_review_admission_presentation_boundary_contract_v0 import (
        default_minimal_pe35_proof_binding,
    )

    composition_input, _, pe26_input, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    broken_pe35 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input,
        lifecycle_metadata=replace(
            pe26_input.pe37_traceability_boundary_input.pe36_boundary_input.pe35_boundary_input.lifecycle_metadata,
            lifecycle_state=HANDOFF_STATE_SUPERSEDED,
        ),
    )
    broken_pe35_proof = default_minimal_pe35_proof_binding(broken_pe35)
    broken_pe36 = replace(
        pe26_input.pe37_traceability_boundary_input.pe36_boundary_input,
        pe35_boundary_input=broken_pe35,
        pe35_proof=broken_pe35_proof,
    )
    bad_boundary = replace(
        pe26_input.pe37_traceability_boundary_input,
        pe36_boundary_input=broken_pe36,
    )
    bad_pe26 = replace(pe26_input, pe37_traceability_boundary_input=bad_boundary)
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=bad_pe26,
        binding=binding,
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False


def test_pe37_traceability_replay_fails() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        evaluate_durable_evidence_traceability_boundary,
    )

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    baseline = evaluate_durable_evidence_traceability_boundary(
        composition_input.pe26_assembly_input.pe37_traceability_boundary_input
    )
    assert baseline["traceability_identity"] is not None
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=composition_input.pe26_assembly_input,
        binding=binding,
        bound_traceability_identities=(baseline["traceability_identity"],),
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("replay" in r for r in result["fail_reasons"])


def test_duplicate_pe37_admission_identity_fails() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
        evaluate_durable_evidence_traceability_boundary,
    )

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    baseline = evaluate_durable_evidence_traceability_boundary(
        composition_input.pe26_assembly_input.pe37_traceability_boundary_input
    )
    assert baseline["admission_identity"] is not None
    bad = mod.LifecycleStaticProofCompositionInput(
        pe32_integration_input=composition_input.pe32_integration_input,
        pe26_assembly_input=composition_input.pe26_assembly_input,
        binding=binding,
        bound_admission_identities=(baseline["admission_identity"],),
    )
    result = mod.evaluate_lifecycle_static_proof_composition(bad)
    assert result["composition_pass"] is False
    assert any("duplicate admission" in r for r in result["fail_reasons"])


def test_unknown_extra_fields_fail() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, _, _, _ = _coherent_lifecycle_proof_fixtures()
    result = mod.evaluate_lifecycle_static_proof_composition(
        composition_input,
        extra_fields={"unexpected_field": "value"},
    )
    assert result["composition_pass"] is False
    assert any("unknown extra field" in r for r in result["fail_reasons"])


def test_secret_credential_command_action_fields_fail() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, _, _, _ = _coherent_lifecycle_proof_fixtures()
    result = mod.evaluate_lifecycle_static_proof_composition(
        composition_input,
        extra_fields={"api_key": "secret-value", "operator_decision": True},
    )
    assert result["composition_pass"] is False
    assert any("forbidden extra field" in r for r in result["fail_reasons"])


def test_composition_deterministic_output() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, _, _, _ = _coherent_lifecycle_proof_fixtures()
    left = mod.evaluate_lifecycle_static_proof_composition(composition_input)
    right = mod.evaluate_lifecycle_static_proof_composition(composition_input)
    assert left == right


def test_composition_does_not_mutate_inputs() -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        serialize_assembly_input_canonical,
    )
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        serialize_integration_input_canonical,
    )

    composition_input, pe32_input, pe26_input, _, _, _ = _coherent_lifecycle_proof_fixtures()
    pe32_before = serialize_integration_input_canonical(pe32_input)
    pe26_before = serialize_assembly_input_canonical(pe26_input)
    mod.evaluate_lifecycle_static_proof_composition(composition_input)
    assert serialize_integration_input_canonical(pe32_input) == pe32_before
    assert serialize_assembly_input_canonical(pe26_input) == pe26_before


def test_existing_valid_preflight_cases_remain_valid_without_lifecycle_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {"repo_root": str(ROOT)},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    )
    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is True
    assert bundle["static_readiness_proof_coherent"] is None


def test_run_bounded_pilot_readiness_blocks_on_invalid_lifecycle_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, binding, _, _ = _coherent_lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_proof_digest="0" * 64)
    bad = replace(composition_input, binding=bad_binding)

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {"repo_root": str(ROOT)},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT,
        ROOT / "config" / "config.toml",
        run_tests=False,
        lifecycle_static_proof=bad,
    )
    assert ok is False
    assert bundle["blocked_at"] == "lifecycle_static_proof"
    assert bundle["static_readiness_proof_coherent"] is False


def test_run_bounded_pilot_readiness_with_valid_lifecycle_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    composition_input, _, _, _, _, _ = _coherent_lifecycle_proof_fixtures()

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {"repo_root": str(ROOT)},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT,
        ROOT / "config" / "config.toml",
        run_tests=False,
        lifecycle_static_proof=composition_input,
    )
    assert ok is True
    assert bundle["static_readiness_proof_coherent"] is True
    assert bundle["lifecycle_static_proof"]["composition_pass"] is True
    assert bundle["lifecycle_static_proof"]["preflight_remains_blocked"] is True
