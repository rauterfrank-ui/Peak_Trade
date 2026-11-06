"""Tests for bounded-pilot operator preflight packet CLI (read-only orchestration)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def _passing_readiness_bundle() -> tuple[bool, dict]:
    return True, {
        "contract": "bounded_pilot_readiness_v1",
        "ok": True,
        "blocked_at": None,
        "message": "ok",
    }


def _green_stop_snapshot() -> dict:
    return {
        "contract": "operator_stop_signal_snapshot_v1",
        "incident_stop_artifact": {"status": "none", "path": None, "parsed": None, "error": None},
        "kill_switch_file": {
            "status": "unavailable",
            "path": "data/kill_switch/state.json",
            "kill_switch_active": None,
            "state": None,
        },
        "consistency_notes": [],
    }


def test_build_packet_green(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 0
    assert packet["contract"] == mod.CONTRACT_ID
    assert packet["summary"]["packet_ok"] is True
    assert packet["summary"]["readiness_ok"] is True
    assert packet["summary"]["stop_snapshot_ok"] is True
    assert packet["bounded_pilot_readiness"]["ok"] is True
    assert packet["stop_signal_snapshot"]["contract"] == "operator_stop_signal_snapshot_v1"
    assert "metadata" in packet
    assert "generated_at_utc" in packet["metadata"]


def test_build_packet_blocked_on_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            False,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "blocked_at": "live_readiness",
                "message": "live readiness failed (1 check(s))",
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 1
    assert packet["summary"]["packet_ok"] is False
    assert packet["summary"]["readiness_ok"] is False
    assert packet["stop_signal_snapshot"] is not None
    assert any("bounded_pilot_readiness" in b for b in (packet["summary"]["blocked"] or []))


def test_build_packet_blocked_on_stop_signal_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )

    def _bad_snapshot(repo: Path) -> dict:
        s = _green_stop_snapshot()
        s["kill_switch_file"] = {
            "status": "error",
            "path": "data/kill_switch/state.json",
            "kill_switch_active": None,
            "state": None,
            "error": "invalid json",
        }
        return s

    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        _bad_snapshot,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 1
    assert packet["summary"]["readiness_ok"] is True
    assert packet["summary"]["stop_snapshot_ok"] is False
    assert packet["summary"]["packet_ok"] is False
    assert any("kill_switch_file" in b for b in (packet["summary"]["blocked"] or []))


def test_build_packet_exit_2_on_stop_snapshot_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )

    def _boom(repo: Path) -> dict:
        raise RuntimeError("snapshot boom")

    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        _boom,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 2
    assert packet["summary"]["packet_ok"] is False
    assert packet["stop_signal_snapshot"].get("orchestrator_error") == "snapshot boom"


def test_build_packet_exit_2_on_readiness_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    def _boom_readiness(*a, **k):
        raise RuntimeError("readiness boom")

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        _boom_readiness,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 2
    assert packet["bounded_pilot_readiness"].get("orchestrator_error") == "readiness boom"
    assert packet["stop_signal_snapshot"] is None


def test_main_json_green(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["bounded_pilot_operator_preflight_packet", "--json", "--repo-root", str(ROOT)],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["contract"] == mod.CONTRACT_ID
    assert out["summary"]["packet_ok"] is True


def test_main_json_exit_2_invalid_repo_root_is_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    not_a_dir = tmp_path / "file_instead_of_dir.txt"
    not_a_dir.write_text("x", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bounded_pilot_operator_preflight_packet",
            "--json",
            "--repo-root",
            str(not_a_dir),
        ],
    )
    assert mod.main() == 2
    data = json.loads(capsys.readouterr().out.strip())
    assert data["contract"] == mod.CONTRACT_ID
    assert "not a directory" in str(data.get("error", ""))


def test_main_json_exit_2_when_build_packet_raises(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    def _outer_boom(*a, **k):
        raise RuntimeError("orchestrator outer failure")

    monkeypatch.setattr(mod, "build_operator_preflight_packet", _outer_boom)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bounded_pilot_operator_preflight_packet",
            "--json",
            "--repo-root",
            str(ROOT),
        ],
    )
    assert mod.main() == 2
    data = json.loads(capsys.readouterr().out.strip())
    assert data["contract"] == mod.CONTRACT_ID
    assert "orchestrator outer failure" in str(data.get("error", ""))


def _lifecycle_proof_fixtures():
    from tests.ops.test_check_bounded_pilot_readiness import _coherent_lifecycle_proof_fixtures

    return _coherent_lifecycle_proof_fixtures()


def test_build_packet_with_valid_lifecycle_static_proof_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, _, _, _ = _lifecycle_proof_fixtures()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            True,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": True,
                "blocked_at": None,
                "static_readiness_proof_coherent": True,
                "lifecycle_static_proof": {
                    "composition_mode": (
                        "bounded_pilot_readiness_lifecycle_static_proof_composition_v0"
                    ),
                    "composition_pass": True,
                    "fail_reasons": [],
                },
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )

    packet, code = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        run_tests=False,
        lifecycle_static_proof=composition_input,
    )
    assert code == 0
    handoff = packet["lifecycle_static_proof_handoff"]
    assert handoff["handoff_pass"] is True
    assert handoff["proof_status"] == packet_mod.PROOF_STATUS_VALID
    assert handoff["blocker_state"] == "blocked"
    assert packet["packet_identity"]
    assert packet["packet_digest"]
    assert packet["summary"]["lifecycle_static_proof_handoff_ok"] is True


def test_build_packet_missing_lifecycle_proof_identity_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, binding, _, _ = _lifecycle_proof_fixtures()
    bad_binding = replace(binding, pe32_proof_identity="")
    bad = replace(composition_input, binding=bad_binding)
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            False,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "blocked_at": "lifecycle_static_proof",
                "static_readiness_proof_coherent": False,
                "lifecycle_static_proof": {
                    "composition_pass": False,
                    "fail_reasons": ["binding: pe32_proof_identity required"],
                },
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    packet, code = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=bad,
    )
    assert code == 1
    assert packet["summary"]["packet_ok"] is False
    assert (
        packet["lifecycle_static_proof_handoff"]["proof_status"] == packet_mod.PROOF_STATUS_REJECTED
    )


def test_build_packet_injected_binding_drift_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import replace

    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, _, _, _ = _lifecycle_proof_fixtures()
    composition = {
        "composition_mode": "bounded_pilot_readiness_lifecycle_static_proof_composition_v0",
        "composition_pass": True,
        "fail_reasons": [],
    }
    expected = packet_mod.build_lifecycle_static_proof_handoff_binding(
        composition_input, composition
    )
    drifted = replace(expected, pe32_proof_digest="f" * 64)
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            True,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": True,
                "static_readiness_proof_coherent": True,
                "lifecycle_static_proof": composition,
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    packet, code = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
        lifecycle_static_proof_handoff_binding=drifted,
    )
    assert code == 1
    assert packet["lifecycle_static_proof_handoff"]["handoff_pass"] is False
    assert any(
        "pe32_proof_digest mismatch" in r
        for r in packet["lifecycle_static_proof_handoff"]["fail_reasons"]
    )


def test_build_packet_unknown_extra_fields_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, _, _, _ = _lifecycle_proof_fixtures()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            False,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "blocked_at": "lifecycle_static_proof",
                "lifecycle_static_proof": {
                    "composition_pass": False,
                    "fail_reasons": ["unknown extra field: unexpected_field"],
                },
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    packet, code = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
        lifecycle_handoff_extra_fields={"unexpected_field": "value"},
    )
    assert code == 1
    assert packet["summary"]["packet_ok"] is False


def test_build_packet_forbidden_secret_field_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, _, _, _ = _lifecycle_proof_fixtures()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (False, {"contract": "bounded_pilot_readiness_v1", "ok": False}),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    packet, code = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
        lifecycle_handoff_extra_fields={"api_key": "secret"},
    )
    assert code == 1
    assert any("lifecycle_static_proof_handoff" in b for b in packet["summary"]["blocked"])


def test_packet_identity_and_digest_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod

    composition_input, _, _, _, _, _ = _lifecycle_proof_fixtures()
    composition = {
        "composition_mode": "bounded_pilot_readiness_lifecycle_static_proof_composition_v0",
        "composition_pass": True,
        "fail_reasons": [],
    }

    def _readiness(*a, **k):
        return (
            True,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": True,
                "static_readiness_proof_coherent": True,
                "lifecycle_static_proof": composition,
            },
        )

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        _readiness,
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    left, _ = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
    )
    right, _ = packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
    )
    assert left["packet_identity"] == right["packet_identity"]
    assert left["packet_digest"] == right["packet_digest"]
    assert (
        left["lifecycle_static_proof_handoff"]["lifecycle_static_proof_identity"]
        == right["lifecycle_static_proof_handoff"]["lifecycle_static_proof_identity"]
    )


def test_build_packet_does_not_mutate_lifecycle_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as packet_mod
    from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
        serialize_assembly_input_canonical,
    )
    from src.ops.bounded_futures_testnet_readiness_decision_lifecycle_integration_contract_v0 import (
        serialize_integration_input_canonical,
    )

    composition_input, pe32_input, pe26_input, _, _, _ = _lifecycle_proof_fixtures()
    pe32_before = serialize_integration_input_canonical(pe32_input)
    pe26_before = serialize_assembly_input_canonical(pe26_input)
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            True,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": True,
                "static_readiness_proof_coherent": True,
                "lifecycle_static_proof": {"composition_pass": True, "fail_reasons": []},
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    packet_mod.build_operator_preflight_packet(
        ROOT,
        ROOT / "config" / "config.toml",
        lifecycle_static_proof=composition_input,
    )
    assert serialize_integration_input_canonical(pe32_input) == pe32_before
    assert serialize_assembly_input_canonical(pe26_input) == pe26_before
