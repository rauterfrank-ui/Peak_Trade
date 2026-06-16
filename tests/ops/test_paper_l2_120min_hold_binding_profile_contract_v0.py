"""Static contract tests for Paper-L2 120min hold-binding profile v0.

Includes FALSE_CONFIDENCE interpretation guard static crosslink (v0): fail-closed
retention of PR #4123 / Scheduler Boundary §10b P0 markers. Archive charter is
external authority (Durable Archive); this module reflects repo markers only.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
ADAPTER = ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
L2_CONTRACT = ROOT / "scripts" / "ops" / "paper_l2_120min_hold_binding_approval_v0.py"
GUARD = ROOT / "scripts" / "ops" / "scheduler_start_boundary_guard_v0.py"
BOUNDARY_SPEC = ROOT / "docs" / "ops" / "specs" / "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md"
PREFLIGHT = ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
FIXTURE = ROOT / "tests" / "fixtures" / "ops" / "paper_l2_120min_hold_binding_approval_sample.md"

ARCHIVE_ROOT = "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
ARCHIVE_FALSE_CONFIDENCE_CHARTER_BUNDLE = (
    f"{ARCHIVE_ROOT}/charter/"
    "false_confidence_interpretation_guard_after_systemwide_safe_scope_inventory_"
    "operator_go_autofill_no_run_v1_20260611T111453Z"
)

PACKAGE_MARKER = "FALSE_CONFIDENCE_INTERPRETATION_GUARD_REPO_STATIC_CROSSLINK_V0=true"

# Scheduler Boundary §10b P0 namespace / false-confidence markers (PR #4123).
BOUNDARY_SPEC_P0_MARKERS: tuple[str, ...] = (
    "PAPER_L2_120MIN_HOLD_BINDING_PROFILE_V0=true",
    "PAPER_L2_120MIN_HOLD_BINDING_PROFILE_NON_AUTHORIZING=true",
    "PAPER_L2_120MIN_HOLD_BINDING_NO_TRADING_LOGIC_MUTATION=true",
    "PAPER_L2_120MIN_HOLD_BINDING_MASTER_V2_DOUBLE_PLAY_UNCHANGED=true",
    "PAPER_TL_L2_NAMESPACE=paper_trading_logic_evidence_ladder_step_2",
    "PAPER_TL_L2_NOT_MASTER_V2_G5_L2=true",
    "PAPER_TL_L2_PROVES_INFRASTRUCTURE_SAFETY_ONLY=true",
    "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false",
    "LINEAGE_EDGE_STEP0_TO_PAPER_TL_L2=MISSING_RUNTIME_BRIDGE",
    "BULL_BEAR_SIDE_SWITCH_AT_PAPER_TL_L2=NOT_REACHED",
)

# FI-001 / FI-002: repo markers must not imply full Master-V2 / trading-logic proof.
FI001_REPO_MARKERS: tuple[str, ...] = (
    "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false",
    "PAPER_TL_L2_PROVES_INFRASTRUCTURE_SAFETY_ONLY=true",
    "LINEAGE_EDGE_STEP0_TO_PAPER_TL_L2=MISSING_RUNTIME_BRIDGE",
)
FI002_REPO_MARKERS: tuple[str, ...] = (
    "PAPER_L2_120MIN_HOLD_BINDING_NO_TRADING_LOGIC_MUTATION=true",
    "PAPER_L2_120MIN_HOLD_BINDING_MASTER_V2_DOUBLE_PLAY_UNCHANGED=true",
    "PAPER_TL_L2_NOT_MASTER_V2_G5_L2=true",
)

FIXTURE_FALSE_CONFIDENCE_MARKERS: tuple[str, ...] = (
    "PAPER_TL_L2_STATUS=ACHIEVED",
    "UNQUALIFIED_L2_CLAIM_FORBIDDEN=true",
    "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false",
    "MASTER_V2_G5_L2_STATUS=NOT_STARTED_OR_EXTERNAL",
)

FORBIDDEN_DIFF_PREFIXES = (
    "src/strategies/",
    "scripts/double_play",
    "master_v2",
    "path_b",
)


def test_l2_120min_contract_profile_constant() -> None:
    text = L2_CONTRACT.read_text(encoding="utf-8")
    assert 'CONTRACT_PROFILE = "paper_l2_120min_hold_binding_v0"' in text
    assert "L2_DURATION_SECONDS = 7200" in text


def test_adapter_wires_l2_120min_profile_and_hold_env() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    assert "paper_l2_120min_hold_binding_approval_v0 as contract_l2_120min" in text
    assert "contract_l2_120min.CONTRACT_PROFILE" in text
    assert "SCHEDULER_HOLD_RUNTIME_OUTROOT_ENV" in text
    assert "SCHEDULER_HOLD_RUNTIME_RUN_ID_ENV" in text
    assert "_profiles_with_hold_runtime_env_bridge" in text


def test_scheduler_guard_exports_hold_runtime_env_names() -> None:
    text = GUARD.read_text(encoding="utf-8")
    assert "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_OUTROOT" in text
    assert "PEAK_TRADE_SCHEDULER_HOLD_RUNTIME_RUN_ID" in text
    assert "build_scheduler_hold_runtime_binding_v0" in text


def test_boundary_spec_references_l2_120min_profile_section() -> None:
    text = BOUNDARY_SPEC.read_text(encoding="utf-8")
    assert "paper_l2_120min_hold_binding_v0" in text
    assert "## 10b." in text


def _preflight_section_2a() -> str:
    text = PREFLIGHT.read_text(encoding="utf-8")
    return text.split("## 2a. Primary evidence retention invariant v0", 1)[1].split("## 2a.1", 1)[0]


def test_preflight_section_2a_reciprocal_crosslink_paper_l2_120min_v1() -> None:
    section = _preflight_section_2a()
    assert "paper_l2_120min_hold_binding_v0" in section
    assert "7200" in section
    assert "§10b" in section
    assert "gap4_req_a_paper_bounded_v0" in section
    assert "§10a" in section
    assert "fully implemented" in section.lower()
    assert "test_paper_l2_120min_hold_binding_profile_contract_v0.py" in section
    collapsed = section.replace("**", "")
    assert "does not authorize execute or preflight lift" in collapsed.lower()


def test_boundary_spec_declares_paper_tl_l2_namespace_guards() -> None:
    text = BOUNDARY_SPEC.read_text(encoding="utf-8")
    assert "PAPER_TL_L2_NOT_MASTER_V2_G5_L2=true" in text
    assert "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false" in text
    assert "PAPER_TL_L2_PROVES_INFRASTRUCTURE_SAFETY_ONLY=true" in text


def test_fixture_declares_paper_tl_l2_namespace_guard() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    assert "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false" in text
    assert "MASTER_V2_G5_L2_STATUS=NOT_STARTED_OR_EXTERNAL" in text
    assert "UNQUALIFIED_L2_CLAIM_FORBIDDEN=true" in text


def test_l2_contract_docstring_qualifies_paper_tl_namespace() -> None:
    text = L2_CONTRACT.read_text(encoding="utf-8")
    assert "Paper-TL-L2" in text
    assert "Master V2 G5-L2" in text


def test_pr_scope_excludes_trading_and_double_play_paths() -> None:
    touched = [
        ADAPTER,
        L2_CONTRACT,
        ROOT / "tests" / "ops" / "test_run_paper_only_bounded_observation_adapter_v0.py",
        SELF,
    ]
    for path in touched:
        rel = path.relative_to(ROOT).as_posix().lower()
        for forbidden in FORBIDDEN_DIFF_PREFIXES:
            assert forbidden not in rel


def test_false_confidence_static_crosslink_package_marker_v0() -> None:
    text = SELF.read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text


def test_false_confidence_archive_charter_authority_path_constant_v0() -> None:
    """Archive charter is external authority; repo test anchors path only (no CI filesystem)."""
    text = SELF.read_text(encoding="utf-8")
    assert "ARCHIVE_FALSE_CONFIDENCE_CHARTER_BUNDLE" in text
    assert ARCHIVE_ROOT in text
    assert "false_confidence_interpretation_guard_after_systemwide_safe_scope_inventory" in text
    assert "operator_go_autofill_no_run_v1_20260611T111453Z" in text
    assert ARCHIVE_FALSE_CONFIDENCE_CHARTER_BUNDLE == (
        f"{ARCHIVE_ROOT}/charter/"
        "false_confidence_interpretation_guard_after_systemwide_safe_scope_inventory_"
        "operator_go_autofill_no_run_v1_20260611T111453Z"
    )


def test_boundary_spec_retains_paper_tl_l2_p0_marker_set_v0() -> None:
    text = BOUNDARY_SPEC.read_text(encoding="utf-8")
    section_start = text.index("## 10b.")
    section_text = text[section_start : section_start + 2500]
    for marker in BOUNDARY_SPEC_P0_MARKERS:
        assert marker in section_text, f"missing §10b P0 marker: {marker}"


def test_fixture_retains_false_confidence_namespace_guards_v0() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    for marker in FIXTURE_FALSE_CONFIDENCE_MARKERS:
        assert marker in text, f"missing fixture false-confidence marker: {marker}"
    assert "not Master V2 / Double Play runtime" in text


def test_false_confidence_fi001_fi002_reflected_in_repo_markers_v0() -> None:
    boundary = BOUNDARY_SPEC.read_text(encoding="utf-8")
    fixture = FIXTURE.read_text(encoding="utf-8")
    for marker in FI001_REPO_MARKERS:
        assert marker in boundary, f"FI-001 boundary marker missing: {marker}"
    assert "PAPER_TL_L2_STATUS=ACHIEVED" in fixture
    for marker in FI002_REPO_MARKERS:
        assert marker in boundary, f"FI-002 boundary marker missing: {marker}"
    assert "UNQUALIFIED_L2_CLAIM_FORBIDDEN=true" in fixture


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def test_docs_truth_map_pr4123_semantic_claim_guard_chronicle_v0() -> None:
    """DOCS_TRUTH_MAP must record PR #4123 semantic claim boundary guard on main."""
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(truth_map, "PR #4123 —")

    for required in (
        "semantic claim",
        "PAPER_TL_L2_PROVES_INFRASTRUCTURE_SAFETY_ONLY=true",
        "PAPER_TL_L2_PROVES_MASTER_V2_RUNTIME=false",
        "SEMANTIC_LINEAGE_VERDICT=PARTIAL",
        "FULL_MASTER_V2_DOUBLE_PLAY_SEMANTIC_LINEAGE_VERIFIED=false",
        "non-authorizing",
    ):
        assert required.lower() in row.lower()


def test_docs_truth_map_pr4124_false_confidence_guard_chronicle_v0() -> None:
    """DOCS_TRUTH_MAP must record PR #4124 FALSE_CONFIDENCE crosslink guard on main."""
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(truth_map, "PR #4124 —")

    for required in (
        "FALSE_CONFIDENCE",
        "FALSE_CONFIDENCE_INTERPRETATION_GUARD_REPO_STATIC_CROSSLINK_V0=true",
        "OPEN_GUARD_CHARTER_GAP=false",
        "non-authorizing",
    ):
        assert required.lower() in row.lower()


def test_docs_truth_map_paper_l2_guard_stack_chronicle_v0() -> None:
    """DOCS_TRUTH_MAP must record Paper-L2 guard stack CLOSED on main."""
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map, "Paper-L2 semantic + FALSE_CONFIDENCE + Venv guard stack"
    )

    for required in (
        "b585b351",
        "PR #4123–#4125",
        "GUARD_REGRESSION_ON_MAIN=false",
        "SEMANTIC_LINEAGE_VERDICT=PARTIAL",
        "non-authorizing",
    ):
        assert required.lower() in row.lower()
