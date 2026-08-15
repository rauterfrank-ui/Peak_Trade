"""Fail-closed verifier for R5 realistic sim/replay semantics v1."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from src.execution.replay_pack.contract import CONTRACT_VERSION as I79_CONTRACT_V1
from src.execution.replay_pack.contract import REQUIRED_FILES as I79_REQUIRED_V1
from src.execution.replay_pack.contract_v2 import CONTRACT_VERSION as I79_CONTRACT_V2
from src.execution.replay_pack.contract_v2 import FIFO_SNAPSHOT_RELPATH
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.constants_v1 import (
    I67_CLASSIFICATION as R4_I67_CLASSIFICATION,
    I67_SUBSTITUTE_FORBIDDEN as R4_I67_SUBSTITUTE_FORBIDDEN,
)
from src.ops.canonical_i17_productive_shadow_contract_readiness_v1.verifier_v1 import (
    evaluate_r4_i17_shadow_contract_readiness_v1,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.constants_v1 import (
    ACTIVATED,
    AUTHORITY_EFFECT,
    CANARY_EXECUTE,
    CAP7_2_SIM_PORT_RELPATH,
    CAP7_INTERNAL_SIM_RELPATH,
    CAP7_OFFLINE_MD_REPLAY_RELPATH,
    CAPABILITY_ID,
    CLUSTER_ID,
    CONTRACT_ID,
    CONTRACT_OWNER,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    DONE_CRITERION,
    I17_CANONICAL_CLOSEOUT_STATUS,
    I17_RERUN_AUTHORIZED,
    I67_CALLER_RELPATH,
    I67_CAP7_EQUIVALENCE,
    I67_I17_EQUIVALENCE,
    I67_OWNER_RELPATH,
    I67_ROLE,
    I67_SUBSTITUTES_CAP7,
    I67_SUBSTITUTES_I17,
    I79_BUILDER_RELPATH,
    I79_CLI_RELPATH,
    I79_CONTRACT_V1_RELPATH,
    I79_CONTRACT_V2_RELPATH,
    I79_DOCS_V1_RELPATH,
    I79_DOCS_VNEXT_RELPATH,
    I79_I17_EQUIVALENCE,
    I79_ROLE,
    I79_SUBSTITUTES_CAP7,
    I79_SUBSTITUTES_CAP7_OFFLINE_MD_REPLAY,
    I79_SUBSTITUTES_I17,
    I79_VALIDATOR_RELPATH,
    LIVE_AUTHORIZED,
    MAX_AGE_ALLOWED_USES,
    MAX_AGE_ENFORCEMENT_ENABLED,
    MAX_AGE_PRODUCTIVE_GATE,
    MAX_AGE_ROLE,
    NAME_COLLISION_EQUIVALENCE,
    NETWORK_EFFECT,
    NEW_EXECUTION_PIPELINE,
    NEW_REPLAY_ENGINE,
    ORDER_EFFECT,
    PACKAGE_MARKER,
    PAPER_EXCHANGE_ORDER_EFFECT,
    PRODUCTIVE_CALLER_EXISTS,
    PROMOTION_AUTHORITY,
    PROMOTION_ELIGIBLE_DEFAULT,
    R6_MULTI_FUTURE_AUTHORIZED,
    REMEDIATION_ID,
    REQUIRED_OWNER_RELPATHS,
    RUNTIME_AUTHORITY_IMPACT,
    RUNTIME_EFFECT,
    SOURCE_GAP_IDS,
    TARGET_BINDING_I67,
    TARGET_BINDING_I79,
    TESTNET_AUTHORIZED,
    TRADING_GRANT,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.lineage_v1 import (
    digest_mapping,
    load_layer_config_v1,
    repo_root,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.matrix_v1 import (
    MODE_CLASS_ROWS,
    REQUIRED_DIMENSIONS,
    SEMANTICS_MATRIX,
    require_dimension,
)
from src.ops.canonical_realistic_sim_replay_semantics_v1.models_v1 import (
    EquivalenceClass,
    ModeClass,
    RealisticSimReplaySemanticsError,
)
from src.sim.paper.simulator import PaperTradingSimulator

_PACKAGE_REL = Path("src") / "ops" / "canonical_realistic_sim_replay_semantics_v1"
_FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "src.orders",
        "src.live",
        "src.execution_simple",
        "src.intents",
    }
)
_FORBIDDEN_REPLAY_RUNTIME_IMPORTS = frozenset(
    {
        "src.execution.replay_pack.runner",
        "src.execution.replay_pack.builder",
        "src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.replay_engine_v1",
        "src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1",
    }
)
_I17_OWNER_PREFIXES = (
    "src/ops/paper_shadow_observation_operator_go_session_preregistration_v1/",
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/",
    "src/ops/integrated_paper_shadow_observation_session_v1/",
    "src/ops/canonical_i17_productive_shadow_contract_readiness_v1/",
)
_I67_IMPORT_ROOTS = ("src.sim.paper",)


def _reject(message: str) -> None:
    raise RealisticSimReplaySemanticsError(message)


def _require(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        _reject(f"config_field_mismatch:{key}:expected={expected!r}:actual={actual!r}")


def _iter_import_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return tuple(names)


def validate_layer_config_v1(payload: Mapping[str, Any]) -> None:
    _require(payload, "activated", False)
    _require(payload, "authority_effect", AUTHORITY_EFFECT)
    _require(payload, "canary_execute", False)
    _require(payload, "capability_id", CAPABILITY_ID)
    _require(payload, "cluster_id", CLUSTER_ID)
    _require(payload, "contract_id", CONTRACT_ID)
    _require(payload, "contract_owner", CONTRACT_OWNER)
    _require(payload, "contract_version", CONTRACT_VERSION)
    _require(payload, "core_logic_change", CORE_LOGIC_CHANGE)
    _require(payload, "done_criterion", DONE_CRITERION)
    _require(payload, "i17_canonical_closeout_status", I17_CANONICAL_CLOSEOUT_STATUS)
    _require(payload, "i17_rerun_authorized", False)
    _require(payload, "i67_cap7_equivalence", False)
    _require(payload, "i67_i17_equivalence", False)
    _require(payload, "i67_role", I67_ROLE)
    _require(payload, "i67_substitutes_cap7", False)
    _require(payload, "i67_substitutes_i17", False)
    _require(payload, "i79_i17_equivalence", False)
    _require(payload, "i79_role", I79_ROLE)
    _require(payload, "i79_substitutes_cap7", False)
    _require(payload, "i79_substitutes_cap7_offline_md_replay", False)
    _require(payload, "i79_substitutes_i17", False)
    _require(payload, "live_authorized", False)
    _require(payload, "max_age_allowed_uses", list(MAX_AGE_ALLOWED_USES))
    _require(payload, "max_age_enforcement_enabled", False)
    _require(payload, "max_age_productive_gate", False)
    _require(payload, "max_age_role", MAX_AGE_ROLE)
    _require(payload, "name_collision_equivalence", False)
    _require(payload, "network_effect", False)
    _require(payload, "new_execution_pipeline", False)
    _require(payload, "new_replay_engine", False)
    _require(payload, "order_effect", ORDER_EFFECT)
    _require(payload, "package_marker", PACKAGE_MARKER)
    _require(payload, "paper_exchange_order_effect", False)
    _require(payload, "productive_caller_exists", False)
    _require(payload, "promotion_authority", False)
    _require(payload, "promotion_eligible_default", False)
    _require(payload, "r6_multi_future_authorized", False)
    _require(payload, "remediation_id", REMEDIATION_ID)
    _require(payload, "runtime_authority_impact", RUNTIME_AUTHORITY_IMPACT)
    _require(payload, "runtime_effect", False)
    _require(payload, "source_gap_ids", list(SOURCE_GAP_IDS))
    _require(payload, "target_binding_i67", TARGET_BINDING_I67)
    _require(payload, "target_binding_i79", TARGET_BINDING_I79)
    _require(payload, "testnet_authorized", False)
    _require(payload, "trading_grant", False)


def assert_package_import_boundary_v1(root: Path | None = None) -> None:
    package = (root or repo_root()) / _PACKAGE_REL
    for path in sorted(package.glob("*.py")):
        for name in _iter_import_names(path):
            for forbidden in _FORBIDDEN_IMPORT_ROOTS:
                if name == forbidden or name.startswith(f"{forbidden}."):
                    _reject(f"forbidden_import:{path.name}:{name}")
            if name in _FORBIDDEN_REPLAY_RUNTIME_IMPORTS:
                _reject(f"runtime_replay_imported:{path.name}:{name}")


def assert_required_owners_present_v1(root: Path | None = None) -> None:
    base = root or repo_root()
    for rel in REQUIRED_OWNER_RELPATHS:
        path = base / rel
        if rel.endswith("/"):
            if not path.is_dir():
                _reject(f"owner_dir_missing:{rel}")
            continue
        if not path.is_file():
            _reject(f"owner_file_missing:{rel}")


def assert_semantics_matrix_complete_and_distinct_v1() -> None:
    present = tuple(row.dimension for row in SEMANTICS_MATRIX)
    if present != REQUIRED_DIMENSIONS:
        _reject(f"dimension_mismatch:expected={REQUIRED_DIMENSIONS}:actual={present}")
    for dimension in REQUIRED_DIMENSIONS:
        row = require_dimension(dimension)
        if row.equivalence is not EquivalenceClass.DISTINCT:
            _reject(f"dimension_not_distinct:{dimension}")
        cells = (
            row.cap7_internal_sim,
            row.cap7_offline_md_replay,
            row.i67_paper_sim,
            row.i79_replay_pack,
            row.i17_productive_shadow,
        )
        if len(set(cells)) != 5:
            _reject(f"cell_collision:{dimension}")
    modes = tuple(row.mode for row in MODE_CLASS_ROWS)
    expected_modes = (
        ModeClass.SIMULATION,
        ModeClass.PAPER,
        ModeClass.REPLAY,
        ModeClass.SHADOW,
        ModeClass.PRODUCTIVE_SHADOW,
        ModeClass.PAPER_EXCHANGE,
    )
    if modes != expected_modes:
        _reject(f"mode_class_mismatch:{modes}")
    for row in MODE_CLASS_ROWS:
        if row.promotion_eligible or row.order_effect != "NONE":
            _reject(f"mode_class_authority:{row.mode.value}")


def assert_i67_is_supporting_and_unwired_from_i17_v1(root: Path | None = None) -> None:
    if PaperTradingSimulator.__module__ != "src.sim.paper.simulator":
        _reject("i67_owner_drift")
    if I67_SUBSTITUTES_I17 or I67_SUBSTITUTES_CAP7 or I67_CAP7_EQUIVALENCE or I67_I17_EQUIVALENCE:
        _reject("i67_equivalence_or_substitute_claimed")
    if I67_ROLE != TARGET_BINDING_I67:
        _reject("i67_role_drift")
    base = root or repo_root()
    for rel in (I67_OWNER_RELPATH, I67_CALLER_RELPATH):
        for name in _iter_import_names(base / rel):
            if name.startswith("src.ops.wallclock_full_canonical_decision_to_simulated"):
                _reject(f"i67_imports_cap7:{rel}:{name}")
            if name.startswith("src.ops.integrated_paper_shadow"):
                _reject(f"i67_imports_i17:{rel}:{name}")
            if name.startswith("src.orders") or name.startswith("src.live"):
                _reject(f"i67_imports_order_or_live:{rel}:{name}")
            if name.startswith("src.execution.replay_pack"):
                _reject(f"i67_imports_i79:{rel}:{name}")
    src_root = base / "src"
    hits: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        rel = path.relative_to(base).as_posix()
        if rel.startswith("src/sim/paper/"):
            continue
        if rel.startswith(_PACKAGE_REL.as_posix() + "/"):
            continue
        if not any(rel.startswith(prefix) for prefix in _I17_OWNER_PREFIXES):
            continue
        for name in _iter_import_names(path):
            for root_name in _I67_IMPORT_ROOTS:
                if name == root_name or name.startswith(f"{root_name}."):
                    hits.append(f"{rel}:{name}")
    if hits:
        _reject(f"i17_imports_i67:{hits}")


def assert_i79_existing_pack_bound_non_authoritative_v1(root: Path | None = None) -> None:
    if str(I79_CONTRACT_V1) != "1" or str(I79_CONTRACT_V2) != "2":
        _reject("i79_contract_version_drift")
    if "manifest.json" not in I79_REQUIRED_V1:
        _reject("i79_v1_manifest_missing_from_required")
    if FIFO_SNAPSHOT_RELPATH != "ledger/ledger_fifo_snapshot.json":
        _reject("i79_v2_fifo_path_drift")
    if any(
        (
            I79_SUBSTITUTES_I17,
            I79_SUBSTITUTES_CAP7,
            I79_SUBSTITUTES_CAP7_OFFLINE_MD_REPLAY,
            I79_I17_EQUIVALENCE,
        )
    ):
        _reject("i79_equivalence_or_substitute_claimed")
    base = root or repo_root()
    vnext = (base / I79_DOCS_VNEXT_RELPATH).read_text(encoding="utf-8")
    if "NO-LIVE HARD" not in vnext:
        _reject("i79_vnext_missing_no_live_hard")
    cli = (base / I79_CLI_RELPATH).read_text(encoding="utf-8")
    if "src.execution.replay_pack.builder" not in cli:
        _reject("i79_cli_not_bound_to_existing_pack")
    cap7_replay = (base / CAP7_OFFLINE_MD_REPLAY_RELPATH).read_text(encoding="utf-8")
    if "src.execution.replay_pack" in cap7_replay:
        _reject("cap7_offline_md_replay_imports_i79")
    i79_contract = (base / I79_CONTRACT_V1_RELPATH).read_text(encoding="utf-8")
    if "replay_engine_v1" in i79_contract:
        _reject("i79_contract_imports_cap7_replay_engine")


def reject_equivalence_claim_v1(*, left: str, right: str, claimed_equivalent: bool) -> None:
    if claimed_equivalent:
        _reject(f"equivalence_unproven:{left}:{right}")
    if left == right:
        _reject(f"self_equivalence_forbidden:{left}")
    if NAME_COLLISION_EQUIVALENCE:
        _reject("name_collision_treated_as_equivalence")


def evaluate_r5_realistic_sim_replay_v1(*, root: Path | None = None) -> Mapping[str, Any]:
    payload = load_layer_config_v1(root)
    validate_layer_config_v1(payload)
    assert_package_import_boundary_v1(root)
    assert_required_owners_present_v1(root)
    assert_semantics_matrix_complete_and_distinct_v1()
    assert_i67_is_supporting_and_unwired_from_i17_v1(root)
    assert_i79_existing_pack_bound_non_authoritative_v1(root)
    reject_equivalence_claim_v1(left="I67", right="CAP7", claimed_equivalent=False)
    reject_equivalence_claim_v1(left="I67", right="I17", claimed_equivalent=False)
    reject_equivalence_claim_v1(left="I79", right="I17", claimed_equivalent=False)
    reject_equivalence_claim_v1(
        left="I79", right="CAP7_OFFLINE_MD_REPLAY", claimed_equivalent=False
    )
    if any(
        (
            ACTIVATED,
            PRODUCTIVE_CALLER_EXISTS,
            NEW_EXECUTION_PIPELINE,
            NEW_REPLAY_ENGINE,
            TRADING_GRANT,
            PROMOTION_AUTHORITY,
            PROMOTION_ELIGIBLE_DEFAULT,
            LIVE_AUTHORIZED,
            TESTNET_AUTHORIZED,
            CANARY_EXECUTE,
            NETWORK_EFFECT,
            PAPER_EXCHANGE_ORDER_EFFECT,
            R6_MULTI_FUTURE_AUTHORIZED,
            I17_RERUN_AUTHORIZED,
            MAX_AGE_ENFORCEMENT_ENABLED,
            MAX_AGE_PRODUCTIVE_GATE,
        )
    ):
        _reject("authority_or_activation_flag_raised")
    r4 = evaluate_r4_i17_shadow_contract_readiness_v1(root=root)
    if r4["verdict"] != "PASS_R4_I17_SHADOW_CONTRACT_READINESS_V1":
        _reject(f"r4_regression:{r4['verdict']}")
    if R4_I67_SUBSTITUTE_FORBIDDEN is not True:
        _reject("r4_i67_substitute_forbidden_drift")
    if R4_I67_CLASSIFICATION != "LOCAL_PAPER_SIMULATION_NOT_I17":
        _reject("r4_i67_classification_drift")
    claims = {
        "activated": ACTIVATED,
        "authority_effect": AUTHORITY_EFFECT,
        "canary_execute": CANARY_EXECUTE,
        "capability_id": CAPABILITY_ID,
        "cap7_internal_sim_owner_present": True,
        "cap7_offline_md_replay_relpath": CAP7_OFFLINE_MD_REPLAY_RELPATH,
        "cap7_2_sim_port_relpath": CAP7_2_SIM_PORT_RELPATH,
        "cap7_internal_sim_relpath": CAP7_INTERNAL_SIM_RELPATH,
        "cluster_id": CLUSTER_ID,
        "config_digest": digest_mapping(payload),
        "core_logic_change": CORE_LOGIC_CHANGE,
        "done_criterion": DONE_CRITERION,
        "duplicate_execution_authority_found": False,
        "duplicate_promotion_authority_found": False,
        "eg_i67_cap7_status": "CLOSED_PROVEN_FORENSIC_KEEP_GOVERNED_SUPPORTING_DISTINCT",
        "i17_canonical_closeout_status": I17_CANONICAL_CLOSEOUT_STATUS,
        "i17_rerun_authorized": I17_RERUN_AUTHORIZED,
        "i67_cap7_equivalence_status": "NOT_PROVEN_DISTINCT",
        "i67_i17_equivalence_status": "NOT_PROVEN_DISTINCT",
        "i67_owner_relpath": I67_OWNER_RELPATH,
        "i67_role_status": I67_ROLE,
        "i79_builder_relpath": I79_BUILDER_RELPATH,
        "i79_cli_relpath": I79_CLI_RELPATH,
        "i79_contract_v1": str(I79_CONTRACT_V1),
        "i79_contract_v1_relpath": I79_CONTRACT_V1_RELPATH,
        "i79_contract_v2": str(I79_CONTRACT_V2),
        "i79_contract_v2_relpath": I79_CONTRACT_V2_RELPATH,
        "i79_docs_v1_relpath": I79_DOCS_V1_RELPATH,
        "i79_docs_vnext_relpath": I79_DOCS_VNEXT_RELPATH,
        "i79_replay_status": "CLOSED_PROVEN_FORENSIC_EXISTING_V1_V2_PACK_BOUND_NON_AUTHORITATIVE",
        "i79_role_status": I79_ROLE,
        "i79_validator_relpath": I79_VALIDATOR_RELPATH,
        "implementation_required": True,
        "implementation_status": "ADDITIVE_SEMANTICS_CONTRACT_REUSING_EXISTING_SURFACES",
        "live_authorized": LIVE_AUTHORIZED,
        "matrix_dimension_count": len(SEMANTICS_MATRIX),
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "max_age_role": MAX_AGE_ROLE,
        "mode_semantics_attested": True,
        "name_collision_equivalence": NAME_COLLISION_EQUIVALENCE,
        "network_effect": NETWORK_EFFECT,
        "new_execution_pipeline": NEW_EXECUTION_PIPELINE,
        "new_replay_engine": NEW_REPLAY_ENGINE,
        "order_effect": ORDER_EFFECT,
        "package_marker": PACKAGE_MARKER,
        "paper_exchange_order_effect": PAPER_EXCHANGE_ORDER_EFFECT,
        "productive_caller_exists": PRODUCTIVE_CALLER_EXISTS,
        "promotion_authority": PROMOTION_AUTHORITY,
        "r4_verdict": r4["verdict"],
        "r5_canonical_closeout_status": "CLOSED_PROVEN_FORENSIC",
        "r6_multi_future_authorized": R6_MULTI_FUTURE_AUTHORIZED,
        "remediation_id": REMEDIATION_ID,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "runtime_effect": RUNTIME_EFFECT,
        "second_execution_pipeline_risk": "NONE_CAP7_CANONICAL_I67_SUPPORTING_I79_BUNDLE_ONLY",
        "second_promotion_path_risk": "NONE_NO_SURFACE_GRANTS_PROMOTION",
        "second_replay_authority_risk": "NONE_CAP7_MD_REPLAY_DISTINCT_FROM_I79_BUNDLE",
        "simulation_paper_replay_shadow_semantics_status": "ATTESTED_DISTINCT",
        "target_binding_i67": TARGET_BINDING_I67,
        "target_binding_i79": TARGET_BINDING_I79,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "trading_grant": TRADING_GRANT,
        "verdict": "PASS_R5_REALISTIC_SIM_REPLAY_SEMANTICS_V1",
    }
    return MappingProxyType(claims)
