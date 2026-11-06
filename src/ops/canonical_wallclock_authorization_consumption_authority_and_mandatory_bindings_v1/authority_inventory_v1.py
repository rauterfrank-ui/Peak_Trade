"""Authority / call-graph inventory for fail-closed completion capability."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.call_graph_contract_v1 import (
    verify_wallclock_v2_gate_call_graph_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    COMPLETION_CAPABILITY_ID,
)

PRODUCTIVE_WRITER = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/"
    "productive_operator_go_producer_v1.py"
)
PRODUCTIVE_VERIFIER = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/"
    "productive_authorization_verifier_v1.py"
)
PRODUCTIVE_ENTRY = (
    "src/ops/integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1/"
    "productive_run_entrypoint_v1.py"
)
GATEKEEPER = (
    "src/ops/canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1/"
    "wallclock_v2_gatekeeper_v1.py"
)
SESSION_RUNTIME = "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/session_runtime_v1.py"
PACKAGE_INIT = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/__init__.py"
)
FORCED_FIXTURE = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/"
    "forced_wiring_fixture_v2.py"
)
V2_WRITER = (
    "src/ops/canonical_durable_authorization_lifecycle_and_revocation_v1/authorization_writer_v2.py"
)
FORBIDDEN_PRODUCTIVE_V1_SYMBOLS = (
    "build_authorization_artifact_v1",
    "load_authorization_artifact_v1",
    "validate_authorization_artifact_v1",
    "transition_consume_authorization_artifact_v1",
)


@dataclass
class AuthorityInventoryResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    inventory: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "capability": COMPLETION_CAPABILITY_ID,
            "inventory": dict(self.inventory),
            "single_productive_authorization_authority": self.ok,
            "second_authorization_authority_absent": self.ok,
            "productive_authorization_issuance_v2_only": self.ok,
        }


def _src(repo_root: Path, rel: str) -> str:
    return (repo_root / rel).read_text(encoding="utf-8")


def _imports_session_runtime(package_init_src: str) -> bool:
    """True if package __init__ eagerly imports session_runtime at module scope."""
    tree = ast.parse(package_init_src)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module and "session_runtime_v1" in node.module:
                return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "session_runtime_v1" in alias.name:
                    return True
    return False


def verify_productive_authorization_authority_inventory_v1(
    *,
    repo_root: Path,
) -> AuthorityInventoryResultV1:
    blockers: list[str] = []
    notes: list[str] = []
    inventory: dict[str, Any] = {
        "productive_writers": [PRODUCTIVE_WRITER, V2_WRITER],
        "productive_verifiers": [PRODUCTIVE_VERIFIER],
        "productive_consumption_paths": [GATEKEEPER, SESSION_RUNTIME, PRODUCTIVE_ENTRY],
        "productive_wallclock_start_paths": [SESSION_RUNTIME, PRODUCTIVE_ENTRY],
    }

    for rel in (
        PRODUCTIVE_WRITER,
        PRODUCTIVE_VERIFIER,
        PRODUCTIVE_ENTRY,
        GATEKEEPER,
        SESSION_RUNTIME,
        PACKAGE_INIT,
        FORCED_FIXTURE,
        V2_WRITER,
    ):
        if not (repo_root / rel).is_file():
            blockers.append(f"MISSING_SOURCE:{rel}")

    if blockers:
        return AuthorityInventoryResultV1(ok=False, blockers=blockers, inventory=inventory)

    writer_src = _src(repo_root, PRODUCTIVE_WRITER)
    verifier_src = _src(repo_root, PRODUCTIVE_VERIFIER)
    entry_src = _src(repo_root, PRODUCTIVE_ENTRY)
    session_src = _src(repo_root, SESSION_RUNTIME)
    init_src = _src(repo_root, PACKAGE_INIT)
    fixture_src = _src(repo_root, FORCED_FIXTURE)
    gate_src = _src(repo_root, GATEKEEPER)

    for sym in FORBIDDEN_PRODUCTIVE_V1_SYMBOLS:
        if sym in writer_src:
            blockers.append(f"PRODUCTIVE_WRITER_USES_V1:{sym}")
        if sym in verifier_src:
            blockers.append(f"PRODUCTIVE_VERIFIER_USES_V1:{sym}")
        if sym in entry_src and "AUTHORIZATION_SCHEMA_REJECTED_LEGACY" not in entry_src:
            blockers.append(f"PRODUCTIVE_ENTRY_USES_V1:{sym}")

    if "build_authorization_artifact_dict_v2" not in writer_src:
        blockers.append("PRODUCTIVE_WRITER_MISSING_V2_BUILDER")
    else:
        notes.append("PRODUCTIVE_ISSUANCE_V2_ONLY")
    if "parse_authorization_artifact_v2" not in verifier_src:
        blockers.append("PRODUCTIVE_VERIFIER_MISSING_V2_PARSER")
    else:
        notes.append("PRODUCTIVE_VERIFIER_V2_ONLY")
    if "consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1" not in session_src:
        blockers.append("SESSION_RUNTIME_MISSING_V2_GATE")
    if (
        "AUTH_VERIFIED" in session_src
        and "self._transition(WallclockSessionState.AUTH_VERIFIED)" in session_src
    ):
        blockers.append("AUTH_VERIFIED_BEFORE_CONSUMPTION_STILL_PRESENT")
    else:
        notes.append("AUTH_VERIFIED_BEFORE_CONSUMPTION_REMOVED")
    if "evidence_root.mkdir" in session_src:
        # Must appear only after gatekeeper success.
        consume_idx = session_src.find(
            "consume_authorization_for_wallclock_start_via_v2_gatekeeper_v1"
        )
        mkdir_idx = session_src.find("self.evidence_root.mkdir")
        if consume_idx < 0 or mkdir_idx < 0 or mkdir_idx < consume_idx:
            blockers.append("EVIDENCE_MKDIR_NOT_AFTER_CONSUMPTION")
        else:
            notes.append("EVIDENCE_MKDIR_AFTER_CONSUMPTION")
    if _imports_session_runtime(init_src):
        blockers.append("PACKAGE_INIT_EAGER_SESSION_RUNTIME_IMPORT")
    else:
        notes.append("PACKAGE_INIT_NO_EAGER_SESSION_RUNTIME")
    if "wallclock_evidence_v1" in gate_src:
        blockers.append("GATEKEEPER_DEPENDS_ON_WALLCLOCK_EVIDENCE_MODULE")
    else:
        notes.append("GATEKEEPER_USES_PROTOCOL_SINK")
    if "forced_fixture_can_consume_productive_authorization" not in fixture_src:
        blockers.append("FORCED_FIXTURE_MISSING_NON_CONSUMPTION_ATTESTATION")
    if "consume_authorization_artifact_v2" in fixture_src:
        blockers.append("FORCED_FIXTURE_CALLS_PRODUCTIVE_CONSUMPTION")

    call_graph = verify_wallclock_v2_gate_call_graph_v1(repo_root=repo_root)
    if not call_graph.ok:
        blockers.extend(call_graph.blockers)
    else:
        notes.extend(call_graph.notes)

    inventory["call_graph_ok"] = call_graph.ok
    return AuthorityInventoryResultV1(
        ok=not blockers,
        blockers=sorted(set(blockers)),
        notes=notes,
        inventory=inventory,
    )
