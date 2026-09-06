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


def _persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO durable evidence storage owner contract persist"
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
    assert "CAPTURED_IDS_DURABLE_WRITE_BUG_STATUS=OPEN" in spec
    assert "PATH_SOURCE_IMPLEMENTATION=UNBOUND" in spec
    assert "FILE_FSYNC_PRESENT=true" in spec
    assert "DIRECTORY_FSYNC_HARD_GUARANTEE=false" in spec
    assert "ATOMIC_RECORD_APPEND=PARTIAL" in spec
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in spec
    assert (
        "NEXT_DDO_STEP=PEAK_TRADE_DDO_LEDGER_DURABILITY_HARDENING_AND_HOST_BINDING_PREP_V1" in spec
    )
    assert "NO_LEDGER_PATH_IN_HOST=true" in spec
    assert "NO_SECOND_DDO_LEDGER=true" in spec


def test_master_runbook_refers_to_valid_spec() -> None:
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    section = _persist_section(runbook)
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
    live_z2db = runbook.index(
        "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
    )
    persist_start = runbook.index(
        "### 11.13.5 Parallel-track DDO durable evidence storage owner contract persist"
    )
    assert persist_start < live_z2db


def test_map_and_atlas_remain_navigation_only() -> None:
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    atlas = ATLAS_CATALOG.read_text(encoding="utf-8")
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md" in mot
    assert "DOCUMENT_ROLE=NAVIGATION_POINTER_ONLY" in mot or (
        "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY" in mot
    )
    assert "DDO_AUTHORITY_EFFECT=NONE" in mot
    assert "MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY" in mot
    assert "DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1 is" in atlas
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
    captured_ids_at = persist_fn.index("binding.captured_ids.append(record_id)")
    ledger_append_at = persist_fn.index("ledger.append(frozen)")
    assert captured_ids_at < ledger_append_at
    src_learning = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0"
    ledger_py_files = sorted(path.name for path in src_learning.glob("*ledger*.py"))
    assert ledger_py_files == ["ledger_v0.py"]
    sqlite_hits = list(src_learning.glob("*.sqlite"))
    assert sqlite_hits == []
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    assert not any(path.startswith("src/") for path in changed)
