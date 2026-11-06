"""Autonomous Ops Control Plane v0 — frozen state model and non-authority invariants.

Offline/static contract tests only. Aligns with durable external charter:
``Peak_Trade_runtime_evidence_archive_20260520T161443Z/charter/autonomous_ops_control_plane_v0_*/``

Never imports scheduler/runtime modules, never dispatches workflows, never touches
network/AWS/broker/live paths. Does not re-test manifest hashing (see closeout chain owner).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_MODULE = Path(__file__).name

SHADOW_247_GOVERNANCE_CHARTER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
)
PAPER_SHADOW_247_PREFLIGHT = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
RUNTIME_LANE_TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
CLOSEOUT_CHAIN_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_closeout_to_projection_chain_automation_contract_v0.py"
)
TAXONOMY_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_runtime_lane_taxonomy_authority_levels_contract_v0.py"
)

CONTROL_PLANE_STATES_V0: tuple[str, ...] = (
    "STOP_IDLE",
    "PREFLIGHT_BLOCKED",
    "PREFLIGHT_PASS",
    "READY_FOR_OPERATOR_TOKEN",
    "RUNNING",
    "CLOSEOUT_REQUIRED",
    "EVIDENCE_VERIFIED",
    "FAILED_CLOSED",
)

FORBIDDEN_TRANSITIONS_V0: frozenset[tuple[str, str]] = frozenset(
    {
        ("STOP_IDLE", "RUNNING"),
        ("PREFLIGHT_BLOCKED", "RUNNING"),
        ("PREFLIGHT_PASS", "RUNNING"),
        ("RUNNING", "EVIDENCE_VERIFIED"),
        ("FAILED_CLOSED", "RUNNING"),
        ("EVIDENCE_VERIFIED", "RUNNING"),
    }
)

# Semantic paths that must exist for legal progression (not exhaustive runtime simulation).
REQUIRED_INTERMEDIATE_FOR_TARGET: dict[tuple[str, str], tuple[str, ...]] = {
    ("PREFLIGHT_PASS", "RUNNING"): ("READY_FOR_OPERATOR_TOKEN",),
    ("RUNNING", "EVIDENCE_VERIFIED"): ("CLOSEOUT_REQUIRED",),
}

NON_AUTHORITY_INVARIANTS_V0: frozenset[str] = frozenset(
    {
        "docs_are_not_approval",
        "dashboard_is_not_approval",
        "ai_is_not_authority",
        "signal_is_not_trade",
        "preflight_pass_is_not_run_authorization",
        "evidence_verified_is_not_live_approval",
        "stop_idle_is_valid_safety_state",
    }
)

_FORBIDDEN_SOURCE_PATTERNS: tuple[str, ...] = (
    "subprocess.run",
    "subprocess.Popen",
    "os.system",
    "boto3",
    "paramiko",
    "import requests",
    "import urllib",
    "import socket",
    "run_scheduler.main(",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical owner: {path}"
    return path.read_text(encoding="utf-8")


def _this_module_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def test_control_plane_states_v0_frozen_shape() -> None:
    assert len(CONTROL_PLANE_STATES_V0) == 8
    assert len(set(CONTROL_PLANE_STATES_V0)) == 8
    for state in CONTROL_PLANE_STATES_V0:
        assert state == state.upper()
        assert state.isidentifier() or state.replace("_", "").isalnum()
    assert "STOP_IDLE" in CONTROL_PLANE_STATES_V0
    assert "FAILED_CLOSED" in CONTROL_PLANE_STATES_V0
    assert CONTROL_PLANE_STATES_V0[0] != "RUNNING"
    assert "EVIDENCE_VERIFIED" in CONTROL_PLANE_STATES_V0
    assert "RUNNING" in CONTROL_PLANE_STATES_V0


def test_forbidden_transitions_v0_include_required_pairs() -> None:
    required = {
        ("STOP_IDLE", "RUNNING"),
        ("PREFLIGHT_BLOCKED", "RUNNING"),
        ("PREFLIGHT_PASS", "RUNNING"),
        ("RUNNING", "EVIDENCE_VERIFIED"),
        ("FAILED_CLOSED", "RUNNING"),
        ("EVIDENCE_VERIFIED", "RUNNING"),
    }
    assert required <= FORBIDDEN_TRANSITIONS_V0


def test_forbidden_transition_semantics_v0() -> None:
    def is_forbidden(src: str, dst: str) -> bool:
        return (src, dst) in FORBIDDEN_TRANSITIONS_V0

    assert is_forbidden("STOP_IDLE", "RUNNING")
    assert is_forbidden("PREFLIGHT_BLOCKED", "RUNNING")
    assert is_forbidden("PREFLIGHT_PASS", "RUNNING")
    assert is_forbidden("RUNNING", "EVIDENCE_VERIFIED")
    assert is_forbidden("FAILED_CLOSED", "RUNNING")
    assert is_forbidden("EVIDENCE_VERIFIED", "RUNNING")

    assert ("PREFLIGHT_PASS", "RUNNING") in REQUIRED_INTERMEDIATE_FOR_TARGET
    assert REQUIRED_INTERMEDIATE_FOR_TARGET[("PREFLIGHT_PASS", "RUNNING")] == (
        "READY_FOR_OPERATOR_TOKEN",
    )
    assert ("RUNNING", "EVIDENCE_VERIFIED") in REQUIRED_INTERMEDIATE_FOR_TARGET
    assert REQUIRED_INTERMEDIATE_FOR_TARGET[("RUNNING", "EVIDENCE_VERIFIED")] == (
        "CLOSEOUT_REQUIRED",
    )

    assert not is_forbidden("PREFLIGHT_PASS", "READY_FOR_OPERATOR_TOKEN")
    assert not is_forbidden("READY_FOR_OPERATOR_TOKEN", "RUNNING")
    assert not is_forbidden("RUNNING", "CLOSEOUT_REQUIRED")
    assert not is_forbidden("CLOSEOUT_REQUIRED", "EVIDENCE_VERIFIED")
    assert not is_forbidden("EVIDENCE_VERIFIED", "STOP_IDLE")
    assert not is_forbidden("FAILED_CLOSED", "STOP_IDLE")


def test_non_authority_invariants_v0_frozen_literals() -> None:
    assert len(NON_AUTHORITY_INVARIANTS_V0) == 7
    assert "docs_are_not_approval" in NON_AUTHORITY_INVARIANTS_V0
    assert "dashboard_is_not_approval" in NON_AUTHORITY_INVARIANTS_V0
    assert "ai_is_not_authority" in NON_AUTHORITY_INVARIANTS_V0
    assert "signal_is_not_trade" in NON_AUTHORITY_INVARIANTS_V0
    assert "preflight_pass_is_not_run_authorization" in NON_AUTHORITY_INVARIANTS_V0
    assert "evidence_verified_is_not_live_approval" in NON_AUTHORITY_INVARIANTS_V0
    assert "stop_idle_is_valid_safety_state" in NON_AUTHORITY_INVARIANTS_V0


def test_shadow247_governance_charter_crosslink_v0() -> None:
    text = _read(SHADOW_247_GOVERNANCE_CHARTER)
    assert "**STOP_IDLE**" in text
    assert "**Docs ≠ Approval**" in text
    assert "**Dashboard ≠ Approval**" in text
    assert "**Evidence ≠ Approval**" in text
    assert "Signal ≠ Trade" in text or "signal" in text.lower()


def test_paper_shadow_preflight_crosslink_v0() -> None:
    text = _read(PAPER_SHADOW_247_PREFLIGHT)
    assert "**BLOCKED**" in text or "BLOCKED" in text
    assert "READY_FOR_START=false" in text
    assert "FULL_POST_CLOSEOUT_AUTOMATION_IMPLEMENTED=false" in text
    assert "MANIFEST_VERIFY" in text
    assert "Evidence ≠ approval" in text or "Evidence ≠ Approval" in text


def test_runtime_lane_taxonomy_crosslink_v0() -> None:
    text = _read(RUNTIME_LANE_TAXONOMY)
    assert "NON_AUTHORIZING" in text
    assert "READY_FOR_START=false" in text
    assert PAPER_SHADOW_247_PREFLIGHT.name in text


def test_closeout_chain_owner_pointer_v0() -> None:
    text = _read(CLOSEOUT_CHAIN_TEST)
    assert "durable_closeout_copy_verify_v0" in text
    assert "build_post_closeout_projection_payload_v0" in text
    assert "post-closeout" in text.lower()
    assert "verify_manifest_sha256" in text or "MANIFEST" in text
    assert CLOSEOUT_CHAIN_TEST.name == (
        "test_closeout_to_projection_chain_automation_contract_v0.py"
    )


def test_taxonomy_test_module_remains_separate_owner_v0() -> None:
    assert TAXONOMY_TEST.is_file()
    assert TAXONOMY_TEST.name != THIS_MODULE


def test_module_imports_are_stdlib_only_v0() -> None:
    allowed_roots = frozenset({"__future__", "ast", "pathlib"})
    tree = ast.parse(_this_module_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module is not None
            root = node.module.split(".")[0]
            assert root in allowed_roots, f"unexpected import from: {node.module!r}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_roots, f"unexpected import: {alias.name!r}"


def test_module_has_no_runtime_or_network_imports_v0() -> None:
    in_forbidden_tuple = False
    for line in _this_module_source().splitlines():
        if "_FORBIDDEN_SOURCE_PATTERNS" in line:
            in_forbidden_tuple = True
            continue
        if in_forbidden_tuple:
            if line.strip().startswith(")"):
                in_forbidden_tuple = False
            continue
        for pattern in _FORBIDDEN_SOURCE_PATTERNS:
            assert pattern not in line, (
                f"forbidden pattern in contract test source: {pattern!r} line={line!r}"
            )
