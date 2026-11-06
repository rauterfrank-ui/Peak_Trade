"""Contract tests for GHV productive mark cache freshness A/B forensic harness."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.ops.run_ghv_productive_mark_cache_freshness_ab_proof_v1 import (
    _classify_staleness,
    run_ab_proof,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)

_INSTRUMENT = "CAP-USDT-SWAP"
_ENDPOINT = f"{ENDPOINT_PUBLIC_MARK_PRICE}?instId={_INSTRUMENT}"


class _FakeResp:
    def __init__(self, *, status: int, body: bytes, url: str) -> None:
        self.status = status
        self._body = body
        self.url = url

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _mark_body(mark_px: float) -> bytes:
    payload = okx_public_mark_price_payload_v1(native_id=_INSTRUMENT, mark_px=mark_px)
    return json.dumps(payload).encode("utf-8")


def _patch_opener(monkeypatch: pytest.MonkeyPatch, responses: deque[tuple[int, bytes, str]]) -> None:
    opener = MagicMock()
    url = f"https://{AUTHORIZED_HOST}{_ENDPOINT}"

    def _open(req: object, **kwargs: object) -> _FakeResp:
        del kwargs, req
        status, body, resp_url = responses.popleft()
        return _FakeResp(status=status, body=body, url=resp_url or url)

    opener.open.side_effect = _open
    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1.build_opener",
        lambda *_a, **_k: opener,
    )
    monkeypatch.setattr(
        "scripts.ops.run_ghv_productive_mark_cache_freshness_ab_proof_v1.urllib.request.urlopen",
        lambda req, timeout=20.0: _open(req, timeout=timeout),
    )


def test_cacheable_arm_reuses_snapshot_while_dynamic_sees_new_marks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = f"https://{AUTHORIZED_HOST}{_ENDPOINT}"
    responses: deque[tuple[int, bytes, str]] = deque(
        [
            (200, _mark_body(0.06969), url),  # preflight dynamic
            (200, _mark_body(0.06969), url),  # round1 A
            (200, _mark_body(0.06970), url),  # round1 B
            (200, _mark_body(0.06971), url),  # round1 C direct
            (200, _mark_body(0.06972), url),  # round2 B (even order)
            (200, _mark_body(0.06973), url),  # round2 A should cache first mark from A transport
        ]
    )
    _patch_opener(monkeypatch, responses)
    report = run_ab_proof(
        evidence_root=tmp_path,
        instrument=_INSTRUMENT,
        duration_seconds=60.0,
        interval_seconds=0.01,
        use_direct_control=True,
        max_rounds=2,
    )
    assert report["TARGET_AVAILABLE"] is True
    assert report["AB_ONLY_CACHE_POLICY_DIFFERS"] is True
    assert report["A_B_CACHE_ISOLATED"] is True
    assert report["A_HTTP_GET_EXECUTED_COUNT"] == 1
    assert report["A_CACHE_HIT_COUNT"] >= 1
    assert report["B_HTTP_GET_EXECUTED_COUNT"] >= 2
    assert report["B_UNIQUE_MARK_COUNT"] >= 2
    assert report["CACHE_STALENESS_STATUS"] in {
        "PROVEN_CACHE_STALENESS",
        "STRONGLY_SUSPECTED_NOT_PROVEN",
    }


def test_inconclusive_when_market_flat(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    url = f"https://{AUTHORIZED_HOST}{_ENDPOINT}"
    flat = (200, _mark_body(0.07), url)
    responses: deque[tuple[int, bytes, str]] = deque([flat] * 20)
    _patch_opener(monkeypatch, responses)
    report = run_ab_proof(
        evidence_root=tmp_path,
        instrument=_INSTRUMENT,
        duration_seconds=10.0,
        interval_seconds=0.01,
        use_direct_control=True,
        max_rounds=3,
    )
    assert report["CACHE_STALENESS_STATUS"] == "INCONCLUSIVE_NO_MARKET_MOVEMENT"
    assert report["NEXT_ACTION"] == "REPEAT_ONLY_WHEN_VENUE_MOVEMENT_WITNESSED"


def test_separate_transport_instances_do_not_share_cache() -> None:
    t1 = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    t2 = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    assert t1._cache is not t2._cache


def test_classify_proven_requires_movement_witness() -> None:
    status, defect, _ = _classify_staleness(
        metrics_a={
            "SAMPLE_COUNT": 5,
            "UNIQUE_MARK_COUNT": 1,
            "MARK_CHANGE_COUNT": 0,
            "HTTP_GET_EXECUTED_COUNT": 1,
            "CACHE_HIT_COUNT": 4,
        },
        metrics_b={"UNIQUE_MARK_COUNT": 3, "MARK_CHANGE_COUNT": 2},
        metrics_c={"MARK_CHANGE_COUNT": 2, "UNIQUE_MARK_COUNT": 3},
        round_rows=[],
        b_while_a_stale=2,
        c_while_a_stale=1,
        movement_witness=2,
        test_validity=True,
        cache_isolated=True,
    )
    assert status == "PROVEN_CACHE_STALENESS"
    assert defect == "PROVEN"


def test_get_only_no_credentials_in_script_source() -> None:
    source = Path("scripts/ops/run_ghv_productive_mark_cache_freshness_ab_proof_v1.py").read_text(
        encoding="utf-8"
    )
    assert "auth_required=False" in source
    assert "POST" not in source or "POST_COUNT" in source
    assert "build_k1_okx" not in source
    assert GET_CACHE_POLICY_CACHEABLE_SNAPSHOT in source
    assert GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED in source
