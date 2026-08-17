"""I82 emitter-cutover identity-plane contract.

MU6 producer/emitter cutover: ExperimentConfig.get_experiment_id emits
the prepared Package-N SHA256 identity. compute_legacy_experiment_id_md5_12
remains the MD5-12 compatibility alias. No backfill, no legacy
deprecation, no run-id algorithm rewrite, no runtime/trading/Testnet/Live
authority. EG-I82-JOIN remains CLOSED_PROVEN.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_v1 import (
    is_package_n_sha256_canonical_id,
)
from src.experiments.experiment_identity_manifest_v1 import (
    IDENTITY_SCHEMA_VERSION as PACKAGE_N_IDENTITY_SCHEMA_VERSION,
    build_identity_config,
    compute_experiment_identity_id,
    compute_legacy_experiment_id_md5_12,
)
from src.meta.learning_loop.contract_safety_v1 import SCHEMA_VERSION_V1

CONTRACT_ID = "i82_emitter_cutover_preparation_contract_v1"
CONTRACT_VERSION = SCHEMA_VERSION_V1
IDENTITY_SCHEMA_VERSION = "i82_identity_sidecar_compat.v1"
ALIAS_AUTHORITY = "compatibility_only"
LEGACY_SCHEME_MD5_12 = "md5_12"
RUNTIME_AUTHORITY_IMPACT = "NONE"
EMITTER_CUTOVER_EXECUTED = True
LEGACY_MD5_REMOVED = False
BACKFILL_EXECUTED = False
I82_FULL_MIGRATION_PROVEN = False
EG_I82_JOIN_STATUS = "CLOSED_PROVEN"
MG_I82_EMITTER_CUTOVER_STATUS = "EMITTER_CUTOVER_COMPLETE"
PACKAGE_N_IDENTITY_SCHEMA_VERSION_REF = PACKAGE_N_IDENTITY_SCHEMA_VERSION
CUTOVER_OWNER_GO = "OWNER_GO_I82_EMITTER_CUTOVER"

GET_EXPERIMENT_ID_SOURCE_SHA256 = "a779b9690ba41f9248290c301862a291cf52dddd5892601a89ecb1a2467bdfab"
GET_EXPERIMENT_ID_PRE_CUTOVER_SOURCE_SHA256 = (
    "edb8ca5bbea8b4d02fbd47720dafadce8f3bc97cd19267006edaef039bf7d4cb"
)
PRESERVATION_FIXTURE_LEGACY_MD5_12 = "9b586cf2f92a"
PRESERVATION_FIXTURE_CANONICAL_SHA256 = (
    "ef57df63bd82c65dc83258060424653d41180bd0d90c2ebd7f167531449ed36e"
)

INVENTORY_RELATIVE_PATH = "docs/ops/specs/I82_EMITTER_CUTOVER_PREPARATION_INVENTORY_V1.json"

_MD5_12_RE = re.compile(r"^[0-9a-f]{12}$")
_FORBIDDEN_PROMOTION_KEYS = frozenset(
    {
        "canonical_identity_id=legacy_experiment_id",
        "promote_md5_to_sha256",
        "md5_as_canonical",
    }
)

MIGRATION_UNITS: tuple[str, ...] = (
    "MU1_CANONICAL_LEGACY_FIELD_SCHEMA",
    "MU2_SIDECAR_ALIAS_MATERIALIZATION",
    "MU3_DUAL_READ_COMPATIBILITY",
    "MU4_EXPLORER_REPORTING_ADAPTATION",
    "MU5_REGISTRY_EVIDENCE_CONSUMER_ADAPTATION",
    "MU6_PRODUCER_EMITTER_CUTOVER",
    "MU7_LEGACY_DEPRECATION",
)

IMPLEMENTED_IN_THIS_GO: frozenset[str] = frozenset(
    {
        "MU1_CANONICAL_LEGACY_FIELD_SCHEMA",
        "MU2_SIDECAR_ALIAS_MATERIALIZATION",
        "MU3_DUAL_READ_COMPATIBILITY",
        "MU6_PRODUCER_EMITTER_CUTOVER",
    }
)

FORBIDDEN_IN_THIS_GO: frozenset[str] = frozenset(
    {
        "MU7_LEGACY_DEPRECATION",
    }
)


class I82EmitterCutoverPreparationError(ValueError):
    """Fail-closed I82 emitter-cutover preparation contract error."""


def _reject(message: str) -> None:
    raise I82EmitterCutoverPreparationError(message)


def _require_sha256(value: object, *, field: str) -> str:
    if not is_package_n_sha256_canonical_id(value):
        _reject(f"{field} must be an independently verifiable Package-N SHA256 identity")
    return str(value)


def _normalize_legacy_id(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        _reject("legacy_experiment_id must be md5_12 hex or NONE")
    if value in {"", "NONE", "none", "null"}:
        _reject("legacy_experiment_id NONE must be encoded as JSON null, not a sentinel string")
    if _MD5_12_RE.fullmatch(value) is None:
        _reject("legacy_experiment_id must be 12 lowercase hex chars when present")
    return value


@dataclass(frozen=True)
class I82IdentitySidecarV1:
    """Explicit compatibility sidecar. Never a canonical-identity authority."""

    canonical_identity_id: str
    legacy_experiment_id: str | None
    legacy_scheme: str | None
    identity_schema_version: str
    alias_authority: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "canonical_identity_id": self.canonical_identity_id,
            "legacy_experiment_id": self.legacy_experiment_id,
            "legacy_scheme": self.legacy_scheme,
            "identity_schema_version": self.identity_schema_version,
            "alias_authority": self.alias_authority,
        }


def build_i82_identity_sidecar_v1(
    *,
    canonical_identity_id: str,
    legacy_experiment_id: str | None = None,
    legacy_scheme: str | None = None,
    identity_schema_version: str = IDENTITY_SCHEMA_VERSION,
    alias_authority: str = ALIAS_AUTHORITY,
) -> I82IdentitySidecarV1:
    """Build an explicit compatibility sidecar. Does not emit producer IDs."""
    canonical = _require_sha256(canonical_identity_id, field="canonical_identity_id")
    legacy = _normalize_legacy_id(legacy_experiment_id)
    if alias_authority != ALIAS_AUTHORITY:
        _reject("alias_authority must be compatibility_only")
    if identity_schema_version != IDENTITY_SCHEMA_VERSION:
        _reject("identity_schema_version must be i82_identity_sidecar_compat.v1")
    if legacy is None:
        if legacy_scheme is not None:
            _reject("legacy_scheme must be NONE when legacy_experiment_id is NONE")
    else:
        if legacy_scheme != LEGACY_SCHEME_MD5_12:
            _reject("legacy_scheme must be md5_12 when legacy_experiment_id is present")
        if canonical == legacy:
            _reject("canonical_identity_id must not equal legacy_experiment_id")
        if is_package_n_sha256_canonical_id(legacy):
            _reject("legacy_experiment_id must not be a Package-N SHA256 identity")
    return I82IdentitySidecarV1(
        canonical_identity_id=canonical,
        legacy_experiment_id=legacy,
        legacy_scheme=legacy_scheme if legacy is not None else None,
        identity_schema_version=identity_schema_version,
        alias_authority=alias_authority,
    )


def build_i82_identity_sidecar_from_package_n_manifest_v1(
    manifest: Mapping[str, Any],
) -> I82IdentitySidecarV1:
    """Materialize a sidecar from an existing Package-N manifest without mutation."""
    if not isinstance(manifest, Mapping):
        _reject("Package-N manifest must be an object")
    snapshot = dict(manifest)
    canonical = snapshot.get("experiment_identity_id")
    aliases = snapshot.get("legacy_aliases")
    legacy: str | None = None
    if isinstance(aliases, Mapping):
        legacy = aliases.get("legacy_experiment_id_md5_12")
        if legacy is not None and not isinstance(legacy, str):
            _reject("legacy_aliases.legacy_experiment_id_md5_12 must be a string when present")
    sidecar = build_i82_identity_sidecar_v1(
        canonical_identity_id=str(canonical) if canonical is not None else "",
        legacy_experiment_id=legacy,
        legacy_scheme=LEGACY_SCHEME_MD5_12 if legacy is not None else None,
    )
    if dict(manifest) != snapshot:
        _reject("Package-N manifest input was mutated")
    return sidecar


def require_canonical_identity_v1(
    *,
    canonical_identity_id: str | None,
    legacy_experiment_id: str | None = None,
) -> str:
    """Fail closed when a canonical identity is required. Never promote MD5-12."""
    if canonical_identity_id is None or canonical_identity_id == "":
        _reject("canonical identity required; legacy MD5-12 must not substitute")
    canonical = _require_sha256(canonical_identity_id, field="canonical_identity_id")
    legacy = _normalize_legacy_id(legacy_experiment_id)
    if legacy is not None and canonical == legacy:
        _reject("canonical_identity_id must not equal legacy_experiment_id")
    return canonical


def canonical_join_from_legacy_alias_alone_v1(legacy_experiment_id: str | None) -> str:
    """Legacy alias alone never satisfies a canonical Package-N join."""
    _normalize_legacy_id(legacy_experiment_id)
    _reject("legacy alias alone does not satisfy a canonical Package-N identity join")
    raise AssertionError("unreachable")


def lookup_legacy_alias_v1(
    sidecar: I82IdentitySidecarV1,
    *,
    consumer_declares_compatibility: bool,
) -> str | None:
    """Explicit compatibility lookup. Does not authorize canonical joins."""
    if not consumer_declares_compatibility:
        _reject("legacy alias lookup requires an explicit compatibility-supporting consumer")
    if sidecar.alias_authority != ALIAS_AUTHORITY:
        _reject("sidecar alias_authority must remain compatibility_only")
    return sidecar.legacy_experiment_id


def assert_identity_planes_distinct_v1(
    *,
    canonical_identity_id: str,
    legacy_experiment_id: str | None,
) -> None:
    canonical = _require_sha256(canonical_identity_id, field="canonical_identity_id")
    legacy = _normalize_legacy_id(legacy_experiment_id)
    if legacy is None:
        return
    if canonical == legacy:
        _reject("SHA256 canonical and MD5-12 legacy must remain distinct identity planes")
    if len(canonical) == len(legacy):
        _reject("canonical SHA256 and legacy MD5-12 must not share the same width")


def assert_emitter_unmutated_v1() -> None:
    """Cutover assertion: productive emitter source matches frozen SHA256 digest."""
    from src.experiments.base import ExperimentConfig

    source = inspect.getsource(ExperimentConfig.get_experiment_id)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if digest != GET_EXPERIMENT_ID_SOURCE_SHA256:
        _reject("ExperimentConfig.get_experiment_id source digest drifted (emitter mutated)")
    if digest == GET_EXPERIMENT_ID_PRE_CUTOVER_SOURCE_SHA256:
        _reject("ExperimentConfig.get_experiment_id still has pre-cutover MD5-12 source")
    if "hashlib.md5" in source:
        _reject("productive emitter must not compute MD5-12")
    if "compute_experiment_identity_id" not in source:
        _reject("productive emitter must call compute_experiment_identity_id")


def assert_preservation_fixture_v1() -> None:
    """Golden cutover assertion: SHA256 emitter plus retained MD5-12 alias."""
    from src.experiments.base import ExperimentConfig, ParamSweep

    assert_emitter_unmutated_v1()
    config = ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("slow", [50, 100], description="ignored in identity"),
            ParamSweep("fast", [5, 10]),
        ],
        symbols=["ETH/EUR", "BTC/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )
    emitted = config.get_experiment_id()
    mirrored = compute_legacy_experiment_id_md5_12(config)
    canonical = compute_experiment_identity_id(build_identity_config(config))
    if emitted != PRESERVATION_FIXTURE_CANONICAL_SHA256:
        _reject("productive SHA256 emitter output drifted")
    if canonical != PRESERVATION_FIXTURE_CANONICAL_SHA256:
        _reject("canonical SHA256 identity helper drifted")
    if emitted != canonical:
        _reject("get_experiment_id must equal compute_experiment_identity_id")
    if mirrored != PRESERVATION_FIXTURE_LEGACY_MD5_12:
        _reject("legacy MD5-12 alias helper drifted")
    if mirrored == emitted:
        _reject("canonical SHA256 must not equal legacy MD5-12")
    if not is_package_n_sha256_canonical_id(emitted):
        _reject("productive emitter must emit a Package-N SHA256 identity")
    if is_package_n_sha256_canonical_id(mirrored):
        _reject("legacy MD5-12 alias must not be a Package-N SHA256 identity")
    assert_identity_planes_distinct_v1(
        canonical_identity_id=emitted,
        legacy_experiment_id=mirrored,
    )


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def load_i82_cutover_inventory_v1(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root if repo_root is not None else repo_root_from_here()
    path = root / INVENTORY_RELATIVE_PATH
    if not path.is_file():
        _reject(f"inventory missing: {INVENTORY_RELATIVE_PATH}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _reject("inventory root must be an object")
    required = (
        "schema_version",
        "contract_id",
        "bound_origin_main_sha",
        "identity_planes",
        "migration_units",
        "paths",
        "status",
    )
    for key in required:
        if key not in payload:
            _reject(f"inventory missing required field: {key}")
    if payload["contract_id"] != CONTRACT_ID:
        _reject("inventory contract_id mismatch")
    if payload["schema_version"] != CONTRACT_VERSION:
        _reject("inventory schema_version mismatch")
    status = payload["status"]
    if not isinstance(status, Mapping):
        _reject("inventory status must be an object")
    if status.get("EG_I82_JOIN") != EG_I82_JOIN_STATUS:
        _reject("inventory must preserve EG-I82-JOIN=CLOSED_PROVEN")
    if status.get("MG_I82_EMITTER_CUTOVER") != MG_I82_EMITTER_CUTOVER_STATUS:
        _reject("inventory MG-I82-EMITTER-CUTOVER must be EMITTER_CUTOVER_COMPLETE")
    if status.get("EMITTER_CUTOVER_EXECUTED") is not True:
        _reject("inventory must claim emitter cutover executed")
    if status.get("LEGACY_MD5_REMOVED") is not False:
        _reject("inventory must not claim legacy MD5-12 removed")
    if status.get("BACKFILL_EXECUTED") is not False:
        _reject("inventory must not claim backfill executed")
    if status.get("I82_FULL_MIGRATION_PROVEN") is not False:
        _reject("inventory must not claim full I82 migration proven")
    if status.get("RUNTIME_AUTHORITY_CHANGED") is not False:
        _reject("inventory must not claim runtime-authority change")
    units = payload["migration_units"]
    if not isinstance(units, list):
        _reject("inventory migration_units must be a list")
    names = [item.get("id") for item in units if isinstance(item, Mapping)]
    if tuple(names) != MIGRATION_UNITS:
        _reject("inventory migration unit ids drifted")
    for item in units:
        if not isinstance(item, Mapping):
            _reject("migration unit entries must be objects")
        unit_id = item.get("id")
        implemented = item.get("implemented_in_this_go")
        if unit_id in FORBIDDEN_IN_THIS_GO and implemented is not False:
            _reject(f"{unit_id} must remain unimplemented in this cutover GO")
        if unit_id in IMPLEMENTED_IN_THIS_GO and implemented is not True:
            _reject(f"{unit_id} must be marked implemented for this cutover GO")
    paths = payload["paths"]
    if not isinstance(paths, list) or not paths:
        _reject("inventory paths must be a non-empty list")
    required_path_fields = (
        "file",
        "symbol",
        "role",
        "current_value_format",
        "producer_or_consumer",
        "canonical_or_legacy",
        "persisted_or_ephemeral",
        "join_semantics",
        "collision_or_substitution_risk",
        "cutover_dependency",
        "compat_requirement",
        "safe_migration_unit",
    )
    for entry in paths:
        if not isinstance(entry, Mapping):
            _reject("inventory path entries must be objects")
        for field in required_path_fields:
            if field not in entry:
                _reject(f"inventory path missing {field}")
        if entry.get("symbol") == "ExperimentConfig.get_experiment_id":
            if entry.get("implemented_in_this_go") is not True:
                _reject("get_experiment_id MU6 cutover must be implemented")
            if entry.get("current_value_format") != "sha256_hex_64":
                _reject("get_experiment_id must emit sha256_hex_64")
            if entry.get("canonical_or_legacy") != "CANONICAL":
                _reject("get_experiment_id must be the canonical emitter")
        if entry.get("symbol") == "compute_legacy_experiment_id_md5_12":
            if entry.get("implemented_in_this_go") is True:
                _reject("legacy MD5-12 helper must remain the alias plane")
            if entry.get("current_value_format") != "md5_hex_12":
                _reject("legacy helper must remain md5_hex_12")
        if "armstrong_elkaroui_combi_experiment.py" in str(entry.get("file")):
            if entry.get("implemented_in_this_go") is True:
                _reject("armstrong run_id emitter must not be rewritten")
    forbidden = payload.get("forbidden_in_this_go", [])
    if not isinstance(forbidden, list):
        _reject("inventory forbidden_in_this_go must be a list")
    missing_forbidden = sorted(
        _FORBIDDEN_PROMOTION_KEYS.difference(str(item) for item in forbidden)
    )
    if missing_forbidden:
        _reject(f"inventory missing forbidden promotion token: {missing_forbidden[0]}")
    return payload


def validate_inventory_files_exist_v1(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> None:
    root = repo_root if repo_root is not None else repo_root_from_here()
    for entry in payload["paths"]:
        rel = str(entry["file"])
        path = root / rel
        if not path.is_file():
            _reject(f"inventoried file missing: {rel}")
        symbol = str(entry["symbol"])
        text = path.read_text(encoding="utf-8")
        token = symbol.split(".")[-1]
        if token not in text:
            _reject(f"inventoried symbol {symbol!r} not found in {rel}")


__all__ = [
    "ALIAS_AUTHORITY",
    "BACKFILL_EXECUTED",
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "CUTOVER_OWNER_GO",
    "EG_I82_JOIN_STATUS",
    "EMITTER_CUTOVER_EXECUTED",
    "FORBIDDEN_IN_THIS_GO",
    "GET_EXPERIMENT_ID_PRE_CUTOVER_SOURCE_SHA256",
    "GET_EXPERIMENT_ID_SOURCE_SHA256",
    "I82EmitterCutoverPreparationError",
    "I82IdentitySidecarV1",
    "I82_FULL_MIGRATION_PROVEN",
    "IDENTITY_SCHEMA_VERSION",
    "IMPLEMENTED_IN_THIS_GO",
    "INVENTORY_RELATIVE_PATH",
    "LEGACY_MD5_REMOVED",
    "LEGACY_SCHEME_MD5_12",
    "MG_I82_EMITTER_CUTOVER_STATUS",
    "MIGRATION_UNITS",
    "PACKAGE_N_IDENTITY_SCHEMA_VERSION_REF",
    "PRESERVATION_FIXTURE_CANONICAL_SHA256",
    "PRESERVATION_FIXTURE_LEGACY_MD5_12",
    "RUNTIME_AUTHORITY_IMPACT",
    "assert_emitter_unmutated_v1",
    "assert_identity_planes_distinct_v1",
    "assert_preservation_fixture_v1",
    "build_i82_identity_sidecar_from_package_n_manifest_v1",
    "build_i82_identity_sidecar_v1",
    "canonical_join_from_legacy_alias_alone_v1",
    "load_i82_cutover_inventory_v1",
    "lookup_legacy_alias_v1",
    "require_canonical_identity_v1",
    "validate_inventory_files_exist_v1",
]
