"""PRE-LIVE convergence WP contract tests (tmp roots only)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from src.governance.pre_live_fresh_state_and_slice_baseline_convergence_v1 import (
    CAP24_OWNER_GO_TOKEN,
    DECISION_CONFIG,
    OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    execute_pre_live_fresh_state_and_slice_baseline_convergence_v1,
    validate_scoped_owner_go_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
    EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_decision_config_present_and_baseline_aligned() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["owner_go_token"] == OWNER_GO_TOKEN
    assert decision["baseline_origin_main_sha"] == EXPECTED_BASELINE_ORIGIN_MAIN_SHA


def test_fail_closed_without_owner_go_token() -> None:
    probe = validate_scoped_owner_go_v1(repo_root=REPO_ROOT, owner_go_token=None)
    assert probe.ok is False


def test_convergence_on_tmp_productivity_root(monkeypatch: pytest.MonkeyPatch) -> None:
    origin = EXPECTED_BASELINE_ORIGIN_MAIN_SHA
    integrity = MockCurrentProductive29PIntegrityBackendV1(origin_main=origin, head=origin)

    ns = REPO_ROOT / "runtime/current_productive" / f"_test_pre_live_{uuid.uuid4().hex}"
    monkeypatch.setattr(
        "src.governance.pre_live_fresh_state_and_slice_baseline_convergence_v1.fresh_runtime_roots_v1",
        lambda **kwargs: {
            "productivity_root": ns / "cap24_productivity",
            "lane_state_root": ns / "lane_state",
            "post_durable_store": ns / "post_durable_store",
            "evidence_root": ns / "pre_live_evidence",
        },
    )

    try:
        report = execute_pre_live_fresh_state_and_slice_baseline_convergence_v1(
            repo_root=REPO_ROOT,
            owner_go_token=OWNER_GO_TOKEN,
            cap24_owner_go_token=CAP24_OWNER_GO_TOKEN,
            execution_integrity_backend=integrity,
        )
    finally:
        shutil.rmtree(ns, ignore_errors=True)

    assert report["BASELINE_CONVERGENCE_PROVEN"] is True
    assert report["CAP24_FRESHNESS_PROVEN"] is True
    assert report["FRESH_ROOT_ISOLATION_PROVEN"] is True
    assert report["ACTUAL_VENUE_POST_PERFORMED"] is False
