"""GHOSV bounded context pipeline (seven slices, one package)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    PACKAGE_ID,
    SCHEMA_VERSION,
)
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import ingest_evidence_records_v1
from src.ops.ghosv_bounded_context_v1.s02_identity_correlation_v1 import correlate_evidence_v1
from src.ops.ghosv_bounded_context_v1.s03_semantic_integrity_v1 import (
    evaluate_semantic_integrity_v1,
)
from src.ops.ghosv_bounded_context_v1.s04_traffic_light_v1 import (
    aggregate_traffic_by_trade_v1,
    aggregate_traffic_v1,
)
from src.ops.ghosv_bounded_context_v1.s05_critical_incident_v1 import (
    build_critical_incidents_v1,
    dedupe_incident_keys_v1,
)
from src.ops.ghosv_bounded_context_v1.s06_safety_authority_adapter_v1 import (
    evaluate_safety_authority_adapter_v1,
)
from src.ops.ghosv_bounded_context_v1.s07_safety_response_witness_v1 import (
    witness_safety_response_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvBoundedContextResultV1


def run_ghosv_bounded_context_v1(
    raw_records: Sequence[Mapping[str, Any]],
    *,
    detected_at: str = "1970-01-01T00:00:00+00:00",
    external_observations: Mapping[str, bool] | None = None,
    adapter_stub_accept: bool = False,
) -> GhosvBoundedContextResultV1:
    ingest = ingest_evidence_records_v1(raw_records)
    groups = correlate_evidence_v1(ingest.records)
    findings = evaluate_semantic_integrity_v1(records=ingest.records, groups=groups)
    trade_ids = tuple(sorted({g.trade_id for g in groups if g.trade_id}))
    traffic = aggregate_traffic_v1(findings)
    traffic_by_trade = aggregate_traffic_by_trade_v1(findings, trade_ids)
    incidents = build_critical_incidents_v1(
        findings=findings, groups=groups, detected_at=detected_at
    )
    adapter = evaluate_safety_authority_adapter_v1(incidents)
    witness = witness_safety_response_v1(
        incidents=incidents,
        adapter=adapter,
        external_observations=external_observations,
    )
    _ = traffic  # overall also in traffic_by_trade
    return GhosvBoundedContextResultV1(
        package_id=PACKAGE_ID,
        schema_version=SCHEMA_VERSION,
        traffic_overall=aggregate_traffic_v1(findings),
        traffic_by_trade=traffic_by_trade,
        findings=findings,
        incidents=incidents,
        correlation_groups=groups,
        adapter_decision=adapter,
        witness=witness,
        dedupe_keys=dedupe_incident_keys_v1(incidents),
    )
