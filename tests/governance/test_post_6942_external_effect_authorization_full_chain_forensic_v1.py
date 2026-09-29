"""Tests for post-6942 EXTERNAL_EFFECT_AUTHORIZATION full-chain forensic v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6942_external_effect_authorization_full_chain_forensic_v1 import (
    CANONICAL_DECISION_CHAIN,
    DECISION_CONFIG,
    K1_OPAQUE_SIGNING_NEXT_BLOCKER,
    NORMATIVE_SPEC,
    VENUE_POST_OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    build_full_chain_forensic_report_v1,
    probe_downstream_policy_and_sink_chain_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_workpackage_paths_exist() -> None:
    assert (REPO / NORMATIVE_SPEC).is_file()
    assert (REPO / DECISION_CONFIG).is_file()
    decision = json.loads((REPO / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["first_real_blocker"] == "EXTERNAL_EFFECT_AUTHORIZATION"
    assert decision["permit_mint_performed"] is False


def test_canonical_decision_chain_has_six_layers() -> None:
    assert len(CANONICAL_DECISION_CHAIN) == 6


def test_full_chain_probe_extends_6941_without_perform() -> None:
    chain = probe_downstream_policy_and_sink_chain_v1(repo_root=REPO)
    seam = chain["POST_6941_SEAM_PROBE"]
    assert seam["POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN"] is True
    assert chain["FULL_POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN"] is True
    assert chain["CREDENTIAL_ACCESS_BOUND"]["credential_access_performed"] is False
    assert chain["MATERIAL_LOAD_BOUND"]["material_load_admission_granted"] is True
    assert chain["VENUE_POST_ADMISSION"]["post_admission_granted"] is False
    assert seam["ENVELOPE_SEAM_PROBE"] == "NO_PERMIT"


def test_build_report_marks_fixpoint() -> None:
    treasury = {
        "PRE_EXTERNAL_REACHED": True,
        "WHOLE_SYSTEM_E2E_RUN_ID": "test",
        "EVIDENCE_ROOT": "evidence/ops/test",
    }
    report = build_full_chain_forensic_report_v1(
        repo_root=REPO,
        baseline_sha="388a41e2e607c1d2026b5ed35f9c28a6a7314ada",
        treasury_report=treasury,
        map_sha256="abc",
        atlas_sha256="def",
        e2e_run_id="test-run",
        evidence_root="evidence/ops/test",
    )
    assert report["FIXPOINT_REACHED"] is True
    assert (
        report["FIRST_IRREVERSIBLE_OPERATION"] == "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD"
    )
    assert report["VENUE_POST_OWNER"] == VENUE_POST_OWNER_GO_TOKEN
    assert K1_OPAQUE_SIGNING_NEXT_BLOCKER in report["EXACT_OWNER_GO_REQUIRED"][1]
    assert report["EXTERNAL_EFFECT_PERMIT_MINTED"] is False
    assert report["CREDENTIALS_ACCESSED"] is False


def test_orchestrator_script_exists() -> None:
    assert (
        REPO
        / "scripts/ops/run_post_6942_authority_map_atlas_external_effect_authorization_full_chain_v1.py"
    ).is_file()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == "POST_6942_EXTERNAL_EFFECT_AUTHORIZATION_FULL_CHAIN_FORENSIC_V1"
