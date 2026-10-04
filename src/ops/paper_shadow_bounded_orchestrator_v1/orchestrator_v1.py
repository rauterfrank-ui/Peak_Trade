"""Paper-Shadow bounded run orchestrator — composition and lifecycle only."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.canonical_shadow_runtime_enablement_v1.proof_v1 import (
    prove_canonical_shadow_runtime_safety_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_activation_state_v1 import (
    evaluate_shadow_activation_state_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.bounded_limits_v1 import BoundedRunCountersV1
from src.ops.paper_shadow_bounded_orchestrator_v1.fixpoint_self_check_v1 import (
    evaluate_fixpoint_self_check_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.observation_step_v1 import (
    preflight_public_observation_capability_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.owner_go_validator_v1 import (
    validate_owner_go_authorization_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    PaperShadowRunContractV1,
    load_paper_shadow_run_contract_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
    verify_contract_settings_digest_v1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_state_machine_v1 import (
    RunLifecycleState,
    RunStateMachineV1,
)


@dataclass
class PreflightResultV1:
    ok: bool
    final_preflight_state: str
    run_started: bool
    owner_go_consumed: bool
    contract: PaperShadowRunContractV1
    fixpoint: dict[str, Any]
    shadow: dict[str, Any]
    wallclock_preflight: dict[str, Any]
    state_machine: dict[str, Any]
    blockers: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "FINAL_PREFLIGHT_STATE": self.final_preflight_state,
            "RUN_STARTED": self.run_started,
            "OWNER_GO_CONSUMED": self.owner_go_consumed,
            "contract": self.contract.to_dict(),
            "fixpoint": self.fixpoint,
            "shadow": self.shadow,
            "wallclock_preflight": self.wallclock_preflight,
            "state_machine": self.state_machine,
            "blockers": list(self.blockers),
        }


def _scan_orchestrator_for_webui_imports(package_dir: Path) -> int:
    count = 0
    for path in package_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "webui" in node.module:
                count += 1
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "webui" in alias.name:
                        count += 1
    return count


def run_paper_shadow_preflight_only_v1(
    *,
    contract_path: Path,
    repo_root: Path | None = None,
    settings_digest_path: Path | None = None,
) -> PreflightResultV1:
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    contract = load_paper_shadow_run_contract_v1(
        contract_path=Path(contract_path),
        settings_digest_path=settings_digest_path,
    )
    sm = RunStateMachineV1()
    sm.begin_preflight()
    blockers: list[str] = []

    fixpoint = evaluate_fixpoint_self_check_v1(
        repo_root=root,
        expected_fixpoint_sha=contract.fixpoint_sha,
        expected_tree_sha=contract.fixpoint_tree,
        settings_digest=contract.settings_digest,
    )
    if not fixpoint.ok:
        blockers.extend(fixpoint.blockers)

    digest_ok, _expected_digest, _manifest = verify_contract_settings_digest_v1(
        repo_root=root,
        contract=contract,
    )
    if not digest_ok:
        blockers.append("SETTINGS_DIGEST_MISMATCH")

    shadow_state = evaluate_shadow_activation_state_v1(repo_root=root)
    safety = prove_canonical_shadow_runtime_safety_v1()
    if not shadow_state.shadow_implemented or not shadow_state.shadow_activatable:
        blockers.append("SHADOW_NOT_ACTIVATABLE")
    if shadow_state.shadow_authorized or shadow_state.shadow_running:
        blockers.append("SHADOW_ALREADY_AUTHORIZED_OR_RUNNING")
    if safety.get("ok") is not True:
        blockers.append("SHADOW_SAFETY_PROOF_FAILED")

    wallclock = preflight_public_observation_capability_v1(repo_root=root)
    if not wallclock.get("ok"):
        blockers.append("WALLCLOCK_OBSERVATION_PREFLIGHT_FAILED")

    go_val = validate_owner_go_authorization_v1(contract=contract)
    if go_val.owner_go_present:
        blockers.append("UNEXPECTED_OWNER_GO_PRESENT_IN_PREFLIGHT")

    webui_imports = _scan_orchestrator_for_webui_imports(Path(__file__).resolve().parent)
    if webui_imports:
        blockers.append("ORCHESTRATOR_IMPORTS_WEBUI")

    final_state = "GO_READY_AWAITING_EXPLICIT_OWNER_GO"
    if blockers:
        sm.fail()
        final_state = "NO_GO_PREFLIGHT"
    else:
        sm.complete_preflight_ready()

    return PreflightResultV1(
        ok=not blockers,
        final_preflight_state=final_state,
        run_started=False,
        owner_go_consumed=False,
        contract=contract,
        fixpoint=fixpoint.to_dict(),
        shadow={
            **shadow_state.to_dict(),
            "safety": safety,
        },
        wallclock_preflight=wallclock,
        state_machine=sm.to_dict(),
        blockers=tuple(blockers),
    )


def assert_run_not_implicitly_started_v1(*, state: RunLifecycleState) -> None:
    if state in (RunLifecycleState.RUNNING, RunLifecycleState.AUTHORIZED):
        raise RuntimeError("IMPLICIT_RUN_START_FORBIDDEN")
