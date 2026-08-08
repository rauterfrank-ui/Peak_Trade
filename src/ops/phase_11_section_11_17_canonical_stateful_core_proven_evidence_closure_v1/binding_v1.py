"""Static Cap 7.2 → §11.17 CANONICAL_STATEFUL_CORE_PROVEN binding."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.constants_v1 import (
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


class CanonicalStatefulCoreProvenBindingError(RuntimeError):
    """Fail-closed Cap 7.2 binding violation for CANONICAL_STATEFUL_CORE_PROVEN."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_manifest(manifest_path: Path) -> list[dict[str, str]]:
    if not manifest_path.is_file():
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_MANIFEST_MISSING")
    bindings: list[dict[str, str]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        target = manifest_path.parent / rel
        if not target.is_file():
            raise CanonicalStatefulCoreProvenBindingError(f"SOURCE_MANIFEST_TARGET_MISSING:{rel}")
        actual = _sha256_file(target)
        if actual != digest:
            raise CanonicalStatefulCoreProvenBindingError(
                f"SOURCE_MANIFEST_DIGEST_MISMATCH:{rel}:{digest}:{actual}"
            )
        bindings.append(
            {
                "path": str(target.relative_to(_repo_root())),
                "sha256": actual,
            }
        )
    if not bindings:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_MANIFEST_EMPTY")
    return bindings


def bind_canonical_stateful_core_proven_from_cap72_v1() -> dict[str, Any]:
    """Statically bind Cap 7.2 durable evidence to CANONICAL_STATEFUL_CORE_PROVEN=true."""
    root = _repo_root()
    evidence_root = root / "docs" / "evidence" / SOURCE_EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    summary_path = evidence_root / "SUMMARY.json"
    claim_matrix_path = productive / "claim_matrix_v1.json"
    activation_status_path = productive / "activation_status_v1.json"
    source_package = root / "src" / "ops" / "single_future_stateful_no_order_runtime_activation_v1"
    source_spec = (
        root
        / "docs"
        / "ops"
        / "specs"
        / "CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1.md"
    )

    if not evidence_root.is_dir():
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_EVIDENCE_DIR_MISSING")
    if not source_package.is_dir():
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_PACKAGE_MISSING")
    if not source_spec.is_file():
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SPEC_MISSING")

    root_bindings = _verify_manifest(evidence_root / "MANIFEST.sha256")
    nested_manifest = productive / "MANIFEST.sha256"
    nested_bindings = _verify_manifest(nested_manifest) if nested_manifest.is_file() else []

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    claims = json.loads(claim_matrix_path.read_text(encoding="utf-8"))
    activation = json.loads(activation_status_path.read_text(encoding="utf-8"))

    if summary.get("capability_id") != SOURCE_CAPABILITY_ID:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_CAPABILITY_ID_MISMATCH")
    if summary.get("ok") is not True:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_NOT_OK")
    if summary.get("repository_sha") != SOURCE_HISTORICAL_REPOSITORY_SHA:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_REPOSITORY_SHA_MISMATCH")
    if summary.get("evidence_digest") != SOURCE_EVIDENCE_DIGEST:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_EVIDENCE_DIGEST_MISMATCH")
    if summary.get("config_digest") != SOURCE_CONFIG_DIGEST:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_CONFIG_DIGEST_MISMATCH")
    if summary.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE") is not True:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_RUNTIME_NOT_ACTIVE")
    if summary.get("CORE_LOGIC_CHANGE") is not False:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_CORE_LOGIC_CHANGED")
    if summary.get("PUBLIC_MD_NETWORK_SESSION_OBSERVED") is not False:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_SUMMARY_NETWORK_SESSION_OBSERVED")

    for key in REQUIRED_SOURCE_TRUE_CLAIMS:
        if claims.get(key) is not True:
            raise CanonicalStatefulCoreProvenBindingError(f"SOURCE_TRUE_CLAIM_MISSING:{key}")
    for key in REQUIRED_SOURCE_FALSE_CLAIMS:
        if claims.get(key) is not False:
            raise CanonicalStatefulCoreProvenBindingError(f"SOURCE_FALSE_CLAIM_VIOLATED:{key}")

    if activation.get("status") != "ACTIVE":
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_ACTIVATION_STATUS_NOT_ACTIVE")
    if activation.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE") is not True:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_ACTIVATION_RUNTIME_NOT_ACTIVE")
    if activation.get("NETWORK_SESSION_STARTED") is not False:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_ACTIVATION_NETWORK_STARTED")
    if activation.get("LIVE_ORDERS") is not False or activation.get("TESTNET_ORDERS") is not False:
        raise CanonicalStatefulCoreProvenBindingError("SOURCE_ACTIVATION_ORDERS_NOT_FALSE")

    # Explicit non-equivalence: Cap 7.2 proves the stateful core, not Cap 7.1 lifecycle
    # and not Phase 11 READY/ACTIVE/Live/Testnet residuals.
    if SIMULATED_LIFECYCLE_PROVEN is not False:
        raise CanonicalStatefulCoreProvenBindingError("SIMULATED_LIFECYCLE_MUST_REMAIN_FALSE")
    if FULLY_AUTONOMOUS_LIVE_TRADING_READY is not False:
        raise CanonicalStatefulCoreProvenBindingError("READY_MUST_REMAIN_FALSE")
    if FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE is not False:
        raise CanonicalStatefulCoreProvenBindingError("ACTIVE_MUST_REMAIN_FALSE")
    if CANONICAL_STATEFUL_CORE_PROVEN is not True:
        raise CanonicalStatefulCoreProvenBindingError("BOUND_FIELD_CONSTANT_NOT_TRUE")

    evidence_bindings = root_bindings + nested_bindings
    return {
        "ok": True,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "SECTION_11_17_FIELD": SECTION_11_17_FIELD,
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
        "SOURCE_CLAIM_MATRIX_SHA256": _sha256_file(claim_matrix_path),
        "SOURCE_ACTIVATION_STATUS_SHA256": _sha256_file(activation_status_path),
        "SOURCE_SPEC_SHA256": _sha256_file(source_spec),
        "EVIDENCE_BINDINGS": evidence_bindings,
        "EVIDENCE_REUSED": True,
        "REPROOF_EXECUTED": False,
        "FIXTURE_ONLY": False,
        "PRODUCTIVE_BINDING": True,
        "SIMULATED_LIFECYCLE_PROVEN": False,
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
