"""Paper-Shadow bounded run contract RUN_ID schema (fail-closed)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    RunContractError,
    load_paper_shadow_run_contract_v1,
    validate_paper_shadow_run_id_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
    build_run_settings_manifest_v1,
)

REPO = Path(__file__).resolve().parents[2]
FIXPOINT_SHA = "fb8a338c2b47dcf6349588fb2e68e9bc5f8b8ac1"
FIXPOINT_TREE = "921c9ff297b5b124cd011f7dd28640a63dff7fa4"


@pytest.mark.parametrize(
    "run_id",
    [
        "PAPER_SHADOW_RUN_001",
        "PAPER_SHADOW_RUN_002",
        "PAPER_SHADOW_RUN_999",
    ],
)
def test_valid_run_ids_accepted(run_id: str) -> None:
    assert validate_paper_shadow_run_id_v1(run_id) == run_id


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "   ",
        "PAPER_SHADOW_RUN_001 ",
        " PAPER_SHADOW_RUN_001",
        "paper_shadow_run_001",
        "PAPER_SHADOW_RUN_1",
        "PAPER_SHADOW_RUN_01",
        "PAPER_SHADOW_RUN_0000",
        "PAPER_SHADOW_RUN_000",
        "PAPER_SHADOW_RUN_abc",
        "PAPER_SHADOW_RUN_",
        "PAPER_SHADOW_RUN",
        "RUN_001",
        "../PAPER_SHADOW_RUN_001",
        "PAPER_SHADOW_RUN_001/evil",
        "PAPER_SHADOW_RUN_001\n",
        "PAPER_SHADOW_RUN_002_EXTRA",
    ],
)
def test_invalid_run_ids_rejected(run_id: str) -> None:
    with pytest.raises(RunContractError, match="RUN_ID_INVALID"):
        validate_paper_shadow_run_id_v1(run_id)


def test_loader_accepts_run_001_and_002(tmp_path: Path) -> None:
    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    digest = str(manifest["RUN_SETTINGS_DIGEST"])
    for run_id in ("PAPER_SHADOW_RUN_001", "PAPER_SHADOW_RUN_002"):
        path = tmp_path / f"{run_id}.json"
        path.write_text(
            json.dumps(
                {
                    "RUN_ID": run_id,
                    "RUN_TYPE": "BOUNDED_PAPER_SHADOW",
                    "RUN_DURATION_SECONDS": 3600 if run_id.endswith("001") else 14400,
                    "MAX_OBSERVATION_COUNT": 2000,
                    "MAX_CYCLE_COUNT": 2000,
                    "MAX_SIMULATED_EXECUTION_COUNT": 120,
                    "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
                    "ENTER_REQUIRED_FOR_SUCCESS": False,
                    "FIXPOINT_SHA": FIXPOINT_SHA,
                    "FIXPOINT_TREE": FIXPOINT_TREE,
                    "SETTINGS_DIGEST": digest,
                }
            ),
            encoding="utf-8",
        )
        loaded = load_paper_shadow_run_contract_v1(contract_path=path)
        assert loaded.run_id == run_id


def test_loader_rejects_bad_run_id(tmp_path: Path) -> None:
    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "RUN_ID": "PAPER_SHADOW_RUN_BOGUS",
                "SETTINGS_DIGEST": manifest["RUN_SETTINGS_DIGEST"],
                "FIXPOINT_SHA": FIXPOINT_SHA,
                "FIXPOINT_TREE": FIXPOINT_TREE,
                "RUN_DURATION_SECONDS": 3600,
                "MAX_OBSERVATION_COUNT": 1,
                "MAX_CYCLE_COUNT": 1,
                "MAX_SIMULATED_EXECUTION_COUNT": 0,
                "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RunContractError, match="RUN_ID_INVALID"):
        load_paper_shadow_run_contract_v1(contract_path=path)


def test_evidence_run_002_contract_loads() -> None:
    contract = (
        REPO
        / "evidence/research/paper_shadow_run002_postmerge_rebind_preflight_v1/20261005T004200Z/run_contract_v1.json"
    )
    if not contract.is_file():
        pytest.skip("run002 preflight evidence not present")
    loaded = load_paper_shadow_run_contract_v1(
        contract_path=contract,
        settings_digest_path=contract.parent / "run_settings_digest.json",
    )
    assert loaded.run_id == "PAPER_SHADOW_RUN_002"
