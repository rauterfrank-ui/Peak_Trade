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
PREFLIGHT_PROCESS_GATE_HYGIENE_HEADING = (
    "## Preflight Process Gate Hygiene — active-run false-positive guard v0"
)
PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_BLOCK_ANCHOR = "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1=true"
PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_pr4153_closeout_select_single_next_safe_slice_no_run_v1_20260612T000800Z"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_HEADING = (
    "## Order-Capability remaining readiness gap review — docs/tests-only visibility v1"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_GUARD_BLOCK_ANCHOR = (
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1=true"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_preflight_process_gate_hygiene_guard_merge_no_run_v1_20260612T002508Z"
)
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED: dict[str, str] = {
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1": "true",
    "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_DOCS_TESTS_ONLY": "true",
    "ORDER_CAPABILITY_PARKED_READ_ONLY_CONFIRMED": "true",
    "ORDER_CAPABILITY_EXISTING_CROSSLINK_GUARDS_REFERENCED": "true",
    "FIXTURE_BINDING_CROSSLINK_GUARD_REFERENCED": "true",
    "DEMO_INSTRUMENT_RULES_NORMALIZER_CROSSLINK_GUARD_REFERENCED": "true",
    "REMAINING_CONTRACT_SURFACES_INDEXED": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "NO_PREFLIGHT_LIFT": "true",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "AUTHORITY_LIFT": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "RISK_KILLSWITCH_SCOPE_CAPITAL_TOUCHED": "false",
    "NEW_PARALLEL_SSOT_CREATED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "ORDERFLOW_AUTHORIZATION_CREATED": "false",
    "CANCEL_EXECUTE_AUTHORIZATION_CREATED": "false",
    "READY_FOR_OPERATOR_ARMING_CHANGED": "false",
    "RUNTIME_LOGIC_TOUCHED": "false",
    "JSONL_EVIDENCE_DATASET_MUTATION": "false",
    "WORKFLOW_TOUCHED": "false",
    "MARKET_DASHBOARD_TOUCHED": "false",
}
ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_OWNER_TESTS = (
    "test_order_capability_payload_builder_contract_v1.py",
    "test_order_capability_dry_validation_contract_v1.py",
    "test_order_capability_killswitch_abort_binding_contract_v1.py",
    "test_order_capability_cancel_cleanup_failclosed_contract_v1.py",
    "test_order_capability_offline_payload_readiness_v1.py",
    "test_order_capability_private_endpoint_boundary_contract_v1.py",
    "test_order_capability_side_price_qty_rules_contract_v1.py",
    "test_order_capability_demo_instrument_rules_binding_contract_v1.py",
    "test_run_order_capability_fixture_binding_dry_validation_v1.py",
    "test_order_capability_demo_instrument_rules_fixture_normalizer_contract_v1.py",
)
PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED: dict[str, str] = {
    "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1": "true",
    "ACTIVE_RUN_CHECK_PEAK_TRADE_EXPLICIT_ONLY": "true",
    "ACTIVE_RUN_EXCLUDE_MACOS_SYSTEM_SUBSTRING_FALSE_POSITIVES": "true",
    "ACTIVE_RUN_EXCLUDE_SHELL_CURSOR_SELF_MATCH": "true",
    "UNTRACKED_DOT_PYTHON_VERSION_TOLERATED_WHEN_TRACKED_CLEAN": "true",
    "UNTRACKED_DOT_PYTHON_VERSION_MUST_NOT_BE_COMMITTED_OR_DELETED_BY_AUTOMATION": "true",
    "NO_RUNTIME": "true",
    "NO_LIVE": "true",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PREFLIGHT_LIFT": "false",
    "ORDER_CANCEL_EXECUTION_ARMING_TOUCHED": "false",
    "TRADING_LOGIC_TOUCHED": "false",
    "MASTER_V2_LOGIC_TOUCHED": "false",
    "DOUBLE_PLAY_LOGIC_TOUCHED": "false",
    "PARALLEL_DOCS_CREATED": "false",
    "PREFLIGHT_PROCESS_GATE_HYGIENE_DOCS_TESTS_ONLY": "true",
}

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
    "test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py",
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

MV2_READONLY_ALIGNMENT_RC_HEADING = (
    "## Master V2 / Double Play Read-only Alignment Inventory RC v0 — docs reflection v0"
)
MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR = (
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0=true"
)
MV2_READONLY_ALIGNMENT_RC_EXPECTED: dict[str, str] = {
    "MASTER_V2_DOUBLE_PLAY_READONLY_ALIGNMENT_INVENTORY_RC_V0": "true",
    "SLICE_MV2_1_DOCS_REFLECTION_ONLY": "true",
    "RUNTIME_PRODUCER_PARKING_LIFTED": "false",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "STOP_IDLE_PRESERVED": "true",
    "NO_RUNTIME": "true",
    "MASTER_V2_LOGIC_CHANGED": "false",
    "DOUBLE_PLAY_LOGIC_CHANGED": "false",
    "TRADING_AUTHORITY_CHANGED": "false",
    "PARALLEL_MASTER_V2_ALIGNMENT_INDEX_CREATED": "false",
    "FOLLOWUP_DOCS_SLICE_NEEDED": "false",
    "FOLLOWUP_TEST_GUARD_NEEDED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "LIVE_TOUCHED": "false",
    "READY_FOR_OPERATOR_ARMING": "false",
}
PURE_STACK_READINESS_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
)
MV2_PURE_STACK_GUARD = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py"
)

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


