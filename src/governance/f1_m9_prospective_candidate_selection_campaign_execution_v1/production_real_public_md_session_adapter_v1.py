"""Production REAL public-MD session adapter for F1/M9 authorized campaign execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.constants_v1 import (
    BOUND_VENUE_INSTRUMENT_ID,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.models_v1 import (
    PreregisteredSessionRunnerError,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_source_v1 import (
    PublicMdSourceTelemetryV1,
    assert_no_orders_or_credentials_v1,
    build_preregistered_public_md_transport_v1,
    collect_public_mark_samples_v1,
    initialize_session_md_controls_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    EVIDENCE_SOURCE_REAL,
    REAL_MD_SUPPLIER_ID,
    REAL_MD_SUPPLIER_MODULE,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.real_public_md_session_adapter_v1 import (
    RealPublicMdSessionResultV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    HttpFetcher,
)

PRODUCTION_ADAPTER_OWNER_ID: str = "f1_m9_production_real_public_md_session_adapter_v1"
PRODUCTION_ADAPTER_CLASS_ID: str = "ProductionRealPublicMdSessionAdapterV1"

PREREGISTERED_SESSION_IDS: frozenset[str] = frozenset({"session_01", "session_02"})


@dataclass(slots=True)
class ProductionRealPublicMdSessionAdapterV1:
    """Canonical supplier-backed adapter (not FakeRealPublicMdSessionAdapterV1)."""

    http_fetcher: HttpFetcher | None = None
    mark_sample_cycle_count: int = 1

    def execute_work_unit_v1(
        self,
        *,
        work_unit: Mapping[str, Any],
        authorization: Mapping[str, Any],
    ) -> RealPublicMdSessionResultV1:
        session_id = str(work_unit.get("session_id") or "")
        if session_id not in PREREGISTERED_SESSION_IDS:
            raise PreregisteredSessionRunnerError("session_id_not_preregistered")
        if not authorization.get("public_market_data_read_authorized"):
            raise PreregisteredSessionRunnerError("public_market_data_read_not_authorized")
        if str(authorization.get("real_md_supplier_id") or "") != REAL_MD_SUPPLIER_ID:
            raise PreregisteredSessionRunnerError("real_md_supplier_binding_mismatch")

        fetcher = self.http_fetcher
        if fetcher is None:
            from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.real_http_fetcher_v1 import (
                make_real_eea_public_md_fetcher_v1,
            )

            fetcher, _telemetry = make_real_eea_public_md_fetcher_v1()

        telemetry = PublicMdSourceTelemetryV1()
        pacing, _budget, attempt_gate = initialize_session_md_controls_v1(
            session_id=session_id,
            max_cycles=int(self.mark_sample_cycle_count),
            venue_instrument_id=BOUND_VENUE_INSTRUMENT_ID,
            telemetry=telemetry,
        )
        transport, telemetry = build_preregistered_public_md_transport_v1(
            fetcher=fetcher,
            telemetry=telemetry,
            attempt_gate=attempt_gate,
            session_id=session_id,
        )
        transport.open()
        try:
            samples = collect_public_mark_samples_v1(
                transport=transport,
                cycle_count=int(self.mark_sample_cycle_count),
                venue_instrument_id=BOUND_VENUE_INSTRUMENT_ID,
                session_id=session_id,
                telemetry=telemetry,
                rate_limit_policy=pacing,
                attempt_gate=attempt_gate,
            )
        finally:
            transport.close()

        assert_no_orders_or_credentials_v1(telemetry)
        if not samples:
            raise PreregisteredSessionRunnerError("no_public_mark_samples")

        sample_digest = compute_content_sha256(
            {
                "session_id": session_id,
                "supplier_id": REAL_MD_SUPPLIER_ID,
                "samples": [
                    {
                        "mark_price": float(s.mark_price),
                        "event_time_unix_seconds": float(s.event_time_unix_seconds),
                    }
                    for s in samples
                ],
            }
        )
        fetch_count = int(
            telemetry.fetch_count or telemetry.counters.physical_request_attempt_count
        )
        if fetch_count < 1 and not telemetry.market_data_request_occurred:
            raise PreregisteredSessionRunnerError("real_md_fetch_missing")

        return RealPublicMdSessionResultV1(
            session_id=session_id,
            work_unit_index=int(work_unit.get("work_unit_index") or 0),
            evidence_source_class=EVIDENCE_SOURCE_REAL,
            public_md_fetch_count=max(1, fetch_count),
            private_api_effect=bool(telemetry.private_endpoint_request_occurred),
            credential_access=bool(telemetry.credential_access_occurred),
            order_effect=bool(telemetry.order_request_occurred),
            supplier_id=REAL_MD_SUPPLIER_ID,
            supplier_module=REAL_MD_SUPPLIER_MODULE,
            sample_digest=sample_digest,
        )


def build_production_real_public_md_session_adapter_v1(
    *,
    http_fetcher: HttpFetcher | None = None,
    mark_sample_cycle_count: int = 1,
) -> ProductionRealPublicMdSessionAdapterV1:
    return ProductionRealPublicMdSessionAdapterV1(
        http_fetcher=http_fetcher,
        mark_sample_cycle_count=mark_sample_cycle_count,
    )


__all__ = [
    "PRODUCTION_ADAPTER_CLASS_ID",
    "PRODUCTION_ADAPTER_OWNER_ID",
    "PREREGISTERED_SESSION_IDS",
    "ProductionRealPublicMdSessionAdapterV1",
    "build_production_real_public_md_session_adapter_v1",
]
