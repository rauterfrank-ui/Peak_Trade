"""Static Cap 7.1 → §11.17 SIMULATED_LIFECYCLE_PROVEN binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.phase_11_section_11_17_simulated_lifecycle_proven_evidence_closure_v1.constants_v1 import (
    CANONICAL_FIELD_SEMANTICS,
    CANONICAL_STATEFUL_CORE_PROVEN,
    CAPABILITY_ID,
    CLOSURE_METHOD,
    FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    OWNER,
    REQUIRED_SOURCE_FALSE_CLAIMS,
    REQUIRED_SOURCE_TRUE_CLAIMS,
    SECTION_11_17_FIELD,
    SIMULATED_LIFECYCLE_PROVEN,
    SOURCE_CAPABILITY_ID,
    SOURCE_CONFIG_DIGEST,
    SOURCE_EVIDENCE_DIGEST,
    SOURCE_EVIDENCE_DIRNAME,
    SOURCE_HISTORICAL_REPOSITORY_SHA,
    SOURCE_OWNER,
)


class SimulatedLifecycleProvenBindingError(RuntimeError):
    """Fail-closed Cap 7.1 binding violation for SIMULATED_LIFECYCLE_PROVEN."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_manifest(manifest_path: Path) -> list[dict[str, str]]:
    if not manifest_path.is_file():
        raise SimulatedLifecycleProvenBindingError("SOURCE_MANIFEST_MISSING")
    bindings: list[dict[str, str]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        target = manifest_path.parent / rel
        if not target.is_file():
            raise SimulatedLifecycleProvenBindingError(f"SOURCE_MANIFEST_TARGET_MISSING:{rel}")
        actual = _sha256_file(target)
        if actual != digest:
            raise SimulatedLifecycleProvenBindingError(
                f"SOURCE_MANIFEST_DIGEST_MISMATCH:{rel}:{digest}:{actual}"
            )
        bindings.append(
            {
                "path": str(target.relative_to(_repo_root())),
                "sha256": actual,
            }
        )
    if not bindings:
        raise SimulatedLifecycleProvenBindingError("SOURCE_MANIFEST_EMPTY")
    return bindings


def bind_simulated_lifecycle_proven_from_cap71_v1() -> dict[str, Any]:
    """Statically bind Cap 7.1 durable evidence to SIMULATED_LIFECYCLE_PROVEN=true."""
    root = _repo_root()
    evidence_root = root / "docs" / "evidence" / SOURCE_EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    summary_path = evidence_root / "SUMMARY.json"
    result_path = productive / "simulated_entry_reduce_exit_actionability_result_v1.json"
    gates_path = productive / "actionability_gate_results_v1.json"
    no_order_path = productive / "no_order_boundary_proof_v1.json"
    source_package = root / "src" / "ops" / "simulated_entry_reduce_exit_actionability_evidence_v1"
    source_spec = (
        root
        / "docs"
        / "ops"
        / "specs"
        / "CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1.md"
    )

    if not evidence_root.is_dir():
        raise SimulatedLifecycleProvenBindingError("SOURCE_EVIDENCE_DIR_MISSING")
    if not source_package.is_dir():
        raise SimulatedLifecycleProvenBindingError("SOURCE_PACKAGE_MISSING")
    if not source_spec.is_file():
        raise SimulatedLifecycleProvenBindingError("SOURCE_SPEC_MISSING")

    root_bindings = _verify_manifest(evidence_root / "MANIFEST.sha256")
    nested_manifest = productive / "MANIFEST.sha256"
    nested_bindings = _verify_manifest(nested_manifest) if nested_manifest.is_file() else []

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    gates = json.loads(gates_path.read_text(encoding="utf-8"))
    no_order = json.loads(no_order_path.read_text(encoding="utf-8"))
    claims = result.get("claims")
    if not isinstance(claims, dict):
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_CLAIMS_MISSING")
    gate_flags = gates.get("gate_flags")
    if not isinstance(gate_flags, dict):
        raise SimulatedLifecycleProvenBindingError("SOURCE_GATE_FLAGS_MISSING")

    if summary.get("capability_id") != SOURCE_CAPABILITY_ID:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_CAPABILITY_ID_MISMATCH")
    if summary.get("ok") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_NOT_OK")
    if summary.get("repository_sha") != SOURCE_HISTORICAL_REPOSITORY_SHA:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_REPOSITORY_SHA_MISMATCH")
    if summary.get("evidence_digest") != SOURCE_EVIDENCE_DIGEST:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_EVIDENCE_DIGEST_MISMATCH")
    if summary.get("CORE_LOGIC_CHANGE") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_CORE_LOGIC_CHANGED")
    if summary.get("ENTRY_END_TO_END_EVIDENCE_PROVEN") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_ENTRY_NOT_PROVEN")
    if summary.get("EXIT_END_TO_END_EVIDENCE_PROVEN") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_EXIT_NOT_PROVEN")
    if summary.get("NONZERO_FEE_EVIDENCE_PROVEN") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_FEE_NOT_PROVEN")
    if summary.get("NONZERO_SLIPPAGE_EVIDENCE_PROVEN") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_SLIPPAGE_NOT_PROVEN")
    if summary.get("RUNTIME_ACTIVATED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_SUMMARY_RUNTIME_ACTIVATED")

    if result.get("capability_id") != SOURCE_CAPABILITY_ID:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_CAPABILITY_ID_MISMATCH")
    if result.get("ok") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_NOT_OK")
    if result.get("repository_sha") != SOURCE_HISTORICAL_REPOSITORY_SHA:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_REPOSITORY_SHA_MISMATCH")
    if result.get("evidence_digest") != SOURCE_EVIDENCE_DIGEST:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_EVIDENCE_DIGEST_MISMATCH")
    if result.get("config_digest") != SOURCE_CONFIG_DIGEST:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_CONFIG_DIGEST_MISMATCH")
    if result.get("CORE_LOGIC_CHANGE") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_CORE_LOGIC_CHANGED")
    if result.get("RUNTIME_ACTIVATED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_RESULT_RUNTIME_ACTIVATED")
    if gates.get("ok") is not True:
        raise SimulatedLifecycleProvenBindingError("SOURCE_GATES_NOT_OK")

    for key in REQUIRED_SOURCE_TRUE_CLAIMS:
        if claims.get(key) is not True:
            raise SimulatedLifecycleProvenBindingError(f"SOURCE_TRUE_CLAIM_MISSING:{key}")
        if gate_flags.get(key) is not True:
            raise SimulatedLifecycleProvenBindingError(f"SOURCE_GATE_TRUE_CLAIM_MISSING:{key}")
    for key in REQUIRED_SOURCE_FALSE_CLAIMS:
        if claims.get(key) is not False:
            raise SimulatedLifecycleProvenBindingError(f"SOURCE_FALSE_CLAIM_VIOLATED:{key}")
        if gate_flags.get(key) is not False:
            raise SimulatedLifecycleProvenBindingError(f"SOURCE_GATE_FALSE_CLAIM_VIOLATED:{key}")

    if no_order.get("ORDER_SIDE_EFFECT_OCCURRED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_NO_ORDER_SIDE_EFFECT")
    if no_order.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_ORDER_SUBMIT_REACHABLE")
    if no_order.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_CREDENTIAL_ACCESS_REACHABLE")
    if no_order.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_REAL_ADAPTER_CONSTRUCTED")
    if no_order.get("NETWORK_SESSION_STARTED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_NETWORK_SESSION_STARTED")
    if no_order.get("AUTHORIZATION_CONSUMED") is not False:
        raise SimulatedLifecycleProvenBindingError("SOURCE_AUTHORIZATION_CONSUMED")

    if SIMULATED_LIFECYCLE_PROVEN is not True:
        raise SimulatedLifecycleProvenBindingError("BOUND_FIELD_CONSTANT_NOT_TRUE")
    if CANONICAL_STATEFUL_CORE_PROVEN is not True:
        raise SimulatedLifecycleProvenBindingError("PREDECESSOR_CORE_FIELD_MUST_REMAIN_TRUE")
    if FULLY_AUTONOMOUS_LIVE_TRADING_READY is not False:
        raise SimulatedLifecycleProvenBindingError("READY_MUST_REMAIN_FALSE")
    if FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE is not False:
        raise SimulatedLifecycleProvenBindingError("ACTIVE_MUST_REMAIN_FALSE")

    evidence_bindings = root_bindings + nested_bindings
    return {
        "ok": True,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "SECTION_11_17_FIELD": SECTION_11_17_FIELD,
        "SIMULATED_LIFECYCLE_PROVEN": True,
        "CANONICAL_STATEFUL_CORE_PROVEN": True,
        "CLOSURE_METHOD": CLOSURE_METHOD,
        "CANONICAL_FIELD_SEMANTICS": CANONICAL_FIELD_SEMANTICS,
        "SOURCE_CAPABILITY_ID": SOURCE_CAPABILITY_ID,
        "SOURCE_OWNER": SOURCE_OWNER,
        "SOURCE_EVIDENCE_DIRNAME": SOURCE_EVIDENCE_DIRNAME,
        "SOURCE_HISTORICAL_REPOSITORY_SHA": SOURCE_HISTORICAL_REPOSITORY_SHA,
        "SOURCE_EVIDENCE_DIGEST": SOURCE_EVIDENCE_DIGEST,
        "SOURCE_CONFIG_DIGEST": SOURCE_CONFIG_DIGEST,
        "SOURCE_SUMMARY_SHA256": _sha256_file(summary_path),
        "SOURCE_RESULT_SHA256": _sha256_file(result_path),
        "SOURCE_GATE_RESULTS_SHA256": _sha256_file(gates_path),
        "SOURCE_NO_ORDER_BOUNDARY_SHA256": _sha256_file(no_order_path),
        "SOURCE_SPEC_SHA256": _sha256_file(source_spec),
        "EVIDENCE_BINDINGS": evidence_bindings,
        "EVIDENCE_REUSED": True,
        "REPROOF_EXECUTED": False,
        "FIXTURE_ONLY": False,
        "PRODUCTIVE_BINDING": True,
        "TESTNET_LIFECYCLE_PROVEN": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_ORDER_LIFECYCLE_PROVEN": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
        "CAPABILITY_11_13_STARTED": False,
        "NETWORK_SESSION_STARTED": False,
        "CREDENTIAL_ACCESS": False,
        "ORDER_SUBMIT_REACHABLE": False,
        "CORE_LOGIC_CHANGE": False,
    }
