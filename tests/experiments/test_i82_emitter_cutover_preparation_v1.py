"""I82 emitter-cutover preparation — fail-closed identity-plane tests.

Offline only. No exchange, credentials, orders, or runtime authority.
Does not mutate existing emitters.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.cross_lane_identity_join_v1 import is_package_n_sha256_canonical_id
from src.experiments.experiment_identity_manifest_v1 import (
    build_identity_config,
    build_manifest,
    compute_experiment_identity_id,
    compute_legacy_experiment_id_md5_12,
)
from src.ops.i82_emitter_cutover_preparation_contract_v1 import (
    ALIAS_AUTHORITY,
    CONTRACT_ID,
    EG_I82_JOIN_STATUS,
    EMITTER_CUTOVER_EXECUTED,
    FORBIDDEN_IN_THIS_GO,
    GET_EXPERIMENT_ID_SOURCE_SHA256,
    I82EmitterCutoverPreparationError,
    I82_FULL_MIGRATION_PROVEN,
    IDENTITY_SCHEMA_VERSION,
    IMPLEMENTED_IN_THIS_GO,
    LEGACY_MD5_REMOVED,
    LEGACY_SCHEME_MD5_12,
    MG_I82_EMITTER_CUTOVER_STATUS,
    PRESERVATION_FIXTURE_CANONICAL_SHA256,
    PRESERVATION_FIXTURE_LEGACY_MD5_12,
    RUNTIME_AUTHORITY_IMPACT,
    assert_emitter_unmutated_v1,
    assert_identity_planes_distinct_v1,
    assert_preservation_fixture_v1,
    build_i82_identity_sidecar_from_package_n_manifest_v1,
    build_i82_identity_sidecar_v1,
    canonical_join_from_legacy_alias_alone_v1,
    load_i82_cutover_inventory_v1,
    lookup_legacy_alias_v1,
    require_canonical_identity_v1,
    validate_inventory_files_exist_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "src" / "ops" / "i82_emitter_cutover_preparation_contract_v1.py"
EMITTER_PATH = REPO_ROOT / "src" / "experiments" / "base.py"
_MD5_12 = "abcdef012345"
_SHA256 = hashlib.sha256(b"peak-trade-i82-cutover-prep-canonical").hexdigest()


def _sample_config() -> ExperimentConfig:
    return ExperimentConfig(
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


def test_status_flags_remain_preparation_only() -> None:
    assert EG_I82_JOIN_STATUS == "CLOSED_PROVEN"
    assert MG_I82_EMITTER_CUTOVER_STATUS == "PREPARATION_COMPLETE"
    assert EMITTER_CUTOVER_EXECUTED is False
    assert LEGACY_MD5_REMOVED is False
    assert I82_FULL_MIGRATION_PROVEN is False
    assert RUNTIME_AUTHORITY_IMPACT == "NONE"
    assert "MU6_PRODUCER_EMITTER_CUTOVER" in FORBIDDEN_IN_THIS_GO
    assert "MU1_CANONICAL_LEGACY_FIELD_SCHEMA" in IMPLEMENTED_IN_THIS_GO


def test_sha256_canonical_and_md5_12_legacy_are_distinct_planes() -> None:
    config = _sample_config()
    canonical = compute_experiment_identity_id(build_identity_config(config))
    legacy = config.get_experiment_id()
    assert canonical == PRESERVATION_FIXTURE_CANONICAL_SHA256
    assert legacy == PRESERVATION_FIXTURE_LEGACY_MD5_12
    assert canonical != legacy
    assert len(canonical) == 64
    assert len(legacy) == 12
    assert is_package_n_sha256_canonical_id(canonical)
    assert not is_package_n_sha256_canonical_id(legacy)
    assert_identity_planes_distinct_v1(
        canonical_identity_id=canonical,
        legacy_experiment_id=legacy,
    )


def test_legacy_alias_alone_does_not_satisfy_canonical_join() -> None:
    with pytest.raises(I82EmitterCutoverPreparationError, match="legacy alias alone"):
        canonical_join_from_legacy_alias_alone_v1(_MD5_12)


def test_missing_canonical_is_not_replaced_by_md5() -> None:
    with pytest.raises(I82EmitterCutoverPreparationError, match="must not substitute"):
        require_canonical_identity_v1(
            canonical_identity_id=None,
            legacy_experiment_id=_MD5_12,
        )
    with pytest.raises(I82EmitterCutoverPreparationError, match="must not substitute"):
        require_canonical_identity_v1(
            canonical_identity_id="",
            legacy_experiment_id=_MD5_12,
        )
    with pytest.raises(I82EmitterCutoverPreparationError, match="Package-N SHA256"):
        require_canonical_identity_v1(
            canonical_identity_id=_MD5_12,
            legacy_experiment_id=_MD5_12,
        )


def test_explicit_alias_resolution_requires_declared_compatibility() -> None:
    sidecar = build_i82_identity_sidecar_v1(
        canonical_identity_id=_SHA256,
        legacy_experiment_id=_MD5_12,
        legacy_scheme=LEGACY_SCHEME_MD5_12,
    )
    assert sidecar.alias_authority == ALIAS_AUTHORITY
    assert sidecar.identity_schema_version == IDENTITY_SCHEMA_VERSION
    resolved = lookup_legacy_alias_v1(sidecar, consumer_declares_compatibility=True)
    assert resolved == _MD5_12
    with pytest.raises(I82EmitterCutoverPreparationError, match="explicit compatibility"):
        lookup_legacy_alias_v1(sidecar, consumer_declares_compatibility=False)


def test_legacy_none_is_allowed_and_does_not_promote() -> None:
    sidecar = build_i82_identity_sidecar_v1(
        canonical_identity_id=_SHA256,
        legacy_experiment_id=None,
        legacy_scheme=None,
    )
    assert sidecar.legacy_experiment_id is None
    assert sidecar.legacy_scheme is None
    assert lookup_legacy_alias_v1(sidecar, consumer_declares_compatibility=True) is None
    with pytest.raises(I82EmitterCutoverPreparationError, match="JSON null"):
        build_i82_identity_sidecar_v1(
            canonical_identity_id=_SHA256,
            legacy_experiment_id="NONE",
            legacy_scheme=None,
        )


def test_canonical_must_not_equal_legacy() -> None:
    with pytest.raises(I82EmitterCutoverPreparationError, match="Package-N SHA256"):
        build_i82_identity_sidecar_v1(
            canonical_identity_id=_MD5_12,
            legacy_experiment_id=_MD5_12,
            legacy_scheme=LEGACY_SCHEME_MD5_12,
        )


def test_sidecar_from_package_n_manifest_does_not_mutate_manifest() -> None:
    manifest = build_manifest(_sample_config())
    snapshot = dict(manifest)
    sidecar = build_i82_identity_sidecar_from_package_n_manifest_v1(manifest)
    assert dict(manifest) == snapshot
    assert sidecar.canonical_identity_id == PRESERVATION_FIXTURE_CANONICAL_SHA256
    assert sidecar.legacy_experiment_id == PRESERVATION_FIXTURE_LEGACY_MD5_12
    assert sidecar.canonical_identity_id != sidecar.legacy_experiment_id


def test_existing_emitter_behavior_preserved() -> None:
    assert_preservation_fixture_v1()
    assert_emitter_unmutated_v1()
    config = _sample_config()
    first = config.get_experiment_id()
    second = config.get_experiment_id()
    assert first == second == PRESERVATION_FIXTURE_LEGACY_MD5_12
    assert compute_legacy_experiment_id_md5_12(config) == first
    source = EMITTER_PATH.read_text(encoding="utf-8")
    assert "return hashlib.md5(config_str.encode()).hexdigest()[:12]" in source


def test_contract_module_does_not_rewrite_emitter() -> None:
    tree = ast.parse(CONTRACT_PATH.read_text(encoding="utf-8"))
    assigned: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    assigned.add(target.attr)
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
        if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Attribute):
            assigned.add(node.target.attr)
    assert "get_experiment_id" not in assigned
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    assert "hashlib.md5" not in text
    assert "def get_experiment_id" not in text


def test_inventory_complete_and_files_exist() -> None:
    payload = load_i82_cutover_inventory_v1(REPO_ROOT)
    validate_inventory_files_exist_v1(payload, repo_root=REPO_ROOT)
    planes = set(payload["identity_planes"])
    required_planes = {
        "CANONICAL_SHA256_IDENTITY",
        "LEGACY_MD5_12_ALIAS",
        "EXPERIMENT_ID",
        "RUN_ID",
        "PACKAGE_N_IDENTITY",
        "JOIN_KEYS",
        "PERSISTED_FIELDS",
        "FILENAMES_PATHS",
        "MANIFEST_FIELDS",
        "REGISTRY_FIELDS",
        "EXPLORER_FIELDS",
        "REPORTING_FIELDS",
        "EVIDENCE_FIELDS",
    }
    assert required_planes <= planes
    roles = {entry["role"] for entry in payload["paths"]}
    assert required_planes <= roles
    producers = [
        entry
        for entry in payload["paths"]
        if entry["producer_or_consumer"] == "PRODUCER" and entry["canonical_or_legacy"] == "LEGACY"
    ]
    canonical_producers = [
        entry
        for entry in payload["paths"]
        if entry["producer_or_consumer"] == "PRODUCER"
        and entry["canonical_or_legacy"] == "CANONICAL"
    ]
    assert producers
    assert canonical_producers
    assert payload["bound_origin_main_sha"] == "9ba02c96a346c08beb24a09dfad2932534c8789e"
    assert payload["status"]["EG_I82_JOIN"] == "CLOSED_PROVEN"
    assert payload["status"]["MG_I82_EMITTER_CUTOVER"] == "PREPARATION_COMPLETE"
    assert payload["status"]["EMITTER_CUTOVER_EXECUTED"] is False
    assert payload["status"]["I82_FULL_MIGRATION_PROVEN"] is False


def test_existing_package_n_join_invariant_md5_is_not_canonical() -> None:
    assert is_package_n_sha256_canonical_id(PRESERVATION_FIXTURE_CANONICAL_SHA256)
    assert not is_package_n_sha256_canonical_id(PRESERVATION_FIXTURE_LEGACY_MD5_12)
    assert not is_package_n_sha256_canonical_id(_MD5_12)
    joined = require_canonical_identity_v1(
        canonical_identity_id=PRESERVATION_FIXTURE_CANONICAL_SHA256,
        legacy_experiment_id=PRESERVATION_FIXTURE_LEGACY_MD5_12,
    )
    assert joined == PRESERVATION_FIXTURE_CANONICAL_SHA256
    assert joined != PRESERVATION_FIXTURE_LEGACY_MD5_12


def test_no_network_credential_or_order_surface_in_contract() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    forbidden = (
        "okx.com",
        "requests.",
        "httpx",
        "exchange",
        "api_key",
        "secret_key",
        "passphrase",
        "place_order",
        "submit_order",
        "LIVE_AUTHORIZED = True",
    )
    for token in forbidden:
        assert token not in text
    assert CONTRACT_ID == "i82_emitter_cutover_preparation_contract_v1"
    assert (
        GET_EXPERIMENT_ID_SOURCE_SHA256
        == hashlib.sha256(
            __import__("inspect").getsource(ExperimentConfig.get_experiment_id).encode("utf-8")
        ).hexdigest()
    )
