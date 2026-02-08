"""
LayerEnvelope boundary object: contract tests and L3 runner integration.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ai_orchestration.capability_scope_loader import CapabilityScopeLoader
from src.ai_orchestration.layer_envelope import (
    LayerEnvelopeViolation,
    build_layer_envelope,
)
from src.ai_orchestration.l3_runner import L3Runner, L3RunnerError


def test_build_layer_envelope_uses_scope_tooling_allowlist_files_only_for_l3(
    tmp_path: Path,
) -> None:
    scope = CapabilityScopeLoader().load("L3")
    env = build_layer_envelope(
        layer_id="L3",
        inputs={"run_id": "x", "ts_ms": 0, "artifacts": []},
        tooling_allowlist=scope.tooling_allowed,
    )
    assert env.layer_id == "L3"
    assert env.tooling_allowlist == ["files"]
    assert env.learnable_surfaces == []


def test_build_layer_envelope_rejects_empty_tooling_allowlist() -> None:
    with pytest.raises(LayerEnvelopeViolation):
        build_layer_envelope(
            layer_id="L3",
            inputs={"run_id": "x", "ts_ms": 0, "artifacts": []},
            tooling_allowlist=[],
        )


def test_l3_runner_accepts_envelope_inputs_without_learnable_key(tmp_path: Path) -> None:
    scope = CapabilityScopeLoader().load("L3")
    env = build_layer_envelope(
        layer_id="L3",
        inputs={"run_id": "x", "ts_ms": 0, "artifacts": []},
        tooling_allowlist=scope.tooling_allowed,
    )
    out_dir = tmp_path / "l3_out"
    res = L3Runner().run(inputs=env.inputs, out_dir=out_dir, mode="dry-run")
    assert res.run_id.startswith("L3-")
    assert (out_dir / "run_manifest.json").exists()
    assert (out_dir / "operator_output.md").exists()


def test_l3_runner_rejects_disallowed_learnable_surfaces_via_inputs(
    tmp_path: Path,
) -> None:
    inputs = {
        "run_id": "x",
        "ts_ms": 0,
        "artifacts": [],
        "learnable_surfaces": ["scenario_priors"],
    }
    with pytest.raises(L3RunnerError) as e:
        L3Runner().run(inputs=inputs, out_dir=tmp_path / "l3_out", mode="dry-run")
    assert "Learnable surfaces gate" in str(e.value)


def test_envelope_to_dict_is_json_stable(tmp_path: Path) -> None:
    scope = CapabilityScopeLoader().load("L3")
    env = build_layer_envelope(
        layer_id="L3",
        inputs={"run_id": "x", "ts_ms": 0, "artifacts": []},
        tooling_allowlist=scope.tooling_allowed,
    )
    a = json.dumps(env.to_dict(), sort_keys=True)
    b = json.dumps(env.to_dict(), sort_keys=True)
    assert a == b
