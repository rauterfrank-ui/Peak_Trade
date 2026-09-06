"""DDO durable evidence storage owner contract v1.

Documentation guard. Not a second semantic SSOT. No productive host
ledger_path. No runtime file. No second DDO storage implementation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md"
ATLAS_CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
HOST_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
CAPTURE_PATH = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/capture_v0.py"
LEDGER_PATH = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/ledger_v0.py"
AUTHORITY_PATH = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/authority_v0.py"
OWNER_GO = "PEAK_TRADE_OWNER_GO_DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1"
BOUND_SHA = "c14730e99f1b1303b69a117fdc0d6896ee1c1e51"


def _owner_contract_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO durable evidence storage owner contract persist"
    )
    end = text.index(
        "### 11.13.5 Parallel-track DDO ledger durability hardening and host-binding prep persist"
    )
    return text[start:end]


def _hardening_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO ledger durability hardening and host-binding prep persist"
    )
    end = text.index("### 11.13.5 Parallel-track DDO productive host scope input binding persist")
    return text[start:end]


def _scope_input_persist_section(text: str) -> str:
    start = text.index("### 11.13.5 Parallel-track DDO productive host scope input binding persist")
    end = text.index(
        "### 11.13.5 Parallel-track DDO productive host durable ledger binding persist"
    )
    return text[start:end]


def _ledger_binding_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO productive host durable ledger binding persist"
    )
    end = text.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability policy boundary persist"
    )
    return text[start:end]


def _a1_policy_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability policy boundary persist"
    )
    end = text.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability runtime authorization persist"
    )
    return text[start:end]


def _a1_runtime_authorization_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability runtime authorization persist"
    )
    end = text.index(
        "### 11.13.5 Parallel-track DDO A1 crash durability atomic replace or explicit non-requirement persist"
    )
    return text[start:end]


def _a1_crash_durability_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO A1 crash durability atomic replace or explicit non-requirement persist"
    )
    end = text.index("### 11.13.5 Parallel-track DDO A1 durability failure policy binding persist")
    return text[start:end]


def _a1_failure_policy_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO A1 durability failure policy binding persist"
    )
    end = text.index(
        "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
    )
    return text[start:end]


def test_contract_discoverable_and_bound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={BOUND_SHA}" in spec
    assert "DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT" in spec
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1=BOUND" in spec
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER" in spec
    assert "DDO_DURABLE_LEDGER_IMPLEMENTATION=AppendOnlyDdoLedgerV0" in spec
    assert "DDO_DURABLE_EVIDENCE_PATH_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER" in spec
    assert "DDO_PRODUCTIVE_HOST_LEDGER_BINDING=false" in spec
    assert "DDO_RUNTIME_PATH_BOUND=false" in spec
    assert (
        "DDO_DURABILITY_FAILURE_POLICY_CURRENT_STAGE="
        "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
    ) in spec
    assert "DDO_DURABILITY_FAILURE_POLICY_FOR_A1=UNBOUND_NOT_AUTHORIZED" in spec
    assert "DDO_LEDGER_SINGLE_WRITER_REQUIRED=true" in spec
    assert "MULTI_PROCESS_SHARED_WRITES_ALLOWED=false" in spec
    assert "DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY=false" in spec
    assert "DDO_STORAGE_OWNER_CAN_CHANGE_DECISION=false" in spec
    assert "NEW_DDO_STORAGE_IMPLEMENTATION_CREATED=false" in spec
    assert "NEXT_OWNER_GO_REQUIRED=true" in spec
    assert "MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true" in spec
    assert "DDO_AUTHORITY_OWNER=NONE" in spec
    assert "ENVIRONMENT_TOKEN_CURRENT_OBSERVATION_HOST" in spec
    assert "REQUIRED_BUT_UNBOUND" in spec
    assert "ACCOUNT_SCOPE_VALUE_CURRENT_OBSERVATION_HOST" in spec
    assert "SYSTEM_SCOPE_TOKEN" in spec
    assert "canonical_trading_path" in spec
    assert "CAPTURED_IDS_DURABLE_WRITE_BUG_STATUS=CLOSED" in spec
    assert "PATH_SOURCE_IMPLEMENTATION=PRIMITIVE_PRESENT_PRODUCTIVE_UNBOUND" in spec
    assert "DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_V1=COMPLETE" in spec
    assert "DDO_BINDING_READY=true" in spec
    assert "PATH_RESOLUTION_PRIMITIVE_PRESENT=true" in spec
    assert "LOCK_IMPLEMENTATION_ADDED_BY_THIS_SLICE=true" in spec
    assert "FILE_FSYNC_PRESENT=true" in spec
    assert "DIRECTORY_FSYNC_HARD_GUARANTEE=false" in spec
    assert "ATOMIC_RECORD_APPEND=PARTIAL" in spec
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in spec
    assert "NEXT_DDO_STEP=PEAK_TRADE_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1" in spec
    assert "NO_LEDGER_PATH_IN_HOST=true" in spec
    assert "NO_SECOND_DDO_LEDGER=true" in spec
    assert "PEAK_TRADE_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1=BOUND" in spec
    assert "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_V1=BOUND" in spec
    assert "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1=BOUND" in spec
    assert (
        "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1=BOUND"
        in spec
    )
    assert "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1=BOUND" in spec
    assert (
        "A1_DURABILITY_FAILURE_POLICY=BOUND_FAIL_CLOSED_DEPENDENT_MUTATION_FORBIDDEN_ON_UNPROVEN_DURABILITY"
        in spec
    )
    assert "ADJUDICATION_CLASS=PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE" in spec
    assert "ATOMIC_REPLACE_IMPLEMENTED=false" in spec
    assert "EXPLICIT_NONREQUIREMENT_PROVEN=false" in spec
    assert "POWER_LOSS_DURABILITY=UNPROVEN" in spec
    assert "A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED=false" in spec
    assert "IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION=false" in spec
    assert "RUNTIME_AUTHORIZATION_ELIGIBLE=false" in spec
    assert "DURABILITY_CLASS=PLATFORM_HARD_GUARANTEE_NOT_PROVABLE" in spec
    assert "DIRECTORY_FSYNC_STATUS=FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE" in spec
    assert "PATH_RESOLVER_CONSUMED_BY_PRODUCTIVE_HOST=true" in spec
    assert "DURABLE_APPEND_REACHABLE_FROM_HOST=true" in spec
    assert "HOST_SCOPE_INPUT_SEAM=BOUND" in spec
    assert "BINDING_INPUTS_PROVEN=true" in spec
    assert "PATH_RESOLVER_CONSUMED_BY_PRODUCTIVE_HOST=false" in spec
    assert "DEFAULT_PRODUCTIVE_HOST_SCOPE_UNBOUND_UNTIL_EXPLICIT_INJECTION=true" in spec
    assert "NEW_ENVIRONMENT_IDENTITY_DOMAIN_CREATED=false" in spec
    assert "NEW_ACCOUNT_IDENTITY_DOMAIN_CREATED=false" in spec


def test_master_runbook_refers_to_valid_spec() -> None:
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    section = _owner_contract_persist_section(runbook)
    assert SPEC_PATH.is_file()
    assert "docs&#47;ops&#47;specs&#47;DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md" in section
    assert f"OWNER_GO={OWNER_GO}" in section
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1=BOUND" in section
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER" in section
    assert "DDO_DURABLE_LEDGER_IMPLEMENTATION=AppendOnlyDdoLedgerV0" in section
    assert "DDO_DURABLE_EVIDENCE_PATH_OWNER=DDO_DURABLE_EVIDENCE_STORAGE_OWNER" in section
    assert "DDO_PRODUCTIVE_HOST_LEDGER_BINDING=false" in section
    assert "DDO_RUNTIME_PATH_BOUND=false" in section
    assert (
        "DDO_DURABILITY_FAILURE_POLICY_CURRENT_STAGE="
        "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
    ) in section
    assert "DDO_DURABILITY_FAILURE_POLICY_FOR_A1=UNBOUND_NOT_AUTHORIZED" in section
    assert "DDO_LEDGER_SINGLE_WRITER_REQUIRED=true" in section
    assert "DDO_MULTI_PROCESS_SHARED_WRITES_ALLOWED=false" in section
    assert "DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY=false" in section
    assert "DDO_STORAGE_OWNER_CAN_CHANGE_DECISION=false" in section
    assert "NEW_DDO_STORAGE_IMPLEMENTATION_CREATED=false" in section
    assert "NEXT_DDO_STEP_REQUIRES_SEPARATE_OWNER_GO=true" in section
    assert "CURRENT_CANONICAL_SECTION=11.13.5.Z2DA" in section
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in section
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in section
    assert "ATLAS_IMPACT=UPDATED" in section
    assert "ATLAS_MUST_NOT_CREATE_AUTHORITY=true" in section
    assert "DDO_AUTHORITY_OWNER=NONE" in section
    assert "DDO_CAPTURE_RUNTIME_EFFECT=OBSERVATION_ONLY" in section
    assert "MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true" in section
    assert "WP_FA_08_AUTHORIZED=false" in section
    persist_start = runbook.index(
        "### 11.13.5 Parallel-track DDO durable evidence storage owner contract persist"
    )
    hardening_start = runbook.index(
        "### 11.13.5 Parallel-track DDO ledger durability hardening and host-binding prep persist"
    )
    scope_start = runbook.index(
        "### 11.13.5 Parallel-track DDO productive host scope input binding persist"
    )
    ledger_start = runbook.index(
        "### 11.13.5 Parallel-track DDO productive host durable ledger binding persist"
    )
    a1_start = runbook.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability policy boundary persist"
    )
    a1_runtime_start = runbook.index(
        "### 11.13.5 Parallel-track DDO A1 unattended durability runtime authorization persist"
    )
    a1_crash_start = runbook.index(
        "### 11.13.5 Parallel-track DDO A1 crash durability atomic replace or explicit non-requirement persist"
    )
    live_z2db = runbook.index(
        "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
    )
    assert (
        persist_start
        < hardening_start
        < scope_start
        < ledger_start
        < a1_start
        < a1_runtime_start
        < a1_crash_start
        < live_z2db
    )
    hardening = _hardening_persist_section(runbook)
    assert "DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_V1=COMPLETE" in hardening
    assert "CAPTURED_IDS_DURABLE_WRITE_BUG_STATUS=CLOSED" in hardening
    assert "DDO_PRODUCTIVE_HOST_LEDGER_BOUND=false" in hardening
    assert "DDO_RUNTIME_PATH_BOUND=false" in hardening
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in hardening
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in hardening
    scope = _scope_input_persist_section(runbook)
    assert "PEAK_TRADE_DDO_PRODUCTIVE_HOST_SCOPE_INPUT_BINDING_V1=BOUND" in scope
    assert "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_PRODUCTIVE_HOST_SCOPE_INPUT_BINDING_V1" in scope
    assert "HOST_RUNTIME_STATE_ROOT_BINDING=BOUND" in scope
    assert "HOST_ENVIRONMENT_BINDING=BOUND" in scope
    assert "HOST_ACCOUNT_BINDING=BOUND" in scope
    assert "BINDING_INPUTS_PROVEN=true" in scope
    assert "DDO_PRODUCTIVE_HOST_LEDGER_BOUND=false" in scope
    assert "DDO_RUNTIME_PATH_BOUND=false" in scope
    assert "PATH_RESOLVER_CONSUMED_BY_PRODUCTIVE_HOST=false" in scope
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in scope
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in scope
    assert "NEXT_DDO_STEP=PEAK_TRADE_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1" in scope
    ledger_binding = _ledger_binding_persist_section(runbook)
    assert "PEAK_TRADE_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1=BOUND" in ledger_binding
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_V1"
        in ledger_binding
    )
    assert "PATH_RESOLVER_CONSUMED_BY_PRODUCTIVE_HOST=true" in ledger_binding
    assert "RESOLVED_PATH_IS_SCOPE_DERIVED=true" in ledger_binding
    assert "PRODUCTIVE_RUNTIME_PATH_BOUND=true" in ledger_binding
    assert "PRODUCTIVE_HOST_LEDGER_BOUND=true" in ledger_binding
    assert "DURABLE_APPEND_REACHABLE_FROM_HOST=true" in ledger_binding
    assert "DDO_DURABLE_LEDGER_IMPLEMENTATION=AppendOnlyDdoLedgerV0" in ledger_binding
    assert "MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true" in ledger_binding
    assert "DDO_STORAGE_AUTHORITY_IS_TRADING_AUTHORITY=false" in ledger_binding
    assert "DDO_LEARNING_PRODUCTIVE_AUTHORITY=false" in ledger_binding
    assert "TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE=false" in ledger_binding
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in ledger_binding
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in ledger_binding
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in ledger_binding
    a1_policy = _a1_policy_persist_section(runbook)
    assert "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_V1=BOUND" in a1_policy
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_V1" in a1_policy
    )
    assert "A1_UNATTENDED_DURABILITY_POLICY_DEFINED=true" in a1_policy
    assert "A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED=false" in a1_policy
    assert "IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION=false" in a1_policy
    assert "RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE=NONE" in a1_policy
    assert "A1_TRADING_AUTHORITY=false" in a1_policy
    assert "A1_EXECUTION_AUTHORITY=false" in a1_policy
    assert "DDO_LEARNING_PRODUCTIVE_AUTHORITY=false" in a1_policy
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in a1_policy
    assert "SILENT_LEDGER_RESET_ALLOWED=false" in a1_policy
    assert "FALLBACK_LEDGER_ALLOWED=false" in a1_policy
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in a1_policy
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in a1_policy
    a1_runtime = _a1_runtime_authorization_persist_section(runbook)
    assert "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1=BOUND" in a1_runtime
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1"
        in a1_runtime
    )
    assert "IMPLEMENTATION_COMPLETE=true" in a1_runtime
    assert "PRECONDITIONS_PROVEN=false" in a1_runtime
    assert "RUNTIME_AUTHORIZATION_ELIGIBLE=false" in a1_runtime
    assert "RUNTIME_AUTHORIZED=false" in a1_runtime
    assert "A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED=false" in a1_runtime
    assert "IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION=false" in a1_runtime
    assert "RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE=NONE" in a1_runtime
    assert "AUTHORIZATION_SOURCE=NONE" in a1_runtime
    assert "DURABILITY_CLASS=PLATFORM_HARD_GUARANTEE_NOT_PROVABLE" in a1_runtime
    assert "DIRECTORY_FSYNC_STATUS=FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE" in a1_runtime
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in a1_runtime
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in a1_runtime
    assert "MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY=true" in a1_runtime
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in a1_runtime
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in a1_runtime
    assert (
        "NEXT_DDO_STEP=PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1"
        in a1_runtime
    )
    a1_crash = _a1_crash_durability_persist_section(runbook)
    assert (
        "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1=BOUND"
        in a1_crash
    )
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1"
        in a1_crash
    )
    assert "ADJUDICATION_CLASS=PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE" in a1_crash
    assert "EXPLICIT_NONREQUIREMENT_PROVEN=false" in a1_crash
    assert "ATOMIC_REPLACE_IMPLEMENTED=false" in a1_crash
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in a1_crash
    assert "RUNTIME_AUTHORIZED=false" in a1_crash
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in a1_crash
    assert "POWER_LOSS_DURABILITY=UNPROVEN" in a1_crash
    assert "NEXT_DDO_STEP=PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1" in a1_crash
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in a1_crash
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in a1_crash
    a1_failure_policy = _a1_failure_policy_persist_section(runbook)
    assert "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1=BOUND" in a1_failure_policy
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1"
        in a1_failure_policy
    )
    assert (
        "A1_DURABILITY_FAILURE_POLICY=BOUND_FAIL_CLOSED_DEPENDENT_MUTATION_FORBIDDEN_ON_UNPROVEN_DURABILITY"
        in a1_failure_policy
    )
    assert "DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY=FORBIDDEN" in a1_failure_policy
    assert "AMBIGUOUS_RETRY_ALLOWED=false" in a1_failure_policy
    assert "UNKNOWN_PRESERVED=true" in a1_failure_policy
    assert "PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING=false" in a1_failure_policy
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in a1_failure_policy
    assert "RUNTIME_AUTHORIZED=false" in a1_failure_policy
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in a1_failure_policy
    assert (
        "NEXT_DDO_STEP=OWNER_GO_REQUIRED_SEPARATE_SCOPED_DDO_A1_CONTINUATION_NOT_AUTHORIZED_BY_THIS_PERSIST"
        in a1_failure_policy
    )


def test_map_and_atlas_remain_navigation_only() -> None:
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    atlas = ATLAS_CATALOG.read_text(encoding="utf-8")
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_POINTER_ONLY" in mot or (
        "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY" in mot
    )
    assert (
        "DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_ROLE=NAVIGATION_POINTER_ONLY" in mot
    )
    assert "DDO_PRODUCTIVE_HOST_SCOPE_INPUT_BINDING_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert "DDO_PRODUCTIVE_HOST_DURABLE_LEDGER_BINDING_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert "DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert "DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert (
        "DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_ROLE=NAVIGATION_POINTER_ONLY"
        in mot
    )
    assert "DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_ROLE=NAVIGATION_POINTER_ONLY" in mot
    assert "DDO_AUTHORITY_EFFECT=NONE" in mot
    assert "MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY" in mot
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1 is" in atlas
    assert "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZATION_V1 is" in atlas
    assert (
        "PEAK_TRADE_DDO_A1_CRASH_DURABILITY_ATOMIC_REPLACE_OR_EXPLICIT_NONREQUIREMENT_V1" in atlas
    )
    assert "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1 is bound" in atlas
    assert "PRODUCTIVE_HOST_LEDGER_BINDING" in atlas
    assert "Atlas is not trading authority" in atlas
    assert (
        "current_canonical: true"
        not in atlas.split("id: RUNTIME_COMPONENT:ddo_ledger_v0", 1)[1][:800]
    )


def test_no_productive_host_ledger_path_and_no_second_store() -> None:
    host = HOST_PATH.read_text(encoding="utf-8")
    capture = CAPTURE_PATH.read_text(encoding="utf-8")
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    authority = AUTHORITY_PATH.read_text(encoding="utf-8")
    assert (
        "ddo_capture_binding: DdoCaptureBindingV0 = field(default_factory=DdoCaptureBindingV0)"
        in host
    )
    assert "ledger_path: Path | str | None = None" in capture
    assert "class AppendOnlyDdoLedgerV0:" in ledger
    assert 'AUTHORITY_OWNER: Final[str] = "NONE"' in authority
    persist_fn = capture[capture.index("def _persist(") :]
    persist_fn = persist_fn[: persist_fn.index("\ndef _view(")]
    persisted_at = persist_fn.index("binding.persisted_ids.append(record_id)")
    ledger_append_at = persist_fn.index("ledger.append(frozen)")
    assert ledger_append_at < persisted_at
    src_learning = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0"
    ledger_py_files = sorted(path.name for path in src_learning.glob("*ledger*.py"))
    assert ledger_py_files == ["ledger_v0.py"]
    sqlite_hits = list(src_learning.glob("*.sqlite"))
    assert sqlite_hits == []
    host_default = (
        "ddo_capture_binding: DdoCaptureBindingV0 = field(default_factory=DdoCaptureBindingV0)"
    )
    assert host_default in host
    assert "ddo_durable_evidence_runtime_state_root: Optional[str] = None" in host
    assert 'ddo_evidence_environment_binding_status: str = "UNBOUND"' in host
    assert "ddo_observation_host_scope: Optional[DdoObservationHostScopeInputsV1] = None" in host
    assert "resolve_ddo_durable_evidence_path_v1(" not in host
    binding_path = (
        REPO_ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "ddo_observation_host_scope_binding_v1.py"
    )
    binding = binding_path.read_text(encoding="utf-8")
    assert "resolve_ddo_durable_evidence_path_v1(" in binding
    assert "class DdoObservationHostScopeInputsV1" in binding
    assert "ddo_durable_ledger_path: Optional[str] = None" in host
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    allowed_src_prefixes = (
        "src/learning/deterministic_decision_outcome_v0/",
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/",
    )
    unexpected = [
        path
        for path in changed
        if path.startswith("src/") and not path.startswith(allowed_src_prefixes)
    ]
    assert unexpected == []
