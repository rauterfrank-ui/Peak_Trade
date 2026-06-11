"""Shared Registry v1 projection consumer smoke fixtures (test-only, non-authorizing).

Consumers: Notion §6a.1, Notion dry-run writer §6a.1.1, Market Dashboard §6a.2, projection payload builder §6a.0.9, future S3 export gate tests.
Does not define runtime authority, Registry v2, or new lanes.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REGISTRY_V1_PROJECTION_CONSUMER_SMOKE_FIXTURES_V0 = True

REPO_ROOT = Path(__file__).resolve().parents[4]
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"

CANONICAL_DURABLE_CLOSEOUT_ATTACH_HOOK_OWNERS_V0: dict[str, str] = {
    "scheduler_completion": "scripts/run_scheduler.py",
    "paper_bounded_adapter": "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py",
    "shadow_bounded_adapter": "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
    "testnet_bounded_adapter": "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
    "supervisor_evidence_pack": "scripts/ops/pack_online_readiness_supervisor_evidence_v0.py",
}

VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_GUARD_MARKERS: tuple[str, ...] = (
    "VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true",
    "ALL_FIVE_ATTACH_HOOK_SURFACES_VALIDATE_PATHS_MATRIX_COVERED=true",
    "TESTNET_VALIDATE_PATHS_SURFACE_INCLUDED=true",
    "SHADOW_VALIDATE_PATHS_IMPORT_CHAIN_GUARDED=true",
    "SCHEDULER_VALIDATE_PATHS_SURFACE_GUARDED=true",
    "SUPERVISOR_VALIDATE_PATHS_SURFACE_GUARDED=true",
    "NEW_PARALLEL_VALIDATION_LOGIC_CREATED=false",
)

VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_V0: dict[str, dict[str, tuple[str, ...] | str]] = {
    "paper_bounded_adapter": {
        "rel_path": "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py",
        "binding_mode": "canonical_definer",
        "required_in_source": (
            "def validate_durable_closeout_invoke_paths(",
            "_validate_source_dest_distinct",
            "maybe_invoke_durable_closeout_after_archive",
        ),
        "forbidden_in_source": (),
    },
    "shadow_bounded_adapter": {
        "rel_path": "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
        "binding_mode": "paper_import_delegation",
        "required_in_source": (
            "from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import",
            "maybe_invoke_durable_closeout_after_archive",
            "validate_durable_closeout_invoke_cli_args",
        ),
        "forbidden_in_source": (
            "def validate_durable_closeout_invoke_paths(",
            "def _validate_source_dest_distinct(",
        ),
    },
    "testnet_bounded_adapter": {
        "rel_path": "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
        "binding_mode": "paper_import_delegation",
        "required_in_source": (
            "from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import",
            "maybe_invoke_durable_closeout_after_archive",
            "validate_durable_closeout_invoke_cli_args",
        ),
        "forbidden_in_source": (
            "def validate_durable_closeout_invoke_paths(",
            "def _validate_source_dest_distinct(",
        ),
    },
    "scheduler_completion": {
        "rel_path": "scripts/run_scheduler.py",
        "binding_mode": "paper_import_at_invoke",
        "required_in_source": (
            "validate_durable_closeout_invoke_paths",
            "invoke_scheduler_durable_closeout_after_completion",
        ),
        "forbidden_in_source": (
            "def validate_durable_closeout_invoke_paths(",
            "def _validate_source_dest_distinct(",
        ),
    },
    "supervisor_evidence_pack": {
        "rel_path": "scripts/ops/pack_online_readiness_supervisor_evidence_v0.py",
        "binding_mode": "paper_import_at_invoke",
        "required_in_source": (
            "validate_durable_closeout_invoke_paths",
            "invoke_supervisor_pack_durable_closeout_after_pack",
        ),
        "forbidden_in_source": (
            "def validate_durable_closeout_invoke_paths(",
            "def _validate_source_dest_distinct(",
        ),
    },
}

POST_INVOKE_RESULT_CLASSIFICATION_MATRIX_GUARD_MARKERS: tuple[str, ...] = (
    "POST_INVOKE_RESULT_CLASSIFICATION_MATRIX_GUARD_V0=true",
    "ALL_FIVE_ATTACH_HOOK_SURFACES_RESULT_CLASSIFICATION_COVERED=true",
    "SCHEDULER_RESULT_CLASSIFICATION_SURFACE_GUARDED=true",
    "SUPERVISOR_RESULT_CLASSIFICATION_SURFACE_GUARDED=true",
    "STATUS_CLASSIFICATION_GUARDED=true",
    "HELPER_RC_CLASSIFICATION_GUARDED=true",
    "NON_AUTHORIZING_CLASSIFICATION_GUARDED=true",
    "NEW_PARALLEL_CLASSIFICATION_LOGIC_CREATED=false",
)

POST_INVOKE_RESULT_CLASSIFICATION_CROSS_SURFACE_PARITY_MATRIX_V0: dict[
    str, dict[str, tuple[str, ...] | str]
] = {
    "paper_bounded_adapter": {
        "rel_path": "scripts/ops/run_paper_only_bounded_observation_adapter_v0.py",
        "binding_mode": "canonical_definer",
        "emit_function": "emit_bounded_adapter_durable_closeout_machine_lines",
        "required_in_emit_body": (
            "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS=blocked",
            'status = "pass" if rc == 0 else "failed"',
            "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_STATUS={status}",
            "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC=not_run",
            "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_HELPER_RC={rc}",
            "BOUNDED_ADAPTER_DURABLE_CLOSEOUT_NON_AUTHORIZING=true",
        ),
        "forbidden_in_source": (),
    },
    "shadow_bounded_adapter": {
        "rel_path": "scripts/ops/run_shadow_bounded_observation_adapter_v0.py",
        "binding_mode": "paper_import_delegation",
        "required_in_source": (
            "from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import",
            "maybe_invoke_durable_closeout_after_archive",
        ),
        "forbidden_in_source": ("def emit_bounded_adapter_durable_closeout_machine_lines(",),
    },
    "testnet_bounded_adapter": {
        "rel_path": "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
        "binding_mode": "paper_import_delegation",
        "required_in_source": (
            "from scripts.ops.run_paper_only_bounded_observation_adapter_v0 import",
            "maybe_invoke_durable_closeout_after_archive",
        ),
        "forbidden_in_source": ("def emit_bounded_adapter_durable_closeout_machine_lines(",),
    },
    "scheduler_completion": {
        "rel_path": "scripts/run_scheduler.py",
        "binding_mode": "prefix_scoped_emit",
        "emit_function": "emit_scheduler_durable_closeout_machine_lines",
        "invoked_helper_rc_mode": "exit_code_fail_closed_surrogate",
        "required_in_emit_body": (
            "SCHEDULER_DURABLE_CLOSEOUT_STATUS=blocked",
            "SCHEDULER_DURABLE_CLOSEOUT_HELPER_RC=not_run",
            "SCHEDULER_DURABLE_CLOSEOUT_NON_AUTHORIZING=true",
            "SCHEDULER_DURABLE_CLOSEOUT_EXIT_CODE",
        ),
        "forbidden_in_source": ("def emit_bounded_adapter_durable_closeout_machine_lines(",),
    },
    "supervisor_evidence_pack": {
        "rel_path": "scripts/ops/pack_online_readiness_supervisor_evidence_v0.py",
        "binding_mode": "prefix_scoped_emit",
        "emit_function": "emit_supervisor_pack_durable_closeout_machine_lines",
        "invoked_helper_rc_mode": "exit_code_fail_closed_surrogate",
        "required_in_emit_body": (
            "SUPERVISOR_PACK_DURABLE_CLOSEOUT_STATUS=blocked",
            "SUPERVISOR_PACK_DURABLE_CLOSEOUT_HELPER_RC=not_run",
            "SUPERVISOR_PACK_DURABLE_CLOSEOUT_NON_AUTHORIZING=true",
            "SUPERVISOR_PACK_DURABLE_CLOSEOUT_EXIT_CODE",
        ),
        "forbidden_in_source": ("def emit_bounded_adapter_durable_closeout_machine_lines(",),
    },
}


def durable_closeout_emit_function_body(rel_path: str, emit_function: str) -> str:
    """Return source text for a top-level emit helper (test-only static guard aid)."""
    text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
    start_token = f"def {emit_function}("
    start = text.index(start_token)
    lines = text[start:].splitlines()
    body_lines = [lines[0]]
    for line in lines[1:]:
        if line.startswith("def ") and not line.startswith("    "):
            break
        body_lines.append(line)
    return "\n".join(body_lines)


POST_CLOSEOUT_AUTOMATION_HOOK_OWNER_PRECHECK_MARKERS: tuple[str, ...] = (
    "POST_CLOSEOUT_AUTOMATION_HOOK_OWNER_PRECHECK_V0=true",
    "HOOK_AUTOMATION_OWNER_STATUS=identified",
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_IMPLEMENTED=true",
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_NON_AUTHORIZING=true",
    "DURABLE_CLOSEOUT_ATTACH_HOOK_V0_DEFAULT_OFF=true",
    "POST_CLOSEOUT_AUTOMATION_HOOK_IMPLEMENTED=false",
    "POST_CLOSEOUT_AUTOMATION_HOOK_AUTO_INSTALL=false",
    "POST_CLOSEOUT_AUTOMATION_LAUNCHCTL_FORBIDDEN=true",
    "POST_CLOSEOUT_CHAIN_EXECUTE_SCRIPT_FORBIDDEN=true",
    "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false",
    "PREFLIGHT_BLOCKED_LIFTED=false",
    "READY_FOR_START_AFTER_SLICE=false",
    "HOOK_ATTACH_AFTER_RUN_COMPLETION_ONLY=true",
    "HOOK_ATTACH_AFTER_DURABLE_PRIMARY_EVIDENCE_ONLY=true",
    "HOOK_ATTACH_AFTER_MANIFEST_VERIFY_RC_ZERO_ONLY=true",
    "HOOK_MUST_REUSE_EXISTING_CHAIN_OWNERS=true",
    "HOOK_MUST_FAIL_CLOSED=true",
    "NO_SCHEDULER_BEHAVIOR_CHANGE_IN_PRECHECK=true",
    "NO_NOTION_WRITE_IN_PRECHECK=true",
    "NO_MARKET_GLOBAL_ENABLEMENT_IN_PRECHECK=true",
    "POST_CLOSEOUT_AUTOMATION_HOOK_OWNER_PRECHECK_DOCS_TESTS_ONLY=true",
    "TAXONOMY_PREFLIGHT_2B3_CLOSEOUT_VALIDATION_CROSSLINK_V0=true",
    "DURABLE_CLOSEOUT_ADAPTER_PRE_INVOKE_VALIDATION=true",
    "BOUNDED_ADAPTER_OBSERVATION_CLOSEOUT_DECOUPLED=true",
    "DURABLE_CLOSEOUT_IDENTICAL_SOURCE_DEST_REJECTED=true",
    "DURABLE_CLOSEOUT_FORCE_REQUIRES_DISTINCT_PATHS=true",
    "BLOCKER_HINT_MACHINE_READABLE=true",
    "AUTHORITATIVE_STATUS_HIERARCHY_V0=true",
    "HISTORICAL_PRE_RECOVERY_FAIL_NOT_CURRENT_STATUS=true",
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "VALIDATE_PATHS_CROSS_SURFACE_PARITY_MATRIX_GUARD_V0=true",
    "NEW_PARALLEL_VALIDATION_LOGIC_CREATED=false",
    "POST_INVOKE_RESULT_CLASSIFICATION_MATRIX_GUARD_V0=true",
    "ALL_FIVE_ATTACH_HOOK_SURFACES_RESULT_CLASSIFICATION_COVERED=true",
    "NEW_PARALLEL_CLASSIFICATION_LOGIC_CREATED=false",
)

POST_CLOSEOUT_PROJECTION_AUTOMATION_CHARTER_MARKERS: tuple[str, ...] = (
    "POST_CLOSEOUT_PROJECTION_AUTOMATION_V0=true",
    "NOTION_POST_CLOSEOUT_SYNC_V0=true",
    "MARKET_DASHBOARD_READONLY_RUN_PROJECTION_V0=true",
    "POST_CLOSEOUT_PROJECTION_AUTOMATION_ENABLED=false",
    "NOTION_POST_CLOSEOUT_SYNC_ENABLED=false",
    "MARKET_DASHBOARD_RUN_PROJECTION_ENABLED=false",
    "RUNTIME_CONTROL_FROM_PROJECTION=false",
    "DASHBOARD_RUNTIME_CONTROL=false",
    "BROKER_EXCHANGE_AUTHORITY=false",
    "PROJECTION_AFTER_CLOSEOUT_ONLY=true",
    "PROJECTION_AFTER_MANIFEST_VERIFY_ONLY=true",
    "REPO_AND_DURABLE_EVIDENCE_REMAIN_CANONICAL=true",
    "NOTION_IS_PROJECTION_ONLY=true",
    "MARKET_DASHBOARD_IS_PROJECTION_ONLY=true",
    "NO_PARALLEL_MARKET_SURFACE=true",
    "NO_PARALLEL_NOTION_DB=true",
    "NO_PARALLEL_READMODEL=true",
)

POST_CLOSEOUT_PROJECTION_PAYLOAD_BUILDER_PLANNING_MARKERS: tuple[str, ...] = (
    "POST_CLOSEOUT_PROJECTION_PAYLOAD_BUILDER_PLANNING_CONTRACT_V0=true",
    "BUILD_POST_CLOSEOUT_PROJECTION_PAYLOAD_V0=planning_target_only",
    "PAYLOAD_BUILDER_IMPLEMENTED=false",
    "PAYLOAD_BUILDER_SCRIPT_FORBIDDEN_IN_THIS_SLICE=true",
    "PROJECTION_PAYLOAD_AFTER_CLOSEOUT_ONLY=true",
    "PROJECTION_PAYLOAD_AFTER_MANIFEST_VERIFY_ONLY=true",
    "PROJECTION_PAYLOAD_READS_FINALIZED_EVIDENCE_ONLY=true",
    "PROJECTION_PAYLOAD_WRITES_LOCAL_JSON_ONLY=true",
    "PROJECTION_PAYLOAD_DOES_NOT_WRITE_NOTION=true",
    "PROJECTION_PAYLOAD_DOES_NOT_WRITE_DASHBOARD=true",
    "PROJECTION_PAYLOAD_DOES_NOT_CALL_S3_AWS_RCLONE=true",
    "PROJECTION_PAYLOAD_DOES_NOT_START_RUNTIME=true",
    "PROJECTION_PAYLOAD_AUTHORITY=false",
    "NOTION_CONSUMER_WRITE_PERMITTED=false",
    "MARKET_DASHBOARD_CONSUMER_WRITE_PERMITTED=false",
    "POST_CLOSEOUT_PROJECTION_PAYLOAD_BUILDER_PLANNING_DOCS_TESTS_ONLY=true",
)

PLANNED_PROJECTION_PAYLOAD_OUTPUT_FIELDS: tuple[str, ...] = (
    "schema_version",
    "run_id",
    "projection_ready",
    "projection_blocked_reason",
    "manifest_verify_rc",
    "closeout_accepted",
    "primary_evidence_finalized",
    "registry_pointer",
    "closeout_pointer",
    "authority",
    "notion_consumer",
    "market_dashboard_consumer",
)

POST_CLOSEOUT_NOTION_DRY_RUN_WRITER_PLANNING_MARKERS: tuple[str, ...] = (
    "NOTION_POST_CLOSEOUT_DRY_RUN_WRITER_PLANNING_CONTRACT_V0=true",
    "NOTION_POST_CLOSEOUT_DRY_RUN_WRITER_V0=planning_target_only",
    "NOTION_DRY_RUN_WRITER_IMPLEMENTED=false",
    "NOTION_DRY_RUN_WRITER_SCRIPT_FORBIDDEN_IN_THIS_SLICE=true",
    "NOTION_DRY_RUN_WRITER_DEFAULT_DRY_RUN=true",
    "NOTION_DRY_RUN_WRITER_WRITE_DEFAULT=false",
    "NOTION_DRY_RUN_WRITER_REQUIRES_CONFIRM_TOKEN=true",
    "NOTION_DRY_RUN_WRITER_CONFIRM_TOKEN=NOTION_POST_CLOSEOUT_SYNC_V0",
    "NOTION_DRY_RUN_WRITER_REQUIRES_BOUNDARY_TEXT_VERIFIED=true",
    "NOTION_DRY_RUN_WRITER_REQUIRES_EXISTING_TARGET_DB=true",
    "NOTION_DRY_RUN_WRITER_CREATES_DB=false",
    "NOTION_DRY_RUN_WRITER_DESTRUCTIVE_OPS=false",
    "NOTION_DRY_RUN_WRITER_AFTER_CLOSEOUT_ONLY=true",
    "NOTION_DRY_RUN_WRITER_AFTER_MANIFEST_VERIFY_ONLY=true",
    "NOTION_DRY_RUN_WRITER_DOES_NOT_CALL_MCP_WRITE=true",
    "NOTION_MCP_WRITE_READY=false",
    "NOTION_AUTHORITY=false",
    "LIVE_AUTHORITY=false",
    "TESTNET_AUTHORITY=false",
    "BROKER_EXCHANGE_AUTHORITY=false",
    "NO_PARALLEL_NOTION_DB=true",
)

PLANNED_NOTION_DRY_RUN_OUTPUT_FIELDS: tuple[str, ...] = (
    "would_create_or_update",
    "target_database_safe_name",
    "field_mapping_preview",
    "projection_blocked_reason",
    "operator_review_required",
)


def taxonomy_section_6a08() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "### 6a.0.8 Post-Closeout Projection Automation Charter v0 (docs/tests-only)", 1
    )[1].split(
        "### 6a.0.9 Shared Projection Payload Builder Planning Contract v0 (planning-only)", 1
    )[0]


def taxonomy_section_6a08_1() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "#### 6a.0.8.1 Post-Closeout Automation Hook Owner Precheck v0 (docs/tests-only)", 1
    )[1].split(
        "### 6a.0.9 Shared Projection Payload Builder Planning Contract v0 (planning-only)", 1
    )[0]


def taxonomy_section_6a09() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "### 6a.0.9 Shared Projection Payload Builder Planning Contract v0 (planning-only)", 1
    )[1].split("### 6a.1 Notion post-closeout sync projection contract v0", 1)[0]


def taxonomy_section_6a11() -> str:
    text = TAXONOMY_SPEC.read_text(encoding="utf-8")
    return text.split(
        "### 6a.1.1 Notion post-closeout dry-run writer planning contract v0 (planning-only)",
        1,
    )[1].split("### 6a.2 Market Dashboard read-only run projection contract v0", 1)[0]


# Canonical pointer/status fields for Registry v1 projection consumers (§6a.1 + §6a.2 aligned).
ALLOWED_PROJECTION_FIELDS: tuple[str, ...] = (
    "run_id",
    "lane_id",
    "composition_id",
    "record_kind",
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "evidence_status",
    "review_verdict",
    "manifest_verified",
    "archive_path",
)

RUN_PROJECTION_FIELDS: tuple[str, ...] = (
    "run_id",
    "lane_id",
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "evidence_status",
    "review_verdict",
    "manifest_verified",
    "archive_path",
)

# Subset referenced by future S3 finalized-evidence export gate contract tests (no S3 impl here).
S3_RELEVANT_PROJECTION_FIELDS: tuple[str, ...] = (
    "evidence_transport",
    "manifest_verified",
    "archive_path",
    "evidence_status",
)

TOP_LEVEL_PROJECTION_SUMMARY_FIELDS: tuple[str, ...] = (
    "verdict",
    "issues",
    "blockers",
    "archive_root",
)

SECTION_6A_METADATA_FIELDS: tuple[str, ...] = (
    "runtime_host",
    "runtime_backend",
    "runtime_mode",
    "evidence_root_type",
    "evidence_transport",
    "notion_projection",
    "market_dashboard_projection",
    "live_authority",
    "testnet_authority",
)

DEFAULT_COMPOSITION_RUN_ID = "daemon_paper_24h_fixture_projection_v0"


def load_registry_module(
    *, module_name: str = "build_generic_evidence_run_registry_v1_projection_consumer"
):
    spec = importlib.util.spec_from_file_location(module_name, REGISTRY_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_lane_manifest(run_dir: Path) -> None:
    entries: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        rel = path.relative_to(run_dir).as_posix()
        entries.append(f"{sha256_file(path)}  {rel}")
    (run_dir / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def write_lane(
    archive: Path,
    lane: str,
    run_id: str,
    *,
    review: str | None = None,
) -> Path:
    run_dir = archive / "runs" / lane / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence.txt").write_text(f"{lane}:{run_id}\n", encoding="utf-8")
    if review is not None:
        review_dir = run_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "REVIEW_RESULT.json").write_text(
            json.dumps({"verdict": review, "issues": []}) + "\n",
            encoding="utf-8",
        )
    write_lane_manifest(run_dir)
    return run_dir


def write_composition(archive: Path, run_id: str) -> Path:
    comp_dir = archive / "runs" / "daemon_paper_24h" / run_id
    comp_dir.mkdir(parents=True, exist_ok=True)
    (comp_dir / "COMPOSITION_INDEX.md").write_text(
        "composition_index_authority=false\n",
        encoding="utf-8",
    )
    manifests = comp_dir / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    rel = "COMPOSITION_INDEX.md"
    digest = sha256_file(comp_dir / rel)
    (manifests / "MANIFEST.sha256").write_text(f"{digest}  {rel}\n", encoding="utf-8")
    return comp_dir


def write_minimal_paper_run(archive: Path, run_id: str = "paper_run") -> Path:
    """Minimal verified paper lane archive for projection consumer smoke tests."""
    return write_lane(archive, "paper", run_id)


def build_registry(archive: Path, *, repo_root: Path | None = None) -> dict[str, Any]:
    mod = load_registry_module()
    return mod.build_registry(
        mod.BuildContext(archive_root=archive, repo_root=repo_root or REPO_ROOT)
    )


def assert_non_authorizing_run_projection_defaults(run: dict[str, Any]) -> None:
    for field in RUN_PROJECTION_FIELDS:
        if field not in run:
            raise AssertionError(f"missing projection field {field!r} on runs[] row")
    if run.get("live_authority") is not False:
        raise AssertionError("live_authority must be false on projection consumer fixture runs")
    if run.get("testnet_authority") is not False:
        raise AssertionError("testnet_authority must be false on projection consumer fixture runs")
    if run.get("notion_projection") != "disabled":
        raise AssertionError("notion_projection must be disabled by default")
    if run.get("market_dashboard_projection") != "disabled":
        raise AssertionError("market_dashboard_projection must be disabled by default")
