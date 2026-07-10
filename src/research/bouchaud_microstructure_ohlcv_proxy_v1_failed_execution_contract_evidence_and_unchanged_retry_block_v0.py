"""Failed execution-contract evidence registration for bouchaud_microstructure_ohlcv_proxy/v1.

Offline-only ratification slice: registers pre-backtest sizing-digest execution failure,
preserves prior failed evaluation lineage, and blocks unchanged-binding retry.
No economic reevaluation, no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_FAILED_EXECUTION_CONTRACT_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0=true"
)
SCHEMA_VERSION = (
    "bouchaud_microstructure_ohlcv_proxy_v1_failed_execution_contract_evidence_and_"
    "unchanged_retry_block.v0"
)
REGISTRATION_ID = (
    "bouchaud_microstructure_ohlcv_proxy_v1_failed_execution_contract_evidence_and_"
    "unchanged_retry_block_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_FAILED_EXECUTION_CONTRACT_EVIDENCE_AND_UNCHANGED_RETRY_BLOCK_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_REPAIR_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_SIZING_DIGEST_RATIFICATION_AND_"
    "ADMISSIBILITY_GUARD_EXTENSION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_failed_execution_contract_evidence_and_"
    "unchanged_retry_block_v0.json"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = "config/research/bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0.json"

STRATEGY_ID = "bouchaud_microstructure"
STRATEGY_VERSION = "v1"
RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"
BINDING_CLASSIFICATION = "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PRIOR_FAILED_ATTEMPT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T174747Z"
)
PRIOR_BLOCKED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T172515Z"
)
PR5098_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5098_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_"
    "economic_baseline_evaluation_runner_and_scope_ratification_v0_20260710T174350Z"
)

OLD_SIZING_CONFIG_DIGEST = "c0b377c523ccc6ed8c69e0976c36f19ba6d1f5f01080aecd36004f9d87bcddee"
NEW_SIZING_CONFIG_DIGEST = "c75b7f115c62977a4e6a089c02c3eabe660cf6bf23c295229fd25294790616f0"
OLD_EVALUATION_CONFIG_DIGEST = "a9c0f1d859855ef406e3f7cdc31e4f71ddf86e18d7e97a0bea2b2d0d1fdd1472"
NEW_EVALUATION_CONFIG_DIGEST = "a3af95053e4a60d302c47465d40b82d2002b75d51a2822a01d756b167bfafd95"
OLD_BINDING_DIGEST = "39a783904714eb988e9a5fee34e6474e0bb65821ddf525af8df53268906f6e7c"
NEW_BINDING_DIGEST = "99d6153cfc25e550a429cde04a2d684c56e0e84369cc3e1196cae9f91ac26422"
DATA_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
STRATEGY_PARAMS_DIGEST = "bda8f9eb343ce818a1c56e69377c3c10c0c014bcb1f16053b0c897bd0a304b3f"
PRIMARY_FAILURE_CLASS = "offline_evaluation_sizing_contract_invalid:sizing_config_digest_mismatch"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = "WAIT_FOR_PR_CHECKS_THEN_SEPARATE_MERGE_CLOSEOUT_GO"


class RegistrationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ManifestVerification:
    bundle_path: Path
    manifest_verify_rc: int


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_registration_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "registration_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def verify_manifest_sha256(bundle_dir: Path) -> ManifestVerification:
    manifest = bundle_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=1)
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=proc.returncode)


def build_failed_attempt_registration_payload_v0() -> dict[str, Any]:
    return {
        "FAILED_EXECUTION_CONTRACT_EVIDENCE": True,
        "ECONOMIC_NEGATIVE_EDGE_EVIDENCE": False,
        "ECONOMIC_BACKTEST_COMPLETED": False,
        "ECONOMIC_METRICS_NOT_EXECUTED": True,
        "TRADE_COUNT_NOT_EVALUATED": True,
        "UNCHANGED_RETRY_ALLOWED": False,
        "PREVIOUS_FAILED_ATTEMPT_REF": str(PRIOR_FAILED_ATTEMPT_DIR),
        "PRIOR_BLOCKED_EVALUATION_REF": str(PRIOR_BLOCKED_EVALUATION_DIR),
        "PRIMARY_FAILURE_CLASS": PRIMARY_FAILURE_CLASS,
        "economic_evaluation_executed": False,
        "trade_count": None,
        "sample_sufficiency_status": "NOT_EVALUATED",
        "historical_evidence_mutated": False,
        "profitability_claim_allowed": False,
    }


def build_registration_payload_v0(repo_root: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_kind": REGISTRATION_ID,
        "artifact_version": REGISTRATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_classification": BINDING_CLASSIFICATION,
        "binding_config_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "binding_digest": NEW_BINDING_DIGEST,
        "config_digest": NEW_EVALUATION_CONFIG_DIGEST,
        "cost_policy_changed": False,
        "data_digest": DATA_DIGEST,
        "dataset_changed": False,
        "durable_evidence_refs": (
            f"{PRIOR_FAILED_ATTEMPT_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{PRIOR_BLOCKED_EVALUATION_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{PR5098_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0)"
        ),
        "economic_evaluation_executed": False,
        "economic_negative_edge_evidence": False,
        "exact_binding_retry_guard_report": {
            "binding_digest": NEW_BINDING_DIGEST,
            "blocked_retry_axes": [
                "UNCHANGED_BINDING_RETRY",
                "SAME_BINDING_RETRY",
                "UNCHANGED_SIZING_DIGEST_RETRY",
            ],
            "exact_binding_retry_blocked": True,
            "research_scope": RESEARCH_SCOPE,
            "same_binding_retry_allowed": False,
            "schema_version": "exact_binding_retry_guard_report.v0",
            "unchanged_retry_blocked": True,
        },
        "failed_attempt_registration": build_failed_attempt_registration_payload_v0(),
        "failed_execution_contract_evidence": True,
        "go_token": OPERATOR_GO_TOKEN,
        "identity_relation": {
            "binding_classification": BINDING_CLASSIFICATION,
            "cryptographic_binding_identity_changed": True,
            "dataset_digest": DATA_DIGEST,
            "new_binding_digest": NEW_BINDING_DIGEST,
            "new_evaluation_config_digest": NEW_EVALUATION_CONFIG_DIGEST,
            "new_sizing_config_digest": NEW_SIZING_CONFIG_DIGEST,
            "old_binding_digest": OLD_BINDING_DIGEST,
            "old_evaluation_config_digest": OLD_EVALUATION_CONFIG_DIGEST,
            "old_sizing_config_digest": OLD_SIZING_CONFIG_DIGEST,
            "prior_failed_attempt_ref": str(PRIOR_FAILED_ATTEMPT_DIR),
            "schema_version": "bouchaud_failed_execution_contract_identity_relation.v0",
            "semantic_binding_identity_changed": False,
            "strategy_params_digest": STRATEGY_PARAMS_DIGEST,
        },
        "immutable_binding_retry_allowed": False,
        "new_distinct_research_scope_or_new_evidence_class_required": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "offline_only": True,
        "old_binding_digest_at_prior_failed_attempt": OLD_BINDING_DIGEST,
        "order_effect": "NONE",
        "prior_failed_attempt_bundle": str(PRIOR_FAILED_ATTEMPT_DIR),
        "research_scope": RESEARCH_SCOPE,
        "risk_sizing_semantics_changed": False,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "scope_ratification_config_ref": SCOPE_RATIFICATION_CONFIG_REL_PATH,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "supersession_mode": "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY",
        "unchanged_retry_allowed": False,
        "unchanged_retry_blocked": True,
        "verdict": "FAILED_EXECUTION_CONTRACT_EVIDENCE_REGISTERED_V0",
    }
    payload["registration_digest"] = compute_registration_digest(payload)
    committed = repo_root / CONFIG_REL_PATH
    if committed.is_file():
        existing = json.loads(committed.read_text(encoding="utf-8"))
        if existing.get("registration_digest") == payload["registration_digest"]:
            return existing
    return payload


def register_failed_execution_contract_evidence_v0(repo_root: Path) -> dict[str, Any]:
    verifications = (
        verify_manifest_sha256(PRIOR_FAILED_ATTEMPT_DIR),
        verify_manifest_sha256(PRIOR_BLOCKED_EVALUATION_DIR),
        verify_manifest_sha256(PR5098_CLOSEOUT_DIR),
    )
    if any(item.manifest_verify_rc != 0 for item in verifications):
        raise ValueError("source_manifest_verification_failed")
    return build_registration_payload_v0(repo_root)
