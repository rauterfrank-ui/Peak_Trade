"""S6 C1 mark/index enrichment join contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_fresh_c1_mark_index_evidence_join_v1 import (
    collect_current_productive_s6_c1_poll_mark_index_evidence_v1,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    NATIVE_ID,
)


@dataclass
class _GetResult:
    get_performed: bool
    payload: dict[str, Any] | None


class _IndexTransport:
    def get(
        self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str
    ) -> _GetResult:
        del endpoint, pretrade_decision_id
        assert auth_required is False
        return _GetResult(
            get_performed=True,
            payload={
                "code": "0",
                "data": [{"instId": "0G-USDT", "idxPx": "0.33"}],
            },
        )


def test_collect_mark_index_enrichment_with_mocked_eea(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1 import acquire_v1

    def _fake_acquire(**kwargs: object) -> acquire_v1.EeaUniverseAcquisitionResultV1:
        del kwargs
        return acquire_v1.EeaUniverseAcquisitionResultV1(
            ok=True,
            host="eea.okx.com",
            venue="OKX",
            source_kind="PUBLIC",
            source_event_time="2026-01-01T00:00:00Z",
            instruments_payload={"code": "0", "data": []},
            mark_price_payload={
                "code": "0",
                "data": [{"instId": NATIVE_ID, "markPx": "0.34", "idxPx": "0.33"}],
            },
            endpoints_used=("/api/v5/public/mark-price",),
            methods_used=("GET",),
            post_count="0",
            request_count=1,
            venue_live_contact=True,
            failure_codes=(),
            provenance={},
        )

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_s6_fresh_c1_mark_index_evidence_join_v1."
        "acquire_eea_universe_inventory_v1",
        _fake_acquire,
    )
    evidence = collect_current_productive_s6_c1_poll_mark_index_evidence_v1(
        transport=_IndexTransport(),
        venue_native_id=NATIVE_ID,
        pretrade_decision_id="test",
    )
    assert evidence.mark_price_payload
    assert evidence.instrument_match_proven is True
    assert evidence.mark_fresh is True


def test_collect_mark_index_when_mark_payload_lacks_idx_px(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1 import acquire_v1

    def _fake_acquire(**kwargs: object) -> acquire_v1.EeaUniverseAcquisitionResultV1:
        del kwargs
        return acquire_v1.EeaUniverseAcquisitionResultV1(
            ok=True,
            host="eea.okx.com",
            venue="OKX",
            source_kind="PUBLIC",
            source_event_time="2026-01-01T00:00:00Z",
            instruments_payload={"code": "0", "data": []},
            mark_price_payload={
                "code": "0",
                "data": [{"instId": NATIVE_ID, "markPx": "0.34"}],
            },
            endpoints_used=("/api/v5/public/mark-price",),
            methods_used=("GET",),
            post_count="0",
            request_count=1,
            venue_live_contact=True,
            failure_codes=(),
            provenance={},
        )

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_s6_fresh_c1_mark_index_evidence_join_v1."
        "acquire_eea_universe_inventory_v1",
        _fake_acquire,
    )
    evidence = collect_current_productive_s6_c1_poll_mark_index_evidence_v1(
        transport=_IndexTransport(),
        venue_native_id=NATIVE_ID,
        pretrade_decision_id="test-no-idx-on-mark",
    )
    assert evidence.index_tickers_payload is not None
