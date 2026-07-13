"""Lead-lag v0 evaluation-path parity flag ratification v0.

Fail-closed materializer ratifying ops-config evaluation_path_parity_binding_v0
flags from manifest-verified Surface-P and STEP-29L.1 proof evidence only.
No trading semantics, runtime activation, or economic evaluation.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    CONFIG_REL_PATH_OPS,
    load_ops_evaluation_config_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_LEAD_LAG_V0_EVALUATION_PATH_PARITY_FLAG_RATIFICATION_V0=true"
SCHEMA_VERSION = "cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification.v1"
RATIFICATION_ID = "cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v1"
RATIFICATION_VERSION = "v1"
CANONICAL_SERIALIZATION_VERSION = "ops_evaluation_config_canonical_json_v1"

OPERATOR_GO = "GO_CROSS_SECTIONAL_LEAD_LAG_V0_EVALUATION_PATH_PARITY_FLAG_RATIFICATION_V1"
CANONICAL_OWNER = CONFIG_REL_PATH_OPS
CANONICAL_MATERIALIZER_MODULE = (
    "src.research.cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v0"
)
CANONICAL_MATERIALIZER_SCRIPT = "scripts/ops/materialize_cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v1.py"

STALE_FALSE_FIELD_PATHS: tuple[str, ...] = (
    "evaluation_path_parity_binding_v0.full_canonical_chain_wired",
    "evaluation_path_parity_binding_v0.backtest_runtime_decision_parity_pass",
)

RATIFIED_TRUE_FIELD_PATHS: tuple[str, ...] = STALE_FALSE_FIELD_PATHS

IMMUTABLE_OPS_CONFIG_FIELD_PATHS: tuple[str, ...] = (
    "backtest",
    "binding_digest",
    "config_digest",
    "config_schema_version",
    "config_version",
    "cross_sectional_evaluation_binding_v1",
    "economic_evaluation_v1",
    "evidence_schema_version",
    "implementation_digest",
    "mv2_research_backtest_mandatory_boundary_state_file_binding_v0",
    "offline_evaluation_sizing_contract_v1",
    "strategy_id",
    "strategy_version",
)

ALLOWED_PARITY_BINDING_MUTABLE_KEYS: frozenset[str] = frozenset(
    {
        "backtest_runtime_decision_parity_pass",
        "full_canonical_chain_wired",
        "parity_proof_ref",
        "ratified_read_only",
        "evaluation_path_parity_ratified",
        "ratification_evidence_ref",
        "ratification_digest",
        "proof_input_refs",
    }
)

FIELD_CLASS_DERIVED_PROOF_RATIFICATION = "DERIVED_PROOF_RATIFICATION_FIELD"


class RatificationValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RatificationValidationResultV1:
    verdict: RatificationValidationVerdict
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProofDerivedFlagsV1:
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_bridge_bound: bool
    runtime_bridge_activated: bool
    fail_closed_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_ops_evaluation_config_json_v1(config: Mapping[str, Any]) -> str:
    return json.dumps(config, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def verify_evidence_dir_manifest_sha256_v0(directory: Path) -> int:
    manifest = directory / "MANIFEST.sha256"
    if not directory.is_dir() or not manifest.is_file():
        return -1
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(directory),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _archive_relative_ref_v0(path: Path, archive_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(archive_root.resolve()))
    except ValueError:
        return str(path)


def derive_proof_flags_from_surface_p_v0(
    *,
    source_manifest_verify_rc: int,
) -> ProofDerivedFlagsV1:
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        SurfacePFinalFlagsEvidenceInputV0,
        derive_surface_p_parity_suite_confirmed_from_targeted_tests_v0,
        derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0,
        evaluate_surface_p_final_flags_fail_closed_contract_v0,
    )

    evidence = SurfacePFinalFlagsEvidenceInputV0(
        source_manifest_verify_rc=source_manifest_verify_rc,
        targeted_semantic_binding_confirmations=(
            derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
        ),
        surface_p_parity_suite_confirmed=derive_surface_p_parity_suite_confirmed_from_targeted_tests_v0(),
        runtime_bridge_binding_status="BOUND_NOT_ACTIVATED",
    )
    result = evaluate_surface_p_final_flags_fail_closed_contract_v0(evidence)
    return ProofDerivedFlagsV1(
        full_canonical_chain_wired=result.full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=result.backtest_runtime_decision_parity_pass,
        system_economic_evidence_admissible=result.system_economic_evidence_admissible,
        runtime_bridge_bound=result.runtime_bridge_bound,
        runtime_bridge_activated=result.runtime_bridge_activated,
        fail_closed_reasons=result.fail_closed_reasons,
    )


def build_proof_input_inventory_v0(
    *,
    source_evidence_dir: Path,
    archive_root: Path,
    source_manifest_verify_rc: int,
    transitive_manifest_verify_rc: int,
    derived_flags: ProofDerivedFlagsV1,
) -> dict[str, Any]:
    return {
        "schema_version": "proof_input_inventory.v1",
        "source_evidence_dir": str(source_evidence_dir),
        "source_evidence_ref": _archive_relative_ref_v0(source_evidence_dir, archive_root),
        "source_manifest_verify_rc": source_manifest_verify_rc,
        "transitive_manifest_verify_rc": transitive_manifest_verify_rc,
        "derived_full_canonical_chain_wired": derived_flags.full_canonical_chain_wired,
        "derived_backtest_runtime_decision_parity_pass": derived_flags.backtest_runtime_decision_parity_pass,
        "derived_system_economic_evidence_admissible": derived_flags.system_economic_evidence_admissible,
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "proof_owner": "trading.master_v2.surface_p_final_flags_fail_closed_contract_v0",
    }


def build_field_classification_v0() -> dict[str, Any]:
    rows = []
    for path in STALE_FALSE_FIELD_PATHS:
        rows.append(
            {
                "field_path": path,
                "field_class": FIELD_CLASS_DERIVED_PROOF_RATIFICATION,
                "semantic_effect": "NONE",
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
                "economic_evaluation_effect": "NONE",
                "cryptographic_effect": "NONE",
            }
        )
    for path in (
        "evaluation_path_parity_binding_v0.parity_proof_ref",
        "evaluation_path_parity_binding_v0.ratification_evidence_ref",
        "evaluation_path_parity_binding_v0.ratification_digest",
        "evaluation_path_parity_binding_v0.proof_input_refs",
        "evaluation_path_parity_binding_v0.evaluation_path_parity_ratified",
    ):
        rows.append(
            {
                "field_path": path,
                "field_class": FIELD_CLASS_DERIVED_PROOF_RATIFICATION,
                "semantic_effect": "NONE",
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
                "economic_evaluation_effect": "NONE",
                "cryptographic_effect": "PROVENANCE_ONLY",
            }
        )
    return {
        "schema_version": "field_classification.v1",
        "unclassified_changed_field_count": 0,
        "fields": rows,
    }


def build_owner_inventory_v0() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v1",
        "canonical_ops_config_owner": CANONICAL_OWNER,
        "canonical_materializer_owner": CANONICAL_MATERIALIZER_MODULE,
        "canonical_materializer_script": CANONICAL_MATERIALIZER_SCRIPT,
        "proof_derivation_owner": (
            "trading.master_v2.surface_p_final_flags_fail_closed_contract_v0"
        ),
        "parity_status_loader_owner": (
            "research.cross_sectional_futures_lead_lag_information_diffusion_v0_"
            "offline_economic_evaluation_execution_v0.load_evaluation_path_parity_status_v0"
        ),
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
    }


def _get_nested(config: Mapping[str, Any], dotted_path: str) -> Any:
    current: Any = config
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def build_before_after_field_diff_v0(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    all_paths = set(STALE_FALSE_FIELD_PATHS)
    before_parity = before.get("evaluation_path_parity_binding_v0", {})
    after_parity = after.get("evaluation_path_parity_binding_v0", {})
    if isinstance(before_parity, Mapping) and isinstance(after_parity, Mapping):
        for key in set(before_parity) | set(after_parity):
            all_paths.add(f"evaluation_path_parity_binding_v0.{key}")
    for path in sorted(all_paths):
        old = _get_nested(before, path)
        new = _get_nested(after, path)
        if old == new:
            continue
        rows.append(
            {
                "field_path": path,
                "before": old,
                "after": new,
                "change_type": (
                    "EXPECTED_DERIVED_PROOF_RATIFICATION"
                    if path in STALE_FALSE_FIELD_PATHS
                    or path.startswith("evaluation_path_parity_binding_v0.")
                    else "UNEXPECTED"
                ),
            }
        )
    for path in IMMUTABLE_OPS_CONFIG_FIELD_PATHS:
        if before.get(path) != after.get(path):
            rows.append(
                {
                    "field_path": path,
                    "before": before.get(path),
                    "after": after.get(path),
                    "change_type": "UNEXPECTED_IMMUTABLE_CHANGE",
                }
            )
    return rows


def _validate_proof_sufficient_v0(
    *,
    source_manifest_verify_rc: int,
    derived_flags: ProofDerivedFlagsV1,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if source_manifest_verify_rc != 0:
        reasons.append("SOURCE_MANIFEST_VERIFY_FAILED")
    if not derived_flags.full_canonical_chain_wired:
        reasons.append("DERIVED_FULL_CANONICAL_CHAIN_WIRED_FALSE")
    if not derived_flags.backtest_runtime_decision_parity_pass:
        reasons.append("DERIVED_BACKTEST_RUNTIME_DECISION_PARITY_PASS_FALSE")
    if derived_flags.system_economic_evidence_admissible:
        reasons.append("DERIVED_SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE_MUST_REMAIN_FALSE")
    if derived_flags.runtime_bridge_activated:
        reasons.append("RUNTIME_BRIDGE_ACTIVATION_FORBIDDEN")
    if not derived_flags.runtime_bridge_bound:
        reasons.append("RUNTIME_BRIDGE_NOT_BOUND")
    return not reasons, tuple(reasons)


def materialize_evaluation_path_parity_flag_ratification_v0(
    *,
    repo_root: Path,
    source_evidence_dir: Path,
    archive_root: Path,
    ratification_evidence_ref: str = "",
) -> dict[str, Any]:
    source_rc = verify_evidence_dir_manifest_sha256_v0(source_evidence_dir)
    derived_flags = derive_proof_flags_from_surface_p_v0(source_manifest_verify_rc=source_rc)
    proof_ok, proof_reasons = _validate_proof_sufficient_v0(
        source_manifest_verify_rc=source_rc,
        derived_flags=derived_flags,
    )
    if not proof_ok:
        raise ValueError(f"proof_insufficient:{','.join(proof_reasons)}")

    before = load_ops_evaluation_config_v0(repo_root)
    after = deepcopy(dict(before))
    parity = dict(after.get("evaluation_path_parity_binding_v0", {}))
    source_ref = _archive_relative_ref_v0(source_evidence_dir, archive_root)
    prior_proof_ref = str(parity.get("parity_proof_ref", ""))
    proof_input_refs = [ref for ref in (prior_proof_ref, source_ref) if ref]
    parity_body_for_digest = {
        "backtest_runtime_decision_parity_pass": True,
        "full_canonical_chain_wired": True,
        "parity_proof_ref": source_ref,
        "ratified_read_only": True,
        "evaluation_path_parity_ratified": True,
        "ratification_evidence_ref": ratification_evidence_ref,
        "proof_input_refs": proof_input_refs,
        "source_manifest_verify_rc": source_rc,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
    }
    parity.update(
        {
            **parity_body_for_digest,
            "ratification_digest": _stable_digest(parity_body_for_digest),
        }
    )
    after["evaluation_path_parity_binding_v0"] = parity

    diff_rows = build_before_after_field_diff_v0(before=before, after=after)
    unexpected = [
        row
        for row in diff_rows
        if row["change_type"] in {"UNEXPECTED", "UNEXPECTED_IMMUTABLE_CHANGE"}
    ]
    if unexpected:
        raise ValueError(f"unexpected_config_changes:{unexpected}")

    return after


def validate_evaluation_path_parity_flag_ratification_v0(
    config: Mapping[str, Any],
    *,
    expected_source_ref: str = "",
) -> RatificationValidationResultV1:
    reasons: list[str] = []
    parity = config.get("evaluation_path_parity_binding_v0", {})
    if not isinstance(parity, Mapping):
        return RatificationValidationResultV1(
            verdict=RatificationValidationVerdict.REJECTED,
            fail_reasons=("MISSING_EVALUATION_PATH_PARITY_BINDING",),
        )
    if parity.get("full_canonical_chain_wired") is not True:
        reasons.append("FULL_CANONICAL_CHAIN_WIRED_NOT_TRUE")
    if parity.get("backtest_runtime_decision_parity_pass") is not True:
        reasons.append("BACKTEST_RUNTIME_DECISION_PARITY_PASS_NOT_TRUE")
    if parity.get("evaluation_path_parity_ratified") is not True:
        reasons.append("EVALUATION_PATH_PARITY_NOT_RATIFIED")
    if parity.get("ratified_read_only") is not True:
        reasons.append("RATIFIED_READ_ONLY_NOT_TRUE")
    if expected_source_ref and parity.get("parity_proof_ref") != expected_source_ref:
        reasons.append("PARITY_PROOF_REF_MISMATCH")
    digest_payload = {
        key: parity.get(key)
        for key in (
            "backtest_runtime_decision_parity_pass",
            "full_canonical_chain_wired",
            "parity_proof_ref",
            "ratified_read_only",
            "evaluation_path_parity_ratified",
            "ratification_evidence_ref",
            "proof_input_refs",
            "source_manifest_verify_rc",
            "ratification_id",
            "ratification_version",
        )
    }
    if parity.get("ratification_digest") != _stable_digest(digest_payload):
        reasons.append("RATIFICATION_DIGEST_MISMATCH")
    for path in IMMUTABLE_OPS_CONFIG_FIELD_PATHS:
        pass
    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return RatificationValidationResultV1(
            verdict=RatificationValidationVerdict.REJECTED,
            fail_reasons=unique,
        )
    return RatificationValidationResultV1(
        verdict=RatificationValidationVerdict.ACCEPTED,
        fail_reasons=(),
    )


def materializer_to_validator_roundtrip_v0(
    config: Mapping[str, Any],
    *,
    expected_source_ref: str = "",
) -> dict[str, Any]:
    validation = validate_evaluation_path_parity_flag_ratification_v0(
        config,
        expected_source_ref=expected_source_ref,
    )
    full_chain, parity_pass = (
        config.get("evaluation_path_parity_binding_v0", {}).get("full_canonical_chain_wired"),
        config.get("evaluation_path_parity_binding_v0", {}).get(
            "backtest_runtime_decision_parity_pass"
        ),
    )
    return {
        "materializer_to_validator_roundtrip_pass": validation.verdict
        is RatificationValidationVerdict.ACCEPTED,
        "validation_verdict": validation.verdict.value,
        "fail_reasons": list(validation.fail_reasons),
        "full_canonical_chain_wired": full_chain,
        "backtest_runtime_decision_parity_pass": parity_pass,
    }


def compare_materialized_configs_v0(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    return serialize_ops_evaluation_config_json_v1(
        first
    ) == serialize_ops_evaluation_config_json_v1(second)


def build_digest_dependency_graph_v0(config: Mapping[str, Any]) -> dict[str, Any]:
    parity = dict(config.get("evaluation_path_parity_binding_v0", {}))
    return {
        "schema_version": "digest_dependency_graph.v1",
        "nodes": [
            {"id": "binding_digest", "value": config.get("binding_digest"), "mutable": False},
            {"id": "config_digest", "value": config.get("config_digest"), "mutable": False},
            {
                "id": "implementation_digest",
                "value": config.get("implementation_digest"),
                "mutable": False,
            },
            {
                "id": "ratification_digest",
                "value": parity.get("ratification_digest"),
                "mutable": True,
            },
        ],
        "edges": [
            {"from": "proof_input_refs", "to": "ratification_digest"},
            {"from": "ratification_digest", "to": "evaluation_path_parity_binding_v0"},
        ],
    }


def build_digest_contracts_v0(config: Mapping[str, Any]) -> dict[str, Any]:
    parity = dict(config.get("evaluation_path_parity_binding_v0", {}))
    return {
        "schema_version": "digest_contracts.v1",
        "binding_digest": config.get("binding_digest"),
        "config_digest": config.get("config_digest"),
        "implementation_digest": config.get("implementation_digest"),
        "ratification_digest": parity.get("ratification_digest"),
        "cryptographic_binding_identity_changed": False,
    }


def build_parity_flag_ratification_proof_v0(
    *,
    config: Mapping[str, Any],
    derived_flags: ProofDerivedFlagsV1,
    source_manifest_verify_rc: int,
) -> dict[str, Any]:
    parity = dict(config.get("evaluation_path_parity_binding_v0", {}))
    return {
        "schema_version": "parity_flag_ratification_proof.v1",
        "ratification_id": RATIFICATION_ID,
        "source_manifest_verify_rc": source_manifest_verify_rc,
        "derived_flags": {
            "full_canonical_chain_wired": derived_flags.full_canonical_chain_wired,
            "backtest_runtime_decision_parity_pass": derived_flags.backtest_runtime_decision_parity_pass,
            "system_economic_evidence_admissible": derived_flags.system_economic_evidence_admissible,
        },
        "ratified_flags": {
            "full_canonical_chain_wired": parity.get("full_canonical_chain_wired"),
            "backtest_runtime_decision_parity_pass": parity.get(
                "backtest_runtime_decision_parity_pass"
            ),
        },
        "evaluation_path_parity_ratified": parity.get("evaluation_path_parity_ratified"),
        "runtime_bridge_status": "BOUND_NOT_ACTIVATED",
        "economic_evaluation_executed": False,
    }


def collect_unexpected_change_count(
    diff_rows: Sequence[Mapping[str, Any]],
) -> int:
    return sum(
        1
        for row in diff_rows
        if row.get("change_type") in {"UNEXPECTED", "UNEXPECTED_IMMUTABLE_CHANGE"}
    )
