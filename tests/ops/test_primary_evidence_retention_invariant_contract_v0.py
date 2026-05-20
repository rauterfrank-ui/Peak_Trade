"""Static contract tests for primary evidence retention invariant v0 (offline, no runtime)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _adapter_text() -> str:
    return PAPER_ADAPTER.read_text(encoding="utf-8")


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_canonical_owner_declares_primary_evidence_required_for_every_run() -> None:
    text = _owner_text()
    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in text
    assert "## 2a. Primary evidence retention invariant v0" in text


def test_canonical_owner_applies_to_all_run_types() -> None:
    text = _owner_text()
    for run_type in (
        "Paper",
        "Shadow",
        "Testnet",
        "Live/Canary",
        "Scheduler",
        "Supervisor",
        "Daemon",
        "Smoke",
        "bounded trial",
        "runtime adapter",
    ):
        assert run_type in text


def test_canonical_owner_requires_durable_archive_outside_tmp() -> None:
    text = _owner_text()
    assert "durable archive outside `/tmp`" in text
    assert "archive verification passes" in text


def test_canonical_owner_requires_manifest_and_sha256_verification() -> None:
    text = _owner_text()
    assert "MANIFEST.sha256" in text
    assert "shasum -a 256 -c" in text
    assert "RC=0" in text


def test_canonical_owner_requires_closeout_and_postrun_review() -> None:
    text = _owner_text()
    assert "closeout present" in text
    assert "postrun/review present" in text
    assert "REVIEW_RESULT.json" in text


def test_canonical_owner_rejects_non_primary_evidence_sources() -> None:
    text = _owner_text()
    forbidden = (
        "/tmp`-only artifacts",
        "transcript-only evidence",
        "Notion pointer-only evidence",
        "chat-summary-only evidence",
        "unverified archive copies",
    )
    for phrase in forbidden:
        assert phrase in text


def test_canonical_owner_forbids_gate_clearance_from_documentary_only() -> None:
    text = _owner_text()
    assert "No gate clearance" in text
    assert "degraded or documentary evidence alone" in text


def test_canonical_owner_no_automatic_24h_72h_rerun_after_paper120() -> None:
    text = _owner_text()
    assert "automatic **24h** or **72h** rerun requirement" in text
    assert "Paper120" in text


def test_canonical_owner_run_not_complete_until_archive_verification() -> None:
    text = _owner_text()
    assert "A run is **not complete** until **archive verification passes**" in text


def test_paper_adapter_plan_only_default_and_execute_gated() -> None:
    text = _adapter_text()
    assert "plan-only default" in text
    assert "--plan-only" in text or '"plan-only"' in text
    assert "--execute" in text
    assert "requires --approval-record" in text or "execute requires --approval-record" in text


def test_paper_adapter_archive_root_must_be_outside_tmp() -> None:
    text = _adapter_text()
    assert "archive root must be outside /tmp" in text


def test_canonical_owner_references_paper_adapter_implementation() -> None:
    text = _owner_text()
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text
    assert "plan-only default" in text
    assert "archive root outside `/tmp`" in text
