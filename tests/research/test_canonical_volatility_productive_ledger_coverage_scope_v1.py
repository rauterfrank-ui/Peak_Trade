"""Campaign-scoped productive coverage evaluation (historical inertness R1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    LEDGER_EVALUATION_SEMANTICS_FORENSIC_GLOBAL,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.coverage_v1 import (
    evaluate_coverage_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.evaluability_v1 import (
    coverage_by_age_bucket_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_campaign_scope_v1 import (
    filter_productive_records_to_campaign_scope_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.ledger_v1 import (
    valid_productive_records_from_ledger_v1,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_runner_v1 import (
    deterministic_productive_mark_path_v1,
    run_productive_bridge_accumulation_session_v1,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    MINIMUM_EVIDENCE_COUNT,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.failed_s01_session_recovery_governance_v1 import (
    evaluate_failed_s01_campaign_governance_v1,
)
from research.canonical_volatility_numeric_max_age_productive_campaign_r1_recovery_active_binding_v1.active_binding_v1 import (
    load_active_campaign_binding_v1,
)

ROOT = Path(__file__).resolve().parents[2]
REPO_SHA = "51a3625b3666bc905b89ba9a8ad1bcfe84494430"
CURRENT_CAMPAIGN = "cv_maxage_productive_evidence_campaign_v1_current_cov_scope"
CURRENT_S01 = f"{CURRENT_CAMPAIGN}_s01_cov_a"
HIST_CAMPAIGN = "cv_maxage_productive_evidence_campaign_v1_1a638769c1dcb066"
HIST_S01 = f"{HIST_CAMPAIGN}_s01_hist_b"
SEED_SAMPLE_COUNT = 62
HIST_START_UNIX = 1_800_000_000.0


def _paths(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    return (
        tmp_path / "prod.jsonl",
        tmp_path / "join.jsonl",
        tmp_path / "q.jsonl",
        tmp_path / "persist.json",
    )


def _run_session(
    tmp_path: Path,
    *,
    campaign_id: str,
    session_id: str,
    persist_suffix: str,
    start_unix: float = 1_700_000_000.0,
) -> tuple[Path, Path, Path]:
    prod, join, q, _persist = _paths(tmp_path)
    run_productive_bridge_accumulation_session_v1(
        session_id=session_id,
        campaign_id=campaign_id,
        repository_sha=REPO_SHA,
        samples=deterministic_productive_mark_path_v1(
            count=SEED_SAMPLE_COUNT,
            start_unix=start_unix,
        ),
        repo_root=ROOT,
        productive_ledger_path=prod,
        join_ledger_path=join,
        quarantine_ledger_path=q,
        typed_volatility_persistence_path=tmp_path / f"persist_{persist_suffix}.json",
    )
    return prod, join, q


def _scoped_coverage(prod: Path, q: Path, *, campaign: str, session_id: str):
    return evaluate_coverage_from_ledger_v1(
        productive_ledger_path=prod,
        quarantine_ledger_path=q,
        coverage_scope_campaign_id=campaign,
        coverage_scope_session_ids=(session_id,),
    )


@pytest.fixture(name="mixed_ledger")
def fixture_mixed_ledger(tmp_path: Path) -> tuple[Path, Path]:
    prod, _join, q = _run_session(
        tmp_path,
        campaign_id=CURRENT_CAMPAIGN,
        session_id=CURRENT_S01,
        persist_suffix="a",
    )
    _run_session(
        tmp_path,
        campaign_id=HIST_CAMPAIGN,
        session_id=HIST_S01,
        persist_suffix="b",
        start_unix=HIST_START_UNIX,
    )
    return prod, q


def test_foreign_campaign_contributes_zero_to_current_coverage(
    mixed_ledger: tuple[Path, Path],
) -> None:
    prod, q = mixed_ledger
    all_valid = valid_productive_records_from_ledger_v1(prod)
    current_only = filter_productive_records_to_campaign_scope_v1(
        all_valid,
        campaign_id=CURRENT_CAMPAIGN,
        authorized_session_ids=(CURRENT_S01,),
    )
    scoped = _scoped_coverage(prod, q, campaign=CURRENT_CAMPAIGN, session_id=CURRENT_S01)
    forensic = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=prod,
        quarantine_ledger_path=q,
        coverage_evaluation_semantics=LEDGER_EVALUATION_SEMANTICS_FORENSIC_GLOBAL,
    )
    assert scoped.valid_evidence_count == len(current_only)
    assert forensic.valid_evidence_count == len(all_valid)
    assert len(current_only) < len(all_valid)
    assert scoped.valid_evidence_count < forensic.valid_evidence_count


def test_foreign_campaign_cannot_satisfy_current_minimum_gaps(
    mixed_ledger: tuple[Path, Path],
) -> None:
    prod, q = mixed_ledger
    scoped = _scoped_coverage(prod, q, campaign=CURRENT_CAMPAIGN, session_id=CURRENT_S01)
    forensic = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=prod,
        quarantine_ledger_path=q,
        coverage_evaluation_semantics=LEDGER_EVALUATION_SEMANTICS_FORENSIC_GLOBAL,
    )
    assert scoped.valid_evidence_count < int(MINIMUM_EVIDENCE_COUNT)
    assert scoped.session_count < int(MINIMUM_SESSION_COUNT)
    assert scoped.regime_count < int(MINIMUM_REGIME_COUNT)
    assert "MINIMUM_EVIDENCE_COUNT" in scoped.coverage_gaps
    assert "MINIMUM_SESSION_COUNT" in scoped.coverage_gaps
    assert "MINIMUM_REGIME_COUNT" in scoped.coverage_gaps
    if forensic.valid_evidence_count >= int(MINIMUM_EVIDENCE_COUNT):
        assert scoped.ready_for_research_execution is False
        assert forensic.ready_for_research_execution != scoped.ready_for_research_execution or (
            forensic.session_count > scoped.session_count
        )


def test_foreign_campaign_cannot_satisfy_age_grid_for_current(
    mixed_ledger: tuple[Path, Path],
) -> None:
    prod, _q = mixed_ledger
    all_valid = valid_productive_records_from_ledger_v1(prod)
    scoped_records = filter_productive_records_to_campaign_scope_v1(
        all_valid,
        campaign_id=CURRENT_CAMPAIGN,
        authorized_session_ids=(CURRENT_S01,),
    )
    scoped_age = coverage_by_age_bucket_v1(scoped_records)
    forensic_age = coverage_by_age_bucket_v1(all_valid)
    scoped_total_fresh = sum(
        bucket["fresh_count"] for bucket in scoped_age["age_bucket_coverage_matrix"].values()
    )
    forensic_total_fresh = sum(
        bucket["fresh_count"] for bucket in forensic_age["age_bucket_coverage_matrix"].values()
    )
    assert scoped_total_fresh < forensic_total_fresh


def test_missing_current_campaign_scope_fails_closed(tmp_path: Path) -> None:
    prod, _join, q = _run_session(
        tmp_path,
        campaign_id=CURRENT_CAMPAIGN,
        session_id=CURRENT_S01,
        persist_suffix="only",
    )
    with pytest.raises(
        ProductiveEvidenceAccumulationError,
        match="coverage_scope_required_for_current_productive",
    ):
        evaluate_coverage_from_ledger_v1(
            productive_ledger_path=prod,
            quarantine_ledger_path=q,
        )


def test_correctly_scoped_current_coverage_evaluates_normally(tmp_path: Path) -> None:
    prod, _join, q = _run_session(
        tmp_path,
        campaign_id=CURRENT_CAMPAIGN,
        session_id=CURRENT_S01,
        persist_suffix="norm",
    )
    report = _scoped_coverage(prod, q, campaign=CURRENT_CAMPAIGN, session_id=CURRENT_S01)
    assert report.valid_evidence_count >= 1
    assert report.session_count == 1
    assert report.threshold_status == "UNRESOLVED_MAX_AGE"


def test_forensic_global_coverage_remains_available(mixed_ledger: tuple[Path, Path]) -> None:
    prod, q = mixed_ledger
    scoped = _scoped_coverage(prod, q, campaign=CURRENT_CAMPAIGN, session_id=CURRENT_S01)
    forensic = evaluate_coverage_from_ledger_v1(
        productive_ledger_path=prod,
        quarantine_ledger_path=q,
        coverage_evaluation_semantics=LEDGER_EVALUATION_SEMANTICS_FORENSIC_GLOBAL,
    )
    assert forensic.valid_evidence_count > scoped.valid_evidence_count


def test_d01_retry_and_s02_remain_forbidden() -> None:
    binding = load_active_campaign_binding_v1(repo_root=ROOT)
    auth = (
        ROOT
        / "docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1"
        / "campaigns/cv_maxage_productive_evidence_campaign_v1_d01e77c281c7a34d"
        / "authorization/campaign_authorization.json"
    )
    gov = evaluate_failed_s01_campaign_governance_v1(
        binding=binding,
        evidence_root=ROOT,
        authorization_artifact_path=auth,
        authorization_id="cv_maxage_campaign_auth_v1_fdbc845e13f1abfc",
    )
    assert gov.failed_s01_closed is True
    assert gov.s01_retry_same_session_forbidden is True
    assert gov.s02_start_forbidden is True
    assert gov.retained_estimate_carrier_present is False
