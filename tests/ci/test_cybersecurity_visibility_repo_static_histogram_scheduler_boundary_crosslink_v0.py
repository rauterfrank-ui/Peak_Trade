"""Static contract for Cybersecurity Visibility repo-static histogram scheduler-boundary crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
touches runtime, scheduler, daemon, adapter, hooks, launchctl, Notion, Market,
broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.ci.cybersecurity_visibility_retained_risk_row_assertions_v0 import (
    assert_retained_r001_r002_r007_pending_or_derived_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

HISTOGRAM_CLASSIFICATION = "scheduler_or_runtime_boundary"
HISTOGRAM_ROW_RX = re.compile(
    rf"^\| `{re.escape(HISTOGRAM_CLASSIFICATION)}` \| (\d+) \| (.+) \|$",
    re.MULTILINE,
)
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)

REQUIRED_SCHEDULER_REUSE_OWNERS: tuple[str, ...] = (
    "tests/ops/test_scheduler_boundary_hard_block_contract_v0.py",
    "tests/ops/test_p67_library_scheduler_boundary_opt_in_v0.py",
)
GROUPING_REFLECTION_GUARD_MODULE = "tests/ci/test_csc_rchain_v1_grouping_reflection_contract_v0.py"
ACCEPTED_SUBGROUP_002_INFRA = "CSC-RCHAIN-v1-002-infra"
ACCEPTED_SUBGROUP_002_INTEGRATION = "CSC-RCHAIN-v1-002-integration"
ACCEPTED_SUBGROUP_002_P101 = "CSC-RCHAIN-v1-002-p101"
ACCEPTED_SUBGROUP_002_P117 = "CSC-RCHAIN-v1-002-p117"
ACCEPTED_SUBGROUP_002_P50 = "CSC-RCHAIN-v1-002-p50"
GOVERNED_REFLECTION_SUBGROUP_003F_A = "CSC-RCHAIN-v1-003f-A"
OPERATOR_ACCEPT_003F_A_SLICE_1 = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/operator_accept_artifact_csc_rchain_003f_a_slice_1_v0_20260602T202456Z"
)
NARROWING_BASENAMES_003F_A: tuple[str, ...] = (
    "network_gate.py",
    "shadow_session_scheduler_v1.py",
    "run_shadowloop_pack_v1.py",
)
CANDIDATE_IDS_003F_A: tuple[str, ...] = (
    "CSC-LOSSLESS-v1-000264",
    "CSC-LOSSLESS-v1-000265",
    "CSC-LOSSLESS-v1-000266",
    "CSC-LOSSLESS-v1-000267",
    "CSC-LOSSLESS-v1-000268",
    "CSC-LOSSLESS-v1-000293",
    "CSC-LOSSLESS-v1-000294",
    "CSC-LOSSLESS-v1-000308",
    "CSC-LOSSLESS-v1-000309",
    "CSC-LOSSLESS-v1-000310",
    "CSC-LOSSLESS-v1-000311",
    "CSC-LOSSLESS-v1-000312",
    "CSC-LOSSLESS-v1-000313",
    "CSC-LOSSLESS-v1-000314",
    "CSC-LOSSLESS-v1-000315",
    "CSC-LOSSLESS-v1-000316",
    "CSC-LOSSLESS-v1-000326",
    "CSC-LOSSLESS-v1-000327",
    "CSC-LOSSLESS-v1-000328",
    "CSC-LOSSLESS-v1-000329",
)

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "scheduler start authorized",
    "runtime start authorized",
    "testnet approved",
    "live approved",
    "operator bypass",
    "ready_for_start=true",
    "preflight_blocked_lifted=true",
)


def _ci_audit_text() -> str:
    assert CI_AUDIT_KNOWN_ISSUES.is_file()
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _histogram_section(text: str) -> str:
    start = text.find("**Interim classification histogram")
    assert start != -1, "histogram section missing"
    end = text.find("**Lossless recovery still required")
    assert end != -1, "histogram section end missing"
    return text[start:end]


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def _csc_rchain_accepted_groups_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1 accepted groups reflection guard v0")
    end_marker = "### CSC-RCHAIN-v1-003f-A governed reflection guard v0"
    if end_marker in text[start:]:
        end = text.index(end_marker, start)
    else:
        end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _csc_rchain_003f_a_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1-003f-A governed reflection guard v0")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def test_cybersecurity_visibility_repo_static_histogram_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_V0=true"
        in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "24"
    notes_cell = match.group(2)
    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert f"Reuse `{owner_path}`" in notes_cell
        assert (REPO_ROOT / owner_path).is_file(), f"missing reuse owner module: {owner_path}"

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert owner_path in reuse_paths

    assert_retained_r001_r002_r007_pending_or_derived_evidence(_risk_table_rows(text))

    for owner_path in REQUIRED_SCHEDULER_REUSE_OWNERS:
        assert owner_path in text

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text

    guard_block = _csc_rchain_accepted_groups_guard_block(text)
    assert ACCEPTED_SUBGROUP_002_INFRA in guard_block
    assert ACCEPTED_SUBGROUP_002_INTEGRATION in guard_block
    assert ACCEPTED_SUBGROUP_002_P101 in guard_block
    assert ACCEPTED_SUBGROUP_002_P117 in guard_block
    assert ACCEPTED_SUBGROUP_002_P50 in guard_block
    assert GROUPING_REFLECTION_GUARD_MODULE in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT=23" in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT=258" in guard_block
    assert "CSC_RCHAIN_V1_HYBRID_AUTHORITY_POINTER_ACTIVE=true" in guard_block
    assert (
        "csc_rchain_v1_external_full_authority_bundle_draft_and_wiring_check_readonly_v0_20260601T104257Z"
        in guard_block
    )
    assert "CSC_RCHAIN_V1_002_P63_ACCEPTED=false" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE=true" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT=238" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_SUBSET_OF_PARK=true" in guard_block
    assert (
        "csc_rchain_v1_post_ops_closeout_contracts_batch_authority_refresh_and_next_batch_ranking_readonly_v0_20260601T133828Z"
        in guard_block
    )
    assert "reviewed-prepared-only" in guard_block.lower()
    assert (
        "does **not** authorize observability/logging/decision-context/execution/runtime/scheduler/shadow/online-readiness"
        in guard_block
    )
    assert "CSC-RCHAIN-v1-002-infra" in guard_block
    assert "parent **002** remains PARK" in guard_block
    assert "network escalation is authorized" not in collapsed
    assert "network enablement" not in collapsed
    assert "live enablement (`LIVE=1` appears only as refusal-test context)" in text
    assert "kill-switch bypass" in text
    assert "p101 stop-playbook semantics changes" in text
    assert "exec-evidence collection enablement" in text
    assert "launchctl execution enablement" in text
    assert "p117 ops-loop semantics changes" in text
    assert "AI model enablement authorization" in text
    assert "AI model policy semantics changes" in text
    assert "PEAKTRADE_STAGE=testnet` enablement" in text

    accepted_line = next(
        line for line in guard_block.splitlines() if line.startswith("CSC_RCHAIN_V1_ACCEPTED_GROUPS=")
    )
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A not in accepted_line


def test_csc_rchain_v1_003f_a_governed_reflection_scheduler_boundary_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    block = _csc_rchain_003f_a_guard_block(text)

    assert "CSC_RCHAIN_V1_003F_A_GOVERNED_REFLECTION_SLICE1_V0=true" in block
    assert "CSC_RCHAIN_V1_003F_A_REFLECTION_DOCS_TESTS_ONLY=true" in block
    assert "CSC_RCHAIN_V1_003F_A_CANDIDATE_COUNT=20" in block
    assert "CSC_RCHAIN_V1_003F_A_EXTERNAL_ACCEPT_READY_COUNT=17" in block
    assert "CSC_RCHAIN_V1_003F_A_NARROWING_REQUIRED_COUNT=3" in block
    assert "CSC_RCHAIN_V1_003F_A_PARK_RETAINED=true" in block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT_UNCHANGED=true" in block
    assert "CSC_RCHAIN_V1_PARK_COUNT_UNCHANGED=true" in block
    assert "REPO_GO_TOKEN=REPO_GO-CSC-RCHAIN-003F-A-SLICE-1" in block
    assert "NO_AWS_NO_NETWORK_OPS=true" in block
    assert "NO_SHADOW_SCHEDULER_EXECUTION=true" in block
    assert "NO_SHADOWLOOP_START=true" in block
    assert "NETWORK_GATE_VISIBILITY_ONLY=true" in block
    assert OPERATOR_ACCEPT_003F_A_SLICE_1 in block
    assert GOVERNED_REFLECTION_SUBGROUP_003F_A in block
    assert THIS_MODULE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block

    for basename in NARROWING_BASENAMES_003F_A:
        assert basename in block
    assert "CSC-LOSSLESS-v1-000264" in block
    assert "000293`–`000294" in block
    assert "000312`–`000316" in block
    assert "000326`–`000329" in block
    assert len(CANDIDATE_IDS_003F_A) == 20

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=258" in text
    assert "CSC_RCHAIN_V1_PARK_COUNT=413" in text
    assert "scheduler start authorized" not in collapsed
    assert "shadowloop start authorized" not in collapsed


def test_cybersecurity_visibility_repo_static_histogram_scheduler_boundary_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert (
        "Cybersecurity Visibility repo-static histogram scheduler-boundary owner crosslink v0"
        in truth_map
    )
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_SCHEDULER_BOUNDARY_CROSSLINK_V0=true"
        in truth_map
        or "scheduler-boundary owner crosslink" in collapsed
    )
    assert "non-authorizing" in collapsed
    assert "input_jsonl_provided=false" in collapsed or "INPUT_JSONL_PROVIDED=false" in truth_map