def test_ci_audit_preflight_process_gate_hygiene_section_present_v1() -> None:
    text = _ci_audit_text()
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_HEADING in text
    assert "### Preflight process gate hygiene docs guard v0" in text
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE in text
    assert "liveactivitiesd" in text
    assert "dns-result-order" in text
    assert "PhotosReliveWidget" in text
    assert "Shell/Cursor self-match" in text
    assert "untracked root `.python-version`" in text
    assert "must **not** commit or delete it blindly" in text
    assert THIS_MODULE in text
    assert "no parallel preflight hygiene anchor" in text.lower()


def test_ci_audit_preflight_process_gate_hygiene_machine_lines_v1() -> None:
    block = _block_containing(_ci_audit_text(), PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED) - values.keys()
    assert not missing, f"missing preflight process gate hygiene keys: {sorted(missing)}"
    for key, expected in PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_preflight_process_gate_hygiene_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Preflight process gate hygiene guard v1" in text
    assert THIS_MODULE in text
    assert "precise Peak_Trade active-run detection" in text
    assert "shell/Cursor self-match exclusion" in text
    assert "tolerated untracked root `.python-version` when tracked clean" in text
    assert "PREFLIGHT_PROCESS_GATE_HYGIENE_GUARD_V1=true" in text
    assert PREFLIGHT_PROCESS_GATE_HYGIENE_INPUT_BUNDLE.split("/")[-1] in text


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


def _mv2_readonly_alignment_rc_section(text: str) -> str:
    start = text.find(MV2_READONLY_ALIGNMENT_RC_HEADING)
    assert start != -1, "missing Master V2 readonly alignment RC v0 section"
    return text[start:]


def test_ci_audit_mv2_readonly_alignment_rc_section_present_v0() -> None:
    text = _ci_audit_text()
    section = _mv2_readonly_alignment_rc_section(text)
    assert "SLICE-MV2-1" in section
    assert "SLICE-MV2-2" in section
    assert PURE_STACK_READINESS_MAP.is_file()
    assert "MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md" in section
    assert "MARKET_SURFACE_V0.md" in section
    assert "parallel alignment index" in section.lower()
    assert "test_master_v2_" in section
    assert THIS_MODULE not in section


def test_ci_audit_mv2_readonly_alignment_rc_machine_lines_v0() -> None:
    text = _ci_audit_text()
    block = _block_containing(text, MV2_READONLY_ALIGNMENT_RC_BLOCK_ANCHOR)
    values = _machine_line_values(block)
    missing = set(MV2_READONLY_ALIGNMENT_RC_EXPECTED) - values.keys()
    assert not missing, f"missing MV2 readonly alignment RC keys: {sorted(missing)}"
    for key, expected in MV2_READONLY_ALIGNMENT_RC_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def _order_capability_remaining_readiness_gap_review_section(text: str) -> str:
    start = text.find(ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_HEADING)
    assert start != -1, "missing Order-Capability remaining readiness gap review section"
    next_heading = text.find("\n## ", start + 1)
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def test_ci_audit_order_capability_remaining_readiness_gap_review_section_present_v1() -> None:
    text = _ci_audit_text()
    section = _order_capability_remaining_readiness_gap_review_section(text)
    assert ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE in section
    assert "visibility/readiness only" in section
    assert "Payload builder" in section
    assert "Dry-validation" in section
    assert "Killswitch abort" in section
    assert "Cancel cleanup" in section
    assert "Offline payload readiness" in section
    assert "Private endpoint boundary" in section
    assert "Side / price / qty rules" in section
    assert "Demo instrument rules binding" in section
    assert "Fixture-binding DOCS_TRUTH_MAP static crosslink" in section
    assert "Demo instrument rules fixture normalizer DOCS_TRUTH_MAP static crosslink" in section
    assert "no parallel readiness ssot" in section.lower()
    assert THIS_MODULE in section
    for module_name in ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_OWNER_TESTS:
        assert module_name in section, f"missing owner test reference {module_name!r}"


def test_ci_audit_order_capability_remaining_readiness_gap_review_machine_lines_v1() -> None:
    block = _block_containing(
        _ci_audit_text(),
        ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_GUARD_BLOCK_ANCHOR,
    )
    values = _machine_line_values(block)
    missing = set(ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED) - values.keys()
    assert not missing, f"missing order capability readiness gap review keys: {sorted(missing)}"
    for key, expected in ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_EXPECTED.items():
        assert values[key] == expected, f"{key}={values[key]!r} expected {expected!r}"


def test_docs_truth_map_order_capability_remaining_readiness_gap_review_chronicle_v1() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert (
        "Order-Capability remaining readiness gap review docs/tests-only visibility guard v1"
        in text
    )
    assert THIS_MODULE in text
    assert "ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_V1=true" in text
    assert "payload builder" in text
    assert "dry-validation" in text
    assert "killswitch abort" in text
    assert "cancel cleanup" in text
    assert "offline payload readiness" in text
    assert "private endpoint" in text
    assert "side-price-qty" in text
    assert "demo-instrument rules binding" in text
    assert "**no** runtime/live/preflight lift/order/cancel/execution/arming/authority lift" in text
    assert ORDER_CAPABILITY_REMAINING_READINESS_GAP_REVIEW_INPUT_BUNDLE.split("/")[-1] in text
