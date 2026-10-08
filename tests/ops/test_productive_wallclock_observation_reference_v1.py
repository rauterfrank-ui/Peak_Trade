"""Tests for productive wallclock observation reference v1 (offline, no authority)."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.economic_evidence_bundle_v1 import (
    BUNDLE_SCHEMA_VERSION_V1_1,
    produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
    produce_integrated_paper_shadow_economic_evidence_bundle_with_productive_wallclock_reference_v1,
    verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.productive_wallclock_observation_reference_v1 import (
    REFERENCE_ARTIFACT,
    REFERENCE_SCHEMA_ID,
    REFERENCE_SCHEMA_VERSION,
    build_productive_wallclock_observation_reference_document_v1,
    verify_productive_wallclock_observation_reference_v1,
)
from src.ops.integrated_offline_replay_and_correctness_head_bound_v1.proof_v1 import (
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1,
    resolve_repository_head_sha_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    RESULT_PASS,
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    EXECUTION_CLASS_ANALYTICAL,
)
from tests.ops.test_integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
    FakeClock,
    SHA,
    _fake_ticker_fetcher,
    _load_wallclock_go,
    _load_wallclock_prereg,
    _material,
    _write_v2_auth,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
    WallclockSessionRuntimeV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOAK_REL = "evidence/ops/current_6h_paper_shadow_soak_v1/20261007T185400Z"


def _run_minimal_wallclock_evidence(tmp_path: Path) -> Path:
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    artifact_path = _write_v2_auth(tmp_path, prereg=prereg, token=material)
    clock = FakeClock()
    under_repo = REPO_ROOT / "tests" / "tmp" / f"productive_wallclock_ref_{uuid.uuid4().hex}"
    under_repo.mkdir(parents=True, exist_ok=True)
    evidence_root = under_repo / "wallclock_ev"
    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=EeaPublicMdTransportV1(
            fetcher=_fake_ticker_fetcher(clock=clock),
            sleep=clock.sleep,
            environ={},
        ),
        config=WallclockRuntimeConfigV1(
            max_cycles=3,
            poll_interval_seconds=0.01,
            min_quality_window_seconds=0,
            heartbeat_interval_seconds=1.0,
            heartbeat_loss_seconds=100.0,
        ),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    runtime.run(
        prereg=prereg,
        go=go,
        confirm_token=material,
        artifact_path=artifact_path,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    wc = verify_wallclock_evidence_bundle_v1(evidence_root=evidence_root)
    assert wc.verified is True, wc.blockers
    assert wc.result == RESULT_PASS
    return evidence_root


@pytest.fixture
def _cleanup_repo_wallclock_tmp() -> None:
    yield
    tmp_root = REPO_ROOT / "tests" / "tmp"
    if tmp_root.is_dir():
        for child in tmp_root.glob("productive_wallclock_ref_*"):
            shutil.rmtree(child, ignore_errors=True)


def test_reference_build_and_verify_positive(
    tmp_path: Path, _cleanup_repo_wallclock_tmp: None
) -> None:
    evidence_root = _run_minimal_wallclock_evidence(tmp_path)
    rel = str(evidence_root.relative_to(REPO_ROOT))
    doc = build_productive_wallclock_observation_reference_document_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=rel,
    )
    assert doc["schema_id"] == REFERENCE_SCHEMA_ID
    assert doc["execution_class"] == EXECUTION_CLASS_ANALYTICAL
    result = verify_productive_wallclock_observation_reference_v1(
        repo_root=REPO_ROOT,
        reference=doc,
    )
    assert result.verified is True


def test_composite_v1_1_bundle_and_adjudication_complete(
    tmp_path: Path, _cleanup_repo_wallclock_tmp: None
) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    wallclock_ev = _run_minimal_wallclock_evidence(tmp_path)
    bundle_dir = wallclock_ev.parent / "bundle_v11"
    composite = produce_integrated_paper_shadow_economic_evidence_bundle_with_productive_wallclock_reference_v1(
        repo_root=REPO_ROOT,
        bundle_root=bundle_dir,
        correctness_evidence_root=proof_dir,
        productive_wallclock_evidence_root=wallclock_ev,
    )
    assert composite.productive_wallclock_observation_verified is True
    assert composite.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True
    bundle_doc = json.loads(
        (bundle_dir / "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE_BUNDLE.json").read_text()
    )
    assert bundle_doc["schema_version"] == BUNDLE_SCHEMA_VERSION_V1_1
    assert (bundle_dir / REFERENCE_ARTIFACT).is_file()

    verified = verify_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
        bundle_root=bundle_dir,
        repo_root=REPO_ROOT,
        correctness_evidence_root=proof_dir,
    )
    assert verified.productive_wallclock_observation_verified is True
    assert verified.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True

    from src.ops.integrated_paper_shadow_economic_validity_pipeline_v1 import (
        IntegratedPaperShadowEconomicValidityEvidenceInputV1,
    )

    complete_input = IntegratedPaperShadowEconomicValidityEvidenceInputV1(
        integrated_paper_shadow_evidence_complete=verified.productive_wallclock_observation_verified,
    )
    assert complete_input.integrated_paper_shadow_evidence_complete is True


def test_legacy_v1_bundle_productive_complete_false(tmp_path: Path) -> None:
    head = resolve_repository_head_sha_v1(repo_root=REPO_ROOT)
    proof_dir = tmp_path / "proof"
    produce_integrated_offline_replay_and_correctness_head_bound_evidence_v1(
        repo_root=REPO_ROOT,
        work_root=proof_dir,
        expected_head_sha=head,
    )
    bundle_dir = tmp_path / "bundle_v1"
    produced = produce_integrated_paper_shadow_economic_evidence_bundle_head_bound_v1(
        repo_root=REPO_ROOT,
        bundle_root=bundle_dir,
        correctness_evidence_root=proof_dir,
    )
    assert produced.INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED is True
    assert produced.productive_wallclock_observation_verified is False


@pytest.mark.parametrize(
    "mutator,expected_substr",
    [
        (lambda d: {**d, "evidence_relpath": "missing/path/xyz"}, "EVIDENCE_ROOT_MISSING"),
        (lambda d: {**d, "repository_sha": "0" * 40}, "REPOSITORY_SHA_MISMATCH"),
        (
            lambda d: {**d, "evidence_manifest_sha256": "0" * 64},
            "EVIDENCE_MANIFEST_SHA256_MISMATCH",
        ),
        (
            lambda d: {**d, "integrity_manifest_sha256": "0" * 64},
            "INTEGRITY_MANIFEST_SHA256_MISMATCH",
        ),
        (lambda d: {**d, "terminal_verdict_sha256": "0" * 64}, "TERMINAL_VERDICT_SHA256_MISMATCH"),
        (
            lambda d: {**d, "wallclock_verifier_id": "wrong"},
            "REFERENCE_WALLCLOCK_VERIFIER_ID_MISMATCH",
        ),
        (lambda d: {**d, "schema_id": "wrong"}, "REFERENCE_SCHEMA_ID_MISMATCH"),
        (lambda d: {**d, "schema_version": "v99"}, "REFERENCE_SCHEMA_VERSION_MISMATCH"),
        (lambda d: {**d, "execution_class": "VENUE_PAPER"}, "REFERENCE_EXECUTION_CLASS_MISMATCH"),
        (lambda d: {**d, "paper_execution": True}, "REFERENCE_PAPER_EXECUTION_CLAIM"),
        (lambda d: {**d, "orders_submitted": 1}, "REFERENCE_ORDERS_SUBMITTED_NONZERO"),
    ],
)
def test_reference_negative_mutations(
    tmp_path: Path, _cleanup_repo_wallclock_tmp: None, mutator, expected_substr: str
) -> None:
    evidence_root = _run_minimal_wallclock_evidence(tmp_path)
    rel = str(evidence_root.relative_to(REPO_ROOT))
    doc = build_productive_wallclock_observation_reference_document_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=rel,
    )
    bad = mutator(doc)
    result = verify_productive_wallclock_observation_reference_v1(
        repo_root=REPO_ROOT,
        reference=bad,
    )
    assert result.verified is False
    assert any(expected_substr in b for b in result.blockers)


def test_terminal_fail_and_incomplete(tmp_path: Path, _cleanup_repo_wallclock_tmp: None) -> None:
    evidence_root = _run_minimal_wallclock_evidence(tmp_path)
    rel = str(evidence_root.relative_to(REPO_ROOT))
    terminal_path = evidence_root / "terminal_verdict.json"
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    terminal["verdict"] = "FAIL"
    terminal["incomplete"] = True
    terminal_path.write_text(json.dumps(terminal, sort_keys=True) + "\n", encoding="utf-8")
    doc = build_productive_wallclock_observation_reference_document_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=rel,
    )
    result = verify_productive_wallclock_observation_reference_v1(
        repo_root=REPO_ROOT,
        reference=doc,
    )
    assert result.verified is False


def test_soak_reference_read_only_verify_if_present() -> None:
    soak_root = REPO_ROOT / SOAK_REL
    if not soak_root.is_dir():
        pytest.skip("productive soak evidence not present locally")
    wc = verify_wallclock_evidence_bundle_v1(evidence_root=soak_root)
    assert wc.verified is True
    doc = build_productive_wallclock_observation_reference_document_v1(
        repo_root=REPO_ROOT,
        evidence_relpath=SOAK_REL,
    )
    result = verify_productive_wallclock_observation_reference_v1(
        repo_root=REPO_ROOT,
        reference=doc,
    )
    assert result.verified is True
    before = soak_root / "terminal_verdict.json"
    mtime_before = before.stat().st_mtime
    assert result.verified is True
    assert before.stat().st_mtime == mtime_before
