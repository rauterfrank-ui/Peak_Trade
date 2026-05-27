"""Static contract tests for post-closeout automation hook owner precheck v0 (taxonomy §6a.0.8.1)."""

from __future__ import annotations

from pathlib import Path

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops.test_closeout_to_projection_chain_automation_contract_v0 import (
    CANONICAL_OWNERS,
    build_post_closeout_automation_readiness_summary,
)
from tests.ops.test_closeout_to_projection_chain_automation_contract_v0 import (
    PostCloseoutAutomationReadinessInputs,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CHAIN_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_closeout_to_projection_chain_automation_contract_v0.py"
)

CANONICAL_HOOK_ATTACH_OWNERS: dict[str, str] = {
    "scheduler_completion": "scripts/run_scheduler.py",
    "shadow_bounded_adapter": "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    "supervisor_evidence_pack": "scripts/ops/pack_online_readiness_supervisor_evidence_v0.py",
}

FORBIDDEN_ATTACH_SURFACES: tuple[str, ...] = (
    "launchctl",
    "GET &#47;market",
    "Notion writer",
    "Market overlay global enablement",
    "Live / Testnet / broker / exchange",
)

FORBIDDEN_ATTACH_BEFORE: tuple[str, ...] = (
    "Before run completion",
    "Before durable primary evidence exists outside `/tmp`",
    "Before `MANIFEST.sha256` verify **RC=0**",
)


def _section_6a08_1() -> str:
    return pc.taxonomy_section_6a08_1()


def test_taxonomy_section_6a08_1_present_with_markers() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "#### 6a.0.8.1 Post-Closeout Automation Hook Owner Precheck v0" in text
    section = _section_6a08_1()
    for marker in pc.POST_CLOSEOUT_AUTOMATION_HOOK_OWNER_PRECHECK_MARKERS:
        assert marker in section


def test_hook_owner_status_identified_documented() -> None:
    section = _section_6a08_1()
    assert "hook_automation_owner_status=identified" in section
    assert "HOOK_AUTOMATION_OWNER_STATUS=identified" in section
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in section


def test_canonical_hook_attach_owners_exist() -> None:
    section = _section_6a08_1()
    for owner_id, rel_path in CANONICAL_HOOK_ATTACH_OWNERS.items():
        assert owner_id in section
        assert rel_path in section
        assert (REPO_ROOT / rel_path).is_file(), f"missing hook attach owner: {rel_path}"


def test_forbidden_attach_points_documented() -> None:
    section = _section_6a08_1()
    for phrase in FORBIDDEN_ATTACH_BEFORE:
        assert phrase in section
    for surface in FORBIDDEN_ATTACH_SURFACES:
        assert surface in section


def test_hook_boundary_no_implementation_in_repo() -> None:
    section = _section_6a08_1()
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in section
    assert "POST_CLOSEOUT_AUTOMATION_LAUNCHCTL_FORBIDDEN=true" in section
    assert "post_closeout_chain_execute_v0.py" in section
    assert not (REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py").exists()


def test_future_hook_must_reuse_chain_owners() -> None:
    section = _section_6a08_1()
    for rel_path in (
        "durable_closeout_copy_verify_v0.py",
        "build_generic_evidence_run_registry_v1.py",
        "build_post_closeout_projection_payload_v0.py",
        "notion_post_closeout_sync_dry_run_v0.py",
    ):
        assert rel_path in section
    for rel_path in CANONICAL_OWNERS.values():
        assert (REPO_ROOT / rel_path).is_file()


def test_preflight_crosslinks_hook_owner_precheck() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "§6a.0.8.1" in text or "6a.0.8.1" in text
    assert "hook_automation_owner_status=identified" in text
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in text
    assert "run_scheduler.py" in text
    assert "pack_online_readiness_supervisor_evidence_v0.py" in text


def test_docs_truth_map_records_hook_owner_precheck() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§6a.0.8.1" in text or "hook owner precheck" in text.lower()


def test_chain_contract_readiness_gate_hook_owner_semantics() -> None:
    text = CHAIN_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert "hook_automation_owner_status" in text
    assert "full_automation_claim_requires_hook_owner_identified" in text
    ok, blockers = build_post_closeout_automation_readiness_summary(
        PostCloseoutAutomationReadinessInputs(
            manual_recovery_required=False,
            hook_automation_owner_status="identified",
            claimed_full_post_closeout_automation_implemented=True,
            closeout_manifest_verify_ok=True,
            projection_manifest_verify_ok=True,
            closeout_root=None,
        )
    )
    assert ok is False
    assert "durable_closeout_missing" in blockers
