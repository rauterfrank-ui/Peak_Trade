"""Ops contract tests for materialize_pit_futures_universe_manifest_dataset_period_binding_v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.materialize_pit_futures_universe_manifest_dataset_period_binding_v0 import (
    CONFIRM_GO,
    run_materialization,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (
    FLEET_CANDIDATES,
    serialize_contract_canonical_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_run_materialization_requires_go_token(tmp_path: Path) -> None:
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    with pytest.raises(SystemExit):
        run_materialization(
            confirm="WRONG_TOKEN",
            staging_root=staging_root,
            durable_evidence_root=tmp_path / "evidence",
        )


def test_run_materialization_end_to_end_from_production_staging(tmp_path: Path) -> None:
    from tests.research.test_pit_futures_universe_manifest_dataset_period_binding_v0 import (
        _build_production_result,
    )
    from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
        production_materialization_envelope_to_dict,
    )
    from src.research.pit_futures_universe_manifest_v1 import manifest_to_dict

    production = _build_production_result()
    staging_root = tmp_path / "staging"
    universe_dir = staging_root / "universe"
    universe_dir.mkdir(parents=True)
    (universe_dir / "pit_futures_universe_manifest_v1.json").write_text(
        json.dumps(manifest_to_dict(production.manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (universe_dir / "production_materialization_envelope_v1.json").write_text(
        json.dumps(
            production_materialization_envelope_to_dict(production.envelope),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    evidence_root = tmp_path / "evidence"
    payload = run_materialization(
        confirm=CONFIRM_GO,
        staging_root=staging_root,
        durable_evidence_root=evidence_root,
    )
    assert payload["verdict"] == "PIT_FUTURES_UNIVERSE_MANIFEST_DATASET_PERIOD_BINDING_COMPLETE"
    assert payload["candidate_count"] == 3
    assert payload["candidate_strategy_ids"] == sorted(sid for sid, _ in FLEET_CANDIDATES)

    contract_path = (
        staging_root / "binding" / "pit_futures_universe_manifest_dataset_period_binding_v0.json"
    )
    assert contract_path.is_file()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract["production_universe_manifest_digest"] == production.manifest.manifest_digest
    assert serialize_contract_canonical_v0(contract).endswith("\n")

    evidence_dir = Path(payload["durable_evidence_path"])
    assert (evidence_dir / "MANIFEST.sha256").is_file()
    assert payload["manifest_verify_rc"] == 0
