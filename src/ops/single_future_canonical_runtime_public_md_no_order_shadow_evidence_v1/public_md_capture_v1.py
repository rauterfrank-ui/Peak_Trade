"""Public market-data capture for Cap 5.2 (OKX public REST only; injectable)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from src.ops.okx_public_market_data_client_v1 import (
    HttpFetcher,
    OkxPublicMarketDataClientError,
    OkxPublicMarketDataClientV1,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.fixture_v1 import (
    FixtureError,
    OfflineMarketDataFixtureV1,
    load_offline_market_data_fixture_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1 import (
    DEFAULT_CAPTURE_TEMPLATE_RELPATH,
    DEFAULT_CYCLE_COUNT,
    DEFAULT_MARK_PRICE_INST_TYPE,
    PUBLIC_MARKET_DATA_ONLY,
    PUBLIC_MD_CLIENT_OWNER,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.models_v1 import (
    canonical_digest_v1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.reason_codes_v1 import (
    PublicMdShadowFailureCodeV1,
)


class PublicMdCaptureError(RuntimeError):
    """Fail-closed public MD capture error."""


SleepFn = Callable[[float], None]


@dataclass(frozen=True)
class PublicMdCaptureBundleV1:
    venue_native_id: str
    inst_type: str
    network_scope: str
    public_market_data_only: bool
    network_access_occurred: bool
    private_api_used: bool
    orders_attempted: bool
    capture_envelopes: tuple[Mapping[str, Any], ...]
    shadow_fixture_payload: Mapping[str, Any]
    capture_digest: str
    client_owner: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue_native_id": self.venue_native_id,
            "inst_type": self.inst_type,
            "network_scope": self.network_scope,
            "public_market_data_only": self.public_market_data_only,
            "network_access_occurred": self.network_access_occurred,
            "private_api_used": self.private_api_used,
            "orders_attempted": self.orders_attempted,
            "capture_envelopes": [dict(x) for x in self.capture_envelopes],
            "shadow_fixture_payload": dict(self.shadow_fixture_payload),
            "capture_digest": self.capture_digest,
            "client_owner": self.client_owner,
            "envelope_count": len(self.capture_envelopes),
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _extract_mark_price(payload: Mapping[str, Any], *, venue_native_id: str) -> str:
    if str(payload.get("code") or "") != "0":
        raise PublicMdCaptureError(
            PublicMdShadowFailureCodeV1.TRANSPORT_FAILURE.value
            + f":provider_code={payload.get('code')!r}"
        )
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.MISSING_MARK_PRICE.value)
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("instId") or "") != venue_native_id:
            continue
        mark = row.get("markPx")
        if mark is None or str(mark).strip() == "":
            raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.MISSING_MARK_PRICE.value)
        try:
            float(str(mark))
        except ValueError as exc:
            raise PublicMdCaptureError(
                PublicMdShadowFailureCodeV1.MISSING_MARK_PRICE.value + ":INVALID"
            ) from exc
        return str(mark)
    raise PublicMdCaptureError(
        PublicMdShadowFailureCodeV1.MISSING_MARK_PRICE.value + ":INST_NOT_FOUND"
    )


def capture_public_mark_prices_v1(
    *,
    venue_native_id: str,
    cycle_count: int = DEFAULT_CYCLE_COUNT,
    inst_type: str = DEFAULT_MARK_PRICE_INST_TYPE,
    fetcher: HttpFetcher | None = None,
    sleep: SleepFn = time.sleep,
    poll_interval_seconds: float = 0.0,
    template_path: Path | None = None,
) -> PublicMdCaptureBundleV1:
    """Capture public mark prices and materialize a Cap-5.1-compatible shadow fixture."""
    if not PUBLIC_MARKET_DATA_ONLY:
        raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.NETWORK_SCOPE_VIOLATION.value)
    if cycle_count < 1:
        raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.CAPTURE_INVALID.value + ":CYCLES")

    template = load_offline_market_data_fixture_v1(
        template_path or (_repo_root() / DEFAULT_CAPTURE_TEMPLATE_RELPATH)
    )
    actionable = [o for o in template.observations if (not o.missing) and (not o.duplicate_of)]
    fetch_count = max(1, min(int(cycle_count), len(actionable) if actionable else int(cycle_count)))
    client = OkxPublicMarketDataClientV1(fetcher=fetcher, sleep=sleep)
    envelopes: list[dict[str, Any]] = []
    marks: list[str] = []
    for idx in range(fetch_count):
        try:
            env = client.get_json(
                "/api/v5/public/mark-price",
                {"instType": inst_type, "instId": venue_native_id},
            )
        except OkxPublicMarketDataClientError as exc:
            raise PublicMdCaptureError(
                PublicMdShadowFailureCodeV1.TRANSPORT_FAILURE.value + f":{exc}"
            ) from exc
        payload = json.loads(env.raw_body_utf8)
        mark = _extract_mark_price(payload, venue_native_id=venue_native_id)
        envelopes.append(env.to_json_dict())
        marks.append(mark)
        if poll_interval_seconds > 0 and idx + 1 < fetch_count:
            sleep(float(poll_interval_seconds))

    fixture_payload = _materialize_shadow_fixture_payload_v1(
        template=template,
        venue_native_id=venue_native_id,
        marks=marks,
    )
    material = {
        "venue_native_id": venue_native_id,
        "inst_type": inst_type,
        "marks": marks,
        "envelope_digests": [e.get("raw_payload_digest") for e in envelopes],
        "fixture_observations": fixture_payload.get("observations"),
    }
    return PublicMdCaptureBundleV1(
        venue_native_id=venue_native_id,
        inst_type=inst_type,
        network_scope="PUBLIC_MARKET_DATA_ONLY",
        public_market_data_only=True,
        network_access_occurred=True,
        private_api_used=False,
        orders_attempted=False,
        capture_envelopes=tuple(envelopes),
        shadow_fixture_payload=fixture_payload,
        capture_digest=canonical_digest_v1(material),
        client_owner=PUBLIC_MD_CLIENT_OWNER,
    )


def _materialize_shadow_fixture_payload_v1(
    *,
    template: OfflineMarketDataFixtureV1,
    venue_native_id: str,
    marks: Sequence[str],
) -> dict[str, Any]:
    raw = json.loads(template.raw_bytes.decode("utf-8"))
    observations = list(raw.get("observations") or [])
    mark_iter = iter(marks)
    assigned = 0
    for obs in observations:
        if bool(obs.get("missing")):
            continue
        if obs.get("duplicate_of"):
            continue
        try:
            mark = next(mark_iter)
        except StopIteration:
            break
        obs["mark_price"] = str(mark)
        assigned += 1
    if assigned < 1:
        raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.CAPTURE_INVALID.value + ":NO_OBS")
    # Preserve full template observation set (roles/duplicate/missing) for Cap 5.1 reuse.
    raw["observations"] = observations
    raw["fixture_id"] = "cap52_public_md_no_order_shadow_capture_v1"
    raw["seed"] = "cap52-public-md-capture-v1"
    raw["notes"] = list(raw.get("notes") or []) + [
        "CAP52_PUBLIC_MD_CAPTURE_MATERIALIZED_FROM_TEMPLATE",
        f"venue_native_id={venue_native_id}",
        f"assigned_public_md_marks={assigned}",
    ]
    baseline = dict(raw.get("mark_price_baseline") or {})
    if marks:
        baseline[venue_native_id] = str(marks[0])
    raw["mark_price_baseline"] = baseline
    return raw


def write_capture_fixture_json_v1(
    *,
    path: Path,
    capture: PublicMdCaptureBundleV1,
    validate: bool = True,
) -> Path:
    path = Path(path)
    # Cap 5.1 fixture loader requires a repo-relative source_path.
    repo_root = _repo_root()
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise PublicMdCaptureError(
            PublicMdShadowFailureCodeV1.CAPTURE_INVALID.value + ":PATH_OUTSIDE_REPO"
        ) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(capture.shadow_fixture_payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if validate:
        try:
            load_offline_market_data_fixture_v1(path)
        except FixtureError as exc:
            raise PublicMdCaptureError(
                PublicMdShadowFailureCodeV1.CAPTURE_INVALID.value + f":{exc}"
            ) from exc
    return path


def build_mock_mark_price_fetcher_v1(
    *,
    venue_native_id: str,
    marks: Sequence[str],
) -> HttpFetcher:
    """Deterministic injectable public GET for tests (no real network)."""
    state = {"i": 0}

    def _fetch(url: str, timeout_seconds: float) -> tuple[int, bytes]:
        _ = timeout_seconds
        lowered = url.lower()
        if "apikey=" in lowered or "/trade/" in lowered or "/account/" in lowered:
            raise PublicMdCaptureError(PublicMdShadowFailureCodeV1.PRIVATE_API_ATTEMPTED.value)
        idx = min(state["i"], len(marks) - 1)
        state["i"] += 1
        mark = marks[idx]
        body = {
            "code": "0",
            "msg": "",
            "data": [{"instId": venue_native_id, "instType": "SWAP", "markPx": str(mark)}],
        }
        return 200, json.dumps(body).encode("utf-8")

    return _fetch


def capture_digest_hex(capture: PublicMdCaptureBundleV1) -> str:
    return sha256_hex(json.dumps(capture.to_dict(), sort_keys=True))
