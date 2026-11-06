"""Tests for post-6941 PRE_EXTERNAL → intent_to_execution seam adjudication v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6941_pre_external_intent_to_execution_seam_adjudication_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    build_seam_adjudication_report_v1,
    probe_intent_to_execution_seam_v1,
    resolve_first_real_blocker_v1,
    summarize_canonical_decision_chain_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_workpackage_paths_exist() -> None:
    assert (REPO / NORMATIVE_SPEC).is_file()
    assert (REPO / DECISION_CONFIG).is_file()
    decision = json.loads((REPO / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["first_real_blocker"] == "EXTERNAL_EFFECT_AUTHORIZATION"
    assert decision["post_allowed"] is False


def test_canonical_decision_chain_loads() -> None:
    chain = summarize_canonical_decision_chain_v1(repo_root=REPO)
    assert len(chain) == 4
    assert chain[0]["layer_id"] == "external_effect_authorization_policy"


def test_seam_probe_fail_closed_without_post() -> None:
    seam = probe_intent_to_execution_seam_v1(repo_root=REPO)
    assert seam["PRE_EXTERNAL_BOUNDARY_OK"] is True
    assert seam["POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN"] is True
    assert seam["INVOKE_SINK_PROBE"] == "FullCoreExternalEffectNotAuthorizedError"
    assert seam["ENVELOPE_SEAM_PROBE"] == "NO_PERMIT"
    standing = seam["STANDING_IMPORT_CONSTANTS"]
    assert standing["EXTERNAL_EFFECT_AUTHORIZED"] is False
    assert standing["POST_ALLOWED"] is False


def test_resolve_blocker_at_pre_external_fixpoint() -> None:
    treasury = {"PRE_EXTERNAL_REACHED": True}
    seam = probe_intent_to_execution_seam_v1(repo_root=REPO)
    blocker, blocker_class, subtype = resolve_first_real_blocker_v1(
        treasury_report=treasury,
        seam_probe=seam,
    )
    assert blocker == "EXTERNAL_EFFECT_AUTHORIZATION"
    assert blocker_class == "OPERATIONAL_EXTERNAL_EFFECT_SINK_FAIL_CLOSED"
    assert subtype == "ENVELOPE_BOUND_ACTUAL_POST_REQUIRES_SCOPED_OWNER_GO"


def test_build_report_marks_fixpoint() -> None:
    treasury = {
        "PRE_EXTERNAL_REACHED": True,
        "WHOLE_SYSTEM_E2E_RUN_ID": "test",
        "EVIDENCE_ROOT": "evidence/ops/test",
    }
    report = build_seam_adjudication_report_v1(
        repo_root=REPO,
        baseline_sha="f8a250ecf568edd216d62cae83c04a8931100e22",
        treasury_report=treasury,
        map_sha256="abc",
        atlas_sha256="def",
        e2e_run_id="test-run",
        evidence_root="evidence/ops/test",
    )
    assert report["FIXPOINT_REACHED"] is True
    assert report["EXTERNAL_EFFECT_AUTHORIZED"] is False
    assert report["VENUE_POST_COUNT"] == 0


def test_orchestrator_script_exists() -> None:
    assert (
        REPO
        / "scripts/ops/run_post_6941_authority_map_atlas_pre_external_intent_to_execution_seam_v1.py"
    ).is_file()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == "POST_6941_PRE_EXTERNAL_INTENT_TO_EXECUTION_SEAM_ADJUDICATION_V1"
