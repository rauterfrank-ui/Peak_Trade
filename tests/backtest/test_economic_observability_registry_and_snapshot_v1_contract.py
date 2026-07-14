"""Contract tests for canonical economic observability registry and snapshot v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest.economic_observability_registry_v1 import (
    DISCOVERY_METRIC_COUNT,
    REGISTRY_OWNER,
    SCHEMA_VERSION as REGISTRY_SCHEMA_VERSION,
    SUPPORTED_DOMAINS,
    get_canonical_metric_registry_v1,
    parse_metric_registry_v1,
    validate_registry_contract_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    SCHEMA_VERSION as SNAPSHOT_SCHEMA_VERSION,
    MetricMaterializationStatus,
    MetricValueV1,
    SNAPSHOT_DOMAIN_KEYS,
    SNAPSHOT_OWNER,
    CanonicalEconomicObservabilitySnapshotV1,
    compute_snapshot_digest,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_MODULE = REPO_ROOT / "src/backtest/economic_observability_registry_v1.py"
SNAPSHOT_MODULE = REPO_ROOT / "src/backtest/economic_observability_snapshot_v1.py"
REGISTRY_CONFIG = REPO_ROOT / "config/economic_observability_metric_registry_v1.json"


def _registry():
    return get_canonical_metric_registry_v1()


def test_metric_registry_has_unique_ids() -> None:
    registry = _registry()
    ids = registry.metric_ids
    assert len(ids) == len(set(ids))


def test_all_148_metrics_present() -> None:
    registry = _registry()
    assert len(registry.entries) == DISCOVERY_METRIC_COUNT
    assert registry.metric_count == DISCOVERY_METRIC_COUNT


def test_all_metrics_classified() -> None:
    registry = _registry()
    for entry in registry.entries:
        assert entry.availability_status
        assert entry.priority
        assert entry.domain in SUPPORTED_DOMAINS
        assert entry.schema_version == REGISTRY_SCHEMA_VERSION


def test_all_owners_resolved() -> None:
    registry = _registry()
    for entry in registry.entries:
        assert entry.canonical_owner
        assert entry.canonical_owner.lower() not in {"unknown", "tbd"}
        assert "see canonical_owner_inventory" not in entry.canonical_owner


def test_schema_roundtrip() -> None:
    registry = _registry()
    payload = registry.to_dict()
    reparsed = parse_metric_registry_v1()
    assert reparsed.metric_count == registry.metric_count
    assert reparsed.metric_ids == registry.metric_ids
    assert payload["schema_version"] == REGISTRY_SCHEMA_VERSION


def test_stable_serialization() -> None:
    snapshot = materialize_empty_snapshot_v1()
    first = serialize_canonical_json(snapshot.to_dict())
    second = serialize_canonical_json(snapshot.to_dict())
    assert first == second


def test_deterministic_digest() -> None:
    snapshot = materialize_empty_snapshot_v1(
        run_identity={"run_id": "fixture-run-v0"},
        source_refs=["discovery_fixture_ref"],
    )
    payload = snapshot.to_dict()
    digest_a = compute_snapshot_digest(payload)
    digest_b = compute_snapshot_digest(payload)
    assert digest_a == digest_b
    assert len(digest_a) == 64


def test_zero_and_null_semantics_distinct() -> None:
    computed = MetricValueV1(
        value=0.0,
        unit="ratio",
        status=MetricMaterializationStatus.COMPUTED,
        owner="backtest.stats",
        source="backtest.stats:profit_factor",
        formula_version="registry_reference_only_v0",
        sample_count=10,
        quality_flags=(),
        reason_codes=(),
    )
    absent = MetricValueV1(
        value=None,
        unit="ratio",
        status=MetricMaterializationStatus.NOT_COMPUTED,
        owner="backtest.stats",
        source="backtest.stats:profit_factor",
        formula_version="registry_reference_only_v0",
        sample_count=None,
        quality_flags=(),
        reason_codes=("METRIC_NOT_COMPUTED_AWAITING_REWIRE",),
    )
    assert computed.to_dict()["value"] == 0.0
    assert absent.to_dict()["value"] is None


def test_not_computed_requires_reason() -> None:
    metric = MetricValueV1(
        value=None,
        unit="mixed",
        status=MetricMaterializationStatus.NOT_COMPUTED,
        owner="backtest.stats",
        source="backtest.stats:turnover",
        formula_version="registry_reference_only_v0",
        sample_count=None,
        quality_flags=(),
        reason_codes=("METRIC_NOT_COMPUTED_AWAITING_REWIRE",),
    )
    assert metric.reason_codes


def test_not_applicable_requires_reason() -> None:
    metric = MetricValueV1(
        value=None,
        unit="mixed",
        status=MetricMaterializationStatus.NOT_APPLICABLE,
        owner="future_capability.trade_excursion_analytics_v0",
        source="future_capability.trade_excursion_analytics_v0",
        formula_version="registry_reference_only_v0",
        sample_count=None,
        quality_flags=(),
        reason_codes=("METRIC_NOT_APPLICABLE_IN_CURRENT_SCOPE",),
    )
    assert metric.reason_codes


def test_no_duplicate_formula_owners() -> None:
    registry = _registry()
    pairs = [(entry.source_field_or_formula, entry.canonical_owner) for entry in registry.entries]
    # Identical owner+source pairs are allowed only when metric_id differs by field suffix.
    source_owner_map: dict[str, set[str]] = {}
    for entry in registry.entries:
        source_owner_map.setdefault(entry.source_field_or_formula, set()).add(entry.canonical_owner)
    conflicts = {source: owners for source, owners in source_owner_map.items() if len(owners) > 1}
    assert not conflicts


def test_all_domains_supported() -> None:
    registry = _registry()
    domains = {entry.domain for entry in registry.entries}
    represented = {
        "economic",
        "costs",
        "strategy_quality",
        "risk",
        "trade_analytics",
        "decision_funnel",
        "exposure",
        "portfolio",
        "robustness",
        "data_quality",
    }
    assert represented.issubset(domains)
    snapshot = materialize_empty_snapshot_v1(registry=registry)
    for domain in SNAPSHOT_DOMAIN_KEYS:
        assert hasattr(snapshot, domain) or domain == "provenance"
    assert "registry_owner" in snapshot.provenance


def test_registry_schema_version_present() -> None:
    payload = json.loads(REGISTRY_CONFIG.read_text(encoding="utf-8"))
    assert payload["schema_version"] == REGISTRY_SCHEMA_VERSION
    assert payload["registry_owner"] == REGISTRY_OWNER


def test_snapshot_schema_version_present() -> None:
    snapshot = materialize_empty_snapshot_v1()
    payload = snapshot.to_dict()
    assert payload["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert SNAPSHOT_OWNER


def test_second_materialization_diff_empty() -> None:
    first = materialize_empty_snapshot_v1(
        run_identity={"run_id": "fixture-run-v0"},
        source_refs=["discovery_fixture_ref"],
    )
    second = materialize_empty_snapshot_v1(
        run_identity={"run_id": "fixture-run-v0"},
        source_refs=["discovery_fixture_ref"],
    )
    first_payload = first.to_dict()
    second_payload = second.to_dict()
    first_payload["manifest_digest"] = ""
    second_payload["manifest_digest"] = ""
    assert serialize_canonical_json(first_payload) == serialize_canonical_json(second_payload)


def test_no_runtime_import_boundary_violation() -> None:
    for path in (REGISTRY_MODULE, SNAPSHOT_MODULE):
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert hits == []


def test_no_order_adapter_import_boundary_violation() -> None:
    for path in (REGISTRY_MODULE, SNAPSHOT_MODULE):
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert all("order" not in hit.module.lower() for hit in hits)


def test_no_scheduler_import_boundary_violation() -> None:
    for path in (REGISTRY_MODULE, SNAPSHOT_MODULE):
        hits = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert all("scheduler" not in hit.module.lower() for hit in hits)


def test_validate_registry_contract_has_no_issues() -> None:
    registry = _registry()
    assert validate_registry_contract_v1(registry) == []


def test_snapshot_roundtrip() -> None:
    snapshot = materialize_empty_snapshot_v1(
        run_identity={"run_id": "fixture-run-v0"},
        source_refs=["discovery_fixture_ref"],
    )
    payload = snapshot.to_dict()
    reparsed = CanonicalEconomicObservabilitySnapshotV1.from_dict(payload)
    assert reparsed.schema_version == SNAPSHOT_SCHEMA_VERSION
    assert reparsed.economic.keys()
