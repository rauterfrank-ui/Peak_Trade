"""Static bridge tests: narrow durable-closeout attach hooks vs full post-closeout automation."""

from __future__ import annotations

from pathlib import Path

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

REPO_ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs/ops/registry/DOCS_TRUTH_MAP.md"
FORBIDDEN_CHAIN_SCRIPT = REPO_ROOT / "scripts/ops/post_closeout_chain_execute_v0.py"

BRIDGE_MARKERS: tuple[str, ...] = (
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true",
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_NON_AUTHORIZING=true",
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_DEFAULT_OFF=true",
    "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
    "PREFLIGHT_BLOCKED_LIFTED=false",
    "READY_FOR_START_AFTER_SLICE=false",
)

ATTACH_OWNER_CLI_FLAGS: dict[str, tuple[str, ...]] = {
    "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py": (
        "--invoke-durable-closeout-v0",
        "--durable-closeout-dest-dir",
    ),
    "scripts/ops/run_shadow_bounded_observation_adapter_v0.py": (
        "add_bounded_adapter_durable_closeout_cli_args",
        "maybe_invoke_durable_closeout_after_archive",
    ),
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py": (
        "add_bounded_adapter_durable_closeout_cli_args",
        "maybe_invoke_durable_closeout_after_archive",
    ),
    "scripts/run_scheduler.py": (
        "--invoke-durable-closeout-after-completion-v0",
        "--durable-closeout-dest-dir",
    ),
    "scripts/ops/pack_online_readiness_supervisor_evidence_v0.py": (
        "--invoke-durable-closeout-after-pack-v0",
        "--durable-closeout-dest-dir",
    ),
}

FORBIDDEN_GATE_LIFT_MARKER_LINES: tuple[str, ...] = (
    "READY_FOR_START_AFTER_SLICE=true",
    "PREFLIGHT_BLOCKED_LIFTED=true",
    "PRE_FLIGHT_BLOCKED_LIFTED=true",
)


def _section_6a08_1() -> str:
    return pc.taxonomy_section_6a08_1()


def test_bridge_markers_in_taxonomy_section_6a08_1() -> None:
    section = _section_6a08_1()
    for marker in BRIDGE_MARKERS:
        assert marker in section


def test_taxonomy_distinguishes_narrow_attach_from_full_automation() -> None:
    section = _section_6a08_1()
    assert "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true" in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in section
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in section
    assert "paper_bounded_adapter" in section
    assert "narrow durable-closeout attach hooks" in section.lower() or (
        "Narrow durable-closeout attach hooks" in section
    )


def test_preflight_bridge_crosslink_preserves_blocked_and_ready_false() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true" in text
    assert "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false" in text
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in text
    assert "PRE_FLIGHT_BLOCKED_LIFTED=false" in text
    assert "READY_FOR_START=false" in text
    assert "Current status: **BLOCKED**." in text


def test_docs_truth_map_records_attach_readiness_bridge() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "Durable closeout attach readiness bridge v0" in text
    assert "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true" in text


def test_attach_owner_cli_flags_present_in_source() -> None:
    for rel_path, flags in ATTACH_OWNER_CLI_FLAGS.items():
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for flag in flags:
            assert flag in source, f"missing {flag!r} in {rel_path}"


def test_all_five_attach_hook_surfaces_covered_in_bridge_guards_v0() -> None:
    owners = pc.CANONICAL_DURABLE_CLOSEOUT_ATTACH_HOOK_OWNERS_V0
    assert len(owners) == 5
    assert "testnet_bounded_adapter" in owners
    assert set(ATTACH_OWNER_CLI_FLAGS) == set(owners.values())


def test_forbidden_parallel_execute_script_absent() -> None:
    assert not FORBIDDEN_CHAIN_SCRIPT.exists()


def test_bridge_section_has_no_gate_lift_markers() -> None:
    section = _section_6a08_1()
    for marker in FORBIDDEN_GATE_LIFT_MARKER_LINES:
        assert marker not in section
    assert "READY_FOR_START_AFTER_SLICE=false" in section
    assert "PREFLIGHT_BLOCKED_LIFTED=false" in section


def test_validate_paths_cross_surface_parity_matrix_guard_v0() -> None:
    owners = pc.CANONICAL_DURABLE_CLOSEOUT_ATTACH_HOOK_OWNERS_V0
    matrix = pc.VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_V0
    assert len(matrix) == 5
    assert set(matrix) == set(owners)
    assert "testnet_bounded_adapter" in matrix
    for owner_id, spec in matrix.items():
        rel_path = str(spec["rel_path"])
        assert owners[owner_id] == rel_path
        source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for token in spec.get("required_in_source", ()):
            assert token in source, f"{owner_id}: missing {token!r} in {rel_path}"
        for forbidden in spec.get("forbidden_in_source", ()):
            assert forbidden not in source, (
                f"{owner_id}: parallel validation logic {forbidden!r} in {rel_path}"
            )
    shadow_spec = matrix["shadow_bounded_adapter"]
    testnet_spec = matrix["testnet_bounded_adapter"]
    assert shadow_spec["binding_mode"] == "paper_import_delegation"
    assert testnet_spec["binding_mode"] == "paper_import_delegation"
    assert matrix["scheduler_completion"]["binding_mode"] == "paper_import_at_invoke"
    assert matrix["supervisor_evidence_pack"]["binding_mode"] == "paper_import_at_invoke"
