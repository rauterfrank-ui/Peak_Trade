"""Static docs guard for external Remote Runtime Charter v0 reflection.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md and DOCS_TRUTH_MAP only. Never starts
runtime, touches AWS/S3/Notion/Market production surfaces, or grants GO.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
THIS_MODULE = Path(__file__).name

CHARTER_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/remote_runtime_charter_v0_20260601T120000Z"
)
CONSOLIDATION_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/remote_runtime_consolidation_after_cyber_input_blocked_v0_20260601T110000Z"
)
LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/local_dry_host_no_run_preflight_charter_v0_20260601T024302Z"
)

GUARD_BLOCK_ANCHOR = "REMOTE_RUNTIME_EXTERNAL_CHARTER_CONTRACT_DOCS_GUARD_V0=true"
LOCAL_DRY_HOST_GUARD_BLOCK_ANCHOR = "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_CHARTER_REFLECTION_V0=true"

GUARD_EXPECTED: dict[str, str] = {
    "REMOTE_RUNTIME_IS_BACKEND": "true",
    "LOCAL_REPO_GATES_REMAIN_AUTHORITATIVE": "true",
    "REMOTE_HOST_HAS_NO_INDEPENDENT_AUTHORITY": "true",
    "S3_AS_FINALIZED_EVIDENCE_TRANSPORT_ONLY": "true",
    "NOTION_AS_PROJECTION_ONLY": "true",
    "MARKET_DASHBOARD_AS_READONLY_PROJECTION_ONLY": "true",
    "MAX_RUNTIME_SECONDS_REQUIRED": "true",
    "FINALIZED_EVIDENCE_REQUIRED": "true",
    "DURABLE_COPY_REQUIRED": "true",
    "MANIFEST_VERIFY_REQUIRED": "true",
    "CYBER_INPUT_JSONL_BLOCKED": "true",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PATH_B_LIFT_DISCUSSION_READY": "false",
    "GLOBAL_PREFLIGHT_LIFTED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "PAPER_STARTED": "false",
    "SHADOW_STARTED": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "NOTION_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "PRODUCTION_CODE_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PARALLEL_BUILDS_CREATED": "false",
    "REMOTE_RUNTIME_EXTERNAL_CHARTER_CONTRACT_DOCS_GUARD_DOCS_TESTS_ONLY": "true",
}
LOCAL_DRY_HOST_GUARD_EXPECTED: dict[str, str] = {
    "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_CHARTER_REFLECTION_V0": "true",
    "LOCAL_DRY_HOST_SCOPE_READY": "true",
    "BACKEND_TARGET": "local-only-dry-host",
    "COST_CEILING": "0_EUR_CLOUD_SPEND",
    "REMOTE_RUNTIME_GO": "false",
    "NO_RUN_CHARTER": "true",
    "FUTURE_OPERATOR_GO_REQUIRED": "true",
    "MAX_RUNTIME_SECONDS_REQUIRED": "true",
    "NO_ACTIVE_RUN_CHECK_REQUIRED": "true",
    "ORPHAN_PROCESS_CHECK_REQUIRED": "true",
    "PRIMARY_EVIDENCE_REQUIRED": "true",
    "DURABLE_COPY_REQUIRED": "true",
    "MANIFEST_VERIFY_REQUIRED": "true",
    "CLOSEOUT_REQUIRED": "true",
    "TMP_ONLY_EVIDENCE_ACCEPTED": "false",
    "SECRETS_INCLUDED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "NOTION_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "PAPER_STARTED": "false",
    "SHADOW_STARTED": "false",
    "TESTNET_STARTED": "false",
    "LIVE_STARTED": "false",
    "PRODUCTION_CODE_TOUCHED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PATH_B_LIFT_DISCUSSION_READY": "false",
    "GLOBAL_PREFLIGHT_LIFTED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PARALLEL_BUILDS_CREATED": "false",
    "LOCAL_DRY_HOST_NO_RUN_PREFLIGHT_DOCS_TESTS_ONLY": "true",
}

RECIPROCAL_OWNER_TESTS = (
    "test_remote_runtime_host_metadata_contract_v0.py",
    "test_s3_finalized_evidence_export_gate_v0.py",
    "test_scheduler_boundary_hard_block_contract_v0.py",
    "test_notion_post_closeout_sync_projection_spec_v0.py",
    "test_market_dashboard_readonly_run_projection_spec_v0.py",
    "test_ops_cockpit_payload_top_level_contract.py",
)

OPS_COCKPIT_OPERATOR_SUMMARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md"
)
OC1_PLANNING_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/ops_cockpit_operator_status_index_rc_v0_slice_oc1_docs_only_20260602T182955Z/"
)
OC_RELEASE_RC_INDEX_HEADING = "## Ops Cockpit / Operator Status Index RC v0 — meta-index v0"
OC_RELEASE_RC_BLOCK_ANCHOR = "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0=true"
OC_RELEASE_RC_EXPECTED: dict[str, str] = {
    "OPS_COCKPIT_OR_OPERATOR_STATUS_INDEX_RC_V0": "true",
    "SLICE_OC1_DOCS_ONLY": "true",
    "OPERATOR_EXPERIENCE_RELEASE_RC_V0_CORE_DONE": "true",
    "CYBERSECURITY_VISIBILITY_RELEASE_RC_V0_CORE_DONE": "true",
    "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0_CORE_DONE": "true",
    "ER_SSOT_PREFLIGHT_POINTER_ONLY": "true",
    "ER3_REPO_FOLLOWUP_DEFERRED": "true",
    "OPS_COCKPIT_REFLECTION_ONLY": "true",
    "OPS_COCKPIT_AUTHORITY_CHANGED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "STOP_IDLE_PRESERVED": "true",
    "RETENTION_ENFORCEMENT_ACTIVATED": "false",
    "NOTION_AS_MIRROR_ONLY": "true",
    "NOTION_WRITES": "false",
    "WORKFLOW_DISPATCH_EXECUTED": "false",
    "NO_RUNTIME": "true",
    "NO_TRADING_AUTHORITY_CHANGE": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "DOUBLE_PLAY_LOGIC_CHANGED": "false",
    "PARALLEL_OPERATOR_STATUS_INDEX_CREATED": "false",
}

FORBIDDEN_PARALLEL_DOC_FRAGMENTS = (
    "REMOTE_RUNTIME_HOST_CONTRACT_V0.md",
    "REMOTE_RUNTIME_CONSOLIDATION_V0.md",
    "REMOTE_RUNTIME_RUNBOOK_V0.md",
    "REMOTE_RUNTIME_AUTHORITY_V0.md",
)

FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def _ci_audit_text() -> str:
    return CI_AUDIT.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[str]:
    return [block.strip() for block in FENCED_BLOCK_RX.findall(text)]


def _block_containing(text: str, anchor: str) -> str:
    for block in _fenced_blocks(text):
        if anchor in block:
            return block
    raise AssertionError(f"missing fenced machine-line block containing {anchor!r}")


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key and value:
            values[key.strip()] = value.strip()
    return values


def test_ci_audit_remote_runtime_charter_section_present() -> None:
    text = _ci_audit_text()
    assert "## Remote Runtime Contract — external charter reflection v0" in text
    assert "### Remote Runtime external charter docs guard v0" in text
    assert CHARTER_PATH in text
    assert CONSOLIDATION_PATH in text
    assert THIS_MODULE in text


def test_ci_audit_guard_machine_lines() -> None:
    block = _block_containing(_ci_audit_text(), GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing guard keys: {sorted(missing)}"
    for key, expected in GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_local_dry_host_no_run_section_present() -> None:
    text = _ci_audit_text()
    assert "## Local Dry Host No-Run Preflight Charter — external reflection v0" in text
    assert "### Local dry host no-run preflight docs guard v0" in text
    assert LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH in text
    assert "no parallel local-dry-host runtime anchor" in text.lower()


def test_ci_audit_local_dry_host_guard_machine_lines() -> None:
    block = _block_containing(_ci_audit_text(), LOCAL_DRY_HOST_GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(LOCAL_DRY_HOST_GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing local dry host guard keys: {sorted(missing)}"
    for key, expected in LOCAL_DRY_HOST_GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_reuses_canonical_owners_not_parallel_surfaces() -> None:
    text = _ci_audit_text()
    section_start = text.index("## Remote Runtime Contract — external charter reflection v0")
    section = text[section_start:]
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md" in section
    assert "primary_evidence_retention_v0.py" in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "no parallel remote-runtime anchor" in section.lower()
    assert "does **not** bypass Cyber" in section or "does not bypass Cyber" in section


def test_docs_truth_map_chronicle_references_guard_and_charter() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert THIS_MODULE in text
    assert "Remote Runtime external charter reflection docs guard v0" in text
    assert "Local Dry Host no-run preflight charter reflection docs guard v0" in text
    assert "REMOTE_RUNTIME_IS_BACKEND=true" in text
    assert "LOCAL_DRY_HOST_SCOPE_READY=true" in text
    assert "FORBIDDEN_NEW_SURFACES=0" in text
    assert CHARTER_PATH.split("/")[-1] in text or "120000Z" in text
    assert LOCAL_DRY_HOST_PREFLIGHT_CHARTER_PATH.split("/")[-1] in text or "024302Z" in text


def test_taxonomy_section_6a_backend_tokens_preserved() -> None:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    assert "REMOTE_RUNTIME_IS_BACKEND_NOT_LANE=true" in text
    assert "S3_FINALIZED_EVIDENCE_TRANSPORT_ONLY=true" in text
    assert "NOTION_PROJECTION_NON_AUTHORIZING=true" in text
    assert "MARKET_DASHBOARD_PROJECTION_READONLY=true" in text


def test_reciprocal_owner_crosslinks_present() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    for module_name in RECIPROCAL_OWNER_TESTS:
        assert module_name in owner_text, f"missing reciprocal owner {module_name!r}"
        peer_text = (REPO_ROOT / "tests" / "ops" / module_name).read_text(encoding="utf-8")
        assert THIS_MODULE in peer_text, f"{module_name} missing reciprocal link to {THIS_MODULE}"


def test_no_parallel_remote_runtime_authority_docs_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    runbooks_dir = REPO_ROOT / "docs" / "ops" / "runbooks"
    for fragment in FORBIDDEN_PARALLEL_DOC_FRAGMENTS:
        assert list(specs_dir.glob(f"*{fragment}*")) == [], fragment
        assert list(runbooks_dir.glob(f"*{fragment}*")) == [], fragment


def test_guard_module_declares_non_authorization() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert "Never starts runtime" in text or "Never starts" in text
    assert "grants GO" in text or "grants go" in text.lower()


def _oc_release_rc_index_section(text: str) -> str:
    start = text.find(OC_RELEASE_RC_INDEX_HEADING)
    assert start != -1, "missing Ops Cockpit / Operator Status Index RC v0 meta-index section"
    return text[start:]


def test_ci_audit_ops_cockpit_operator_status_index_rc_v0_section_present() -> None:
    text = _ci_audit_text()
    section = _oc_release_rc_index_section(text)
    assert "SLICE-OC-1" in section
    assert "SLICE-OC-2" in section
    assert "docs/tests-only" in section
    assert "OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "does **not** duplicate ER body" in section or "does not duplicate ER body" in section
    assert OPS_COCKPIT_OPERATOR_SUMMARY_SPEC.name in section
    assert OC1_PLANNING_BUNDLE_PATH in section
    assert "parallel operator-status hub" in section.lower()
    assert THIS_MODULE not in section


def test_ci_audit_ops_cockpit_operator_status_index_machine_lines() -> None:
    text = _ci_audit_text()
    block = _block_containing(text, OC_RELEASE_RC_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(OC_RELEASE_RC_EXPECTED) - values.keys()
    assert not missing, f"missing OC release RC keys: {sorted(missing)}"
    for key, expected in OC_RELEASE_RC_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_ci_audit_ops_cockpit_operator_status_index_er_preflight_pointer_only() -> None:
    section = _oc_release_rc_index_section(_ci_audit_text())
    assert "ER SSOT — pointer only" in section or "ER SSOT" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "Operator Experience Release RC v0" in section
    assert "Cybersecurity Visibility Release RC v0" in section
    assert "Evidence Durable Closeout Retention RC v0" in section


def test_ci_audit_ops_cockpit_operator_status_index_slice_oc2_guard_owner_v0() -> None:
    section = _oc_release_rc_index_section(_ci_audit_text())
    assert "SLICE-OC-2" in section
    assert "test_ops_cockpit_" in section
    assert "test_ops_cockpit_" in section
    assert "extend existing" in section.lower() or "Tests-ops" in section
