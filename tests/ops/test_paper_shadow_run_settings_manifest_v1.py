"""Canonical Run-001 settings manifest and digest v1."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    DEFAULT_MAX_STALE_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.operational_run_v1 import OperationalRunHooksV1
from src.ops.paper_shadow_bounded_orchestrator_v1.observation_tick_source_v1 import (
    PublicEeaObservationTickSourceV1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    PaperShadowRunContractV1,
    RunContractError,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
    RUN_SETTINGS_MANIFEST_SPEC_VERSION,
    build_digest_payload_v1,
    build_run_settings_manifest_v1,
    compute_run_settings_digest_v1,
    run_settings_digest_spec_v1,
    verify_contract_settings_digest_v1,
)

REPO = Path(__file__).resolve().parents[2]
CANONICAL_FIXPOINT = "1dd90cb053522d953aa7518541da2c0d1940ffee"
CANONICAL_TREE = "16b0dc9e78e0dc1f24ddcb218514e69f5c5462c4"
HISTORICAL_DIGEST = "fedd80e991e1d162ac75f6c7d5bfe3b98b755949d4f79e231739e0cb44eb02e5"


def _run001_contract_raw(*, settings_digest: str) -> dict:
    return {
        "RUN_ID": "PAPER_SHADOW_RUN_001",
        "RUN_TYPE": "BOUNDED_PAPER_SHADOW",
        "RUN_DURATION_SECONDS": 3600,
        "MAX_OBSERVATION_COUNT": 2000,
        "MAX_CYCLE_COUNT": 2000,
        "MAX_SIMULATED_EXECUTION_COUNT": 120,
        "MAX_SIMULATED_OPEN_POSITION_COUNT": 1,
        "ENTER_REQUIRED_FOR_SUCCESS": False,
        "FIXPOINT_SHA": CANONICAL_FIXPOINT,
        "FIXPOINT_TREE": CANONICAL_TREE,
        "SETTINGS_DIGEST": settings_digest,
        "OBSERVATION_SOURCE": "wallclock_public_md_observe_v1",
        "EXECUTION_SINK": "SIMULATED_ONLY",
        "GHV_CONTROL_FIXPOINT_SHA": CANONICAL_FIXPOINT,
    }


def build_current_run001_contract(tmp_path: Path) -> PaperShadowRunContractV1:
    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    raw = _run001_contract_raw(settings_digest=str(manifest["RUN_SETTINGS_DIGEST"]))
    path = tmp_path / "run_contract_v1.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    digest_path = tmp_path / "run_settings_digest.json"
    digest_path.write_text(
        json.dumps(
            {
                "RUN_ID": "PAPER_SHADOW_RUN_001",
                "FIXPOINT_SHA": CANONICAL_FIXPOINT,
                "SETTINGS_DIGEST": manifest["RUN_SETTINGS_DIGEST"],
            }
        ),
        encoding="utf-8",
    )
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
        load_paper_shadow_run_contract_v1,
    )

    return load_paper_shadow_run_contract_v1(
        contract_path=path,
        settings_digest_path=digest_path,
    )


def test_same_manifest_same_digest() -> None:
    m1 = build_run_settings_manifest_v1(repo_root=REPO)
    m2 = build_run_settings_manifest_v1(repo_root=REPO)
    assert m1["RUN_SETTINGS_DIGEST"] == m2["RUN_SETTINGS_DIGEST"]


def test_mapping_order_independent_digest() -> None:
    m = build_run_settings_manifest_v1(repo_root=REPO)
    shuffled = copy.deepcopy(m)
    shuffled["SETTINGS"] = list(reversed(m["SETTINGS"]))
    shuffled["DIGEST_PAYLOAD"] = build_digest_payload_v1(settings=shuffled["SETTINGS"])
    assert compute_run_settings_digest_v1(shuffled) == m["RUN_SETTINGS_DIGEST"]


def test_value_change_changes_digest() -> None:
    base = build_run_settings_manifest_v1(repo_root=REPO)
    mutated = copy.deepcopy(base)
    for row in mutated["SETTINGS"]:
        if row["SETTING_ID"] == "POST_ALLOWED":
            row["VALUE"] = True
    mutated["DIGEST_PAYLOAD"] = build_digest_payload_v1(settings=mutated["SETTINGS"])
    assert compute_run_settings_digest_v1(mutated) != base["RUN_SETTINGS_DIGEST"]


def test_excluded_manifest_metadata_does_not_affect_digest() -> None:
    base = build_run_settings_manifest_v1(repo_root=REPO)
    annotated = copy.deepcopy(base)
    annotated["AUDIT_NOTE"] = "non-semantic"
    assert compute_run_settings_digest_v1(annotated) == base["RUN_SETTINGS_DIGEST"]


def test_missing_digest_payload_fail_closed() -> None:
    m = build_run_settings_manifest_v1(repo_root=REPO)
    del m["DIGEST_PAYLOAD"]
    with pytest.raises(Exception):
        compute_run_settings_digest_v1(m)


def test_unknown_spec_version_fail_closed() -> None:
    m = build_run_settings_manifest_v1(repo_root=REPO)
    m["SPEC_VERSION"] = RUN_SETTINGS_MANIFEST_SPEC_VERSION + 99
    with pytest.raises(Exception):
        compute_run_settings_digest_v1(m)


def test_historical_digest_has_no_authority() -> None:
    manifest = build_run_settings_manifest_v1(repo_root=REPO)
    assert manifest["RUN_SETTINGS_DIGEST"] != HISTORICAL_DIGEST


def test_contract_digest_verification(tmp_path: Path) -> None:
    if (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        != CANONICAL_FIXPOINT
    ):
        pytest.skip("requires canonical fixpoint checkout")
    contract = build_current_run001_contract(tmp_path)
    ok, expected, _ = verify_contract_settings_digest_v1(repo_root=REPO, contract=contract)
    assert ok is True
    assert expected == contract.settings_digest


def test_contract_digest_mismatch_fail_closed(tmp_path: Path) -> None:
    contract = build_current_run001_contract(tmp_path)
    bad = PaperShadowRunContractV1(
        run_id=contract.run_id,
        run_type=contract.run_type,
        run_duration_seconds=contract.run_duration_seconds,
        max_observation_count=contract.max_observation_count,
        max_cycle_count=contract.max_cycle_count,
        max_simulated_execution_count=contract.max_simulated_execution_count,
        max_simulated_open_position_count=contract.max_simulated_open_position_count,
        enter_required_for_success=contract.enter_required_for_success,
        fixpoint_sha=contract.fixpoint_sha,
        fixpoint_tree=contract.fixpoint_tree,
        settings_digest="0" * 64,
        observation_source=contract.observation_source,
        execution_sink=contract.execution_sink,
        ghv_control_fixpoint_sha=contract.ghv_control_fixpoint_sha,
        raw=dict(contract.raw),
    )
    ok, _, _ = verify_contract_settings_digest_v1(repo_root=REPO, contract=bad)
    assert ok is False


def test_execution_sink_mutation_invalidates_digest(tmp_path: Path) -> None:
    contract = build_current_run001_contract(tmp_path)
    raw = dict(contract.raw)
    raw["EXECUTION_SINK"] = "OTHER"
    path = tmp_path / "mutated_contract.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
        load_paper_shadow_run_contract_v1,
    )

    loaded = load_paper_shadow_run_contract_v1(contract_path=path)
    ok, _, _ = verify_contract_settings_digest_v1(repo_root=REPO, contract=loaded)
    assert ok is False


def test_poll_interval_single_owner() -> None:
    assert OperationalRunHooksV1().poll_interval_seconds == DEFAULT_POLL_INTERVAL_SECONDS


def test_staleness_tick_source_owner() -> None:
    src = PublicEeaObservationTickSourceV1(transport=object())  # type: ignore[arg-type]
    assert src.max_stale_seconds == DEFAULT_MAX_STALE_SECONDS


def test_digest_spec_documented() -> None:
    spec = run_settings_digest_spec_v1()
    assert spec.spec_id
    assert spec.domain_separator
    assert spec.hash_algorithm == "SHA-256"
