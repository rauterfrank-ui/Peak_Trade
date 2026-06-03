"""Static contract tests for future-run primary evidence retention hard gate v0 (offline)."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

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
SHADOW_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
TESTNET_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
P67_LIB = REPO_ROOT / "src" / "ops" / "p67" / "shadow_session_scheduler_v1.py"
P72_PACK = REPO_ROOT / "src" / "ops" / "p72" / "run_shadowloop_pack_v1.py"
P79_VERIFY = REPO_ROOT / "scripts" / "ops" / "p79_supervisor_evidence_manifest_verify_v0.py"
P101 = REPO_ROOT / "scripts" / "ops" / "p101_stop_playbook_v1.sh"
P93 = REPO_ROOT / "scripts" / "ops" / "p93_online_readiness_status_dashboard_v1.sh"
POST_STOP = REPO_ROOT / "scripts" / "ops" / "run_online_readiness_post_stop_pack_v0.sh"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
ARTIFACT_RETENTION_CROSSLINK_TESTS = (
    REPO_ROOT
    / "tests"
    / "ci"
    / "test_cybersecurity_visibility_repo_static_histogram_artifact_retention_or_evidence_gap_crosslink_v0.py"
)
RECIPROCAL_CROSSLINK_MARKER = "CYBERSECURITY_VISIBILITY_ARTIFACT_RETENTION_DURABLE_PRIMARY_EVIDENCE_RECIPROCAL_CROSSLINK_V0=true"
_MARKER_TRUE = "=true"
BOUNDED_REVIEW_CONTRACT_TESTS = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_observation_review_durable_primary_evidence_contract_v0.py"
)
MANDATORY_CLOSEOUT_WIRING_TOKEN = "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true"
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

SECTION5_GAP_OWNER = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)


# SLICE-PE-2: static run-type guard matrix (contract/guard only; no runtime enforcement).
class Pe2RunTypeGuardRow(NamedTuple):
    run_type_id: str
    doc_label: str
    implementation_anchor: str | None = None
    extra_doc_phrase: str | None = None


PE2_RUN_TYPE_GUARD_MATRIX: tuple[Pe2RunTypeGuardRow, ...] = (
    Pe2RunTypeGuardRow(
        "paper",
        "Paper",
        "run_paper_only_bounded_observation_adapter_v0.py",
        "bounded observation",
    ),
    Pe2RunTypeGuardRow(
        "shadow",
        "Shadow",
        "review_shadow_bounded_observation_evidence_v0.py",
        "bounded observation",
    ),
    Pe2RunTypeGuardRow(
        "testnet",
        "Testnet",
        "review_testnet_bounded_observation_evidence_v0.py",
        "bounded observation",
    ),
    Pe2RunTypeGuardRow("live", "Live/Canary"),
    Pe2RunTypeGuardRow(
        "bounded_observation",
        "bounded trial",
        extra_doc_phrase="bounded observation",
    ),
    Pe2RunTypeGuardRow("scheduler", "Scheduler", "run_scheduler.py"),
    Pe2RunTypeGuardRow(
        "supervisor",
        "Supervisor",
        "pack_online_readiness_supervisor_evidence_v0.py",
    ),
)

PE2_REQUIRED_RUN_TYPE_IDS = frozenset(row.run_type_id for row in PE2_RUN_TYPE_GUARD_MATRIX)

PE2_ENFORCEMENT_CONTRACT_ONLY_MARKERS = (
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
    "GAP2A1_ENFORCEMENT_DEFAULT_ON=false",
    "GAP2A1_ENFORCEMENT_OPT_IN_ONLY=true",
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
)


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _section_2a1() -> str:
    return _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def _section_2a() -> str:
    return (
        _owner_text()
        .split("## 2a. Primary evidence retention invariant v0", 1)[1]
        .split("## 2a.1", 1)[0]
    )


def _section5_gap2a1() -> str:
    text = SECTION5_GAP_OWNER.read_text(encoding="utf-8")
    return text.split("## §2a.1 Primary Evidence Enforcement Contract v0", 1)[1].split(
        "## Gap 1 Execute Entrypoint Contract v0", 1
    )[0]


def test_canonical_owner_section_2a1_exists_with_hard_gate_tokens() -> None:
    text = _owner_text()
    assert "## 2a.1 Future-run primary evidence hard gate v0" in text
    assert text.index("## 2a.") < text.index("## 2a.1") < text.index("## 2b.")
    for token in HARD_GATE_TOKENS:
        assert token in text


def test_section_2a1_applies_to_all_run_types() -> None:
    section = _section_2a1()
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


def test_pe2_run_type_primary_evidence_guard_matrix_covers_required_lanes_v0() -> None:
    assert PE2_REQUIRED_RUN_TYPE_IDS >= frozenset(
        {
            "paper",
            "shadow",
            "testnet",
            "live",
            "bounded_observation",
            "scheduler",
            "supervisor",
        }
    )


@pytest.mark.parametrize(
    "row",
    PE2_RUN_TYPE_GUARD_MATRIX,
    ids=lambda row: row.run_type_id,
)
def test_pe2_run_type_primary_evidence_guard_matrix_row_v0(row: Pe2RunTypeGuardRow) -> None:
    section_2a = _section_2a()
    section_2a1 = _section_2a1()
    owner = _owner_text()
    gap2a1 = _section5_gap2a1()

    assert row.doc_label in section_2a
    assert row.doc_label in section_2a1
    if row.extra_doc_phrase:
        assert row.extra_doc_phrase in section_2a.lower() or row.extra_doc_phrase in owner.lower()
    if row.implementation_anchor:
        assert row.implementation_anchor in owner

    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in section_2a
    assert "durable archive outside `/tmp`" in section_2a or "outside `/tmp`" in section_2a1
    assert "`/tmp`-only" in section_2a or "/tmp`-only" in section_2a1
    assert "MANIFEST.sha256" in section_2a
    assert "shasum -a 256 -c" in section_2a or "verify_manifest_sha256" in section_2a1
    assert "A run is **not complete** until **archive verification passes**" in section_2a

    for token in HARD_GATE_TOKENS:
        assert token in section_2a1

    assert "not complete" in section_2a1.lower()
    assert "TMP_ONLY_EVIDENCE_INVALID" in section_2a1
    assert "incomplete and invalid" in section_2a1

    for marker in PE2_ENFORCEMENT_CONTRACT_ONLY_MARKERS:
        assert marker in gap2a1

    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=true" not in gap2a1
    assert "READY_FOR_OPERATOR_ARMING=true" not in gap2a1


def test_pe2_run_type_primary_evidence_guard_matrix_enforcement_not_activated_v0() -> None:
    gap2a1 = _section5_gap2a1()
    section_2a1 = _section_2a1()
    assert "default off" in section_2a1.lower() or "opt-in" in section_2a1.lower()
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in section_2a1
    assert "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false" in gap2a1
    assert "GAP2A1_ENFORCEMENT_DEFAULT_ON=false" in gap2a1


def test_section_2a1_references_may_2026_testnet_missing_source_context() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "MISSING_SOURCE=true" in section
    assert "240-min" in section or "240 min" in section


def test_section_2a1_preserves_evidence_not_approval() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "Evidence ≠ approval" in section
    assert "BLOCKED" in section
    assert "STOP_IDLE" in section


def test_section_2a1_readiness_ledger_gate_snapshot_review_input_only() -> None:
    section = _owner_text().split("## 2a.1", 1)[1].split("## 2b.", 1)[0]
    assert "Readiness ledger and gate snapshot (review-input-only)" in section
    assert "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE" in section
    assert "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE" in section
    assert "triple_lane_primary_evidence=true" in section
    assert "authorize runtime" in section
    assert "do not" in section
    assert "do not clear Preflight BLOCKED" in section.replace("**", "")
    assert "do not close GLB-014/GLB-015" in section.replace("**", "")
    assert "GLB-015 clarification" in section


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
    for path in (PAPER_ADAPTER, SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = path.read_text(encoding="utf-8")
        assert "_write_closeout_artifacts" in text
        assert "REVIEW_RESULT.json" in text
        assert "verify_manifest_sha256" in text
        assert "archive root must be outside /tmp" in text


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


def test_section_2a1_contains_mandatory_closeout_wiring_token() -> None:
    section = _section_2a1()
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert "Mandatory durable closeout wiring" in section


def test_section_2a1_links_mandatory_wiring_to_bounded_shadow_testnet_closeouts() -> None:
    section = _section_2a1()
    collapsed = section.lower()
    assert "review_shadow_bounded_observation_evidence_v0.py" in section
    assert "review_testnet_bounded_observation_evidence_v0.py" in section
    assert "--durable-run-root" in section
    assert "shadow" in collapsed
    assert "testnet" in collapsed
    assert "closeout" in collapsed


def test_docs_truth_map_records_mandatory_closeout_wiring_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "2026-05-23" in text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in text
    assert "mandatory durable closeout wiring" in text.lower()
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "--durable-run-root" in text


def test_docs_truth_map_records_pr3634_3635_3636_contract_test_registry_visibility_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = text.lower()
    assert "2026-05-23" in text
    assert "#3634" in text
    assert "checkout v5" in collapsed
    assert "test_workflows_no_pull_request_target_contract_v0.py" in text
    assert "#3635" in text
    assert "bounded adapter crosslink" in collapsed
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in text
    assert "§2a.1" in text or "2a.1" in text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in text or "mandatory closeout wiring" in collapsed
    assert "#3636" in text
    assert "primary evidence invariant" in collapsed
    assert "test_primary_evidence_retention_invariant_contract_v0.py" in text
    assert "--durable-run-root" in text
    assert "non-authorizing" in collapsed


def test_docs_truth_map_records_pr3633_3638_3639_contract_test_registry_visibility_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = text.lower()
    assert "2026-05-23" in text
    assert "#3633" in text
    assert "mandatory wiring crosslink" in collapsed
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in text
    assert "§2a.1" in text or "2a.1" in text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in text or "mandatory closeout wiring" in collapsed
    assert "#3638" in text
    assert "u3 scoped-exception" in collapsed or "u3 scoped exception" in collapsed
    assert "test_preflight_scoped_exception_contract_u3_v0.py" in text
    assert "#3639" in text
    assert "reciprocal crosslink" in collapsed
    assert "test_bounded_observation_review_durable_primary_evidence_contract_v0.py" in text
    assert "test_primary_evidence_retention_invariant_contract_v0.py" in text
    assert "preflight **blocked**" in collapsed or "preflight blocked" in collapsed
    assert "non-authorizing" in collapsed


def test_docs_truth_map_records_pr3641_3642_3643_contract_test_registry_visibility_slice() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = text.lower()
    assert "2026-05-23" in text
    assert "#3641" in text
    assert "scheduler-completion" in collapsed or "scheduler completion" in collapsed
    assert "test_scheduler_completion_primary_evidence_closeout_v0.py" in text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in text or "mandatory closeout wiring" in collapsed
    assert "#3642" in text
    assert "reciprocal crosslink" in collapsed
    assert "test_primary_evidence_retention_invariant_contract_v0.py" in text
    assert "#3643" in text
    assert "u3" in collapsed
    assert "bounded-review" in collapsed or "bounded review" in collapsed
    assert "test_preflight_scoped_exception_contract_u3_v0.py" in text
    assert "test_bounded_observation_review_durable_primary_evidence_contract_v0.py" in text
    assert "§2a.1" in text or "2a.1" in text
    assert "preflight **blocked**" in collapsed or "preflight blocked" in collapsed
    assert "non-authorizing" in collapsed


def test_hard_gate_and_bounded_review_contract_modules_share_mandatory_wiring_anchor() -> None:
    hard_gate_text = Path(__file__).read_text(encoding="utf-8")
    bounded_text = BOUNDED_REVIEW_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in hard_gate_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in bounded_text
    assert (
        str(CANONICAL_OWNER) in bounded_text
        or "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in bounded_text
    )


def test_section_2a1_mandatory_wiring_preserves_opt_in_and_non_authorizing() -> None:
    section = _section_2a1()
    collapsed = section.replace("**", "").lower()
    assert "default off" in collapsed or "opt-in (default off)" in collapsed
    assert "not default-on" in collapsed
    assert "non-authorizing" in collapsed
    assert "evidence ≠ approval" in section or "evidence = approval" not in collapsed
    assert "does not authorize runtime" in collapsed
    assert "does not clear preflight blocked" in collapsed


def test_bounded_review_scripts_expose_durable_run_root_for_mandatory_closeout_wiring() -> None:
    section = _section_2a1()
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        assert review_path.name in section
        assert "--durable-run-root" in text
        assert "validate_durable_primary_evidence_root" in text
        assert "default=None" in text
        assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section


def test_bounded_adapters_reference_preflight_mandatory_wiring_review_owners() -> None:
    section = _section_2a1()
    adapter_review_pairs = (
        (SHADOW_ADAPTER, SHADOW_REVIEW.name),
        (TESTNET_ADAPTER, TESTNET_REVIEW.name),
    )
    for adapter_path, review_name in adapter_review_pairs:
        adapter_text = adapter_path.read_text(encoding="utf-8")
        assert review_name in adapter_text
        assert review_name in section
        assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section


def test_bounded_adapter_execute_surfaces_keep_durable_run_root_default_off() -> None:
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "durable_run_root" not in text
        review_cmd_region = text.split("review_cmd =", 1)[1].split("]", 1)[0]
        assert "--staging-root" in review_cmd_region
        assert "--durable-run-root" not in review_cmd_region


def test_mandatory_wiring_adapter_review_chain_preserves_review_input_only_boundary() -> None:
    section = _section_2a1()
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        collapsed = text.lower()
        assert "non-authorizing" in collapsed
        assert "does not claim readiness" in collapsed or "does not authorize" in collapsed
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        collapsed = text.lower()
        assert (
            "forbidden_command_substrings" in collapsed or "forbidden_env_substrings" in collapsed
        )
        assert "non-authorizing" in collapsed
        assert "live_allowed=false" in collapsed
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true" in section
    assert "does not clear preflight blocked" in section.replace("**", "").lower()


def test_hard_gate_owner_covers_mandatory_wiring_adapter_review_chain() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    for anchor in (
        MANDATORY_CLOSEOUT_WIRING_TOKEN,
        SHADOW_ADAPTER.name,
        TESTNET_ADAPTER.name,
        SHADOW_REVIEW.name,
        TESTNET_REVIEW.name,
        BOUNDED_REVIEW_CONTRACT_TESTS.name,
    ):
        assert anchor in owner_text


def test_pe4_hard_gate_crosslinks_bounded_closeout_lane_matrix_owner_v0() -> None:
    bounded_text = BOUNDED_REVIEW_CONTRACT_TESTS.read_text(encoding="utf-8")
    section = _section_2a1()
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in bounded_text
    assert "PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true" in section
    assert "test_pe4_bounded_observation_mandatory_closeout_completion_contract_row_v0" in (
        bounded_text
    )


def test_pe5_hard_gate_crosslinks_gap4_gap2a1_dependency_owner_v0() -> None:
    gap4_gap2a1 = (
        REPO_ROOT / "tests" / "ops" / "test_gap4_gap2a1_primary_evidence_dependency_contract_v0.py"
    )
    assert gap4_gap2a1.is_file()
    section = _section_2a1()
    for token in (
        "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true",
        "GAP4_OUTPUT_EVIDENCE_DEPENDS_ON_GAP2A1_PRIMARY_EVIDENCE_V0=true",
        "TMP_ONLY_EVIDENCE_INVALID=true",
        "MANIFEST_VERIFY_REQUIRED=true",
    ):
        assert token in section
    assert gap4_gap2a1.name in section or "gap4_gap2a1" in section.lower()


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


def _durable_closeout_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"lifecycle_{tmp_path.name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_lifecycle_closeout_bundle(
    root: Path,
    *,
    verify_log_name: str = "MANIFEST_VERIFY.log",
    verify_rc: int = 0,
    marker_name: str = "HOST_TEARDOWN_EXECUTION_SLICE_V0_REPORT.md",
    nested_mirror: bool = False,
) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    (root / marker_name).write_text("# lifecycle closeout\n", encoding="utf-8")
    (root / verify_log_name).write_text(f"MANIFEST_VERIFY_RC={verify_rc}\n", encoding="utf-8")
    if nested_mirror:
        mirror = root / "remote_archive_mirror"
        mirror.mkdir(parents=True, exist_ok=True)
        (mirror / "evidence.txt").write_text("nested evidence\n", encoding="utf-8")
        (mirror / "MANIFEST.sha256").write_text("# nested-local manifest\n", encoding="utf-8")
    write_manifest_sha256(root)


def test_shared_helper_exposes_lifecycle_closeout_hard_gate_extension() -> None:
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "PRIMARY_EVIDENCE_RETENTION_HARD_GATE_EXTENSION_V0=true" in text
    assert "VALIDATE_DURABLE_LIFECYCLE_CLOSEOUT_ROOT_V0=true" in text
    assert "def parse_manifest_verify_log_rc" in text
    assert "def validate_durable_lifecycle_closeout_root" in text
    assert "LOCAL_MANIFEST_VERIFY.log" in text


def test_validate_durable_lifecycle_closeout_root_accepts_local_manifest_verify_log(
    tmp_path: Path,
) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import validate_durable_lifecycle_closeout_root

    root = _durable_closeout_root(tmp_path)
    _write_lifecycle_closeout_bundle(
        root,
        verify_log_name="LOCAL_MANIFEST_VERIFY.log",
        marker_name="BOUNDED_RUNTIME_GRACEFUL_STOP_AND_DURABLE_CLOSEOUT_REPORT.md",
    )
    ok, reason, detail = validate_durable_lifecycle_closeout_root(root)
    assert ok is True, reason
    assert detail["manifest_verify_log"] == "LOCAL_MANIFEST_VERIFY.log"
    assert detail["classification"] == "lifecycle_closeout_slice_v0"


@pytest.mark.parametrize(
    ("setup", "expected_substring"),
    [
        ("missing_root", "archive root missing"),
        ("tmp_only", "outside /tmp"),
        ("missing_manifest", "MANIFEST.sha256 missing"),
        ("manifest_mismatch", "checksum mismatch"),
        ("missing_verify_log", "manifest verify log missing"),
        ("verify_rc_nonzero", "manifest verify RC must be 0"),
        ("missing_marker", "lifecycle closeout marker artifact missing"),
        ("missing_stop_idle", "final stop-idle marker missing"),
    ],
)
def test_validate_durable_lifecycle_closeout_root_fail_closed_cases(
    tmp_path: Path,
    setup: str,
    expected_substring: str,
) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        validate_durable_lifecycle_closeout_root,
        write_manifest_sha256,
    )

    if setup == "missing_root":
        root = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"missing_{tmp_path.name}"
        require_final = False
    elif setup == "tmp_only":
        root = Path("/tmp") / f"peak_trade_lifecycle_closeout_{tmp_path.name}"
        root.mkdir(parents=True, exist_ok=True)
        _write_lifecycle_closeout_bundle(root)
        require_final = False
    else:
        root = _durable_closeout_root(tmp_path)
        require_final = setup == "missing_stop_idle"
        if setup == "missing_manifest":
            (root / "HOST_TEARDOWN_EXECUTION_SLICE_V0_REPORT.md").write_text(
                "# x\n", encoding="utf-8"
            )
            (root / "MANIFEST_VERIFY.log").write_text("MANIFEST_VERIFY_RC=0\n", encoding="utf-8")
        elif setup == "manifest_mismatch":
            _write_lifecycle_closeout_bundle(root)
            (root / "HOST_TEARDOWN_EXECUTION_SLICE_V0_REPORT.md").write_text(
                "# tampered\n", encoding="utf-8"
            )
        elif setup == "missing_verify_log":
            (root / "HOST_TEARDOWN_EXECUTION_SLICE_V0_REPORT.md").write_text(
                "# x\n", encoding="utf-8"
            )
            write_manifest_sha256(root)
        elif setup == "verify_rc_nonzero":
            _write_lifecycle_closeout_bundle(root, verify_rc=1)
        elif setup == "missing_marker":
            (root / "MANIFEST_VERIFY.log").write_text("MANIFEST_VERIFY_RC=0\n", encoding="utf-8")
            write_manifest_sha256(root)
        elif setup == "missing_stop_idle":
            _write_lifecycle_closeout_bundle(
                root,
                marker_name="HOST_TEARDOWN_PLANNING_SLICE_V0_READONLY.md",
            )
        else:
            _write_lifecycle_closeout_bundle(root)

    ok, reason, _detail = validate_durable_lifecycle_closeout_root(
        root,
        require_final_stop_idle_marker=require_final,
    )
    assert ok is False
    assert expected_substring in reason


def test_validate_durable_lifecycle_closeout_root_passes_with_nested_mirror_parent_manifest(
    tmp_path: Path,
) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import validate_durable_lifecycle_closeout_root

    root = _durable_closeout_root(tmp_path)
    _write_lifecycle_closeout_bundle(
        root,
        nested_mirror=True,
        marker_name="SG_CLEANUP_EXECUTION_SLICE_V0_REPORT.md",
    )
    ok, reason, detail = validate_durable_lifecycle_closeout_root(root)
    assert ok is True, reason
    assert detail["checks"]["manifest_sha256_verify"] is True
    assert (root / "remote_archive_mirror" / "MANIFEST.sha256").is_file()


def test_validate_durable_lifecycle_closeout_root_final_stop_idle_record(tmp_path: Path) -> None:
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import validate_durable_lifecycle_closeout_root

    root = _durable_closeout_root(tmp_path)
    _write_lifecycle_closeout_bundle(
        root,
        marker_name="BOUNDED_REMOTE_LIFECYCLE_FINAL_STOP_IDLE_RECORD.md",
    )
    (root / "BOUNDED_REMOTE_LIFECYCLE_FINAL_STOP_IDLE_MACHINE_LINES.txt").write_text(
        "NEXT_ACTION=STOP_IDLE_LIFECYCLE_COMPLETE_KEEP_IAM_FOR_REUSE\n",
        encoding="utf-8",
    )
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(root)
    ok, reason, detail = validate_durable_lifecycle_closeout_root(
        root,
        require_final_stop_idle_marker=True,
    )
    assert ok is True, reason
    assert detail["classification"] == "final_stop_idle_lifecycle_closeout_v0"


def test_hard_gate_owner_crosslinks_cybersecurity_artifact_retention_histogram_v0() -> None:
    ci_audit = (REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md").read_text(encoding="utf-8")
    assert RECIPROCAL_CROSSLINK_MARKER in ci_audit
    assert "artifact_retention_or_evidence_gap" in ci_audit
    assert Path(__file__).name in ci_audit
    assert ARTIFACT_RETENTION_CROSSLINK_TESTS.is_file()

    crosslink_text = ARTIFACT_RETENTION_CROSSLINK_TESTS.read_text(encoding="utf-8")
    assert Path(__file__).name in crosslink_text
    assert RECIPROCAL_CROSSLINK_MARKER in crosslink_text
    assert "INPUT_JSONL_PROVIDED=false" in ci_audit
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in ci_audit

    ci_lines = {line.strip() for line in ci_audit.splitlines()}
    assert ("INPUT_JSONL_PROVIDED" + _MARKER_TRUE) not in ci_lines

    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in ci_audit
        assert "pending" in ci_audit.lower()


def test_hard_gate_owner_crosslinks_gap4_and_scheduler_dry_run_hardening_v0() -> None:
    gap4_owner = REPO_ROOT / "tests" / "ops" / "test_gap4_output_evidence_paths_contract_v0.py"
    hardening_owner = (
        REPO_ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
    )
    hardening_marker = "SCHEDULER_DRY_RUN_HARDENING_SOURCE_CONTRACT_V0=true"

    assert gap4_owner.is_file()
    assert hardening_owner.is_file()

    gap4_text = gap4_owner.read_text(encoding="utf-8")
    assert "test_scheduler_dry_run_hardening_source_contract_v0.py" in gap4_text
    assert hardening_marker in gap4_text
    assert Path(__file__).name in gap4_text

    hardening_text = hardening_owner.read_text(encoding="utf-8")
    assert "test_gap4_output_evidence_paths_contract_v0.py" in hardening_text
    assert Path(__file__).name in hardening_text
