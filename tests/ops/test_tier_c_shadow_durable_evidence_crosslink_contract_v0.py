"""Static crosslink contract for Tier-C + Shadow durable evidence (v0).

Anchors operator-verified archive bundles into canonical Preflight and Section-5
surfaces. Read-only file-content tests — does not authorize runtime, lifts, or
Testnet execution.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SECTION5 = REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
SELF = Path(__file__).resolve()

ARCHIVE_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)

PACKAGE_MARKER = "TIER_C_SHADOW_DURABLE_EVIDENCE_REPO_STATIC_CROSSLINK_V0=true"

ARCHIVE_BUNDLE_SUFFIXES: tuple[str, ...] = (
    "planning/repo_wide_next_system_step_ranking_after_class4_stop_idle_v0_20260603T175350Z/",
    "runtime/gap2a1_tier1_scheduler_tier_c_positive_manifest_execute_retry_v0_20260603T172211Z/",
    "closeout/gap2a1_tier1_scheduler_tier_c_positive_manifest_post_execute_closeout_and_non_stop_ranking_v0_20260603T172509Z/",
    "runtime/shadow_bounded_dryrun_rehearsal_execute_v0_20260603T172859Z/",
    "runs/shadow/shadow_bounded_dryrun_rehearsal_20260603T172859Z/",
    "closeout/shadow_bounded_dryrun_rehearsal_post_execute_closeout_and_non_stop_ranking_v0_20260603T173011Z/",
    "closeout/class4_external_final_decision_matrix_no_run_v0_20260603T174338Z/",
    "closeout/section5_no_lift_sequence_final_closeout_and_class4_decision_menu_v0_20260603T164910Z/",
)

NON_AUTHORIZING_TOKENS: tuple[str, ...] = (
    PACKAGE_MARKER,
    "TIER_C_POSITIVE_MANIFEST_FINALIZE_CONFIRMED=true",
    "TIER_A_FAIL_CLOSED_CONFIRMED=true",
    "TIER_B_PREFLIGHT_BLOCK_FAIL_CLOSED_CONFIRMED=true",
    "SHADOW_DRYRUN_REHEARSAL_CONFIRMED=true",
    "SHADOW_PRIMARY_EVIDENCE_DURABLE_CONFIRMED=true",
    "SHADOW_HOLD_READINESS_HOLD=true",
    "SHADOW_HOLD_LIFTED=false",
    "PREFLIGHT_LIFT_DIRECTLY_ALLOWED=false",
    "BL002_PATH_B_DIRECTLY_ALLOWED=false",
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "TESTNET_NOW_RECOMMENDED=false",
    "TRADING_ACTION=false",
    "ORDERS_CREATED=false",
    "NETWORK_USED=false",
    "PAPER_TEST_DATA_TOUCHED=false",
    "EVIDENCE_ARCHIVE_ANCHOR_NOT_RUNTIME_AUTHORITY=true",
)

FORBIDDEN_AUTHORITY_CLAIMS: tuple[str, ...] = (
    "preflight lifted",
    "shadow-hold lifted",
    "ready for operator arming=true",
    "runtime approved=true",
    "testnet now recommended=true",
    "normal_testnet_run_allowed_now=true",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical surface: {path}"
    return path.read_text(encoding="utf-8")


def test_package_marker_present_v0() -> None:
    assert PACKAGE_MARKER in _read(SELF)


def test_section5_tier_c_shadow_crosslink_block_v0() -> None:
    text = _read(SECTION5)
    assert "## Tier-C + Shadow durable evidence archive crosslink v0" in text
    for suffix in ARCHIVE_BUNDLE_SUFFIXES:
        assert f"{ARCHIVE_ROOT}/{suffix}" in text
    for token in NON_AUTHORIZING_TOKENS:
        assert token in text
    assert "tests/ops/test_tier_c_shadow_durable_evidence_crosslink_contract_v0.py" in text


def test_preflight_tier_c_shadow_crosslink_block_v0() -> None:
    text = _read(PREFLIGHT)
    assert "### Tier-C + Shadow durable evidence archive anchors (non-authorizing) v0" in text
    for suffix in ARCHIVE_BUNDLE_SUFFIXES:
        assert f"{ARCHIVE_ROOT}/{suffix}" in text
    for token in NON_AUTHORIZING_TOKENS:
        assert token in text
    assert "tests/ops/test_tier_c_shadow_durable_evidence_crosslink_contract_v0.py" in text


def test_crosslink_docs_do_not_claim_runtime_authority_v0() -> None:
    combined = _read(SECTION5) + _read(PREFLIGHT)
    lower = combined.lower()
    for claim in FORBIDDEN_AUTHORITY_CLAIMS:
        assert claim not in lower, f"forbidden authority claim found: {claim!r}"


def test_crosslink_reuses_canonical_owners_not_parallel_surfaces_v0() -> None:
    section5 = _read(SECTION5)
    preflight = _read(PREFLIGHT)
    for owner in (
        "scripts/ops/primary_evidence_retention_v0.py",
        "tests/ops/test_gap2a1_primary_evidence_enforcement_contract_v0.py",
        "tests/ops/test_bounded_observation_review_durable_primary_evidence_contract_v0.py",
    ):
        assert owner in section5 or owner in preflight
