"""Static contract tests for future-run primary evidence retention hard gate v0 (offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
SCHEDULER_BOUNDARY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md"
)
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
SCHEDULER = REPO_ROOT / "scripts" / "run_scheduler.py"
PACK_SCRIPT = REPO_ROOT / "scripts" / "ops" / "pack_online_readiness_supervisor_evidence_v0.py"
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
TESTNET_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
P67_LIB = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_v1.py"
P72_PACK = REPO_ROOT / "src" / "ops" / "p72" / "run_shadowloop_pack_v1.py"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
P101 = REPO_ROOT / "scripts" / "ops" / "p101_stop_playbook_v1.sh"
P93 = REPO_ROOT / "scripts" / "ops" / "p93_online_readiness_status_dashboard_v1.sh"
POST_STOP = REPO_ROOT / "scripts" / "ops" / "run_online_readiness_post_stop_pack_v0.sh"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
COPY_CHECK = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "retention/testnet_240min_existing_bundle_durable_copy_check_v0_20260522T081045Z/"
    "TESTNET_240MIN_EXISTING_BUNDLE_DURABLE_COPY_CHECK_V0.md"
)

HARD_GATE_TOKENS = (
    "RUN_PRIMARY_EVIDENCE_RETENTION_HARD_GATE_V0=true",
    "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true",
    "TMP_ONLY_EVIDENCE_INVALID=true",
    "MANIFEST_VERIFY_REQUIRED=true",
    "CLOSEOUT_REFERENCE_REQUIRED=true",
    "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
)


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def test_canonical_owner_section_2a1_exists_with_hard_gate_tokens() -> None:
    text = _owner_text()
    assert "## 2a.1 Future-run primary evidence hard gate v0" in text
    assert text.index("## 2a.") < text.index("## 2a.1") < text.index("## 2b.")
    for token in HARD_GATE_TOKENS:
        assert token in text


def test_section_2a1_applies_to_all_run_types() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
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
        assert run_type in section


def test_section_2a1_references_may_2026_testnet_missing_source_context() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "MISSING_SOURCE=true" in section
    assert "240-min" in section or "240 min" in section


def test_section_2a1_preserves_evidence_not_approval() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "Evidence ≠ approval" in section
    assert "BLOCKED" in section
    assert "STOP_IDLE" in section


def test_section_2a1_reuses_shared_helper_not_parallel_doc() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "primary_evidence_retention_v0.py" in section
    assert (
        "reuse-before-new" in section.lower()
        or "Implementation anchors (reuse-before-new)" in section
    )


def test_taxonomy_indexes_section_2a1_without_duplicating_rules() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "§2a.1 future-run primary evidence hard gate" in text
    assert "PRIMARY_EVIDENCE_FUTURE_RUN_HARD_GATE_V0=true" in text
    assert "Retention rules remain in preflight §2a/§2b" in text


def test_taxonomy_hard_gate_markers_present() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    for token in (
        "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true",
        "TMP_ONLY_EVIDENCE_INVALID=true",
        "MANIFEST_VERIFY_REQUIRED=true",
        "CLOSEOUT_REFERENCE_REQUIRED=true",
        "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true",
    ):
        assert token in text


def test_shared_helper_exposes_is_under_tmp_and_require_durable_archive_root() -> None:
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def is_under_tmp" in text
    assert "def require_durable_archive_root" in text
    for token in (
        "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true",
        "TMP_ONLY_EVIDENCE_INVALID=true",
        "MANIFEST_VERIFY_REQUIRED=true",
        "CLOSEOUT_REFERENCE_REQUIRED=true",
    ):
        assert token in text


def test_scheduler_imports_shared_is_under_tmp_not_duplicate() -> None:
    text = SCHEDULER.read_text(encoding="utf-8")
    assert "from scripts.ops.primary_evidence_retention_v0 import is_under_tmp" in text
    assert "def _is_under_tmp" not in text
    assert "is_under_tmp(evidence_dir)" in text


def test_pack_script_imports_shared_is_under_tmp_not_duplicate() -> None:
    text = PACK_SCRIPT.read_text(encoding="utf-8")
    assert "is_under_tmp" in text
    assert "from scripts.ops.primary_evidence_retention_v0 import" in text
    assert "def _is_under_tmp" not in text


def test_bounded_adapters_reject_tmp_archive_root_on_execute() -> None:
    for path in (PAPER_ADAPTER, SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "archive root must be outside /tmp" in text
        assert "primary_evidence_retention_v0" in text


def test_bounded_adapters_write_closeout_and_review_on_execute() -> None:
    for path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "_write_closeout_artifacts" in text
        assert "REVIEW_RESULT.json" in text
        assert "verify_manifest_sha256" in text
    paper_text = PAPER_ADAPTER.read_text(encoding="utf-8")
    assert "REVIEW_RESULT.json" in paper_text
    assert "verify_manifest_sha256" in paper_text
    assert "archive root must be outside /tmp" in paper_text


def test_p67_p72_reference_finalize_primary_evidence_root() -> None:
    for path in (P67_LIB, P72_PACK):
        text = path.read_text(encoding="utf-8")
        assert "primary_evidence_enforce" in text
        assert "finalize_primary_evidence_root" in text


def test_p79_verifier_and_post_stop_paths_reference_manifest_and_closeout() -> None:
    p79_text = P79_VERIFY.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in p79_text
    assert "supervisor_session_closeout_v0" in p79_text or "CLOSEOUT_FILENAME" in p79_text
    for script in (P101, P93, POST_STOP):
        text = script.read_text(encoding="utf-8")
        assert "primary-evidence-enforce" in text or "--primary-evidence-enforce" in text
        assert "ARCHIVE_ROOT" in text


def test_scheduler_boundary_cross_references_preflight_hard_gate() -> None:
    text = SCHEDULER_BOUNDARY.read_text(encoding="utf-8")
    assert "§2a.1" in text or "2a.1" in text
    assert "primary evidence" in text.lower()
    assert "SCHEDULER_EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in text


def test_docs_truth_map_records_hard_gate_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§2a.1" in text or "2a.1" in text
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text


@pytest.mark.skipif(not COPY_CHECK.is_file(), reason="operator archive copy-check not present")
def test_operator_copy_check_confirms_missing_source_when_present() -> None:
    text = COPY_CHECK.read_text(encoding="utf-8")
    assert "MISSING_SOURCE=true" in text
    assert "SOURCE_ARTIFACTS_COPIED=false" in text


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (Path("/tmp/evidence"), True),
        (Path("/private/tmp/evidence"), True),
        (Path("/var/tmp/evidence"), False),
    ],
)
def test_is_under_tmp_detects_tmp_roots(path: Path, expected: bool) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp

    assert is_under_tmp(path) is expected


def test_require_durable_archive_root_fails_closed_on_tmp() -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import require_durable_archive_root

    ok, reason = require_durable_archive_root(Path("/tmp/peak_trade_evidence_test"))
    assert ok is False
    assert "outside /tmp" in reason


def test_require_durable_archive_root_accepts_durable_path() -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import require_durable_archive_root

    # Use repo-local path: pytest tmp_path resolves under /tmp on Linux CI.
    durable = REPO_ROOT / "out" / "_pytest_primary_evidence_durable_root"
    durable.mkdir(parents=True, exist_ok=True)
    try:
        ok, reason = require_durable_archive_root(durable)
        assert ok is True, reason
    finally:
        durable.rmdir()
