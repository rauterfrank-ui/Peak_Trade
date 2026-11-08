"""Fresh manifest-verified unit evidence, isolated from dated archive availability."""

import hashlib
import json
from pathlib import Path

import pytest

from trading.master_v2 import surface_p_final_flags_fail_closed_contract_v0 as flags


@pytest.fixture
def verified_current_parity_manifest_v1(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[3]
    paths = (
        "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py",
        "src/trading/master_v2/canonical_order_intent_offline_replay_binding_adapter_v0.py",
        "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    )
    directory = tmp_path / "explicit-current-unit-evidence"
    directory.mkdir()
    record = directory / "synthetic-current-source-binding.json"
    record.write_text(
        json.dumps(
            {
                "scope": "SYNTHETIC_UNIT_EVIDENCE_ONLY",
                "authority": "NONE",
                "runtime_authorization_effect": "NONE",
                "source_sha256": {
                    p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths
                },
            },
            sort_keys=True,
        )
        + "\n"
    )
    (directory / "MANIFEST.sha256").write_text(
        hashlib.sha256(record.read_bytes()).hexdigest() + "  " + record.name + "\n"
    )
    # Exercise the original filesystem/hash verifier, never replace its result.
    assert flags.verify_evidence_dir_manifest_sha256_v0(directory) == 0
    monkeypatch.setattr(flags, "DEFAULT_CANONICAL_PARITY_SOURCE_EVIDENCE_DIR", directory)
    return directory
