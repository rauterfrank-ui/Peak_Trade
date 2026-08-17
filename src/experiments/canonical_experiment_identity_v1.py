"""Phase 1 Canonical Experiment Identity v1 (research metadata only).

This contract binds every COMPLETE research/backtest experiment to explicit
critical inputs. It has no runtime, order, live, funding, canary, or config
write authority.

Package N ``experiment_identity_manifest_v1`` remains an incomplete historical
projection and is not reinterpreted by this schema.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_experiment_identity_v1"
IDENTITY_DOMAIN: Final[str] = "peak_trade.canonical_experiment_identity.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
WORKING_TREE_CLEAN: Final[str] = "CLEAN"
WORKING_TREE_DIRTY: Final[str] = "DIRTY"
PARENT_KIND_ROOT: Final[str] = "ROOT"
PARENT_KIND_PARENT_BOUND: Final[str] = "PARENT_BOUND"
EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY: Final[bool] = False
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

_GIT_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SECRET_KEY_TOKEN_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|secret|password|passwd|token|credential|"
    r"private[_-]?key|access[_-]?key|secret[_-]?key|passphrase|confirm[_-]?token|"
    r"bearer|authorization)",
    re.IGNORECASE,
)
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
    }
)
_ENVIRONMENT_ALLOWED_KEYS = frozenset(
    {
        "python_version",
        "python_implementation",
    }
)
_CRITICAL_DIGEST_FIELDS = (
    "dataset_digest",
    "feature_pipeline_digest",
    "fee_model_digest",
    "slippage_model_digest",
    "funding_model_digest",
    "risk_policy_digest",
    "portfolio_digest",
    "split_policy_digest",
)
_DIGEST_DOMAINS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "strategy_identity": f"{IDENTITY_DOMAIN}.strategy_identity",
        "strategy_params": f"{IDENTITY_DOMAIN}.strategy_params",
        "dataset": f"{IDENTITY_DOMAIN}.dataset",
        "feature_pipeline": f"{IDENTITY_DOMAIN}.feature_pipeline",
        "fee_model": f"{IDENTITY_DOMAIN}.fee_model",
        "slippage_model": f"{IDENTITY_DOMAIN}.slippage_model",
        "funding_model": f"{IDENTITY_DOMAIN}.funding_model",
        "cost_model": f"{IDENTITY_DOMAIN}.cost_model",
        "risk_policy": f"{IDENTITY_DOMAIN}.risk_policy",
        "portfolio": f"{IDENTITY_DOMAIN}.portfolio",
        "split_policy": f"{IDENTITY_DOMAIN}.split_policy",
        "environment": f"{IDENTITY_DOMAIN}.environment",
        "identity": f"{IDENTITY_DOMAIN}.identity",
        "dirty_paths": f"{IDENTITY_DOMAIN}.dirty_paths",
    }
)

_LOGGER = logging.getLogger(__name__)


class CanonicalExperimentIdentityError(ValueError):
    """Fail-closed Canonical Experiment Identity v1 error."""


@dataclass(frozen=True)
class CanonicalCodeProvenanceV1:
    git_sha: str
    working_tree_status: str
    dirty_paths_digest: str | None = None


@dataclass(frozen=True)
class CanonicalExperimentIdentityRequestV1:
    git_sha: str
    working_tree_status: str
    strategy_identity: str
    strategy_params: Mapping[str, Any]
    dataset_digest: str
    feature_pipeline_digest: str
    fee_model_digest: str
    slippage_model_digest: str
    funding_model_digest: str
    risk_policy_digest: str
    portfolio_digest: str
    split_policy_digest: str
    seed: int
    environment: Mapping[str, Any]
    parent_lineage_ref: str | None = None
    dirty_paths_digest: str | None = None


def digest_domain_name(component: str) -> str:
    try:
        return _DIGEST_DOMAINS[component]
    except KeyError as exc:
        raise CanonicalExperimentIdentityError(
            f"unknown digest domain component: {component}"
        ) from exc


def domain_separated_digest(component: str, payload: Mapping[str, Any]) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": digest_domain_name(component),
        "payload": canonicalize_value(payload),
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def canonicalize_value(value: Any, *, path: str = "$") -> Any:
    _reject_secret_key_path(path)
    if isinstance(value, Mapping):
        return canonicalize_mapping(value, path=path)
    if isinstance(value, (set, frozenset)):
        canonical_items = [canonicalize_value(item, path=f"{path}[]") for item in value]
        return sorted(canonical_items, key=_stable_sort_key)
    if isinstance(value, tuple):
        return [canonicalize_value(item, path=f"{path}[]") for item in value]
    if isinstance(value, list):
        return [canonicalize_value(item, path=f"{path}[]") for item in value]
    if isinstance(value, Enum):
        return canonicalize_value(value.value, path=path)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            raise CanonicalExperimentIdentityError(
                f"non-finite float is forbidden in identity canonicalization: {path}"
            )
        return json.loads(json.dumps(value))
    if isinstance(value, str):
        return value
    raise CanonicalExperimentIdentityError(
        f"unsupported type for identity canonicalization at {path}: {type(value)!r}"
    )


def canonicalize_mapping(payload: Mapping[str, Any], *, path: str = "$") -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise CanonicalExperimentIdentityError(f"expected mapping at {path}")
    canonical: dict[str, Any] = {}
    for key in sorted((str(item) for item in payload.keys())):
        _reject_secret_key(key, path=f"{path}.{key}")
        canonical[key] = canonicalize_value(payload[key], path=f"{path}.{key}")
    return canonical


def _reject_secret_key(key: str, *, path: str) -> None:
    if _SECRET_KEY_TOKEN_RE.search(str(key)):
        raise CanonicalExperimentIdentityError(
            f"secret or credential field is forbidden in identity payload: {path}"
        )


def _reject_secret_key_path(path: str) -> None:
    for segment in str(path).split("."):
        token = segment[:-2] if segment.endswith("[]") else segment
        if token and token != "$" and _SECRET_KEY_TOKEN_RE.search(token):
            raise CanonicalExperimentIdentityError(
                f"secret or credential field is forbidden in identity payload: {path}"
            )


def _stable_sort_key(value: Any) -> str:
    if isinstance(value, (str, bytes)) or not isinstance(value, (Mapping, Sequence)):
        return repr(value)
    return deterministic_json_dumps(value)


def _require_git_sha(value: str) -> str:
    if not isinstance(value, str) or not _GIT_SHA1_RE.fullmatch(value):
        raise CanonicalExperimentIdentityError(
            "git_sha must be a 40-char lowercase git SHA-1 hex string"
        )
    return value


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise CanonicalExperimentIdentityError(
            f"{field_name} missing; COMPLETE identity is forbidden (fail-closed)"
        )
    lowered = value.strip().lower()
    if lowered in _UNAVAILABLE_TOKENS:
        raise CanonicalExperimentIdentityError(
            f"{field_name} is unavailable; COMPLETE identity is forbidden (fail-closed)"
        )
    if not is_valid_sha256_hex(value):
        raise CanonicalExperimentIdentityError(
            f"{field_name} must be 64-char lowercase sha256 hex (fail-closed)"
        )
    return value


def _require_seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CanonicalExperimentIdentityError(
            "seed must be an explicit int; implicit or random seed is forbidden"
        )
    return int(value)


def _require_strategy_identity(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value.strip().lower() in _UNAVAILABLE_TOKENS
    ):
        raise CanonicalExperimentIdentityError(
            "strategy_identity missing; COMPLETE identity is forbidden (fail-closed)"
        )
    return value.strip()


def _require_clean_tree(status: Any, dirty_paths_digest: Any) -> None:
    if status == WORKING_TREE_DIRTY:
        raise CanonicalExperimentIdentityError(
            "DIRTY_TREE_PROVENANCE_FAIL_CLOSED: dirty code cannot produce COMPLETE identity"
        )
    if status != WORKING_TREE_CLEAN:
        raise CanonicalExperimentIdentityError("working_tree_status must be CLEAN or DIRTY")
    if dirty_paths_digest is not None:
        raise CanonicalExperimentIdentityError(
            "dirty_paths_digest must be null when working_tree_status is CLEAN"
        )


def _parent_lineage_block(parent_lineage_ref: str | None) -> dict[str, Any]:
    if parent_lineage_ref is None:
        return {
            "kind": PARENT_KIND_ROOT,
            "parent_lineage_ref": None,
        }
    if not isinstance(parent_lineage_ref, str) or not parent_lineage_ref.strip():
        raise CanonicalExperimentIdentityError(
            "parent_lineage_ref must be a non-empty string or null for ROOT"
        )
    if parent_lineage_ref.strip().lower() in _UNAVAILABLE_TOKENS:
        raise CanonicalExperimentIdentityError(
            "parent_lineage_ref cannot use implicit unavailable tokens"
        )
    return {
        "kind": PARENT_KIND_PARENT_BOUND,
        "parent_lineage_ref": parent_lineage_ref,
    }


def _environment_snapshot(environment: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(environment, Mapping):
        raise CanonicalExperimentIdentityError("environment must be a mapping")
    extra = set(str(key) for key in environment.keys()) - _ENVIRONMENT_ALLOWED_KEYS
    if extra:
        raise CanonicalExperimentIdentityError(
            "environment contains non-reproducibility keys that would make "
            f"identical experiments diverge: {sorted(extra)}"
        )
    missing = sorted(_ENVIRONMENT_ALLOWED_KEYS - set(str(key) for key in environment.keys()))
    if missing:
        raise CanonicalExperimentIdentityError(
            f"environment missing required reproducibility keys: {missing}"
        )
    snapshot = canonicalize_mapping(environment)
    for key in _ENVIRONMENT_ALLOWED_KEYS:
        value = snapshot.get(key)
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().lower() in _UNAVAILABLE_TOKENS
        ):
            raise CanonicalExperimentIdentityError(
                f"environment.{key} must be an explicit non-empty string"
            )
    snapshot["identity_schema_version"] = SCHEMA_VERSION
    return snapshot


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


def _log_identity_built(record: Mapping[str, Any]) -> None:
    _LOGGER.info(
        "canonical_experiment_identity_v1 built completeness=%s identity_digest=%s git_sha=%s strategy_identity=%s runtime_authority=%s",
        record.get("completeness"),
        record.get("identity_digest"),
        record.get("git_sha"),
        record.get("strategy_identity"),
        record.get("experiment_identity_has_runtime_authority"),
    )


def inspect_code_provenance_v1(repo_root: Path | str) -> CanonicalCodeProvenanceV1:
    root = Path(repo_root)
    if not root.is_dir():
        raise CanonicalExperimentIdentityError(f"repo_root is not a directory: {root}")
    try:
        git_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        porcelain = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CanonicalExperimentIdentityError(
            "DIRTY_TREE_PROVENANCE_FAIL_CLOSED: git provenance inspect failed"
        ) from exc
    git_sha = _require_git_sha(git_sha)
    lines = sorted(line.replace("\\", "/") for line in porcelain.splitlines() if line.strip())
    if not lines:
        return CanonicalCodeProvenanceV1(
            git_sha=git_sha,
            working_tree_status=WORKING_TREE_CLEAN,
            dirty_paths_digest=None,
        )
    dirty_digest = domain_separated_digest("dirty_paths", {"lines": lines})
    return CanonicalCodeProvenanceV1(
        git_sha=git_sha,
        working_tree_status=WORKING_TREE_DIRTY,
        dirty_paths_digest=dirty_digest,
    )


def build_canonical_experiment_identity_v1(
    request: CanonicalExperimentIdentityRequestV1,
) -> Mapping[str, Any]:
    _require_clean_tree(request.working_tree_status, request.dirty_paths_digest)
    git_sha = _require_git_sha(request.git_sha)
    strategy_identity = _require_strategy_identity(request.strategy_identity)
    seed = _require_seed(request.seed)
    bound_digests = {
        field_name: _require_sha256_digest(field_name, getattr(request, field_name))
        for field_name in _CRITICAL_DIGEST_FIELDS
    }
    strategy_params = canonicalize_mapping(request.strategy_params)
    environment = _environment_snapshot(request.environment)
    parent_lineage = _parent_lineage_block(request.parent_lineage_ref)

    strategy_identity_digest = domain_separated_digest(
        "strategy_identity", {"strategy_identity": strategy_identity}
    )
    strategy_params_digest = domain_separated_digest("strategy_params", strategy_params)
    dataset_digest = domain_separated_digest(
        "dataset", {"source_digest": bound_digests["dataset_digest"]}
    )
    feature_pipeline_digest = domain_separated_digest(
        "feature_pipeline", {"source_digest": bound_digests["feature_pipeline_digest"]}
    )
    fee_model_digest = domain_separated_digest(
        "fee_model", {"source_digest": bound_digests["fee_model_digest"]}
    )
    slippage_model_digest = domain_separated_digest(
        "slippage_model", {"source_digest": bound_digests["slippage_model_digest"]}
    )
    funding_model_digest = domain_separated_digest(
        "funding_model", {"source_digest": bound_digests["funding_model_digest"]}
    )
    cost_model_digest = domain_separated_digest(
        "cost_model",
        {
            "fee_model_digest": fee_model_digest,
            "funding_model_digest": funding_model_digest,
            "slippage_model_digest": slippage_model_digest,
        },
    )
    risk_policy_digest = domain_separated_digest(
        "risk_policy", {"source_digest": bound_digests["risk_policy_digest"]}
    )
    portfolio_digest = domain_separated_digest(
        "portfolio", {"source_digest": bound_digests["portfolio_digest"]}
    )
    split_policy_digest = domain_separated_digest(
        "split_policy", {"source_digest": bound_digests["split_policy_digest"]}
    )
    environment_digest = domain_separated_digest("environment", environment)

    identity_body = {
        "completeness": COMPLETENESS_COMPLETE,
        "cost_model_digest": cost_model_digest,
        "dataset_digest": dataset_digest,
        "digest_algorithm": DIGEST_ALGORITHM,
        "environment": environment,
        "environment_digest": environment_digest,
        "experiment_identity_has_runtime_authority": EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY,
        "feature_pipeline_digest": feature_pipeline_digest,
        "fee_model_digest": fee_model_digest,
        "funding_model_digest": funding_model_digest,
        "git_sha": git_sha,
        "identity_domain": IDENTITY_DOMAIN,
        "parent_lineage": parent_lineage,
        "portfolio_digest": portfolio_digest,
        "risk_policy_digest": risk_policy_digest,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "slippage_model_digest": slippage_model_digest,
        "split_policy_digest": split_policy_digest,
        "strategy_identity": strategy_identity,
        "strategy_identity_digest": strategy_identity_digest,
        "strategy_params_digest": strategy_params_digest,
        "working_tree_status": WORKING_TREE_CLEAN,
    }
    identity_digest = domain_separated_digest("identity", identity_body)
    record = dict(identity_body)
    record["identity_digest"] = identity_digest
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_experiment_identity_v1(record)
    frozen = _freeze(record)
    _log_identity_built(record)
    return frozen


def validate_canonical_experiment_identity_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise CanonicalExperimentIdentityError("identity record must be a mapping")
    record = _plain_mapping(record)
    if record.get("schema_version") != SCHEMA_VERSION:
        raise CanonicalExperimentIdentityError("schema_version mismatch")
    if record.get("identity_domain") != IDENTITY_DOMAIN:
        raise CanonicalExperimentIdentityError("identity_domain mismatch")
    if record.get("completeness") != COMPLETENESS_COMPLETE:
        raise CanonicalExperimentIdentityError("non-COMPLETE identity records are forbidden")
    if record.get("experiment_identity_has_runtime_authority") is not False:
        raise CanonicalExperimentIdentityError(
            "experiment_identity_has_runtime_authority must be false"
        )
    if record.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise CanonicalExperimentIdentityError("runtime_authority_impact must be NONE")
    if record.get("working_tree_status") != WORKING_TREE_CLEAN:
        raise CanonicalExperimentIdentityError(
            "DIRTY_TREE_PROVENANCE_FAIL_CLOSED: COMPLETE identity requires CLEAN tree"
        )
    _require_git_sha(str(record.get("git_sha") or ""))
    _require_seed(record.get("seed"))
    parent_lineage = record.get("parent_lineage")
    if not isinstance(parent_lineage, Mapping):
        raise CanonicalExperimentIdentityError("parent_lineage must be a mapping")
    kind = parent_lineage.get("kind")
    parent_ref = parent_lineage.get("parent_lineage_ref")
    if kind == PARENT_KIND_ROOT:
        if parent_ref is not None:
            raise CanonicalExperimentIdentityError("ROOT parent_lineage_ref must be null")
    elif kind == PARENT_KIND_PARENT_BOUND:
        if not isinstance(parent_ref, str) or not parent_ref.strip():
            raise CanonicalExperimentIdentityError(
                "PARENT_BOUND parent_lineage_ref must be a non-empty string"
            )
    else:
        raise CanonicalExperimentIdentityError("parent_lineage.kind is invalid")

    identity_body = {
        key: record[key] for key in record if key not in {"identity_digest", "integrity"}
    }
    expected_identity_digest = domain_separated_digest("identity", identity_body)
    if record.get("identity_digest") != expected_identity_digest:
        raise CanonicalExperimentIdentityError("identity_digest mismatch")
    expected_integrity = compute_content_sha256(
        {key: value for key, value in record.items() if key != "integrity"}
    )
    integrity = record.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise CanonicalExperimentIdentityError("integrity.content_sha256 mismatch")


__all__ = [
    "COMPLETENESS_COMPLETE",
    "CanonicalCodeProvenanceV1",
    "CanonicalExperimentIdentityError",
    "CanonicalExperimentIdentityRequestV1",
    "DIGEST_ALGORITHM",
    "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY",
    "IDENTITY_DOMAIN",
    "PARENT_KIND_PARENT_BOUND",
    "PARENT_KIND_ROOT",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "WORKING_TREE_CLEAN",
    "WORKING_TREE_DIRTY",
    "build_canonical_experiment_identity_v1",
    "canonicalize_mapping",
    "canonicalize_value",
    "digest_domain_name",
    "domain_separated_digest",
    "inspect_code_provenance_v1",
    "validate_canonical_experiment_identity_v1",
]
