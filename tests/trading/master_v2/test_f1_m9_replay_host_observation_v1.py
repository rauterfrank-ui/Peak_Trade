import json
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType

import pytest

from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
    _canonical_seam,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _market_context,
    _replay_input,
)
from trading.master_v2 import double_play_old_effective_host_contract_v1 as host_contract
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import (
    read_f1_m9_replay_host_observation_v1,
    run_and_write_f1_m9_replay_host_observation_v1,
    verify_evidence_manifest_v1,
    write_integrated_offline_replay_evidence_bundle_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

ROOT = Path(__file__).resolve().parents[3]
_OBSERVATION = "f1_m9_replay_host_observation.json"


def _input(seam, *, hour, minute):
    estimate = build_canonical_volatility_estimate_v1(
        value=0.004321,
        observation_count=61,
        as_of_event_time=datetime(2026, 6, 30, hour, minute, tzinfo=timezone.utc),
        fallback_used=False,
        source_digest="b" * 64,
    )
    context = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        _market_context(volatility_estimate=0.0), estimate
    )
    return _replay_input(
        canonical_market_context=context,
        require_productive_typed_volatility_presence_gate=True,
        productive_typed_volatility_binding_eligibility=evaluate_typed_volatility_binding_eligibility_v1(
            context
        ),
        governed_authorized_productive_parameter_seam_record=MappingProxyType(seam),
    )


def test_real_replay_exports_effective_alpha_and_preserves_original_evidence(tmp_path):
    seam = _canonical_seam(tmp_path)
    replay_input = _input(seam, hour=10, minute=0)
    assert host_contract.integrated_replay_presence_alpha_at_dp_boundary_v1() is True
    default_result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    default_manifest = write_integrated_offline_replay_evidence_bundle_v1(
        out_dir=tmp_path / "default", replay_input=replay_input, replay_result=default_result
    )
    manifest, digest = run_and_write_f1_m9_replay_host_observation_v1(
        out_dir=tmp_path / "observed", replay_input=replay_input
    )
    record = read_f1_m9_replay_host_observation_v1(
        manifest_path=manifest, expected_manifest_sha256=digest
    )
    observation = record["observation"]
    assert observation["configuration_digest"] == seam["configuration_digest"]
    assert observation["seam_digest"] == seam["seam_digest"]
    assert (
        observation["owner_threshold_record_digest"] == seam["threshold_value_authorization_digest"]
    )
    assert observation["configuration_runtime_applied"] is True
    assert observation["threshold_seconds"] == 600.0
    assert observation["estimate_age_seconds"] == 7200.0
    assert observation["typed_estimate_present"] is True
    assert observation["presence_alpha_allowed"] is True
    assert observation["local_enforcement_applied"] is True
    assert observation["local_alpha_allowed"] is False
    assert "ALPHA_BLOCKED_BY_BOUNDED_MAX_AGE_ENFORCEMENT" in observation["local_reason_codes"]
    assert observation["host_uses_presence_alpha"] is True
    assert observation["effective_host_alpha_allowed"] is True
    assert observation["host_compatibility_reasons"] == [
        host_contract.REASON_PRESENCE_ALPHA_AT_DP_BOUNDARY
    ]
    assert record["post_gate_pipeline_observed"] is True
    assert record["decision_evidence_digest"] == default_result.evidence.semantic_digest
    assert record["decision_outcome"] == default_result.evidence.decision_outcome == "no_action"
    assert record["execution_eligible"] is False
    assert record["authority"] == "NONE"

    default_files = {path.name: path.read_bytes() for path in default_manifest.parent.iterdir()}
    observed_files = {path.name: path.read_bytes() for path in manifest.parent.iterdir()}
    assert _OBSERVATION not in default_files
    assert set(observed_files) == set(default_files) | {_OBSERVATION}
    assert all(
        observed_files[name] == data
        for name, data in default_files.items()
        if name != "MANIFEST.sha256"
    )
    assert verify_evidence_manifest_v1(manifest) == 0

    code = """
import json, sys
from pathlib import Path
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import read_f1_m9_replay_host_observation_v1
print(json.dumps(read_f1_m9_replay_host_observation_v1(
    manifest_path=Path(sys.argv[1]), expected_manifest_sha256=sys.argv[2]
)))
"""
    cold = subprocess.run(
        ["./scripts/pt", "-c", code, str(manifest), digest],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    assert json.loads(cold.stdout.splitlines()[-1]) == record
    with pytest.raises(FileExistsError):
        run_and_write_f1_m9_replay_host_observation_v1(
            out_dir=manifest.parent, replay_input=replay_input
        )
    assert {path.name: path.read_bytes() for path in manifest.parent.iterdir()} == observed_files
    (manifest.parent / _OBSERVATION).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="F1_M9_REPLAY_HOST_ARTIFACT_DIGEST_MISMATCH"):
        read_f1_m9_replay_host_observation_v1(
            manifest_path=manifest, expected_manifest_sha256=digest
        )


def test_fresh_and_blocked_replay_keep_separate_host_dispositions(tmp_path, monkeypatch):
    seam = _canonical_seam(tmp_path)
    fresh = _input(seam, hour=11, minute=55)
    manifest, digest = run_and_write_f1_m9_replay_host_observation_v1(
        out_dir=tmp_path / "fresh", replay_input=fresh
    )
    record = read_f1_m9_replay_host_observation_v1(
        manifest_path=manifest, expected_manifest_sha256=digest
    )
    assert record["observation"]["estimate_age_seconds"] == 300.0
    assert record["observation"]["local_alpha_allowed"] is True
    assert record["observation"]["host_uses_presence_alpha"] is True
    assert record["observation"]["effective_host_alpha_allowed"] is True
    assert record["observation"]["host_compatibility_reasons"] == []

    monkeypatch.setattr(
        host_contract, "integrated_replay_presence_alpha_at_dp_boundary_v1", lambda **_kwargs: False
    )
    stale = _input(seam, hour=10, minute=0)
    manifest, digest = run_and_write_f1_m9_replay_host_observation_v1(
        out_dir=tmp_path / "blocked", replay_input=stale
    )
    record = read_f1_m9_replay_host_observation_v1(
        manifest_path=manifest, expected_manifest_sha256=digest
    )
    assert record["observation"]["typed_estimate_present"] is True
    assert record["observation"]["presence_alpha_allowed"] is True
    assert record["observation"]["local_alpha_allowed"] is False
    assert record["observation"]["host_uses_presence_alpha"] is False
    assert record["observation"]["effective_host_alpha_allowed"] is False
    assert record["post_gate_pipeline_observed"] is False
    assert record["replay_pass"] is False
    assert record["decision_outcome"] == "blocked"
    assert record["execution_eligible"] is False

    absent = tmp_path / "absent"
    with pytest.raises(ValueError, match="F1_M9_REPLAY_HOST_DECISION_NOT_OBSERVED"):
        run_and_write_f1_m9_replay_host_observation_v1(
            out_dir=absent,
            replay_input=replace(stale, require_productive_typed_volatility_presence_gate=False),
        )
    assert not absent.exists()
