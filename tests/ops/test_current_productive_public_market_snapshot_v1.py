"""Public OKX market snapshot contract. Injected payloads only. No network."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_public_market_snapshot_v1 import (
    PublicMarketSnapshotError,
    acquire_public_okx_market_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_stored_market_evidence_bind_v1 import (
    assess_stored_market_evidence_directory_v1,
)

_NATIVE = "ADA-USDT-SWAP"
_OBSERVED = 1_700_000_100.0
_TS_MS = "1700000080000"


class _InjectedPublicGet:
    def __init__(self, payloads: dict[str, dict]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, bool]] = []
        self.methods_used = ["GET"]

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del pretrade_decision_id
        self.calls.append((endpoint, auth_required))
        path = endpoint.split("?", 1)[0]
        payload = self.payloads.get(path)
        return SimpleNamespace(
            get_performed=payload is not None,
            method="GET",
            auth_header_sent=False,
            payload=payload,
            error_class="" if payload is not None else "MISSING",
        )


def _fresh_payloads() -> dict[str, dict]:
    row = {"instId": _NATIVE, "ts": _TS_MS}
    return {
        "/api/v5/market/candles": {
            "code": "0",
            "data": [[_TS_MS, "1", "2", "0.5", "1.5", "10", "10", "15", "1"]],
        },
        "/api/v5/market/ticker": {
            "code": "0",
            "data": [{**row, "bidPx": "1.4", "askPx": "1.6", "vol24h": "2500", "idxPx": "1.49"}],
        },
        "/api/v5/public/open-interest": {
            "code": "0",
            "data": [{**row, "oi": "8800"}],
        },
        "/api/v5/public/funding-rate": {
            "code": "0",
            "data": [{**row, "fundingRate": "0.0002"}],
        },
        "/api/v5/public/mark-price": {
            "code": "0",
            "data": [{**row, "markPx": "1.5", "idxPx": "1.49"}],
        },
    }


def test_snapshot_binds_fresh_same_instrument_fields(tmp_path) -> None:
    transport = _InjectedPublicGet(_fresh_payloads())
    snapshot = acquire_public_okx_market_snapshot_v1(
        transport=transport,
        native_id=_NATIVE,
        evidence_dir=tmp_path,
        observed_unix=_OBSERVED,
    )
    assert snapshot.post_count == 0
    assert snapshot.request_count == 5
    assert snapshot.finalized_close_count == 1
    assert snapshot.volume == 2500.0
    assert snapshot.open_interest == 8800.0
    assert snapshot.funding_rate == pytest.approx(0.0002)
    assert snapshot.mark_px == 1.5
    assert all(auth is False for _endpoint, auth in transport.calls)
    assessment = assess_stored_market_evidence_directory_v1(
        evidence_dir=tmp_path,
        native_id=_NATIVE,
    )
    assert assessment.complete is True
    assert assessment.volume == 2500.0


def test_snapshot_rejects_stale_mark_timestamp(tmp_path) -> None:
    payloads = _fresh_payloads()
    payloads["/api/v5/public/mark-price"]["data"][0]["ts"] = "1699990000000"
    with pytest.raises(PublicMarketSnapshotError, match="mark_ts"):
        acquire_public_okx_market_snapshot_v1(
            transport=_InjectedPublicGet(payloads),
            native_id=_NATIVE,
            evidence_dir=tmp_path,
            observed_unix=_OBSERVED,
        )
    assert not (tmp_path / "raw_public_candles_get_v1.json").exists()


def test_snapshot_rejects_foreign_instrument(tmp_path) -> None:
    payloads = _fresh_payloads()
    payloads["/api/v5/public/open-interest"]["data"][0]["instId"] = "BTC-USDT-SWAP"
    with pytest.raises(PublicMarketSnapshotError, match="open_interest"):
        acquire_public_okx_market_snapshot_v1(
            transport=_InjectedPublicGet(payloads),
            native_id=_NATIVE,
            evidence_dir=tmp_path,
            observed_unix=_OBSERVED,
        )
