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

GUARD_BLOCK_ANCHOR = "REMOTE_RUNTIME_EXTERNAL_CHARTER_CONTRACT_DOCS_GUARD_V0=true"

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

RECIPROCAL_OWNER_TESTS = (
    "test_remote_runtime_host_metadata_contract_v0.py",
    "test_s3_finalized_evidence_export_gate_v0.py",
    "test_scheduler_boundary_hard_block_contract_v0.py",
    "test_notion_post_closeout_sync_projection_spec_v0.py",
    "test_market_dashboard_readonly_run_projection_spec_v0.py",
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
    assert "REMOTE_RUNTIME_IS_BACKEND=true" in text
    assert "FORBIDDEN_NEW_SURFACES=0" in text
    assert CHARTER_PATH.split("/")[-1] in text or "120000Z" in text


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
