"""Contract tests for OKX full-panel dataset promotion decision and binding v0."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.research.okx_full_panel_dataset_promotion_decision_and_binding_v0 import (
    GO_TOKEN,
    DATASET_ID,
    DATASET_VERSION,
    IdempotentRepromotionStatus,
    PromotionDecisionStatus,
    UniverseClassificationCode,
    _load_panel_cells,
    build_promotion_binding_v0,
    build_universe_denominator_matrix_v0,
    evaluate_promotion_decision_v0,
    run_okx_full_panel_dataset_promotion_decision_and_binding_v0,
    verify_candidate_integrity_v0,
)
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    read_registry_snapshot_v1,
)
from src.research.cross_sectional_bounded_panel_fetch_v0 import compute_bounded_window_v0

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
CANDIDATE_ROOT = (
    ARCHIVE_ROOT / "datasets/candidates/okx_full_panel_fetch_completeness_v0_20260703T170453Z"
)
REGISTRY_PATH = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/"
    "lifecycle/registry_snapshot_v1.json"
)
IMPLEMENTATION_REF = "bounded_okx_full_panel_fetch_and_completeness_evidence_v0_20260703T170500Z"
CLOSEOUT_REF = "bounded_okx_full_panel_fetch_and_completeness_evidence_closeout_v0_20260703T171256Z"


def _candidate_manifest_digest() -> str:
    manifest = CANDIDATE_ROOT / "MANIFEST.sha256"
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_candidate_integrity_passes_for_staged_candidate() -> None:
    report = verify_candidate_integrity_v0(
        candidate_root=CANDIDATE_ROOT,
        closeout_manifest_digest=_candidate_manifest_digest(),
    )
    assert report.status == "PASS"
    assert report.instrument_count == 118
    assert report.source_archive_count > 0
    assert report.funding_binding_digest
    assert not report.reason_codes


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_changed_candidate_manifest_blocks_promotion(tmp_path: Path) -> None:
    copied = tmp_path / "candidate"
    shutil.copytree(CANDIDATE_ROOT, copied)
    (copied / "fetch_spec.json").write_text('{"tampered": true}\n', encoding="utf-8")
    report = verify_candidate_integrity_v0(candidate_root=copied)
    assert report.status == "BLOCKED"
    assert any("MANIFEST" in code or "MISMATCH" in code for code in report.reason_codes)


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_symlink_candidate_root_blocks_promotion(tmp_path: Path) -> None:
    link = tmp_path / "candidate_link"
    link.symlink_to(CANDIDATE_ROOT)
    report = verify_candidate_integrity_v0(candidate_root=link)
    assert report.status == "BLOCKED"
    assert "CANDIDATE_ROOT_IS_SYMLINK" in report.reason_codes


@pytest.mark.skipif(not REGISTRY_PATH.is_file(), reason="lifecycle registry unavailable")
def test_universe_denominator_covers_all_392_with_reproducible_exclusions() -> None:
    read = read_registry_snapshot_v1(
        root_dir=REGISTRY_PATH.parent,
        relative_path=Path(REGISTRY_PATH.name),
    )
    assert read.snapshot is not None
    window = compute_bounded_window_v0()
    records = build_universe_denominator_matrix_v0(
        snapshot=read.snapshot,
        period_start_ms=window.start_ms,
    )
    assert len(records) == 392
    admissible = [
        r for r in records if r.classification == UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
    ]
    excluded = [
        r for r in records if r.classification != UniverseClassificationCode.LIFECYCLE_ADMISSIBLE
    ]
    assert len(admissible) == 118
    assert len(excluded) == 274
    assert not any(
        r.classification == UniverseClassificationCode.MISSING_LIFECYCLE_EVIDENCE for r in records
    )


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_missing_funding_blocks_promotion() -> None:
    aggregates = json.loads(
        (CANDIDATE_ROOT / "completeness" / "aggregates.json").read_text(encoding="utf-8")
    )
    fetch_spec = json.loads((CANDIDATE_ROOT / "fetch_spec.json").read_text(encoding="utf-8"))
    cells = _load_panel_cells(CANDIDATE_ROOT)
    bad_aggregates = dict(aggregates)
    bad_aggregates["funding_cells_missing"] = 1
    integrity = verify_candidate_integrity_v0(candidate_root=CANDIDATE_ROOT)
    decision, reasons = evaluate_promotion_decision_v0(
        candidate_integrity=integrity,
        universe_records=(),
        cells=cells,
        aggregates=bad_aggregates,
        fetch_spec=fetch_spec,
    )
    assert "FUNDING_CELLS_MISSING" in reasons
    assert decision in {PromotionDecisionStatus.REJECTED, PromotionDecisionStatus.BLOCKED}


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_complete_admissible_universe_passes_promotion_evaluation() -> None:
    read = read_registry_snapshot_v1(
        root_dir=REGISTRY_PATH.parent,
        relative_path=Path(REGISTRY_PATH.name),
    )
    assert read.snapshot is not None
    window = compute_bounded_window_v0()
    universe = build_universe_denominator_matrix_v0(
        snapshot=read.snapshot,
        period_start_ms=window.start_ms,
    )
    integrity = verify_candidate_integrity_v0(
        candidate_root=CANDIDATE_ROOT,
        closeout_manifest_digest=_candidate_manifest_digest(),
    )
    aggregates = json.loads(
        (CANDIDATE_ROOT / "completeness" / "aggregates.json").read_text(encoding="utf-8")
    )
    fetch_spec = json.loads((CANDIDATE_ROOT / "fetch_spec.json").read_text(encoding="utf-8"))
    cells = _load_panel_cells(CANDIDATE_ROOT)
    decision, reasons = evaluate_promotion_decision_v0(
        candidate_integrity=integrity,
        universe_records=universe,
        cells=cells,
        aggregates=aggregates,
        fetch_spec=fetch_spec,
    )
    assert decision == PromotionDecisionStatus.PROMOTED
    assert reasons == ()


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_promotion_does_not_authorize_economic_evaluation_or_runtime() -> None:
    result = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=Path("/tmp/unused_for_eval"),
        repo_root=Path("/tmp/unused_repo"),
        lifecycle_registry_path=REGISTRY_PATH,
        implementation_evidence_ref=IMPLEMENTATION_REF,
        closeout_evidence_ref=CLOSEOUT_REF,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=False,
    )
    assert result.decision == PromotionDecisionStatus.PROMOTED
    assert result.economic_evaluation_authorized is False
    assert result.runtime_effect == "NONE"
    assert result.authority_effect == "NONE"
    assert result.promotion_binding is not None
    assert result.promotion_binding.economic_evaluation_authorized is False


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_duplicate_identical_promotion_is_idempotent_no_op(tmp_path: Path) -> None:
    result = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=tmp_path,
        repo_root=tmp_path / "repo",
        lifecycle_registry_path=REGISTRY_PATH,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=True,
    )
    assert result.decision == PromotionDecisionStatus.PROMOTED
    assert result.idempotent_status == IdempotentRepromotionStatus.NEW_PROMOTION

    second = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=tmp_path,
        repo_root=tmp_path / "repo",
        lifecycle_registry_path=REGISTRY_PATH,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=True,
    )
    assert second.idempotent_status == IdempotentRepromotionStatus.NO_OP_SUCCESS
    assert second.dataset_promoted is True


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_same_version_different_digest_blocks(tmp_path: Path) -> None:
    result = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=tmp_path,
        repo_root=tmp_path / "repo",
        lifecycle_registry_path=REGISTRY_PATH,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=True,
    )
    assert result.promotion_binding is not None
    promoted_root = tmp_path / "datasets/admissible_futures" / DATASET_ID / DATASET_VERSION
    registry_path = promoted_root / "registry_entry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["dataset_content_digest"] = "0" * 64
    registry_path.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    second = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=tmp_path,
        repo_root=tmp_path / "repo2",
        lifecycle_registry_path=REGISTRY_PATH,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=True,
    )
    assert second.idempotent_status == IdempotentRepromotionStatus.CONFLICT_BLOCKED


@pytest.mark.skipif(not CANDIDATE_ROOT.is_dir(), reason="candidate fixture unavailable")
def test_immutable_versioned_binding_created_with_alias_not_sole_binding(tmp_path: Path) -> None:
    result = run_okx_full_panel_dataset_promotion_decision_and_binding_v0(
        confirm=GO_TOKEN,
        candidate_root=CANDIDATE_ROOT,
        durable_archive_root=tmp_path,
        repo_root=tmp_path / "repo",
        lifecycle_registry_path=REGISTRY_PATH,
        closeout_manifest_digest=_candidate_manifest_digest(),
        write_registry=True,
    )
    promoted_root = tmp_path / "datasets/admissible_futures" / DATASET_ID / DATASET_VERSION
    assert (promoted_root / "registry_entry.json").is_file()
    assert (promoted_root / "promotion_binding.json").is_file()
    assert (promoted_root / "candidate_reference.json").is_file()
    alias = json.loads((promoted_root / "alias" / "current.json").read_text(encoding="utf-8"))
    assert alias["not_sole_binding"] is True
    assert alias["versioned_binding_required"] is True
    registry = json.loads((promoted_root / "registry_entry.json").read_text(encoding="utf-8"))
    assert registry["immutable_versioned_binding"] is True


def test_futures_only_and_bitcoin_direction_forbidden_in_binding() -> None:
    binding = build_promotion_binding_v0(
        candidate_integrity=verify_candidate_integrity_v0(
            candidate_root=Path("/nonexistent"),
        ),
        universe_records=(),
        fetch_spec={
            "requested_start_time": "2024-01-01T00:00:00Z",
            "requested_end_time": "2024-09-01T00:00:00Z",
        },
        decision=PromotionDecisionStatus.BLOCKED,
        reason_codes=("TEST",),
        input_evidence_refs=(),
        decision_timestamp_utc="2026-07-03T00:00:00Z",
    )
    assert binding.instrument_binding["futures_only"] is True
    assert binding.instrument_binding["bitcoin_direction_allowed"] is False
