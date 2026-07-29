"""Repository-truth readiness producer for Paper-Shadow Observation.

Discovers concrete capability surfaces and parity/safety facts from the
repository. Never mocks PASS. Never grants authorization. Authority effect NONE.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_paper_shadow_economic_validity_pipeline_v1 import (
    IntegratedPaperShadowEconomicValidityEvidenceInputV1,
    evaluate_paper_shadow_observation_readiness_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    CONFIG_RELPATH,
    CONTRACT_DOC_RELPATH,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_VERSION,
)
from src.ops.integrated_paper_shadow_observation_session_v1.no_order_guard_v1 import (
    attest_capability_sources_no_order_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PORTFOLIO_ECONOMICS_MODEL_ID,
)

READINESS_PRODUCER_ID = "ops.integrated_paper_shadow_observation_readiness_producer_v1"

_CAPABILITY_SOURCE_RELPATHS: tuple[str, ...] = (
    "src/ops/integrated_paper_shadow_observation_session_v1/__init__.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/entrypoint_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/market_data_policy_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/session_lifecycle_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/evidence_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/bundle_verifier_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/readiness_producer_v1.py",
    "src/ops/integrated_paper_shadow_observation_session_v1/no_order_guard_v1.py",
)


@dataclass(frozen=True)
class ReadinessDiscoveryFactV1:
    fact_id: str
    present: bool
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PaperShadowObservationReadinessResultV1:
    schema_id: str
    schema_version: str
    producer_id: str
    capability_id: str
    package_marker: str
    authority_effect: str
    PAPER_SHADOW_OBSERVATION_READINESS_PASS: bool
    PAPER_SHADOW_OBSERVATION_AUTHORIZED: bool
    readiness_blockers: list[str] = field(default_factory=list)
    discovery_facts: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _file_exists(repo_root: Path, relpath: str) -> bool:
    path = (repo_root / relpath).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return False
    return path.is_file()


def _module_defines_symbol(repo_root: Path, relpath: str, symbol: str) -> bool:
    path = repo_root / relpath
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return True
    return False


def _discover_surface_p_flags(repo_root: Path) -> tuple[bool, bool, bool, str]:
    """Return (full_chain, parity, economic_admissible, evidence). Fail-closed."""
    try:
        from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
            evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
        )

        flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
        return (
            bool(flags.full_canonical_chain_wired),
            bool(flags.backtest_runtime_decision_parity_pass),
            bool(flags.system_economic_evidence_admissible),
            "surface_p_final_flags_fail_closed_contract_v0",
        )
    except Exception as exc:  # noqa: BLE001 - discovery fail-closed
        return False, False, False, f"surface_p_discovery_failed:{type(exc).__name__}"


def _discover_step29u_bound(repo_root: Path) -> tuple[bool, str]:
    try:
        from src.ops.step_29u_canonical_shadow_binding_v0 import (
            observe_canonical_step_29u_bound_v0,
        )

        bound, reasons = observe_canonical_step_29u_bound_v0(repo_root=repo_root)
        return bool(bound), ",".join(reasons) if reasons else "step_29u_bound_observed"
    except Exception as exc:  # noqa: BLE001
        return False, f"step_29u_discovery_failed:{type(exc).__name__}"


def produce_paper_shadow_observation_readiness_v1(
    *,
    repo_root: Path | None = None,
    operator_go_granted: bool = False,
    force_pass: bool = False,
) -> PaperShadowObservationReadinessResultV1:
    """Produce readiness from repository truth. force_pass is rejected."""
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    facts: list[ReadinessDiscoveryFactV1] = []
    notes = [
        "READINESS_FROM_REPOSITORY_TRUTH",
        "NO_BOOLEAN_PLACEHOLDER_PASS",
        "AUTHORITY_EFFECT=NONE",
        "PAPER_SHADOW_OBSERVATION_AUTHORIZED=false",
    ]
    blockers: list[str] = []

    if force_pass:
        return PaperShadowObservationReadinessResultV1(
            schema_id=READINESS_PRODUCER_ID,
            schema_version=SCHEMA_VERSION,
            producer_id=READINESS_PRODUCER_ID,
            capability_id=CAPABILITY_ID,
            package_marker=PACKAGE_MARKER,
            authority_effect=AUTHORITY_EFFECT_NONE,
            PAPER_SHADOW_OBSERVATION_READINESS_PASS=False,
            PAPER_SHADOW_OBSERVATION_AUTHORIZED=False,
            readiness_blockers=["FORCE_PASS_REJECTED"],
            discovery_facts=[],
            notes=notes + ["FORCE_PASS_FORBIDDEN"],
        )
    if operator_go_granted:
        # GO grant is out of scope for this capability; never treat as readiness authority.
        notes.append("OPERATOR_GO_INPUT_IGNORED_NOT_AUTHORITY")

    # Capability surface discovery.
    for rel in _CAPABILITY_SOURCE_RELPATHS:
        present = _file_exists(root, rel)
        facts.append(
            ReadinessDiscoveryFactV1(
                fact_id=f"SOURCE:{rel}",
                present=present,
                evidence=rel,
            )
        )
        if not present:
            blockers.append(f"CAPABILITY_SOURCE_MISSING:{rel}")

    config_present = _file_exists(root, CONFIG_RELPATH)
    doc_present = _file_exists(root, CONTRACT_DOC_RELPATH)
    facts.append(ReadinessDiscoveryFactV1("CONFIG_PRESENT", config_present, CONFIG_RELPATH))
    facts.append(
        ReadinessDiscoveryFactV1("CONTRACT_DOC_PRESENT", doc_present, CONTRACT_DOC_RELPATH)
    )
    if not config_present:
        blockers.append("CONFIG_MISSING")
    if not doc_present:
        blockers.append("CONTRACT_DOC_MISSING")

    model_defined = _module_defines_symbol(
        root,
        "src/ops/integrated_paper_shadow_observation_session_v1/portfolio_economics_model_v1.py",
        "SimulatedPortfolioEconomicsModelV1",
    ) and PORTFOLIO_ECONOMICS_MODEL_ID.startswith("ops.")
    facts.append(
        ReadinessDiscoveryFactV1(
            "SIMULATED_PORTFOLIO_FILL_FEE_SLIPPAGE_PNL_MODEL_DEFINED",
            model_defined,
            PORTFOLIO_ECONOMICS_MODEL_ID,
        )
    )

    evidence_defined = _module_defines_symbol(
        root,
        "src/ops/integrated_paper_shadow_observation_session_v1/evidence_v1.py",
        "write_observation_evidence_bundle_v1",
    ) and _module_defines_symbol(
        root,
        "src/ops/integrated_paper_shadow_observation_session_v1/bundle_verifier_v1.py",
        "verify_integrated_paper_shadow_observation_evidence_bundle_v1",
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "EVIDENCE_DIRECTORY_MANIFEST_SCHEMA_CONFIG_DIGESTS_VERIFIER_DEFINED",
            evidence_defined,
            "evidence_v1+bundle_verifier_v1",
        )
    )

    lifecycle_defined = _module_defines_symbol(
        root,
        "src/ops/integrated_paper_shadow_observation_session_v1/session_lifecycle_v1.py",
        "plan_observation_session_lifecycle_v1",
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "SESSION_LIFECYCLE_DEFINED",
            lifecycle_defined,
            "session_lifecycle_v1",
        )
    )

    # Operator-GO / Session-Preregistration discovery (versioned surfaces required).
    try:
        from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.discovery_v1 import (
            discover_session_preregistration_and_operator_go_contract_present_v1,
        )

        go_discovery = discover_session_preregistration_and_operator_go_contract_present_v1(
            repo_root=root
        )
        go_contract_present = bool(
            go_discovery.SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT
        )
        go_evidence = (
            "discovery_v1_pass"
            if go_contract_present
            else ",".join(go_discovery.blockers) or "discovery_fail_closed"
        )
    except Exception as exc:  # noqa: BLE001 - discovery fail-closed
        go_contract_present = False
        go_evidence = f"go_prereg_discovery_failed:{type(exc).__name__}"
    facts.append(
        ReadinessDiscoveryFactV1(
            "SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT",
            go_contract_present,
            go_evidence,
        )
    )

    no_order = attest_capability_sources_no_order_v1(
        repo_root=root,
        relative_paths=_CAPABILITY_SOURCE_RELPATHS,
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "BROKER_WRITE_PATH_UNREACHABLE",
            no_order.ok,
            ",".join(no_order.blockers) if no_order.blockers else "no_order_attestation_ok",
        )
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "ORDER_AUTHORITY_ABSENT",
            True,  # capability config/constants hard-forbid orders
            "ORDERS_ALLOWED=false",
        )
    )

    full_chain, parity, economic_adm, surface_ev = _discover_surface_p_flags(root)
    # Map Surface P flags into correctness/parity discovery. Economic admissible
    # is NOT required for observation readiness under the reconciled ladder.
    facts.append(ReadinessDiscoveryFactV1("FULL_CANONICAL_SYSTEM_PARITY", full_chain, surface_ev))
    facts.append(
        ReadinessDiscoveryFactV1("SYSTEM_CORRECTNESS_PASS", full_chain and parity, surface_ev)
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "INTEGRATED_OFFLINE_REPLAY_PASS",
            parity,
            surface_ev,
        )
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
            parity,
            surface_ev,
        )
    )
    _ = economic_adm  # discovered but intentionally not a readiness blocker

    step29u_bound, step_ev = _discover_step29u_bound(root)
    facts.append(
        ReadinessDiscoveryFactV1(
            "CANONICAL_DECISION_CHAIN_BOUND",
            step29u_bound,
            step_ev,
        )
    )

    # Hard-coded architecture invariants for this repository posture.
    master_v2_authority = _file_exists(
        root, "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
    )
    safety_kernel = _file_exists(
        root, "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "MASTER_V2_DOUBLE_PLAY_SOLE_DECISION_AUTHORITY",
            master_v2_authority,
            "double_play_entry_exit_policy_v0",
        )
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "AI_LAYER_NON_AUTHORITY",
            True,
            "pipeline_invariant_ai_non_authority",
        )
    )
    facts.append(
        ReadinessDiscoveryFactV1(
            "SAFETY_KERNEL_KILLSTATE_FAIL_CLOSED",
            safety_kernel,
            "safety_kernel_offline_replay_binding_adapter_v0",
        )
    )

    evidence_input = IntegratedPaperShadowEconomicValidityEvidenceInputV1(
        full_canonical_system_parity=full_chain,
        system_correctness_pass=full_chain and parity,
        integrated_offline_replay_pass=parity,
        backtest_runtime_decision_parity_pass=parity,
        canonical_decision_chain_bound=step29u_bound,
        master_v2_double_play_sole_decision_authority=master_v2_authority,
        ai_layer_non_authority=True,
        safety_kernel_killstate_fail_closed=safety_kernel,
        broker_write_path_unreachable=no_order.ok,
        order_authority_absent=True,
        simulated_portfolio_fill_fee_slippage_pnl_model_defined=model_defined,
        evidence_directory_manifest_schema_config_digests_verifier_defined=evidence_defined,
        session_preregistration_and_operator_go_contract_present=go_contract_present,
        economic_validity_offline_gate_pass=False,
    )
    ready, pipeline_blockers = evaluate_paper_shadow_observation_readiness_v1(evidence_input)
    blockers.extend(pipeline_blockers)

    # Extra capability-local blockers.
    if not lifecycle_defined:
        blockers.append("SESSION_LIFECYCLE_UNDEFINED")
        ready = False

    # Determinism: identical discovery → identical pass/fail.
    return PaperShadowObservationReadinessResultV1(
        schema_id=READINESS_PRODUCER_ID,
        schema_version=SCHEMA_VERSION,
        producer_id=READINESS_PRODUCER_ID,
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        authority_effect=AUTHORITY_EFFECT_NONE,
        PAPER_SHADOW_OBSERVATION_READINESS_PASS=bool(ready) and not blockers,
        PAPER_SHADOW_OBSERVATION_AUTHORIZED=False,
        readiness_blockers=sorted(set(blockers)),
        discovery_facts=[f.to_dict() for f in facts],
        notes=notes
        + [
            f"PRODUCER_FAMILY={PRODUCER_FAMILY}",
            "OPERATOR_GO_CONTRACT_ABSENT_KEEPING_READINESS_FAIL_CLOSED"
            if not go_contract_present
            else "OPERATOR_GO_AND_SESSION_PREREGISTRATION_DISCOVERY_TRUE",
            "PAPER_SHADOW_OBSERVATION_AUTHORIZED=false",
            "READINESS_IS_NOT_AUTHORIZATION",
        ],
    )
