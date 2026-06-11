"""Static contract tests for post-closeout automation hook owner precheck v0 (taxonomy §6a.0.8.1)."""

from __future__ import annotations

from pathlib import Path

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc
from tests.ops.test_closeout_to_projection_chain_automation_contract_v0 import (
    CANONICAL_OWNERS,
    PostCloseoutAutomationReadinessInputs,
    build_post_closeout_automation_readiness_summary,
    build_post_closeout_hook_contract_summary,
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

CANONICAL_HOOK_ATTACH_OWNERS: dict[str, str] = dict(
    pc.CANONICAL_DURABLE_CLOSEOUT_ATTACH_HOOK_OWNERS_V0
)

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
    assert "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true" in text
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in text
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in text
    assert "PRE_FLIGHT_BLOCKED_LIFTED=false" in text
    assert "READY_FOR_START=false" in text
    assert "run_scheduler.py" in text
    assert "run_paper_only_bounded_observation_adapter_v0.py" in text
    assert "run_shadow_bounded_observation_adapter_v0.py" in text
    assert "run_testnet_bounded_observation_adapter_v0.py" in text
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


def test_chain_contract_exports_hook_contract_summary() -> None:
    text = CHAIN_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert "PostCloseoutHookContractInputs" in text
    assert "build_post_closeout_hook_contract_summary" in text
    assert callable(build_post_closeout_hook_contract_summary)


def test_taxonomy_section_6a08_1_preflight_2b3_closeout_validation_crosslink_v0() -> None:
    section = _section_6a08_1()
    assert "TAXONOMY_PREFLIGHT_2B3_CLOSEOUT_VALIDATION_CROSSLINK_V0=true" in section
    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in section
    assert "§2b.3" in section
    assert "#4128" in section
    assert "#4127" in section
    assert "validate_durable_closeout_invoke_paths" in section
    assert "SCHEDULER_SUPERVISOR_DURABLE_CLOSEOUT_PRE_INVOKE_VALIDATION=true" in section
    assert "run_scheduler.py" in section
    assert "pack_online_readiness_supervisor_evidence_v0.py" in section
    assert "--durable-closeout-force" in section
    assert "BLOCKER_HINT" in section
    assert "durable_closeout_identical_source_dest" in section
    assert "test_scheduler_durable_closeout_hook_pass_through_v0.py" in section
    assert "test_supervisor_pack_durable_closeout_hook_pass_through_v0.py" in section
    assert "AUTHORITATIVE_STATUS_HIERARCHY_V0=true" in section
    assert "MACHINE_SUMMARY.env" in section
    assert "MANIFEST_VERIFY_RC=0" in section
    assert "RUN_CLOSEOUT.md" in section
    assert "HISTORICAL_PRE_RECOVERY_FAIL_NOT_CURRENT_STATUS=true" in section
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in section
    assert "PREFLIGHT_BLOCKED_LIFTED=false" in section
    assert "test_bounded_adapter_invoke_durable_closeout_v0.py" in section
    assert "no-order" in section.lower() or "no-order / no-arming" in section


def test_all_five_attach_hook_surfaces_covered_in_static_guards_v0() -> None:
    assert len(CANONICAL_HOOK_ATTACH_OWNERS) == 5
    assert "testnet_bounded_adapter" in CANONICAL_HOOK_ATTACH_OWNERS
    section = _section_6a08_1()
    for owner_id, rel_path in CANONICAL_HOOK_ATTACH_OWNERS.items():
        assert owner_id in section
        assert rel_path in section


def test_preflight_section_2b3_crosslinks_taxonomy_6a08_1_v0() -> None:
    from tests.ops.test_paper_shadow_247_preflight_contract_v0 import _section_2b3

    section = _section_2b3()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in section
    assert "§6a.0.8.1" in section
