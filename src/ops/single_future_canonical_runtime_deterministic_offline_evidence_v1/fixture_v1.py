"""Versioned deterministic offline market-data fixture loader for Cap 5.1."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.constants_v1 import (
    DEFAULT_CONFIG_RELPATH,
    DEFAULT_FIXTURE_RELPATH,
    FIXTURE_VERSION,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.models_v1 import (
    canonical_digest_v1,
    sha256_hex,
)
from src.ops.single_future_canonical_runtime_deterministic_offline_evidence_v1.reason_codes_v1 import (
    OfflineEvidenceFailureCodeV1,
)


class FixtureError(RuntimeError):
    """Fail-closed fixture validation error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class MarketObservationV1:
    observation_id: str
    event_time_unix: float
    kind: str
    mark_price: Optional[str]
    sequence_role: str
    typed_volatility_present: bool
    duplicate_of: Optional[str]
    missing: bool

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MarketObservationV1":
        mark = payload.get("mark_price")
        return cls(
            observation_id=str(payload["observation_id"]),
            event_time_unix=float(payload["event_time_unix"]),
            kind=str(payload["kind"]),
            mark_price=None if mark is None else str(mark),
            sequence_role=str(payload["sequence_role"]),
            typed_volatility_present=bool(payload.get("typed_volatility_present")),
            duplicate_of=(
                None
                if payload.get("duplicate_of") in (None, "")
                else str(payload.get("duplicate_of"))
            ),
            missing=bool(payload.get("missing")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "event_time_unix": self.event_time_unix,
            "kind": self.kind,
            "mark_price": self.mark_price,
            "sequence_role": self.sequence_role,
            "typed_volatility_present": self.typed_volatility_present,
            "duplicate_of": self.duplicate_of,
            "missing": self.missing,
        }


@dataclass(frozen=True)
class OfflineMarketDataFixtureV1:
    fixture_version: str
    fixture_id: str
    seed_policy: str
    seed: str
    instrument_metadata: Mapping[str, Any]
    companion_instruments: tuple[Mapping[str, Any], ...]
    mark_price_baseline: Mapping[str, str]
    typed_volatility_baseline: Mapping[str, Any]
    checkpoint_after_observation_index: int
    observations: tuple[MarketObservationV1, ...]
    required_sequence_roles: tuple[str, ...]
    notes: tuple[str, ...]
    source_path: str
    raw_bytes: bytes

    @property
    def fixture_digest(self) -> str:
        return sha256_hex(self.raw_bytes)

    def actionable_observations(self) -> tuple[MarketObservationV1, ...]:
        """Observations that participate in replay cycles (exclude missing; keep duplicates counted)."""
        return tuple(o for o in self.observations if not o.missing)

    def replay_mids(self) -> list[float]:
        """Deterministic mid path: skip missing; skip duplicates of already-seen IDs."""
        seen: set[str] = set()
        mids: list[float] = []
        for obs in self.observations:
            if obs.missing:
                continue
            if obs.duplicate_of:
                continue
            if obs.observation_id in seen:
                continue
            if obs.mark_price is None:
                raise FixtureError(OfflineEvidenceFailureCodeV1.MISSING_MARK_PRICE.value)
            seen.add(obs.observation_id)
            mids.append(float(obs.mark_price))
        return mids

    def observation_stats(self) -> dict[str, int]:
        distinct = {
            o.observation_id for o in self.observations if not o.missing and not o.duplicate_of
        }
        duplicates = sum(1 for o in self.observations if o.duplicate_of)
        missing = sum(1 for o in self.observations if o.missing)
        return {
            "distinct_observation_count": len(distinct),
            "duplicate_observation_count": duplicates,
            "missing_observation_count": missing,
            "total_observation_records": len(self.observations),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_version": self.fixture_version,
            "fixture_id": self.fixture_id,
            "seed_policy": self.seed_policy,
            "seed": self.seed,
            "instrument_metadata": dict(self.instrument_metadata),
            "companion_instruments": [dict(x) for x in self.companion_instruments],
            "mark_price_baseline": dict(self.mark_price_baseline),
            "typed_volatility_baseline": dict(self.typed_volatility_baseline),
            "checkpoint_after_observation_index": self.checkpoint_after_observation_index,
            "observations": [o.to_dict() for o in self.observations],
            "required_sequence_roles": list(self.required_sequence_roles),
            "notes": list(self.notes),
            "fixture_digest": self.fixture_digest,
            "source_path": self.source_path,
        }


def load_offline_market_data_fixture_v1(
    path: Path | None = None,
) -> OfflineMarketDataFixtureV1:
    fixture_path = Path(path) if path is not None else _repo_root() / DEFAULT_FIXTURE_RELPATH
    if not fixture_path.is_file():
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":MISSING_FILE")
    raw = fixture_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":JSON") from exc
    if not isinstance(payload, dict):
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":NOT_OBJECT")

    version = str(payload.get("fixture_version") or "")
    if version != FIXTURE_VERSION:
        raise FixtureError(
            OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + f":VERSION={version!r}"
        )
    if str(payload.get("seed_policy") or "") != "EXPLICIT_VERSIONED_NO_RANDOM":
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":SEED_POLICY")

    observations = tuple(
        MarketObservationV1.from_dict(x) for x in (payload.get("observations") or [])
    )
    if not observations:
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":NO_OBSERVATIONS")

    required = tuple(str(x) for x in (payload.get("required_sequence_roles") or []))
    present_roles = {o.sequence_role for o in observations}
    missing_roles = [r for r in required if r not in present_roles]
    if missing_roles:
        raise FixtureError(
            OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value
            + ":MISSING_ROLES:"
            + ",".join(missing_roles)
        )

    instrument = dict(payload.get("instrument_metadata") or {})
    required_meta = ("instId", "instType", "ctType", "ctVal", "tickSz", "lotSz", "minSz")
    for key in required_meta:
        if not instrument.get(key):
            raise FixtureError(
                OfflineEvidenceFailureCodeV1.INVALID_CONTRACT_METADATA.value + f":{key}"
            )

    marks = {str(k): str(v) for k, v in dict(payload.get("mark_price_baseline") or {}).items()}
    if instrument["instId"] not in marks:
        raise FixtureError(OfflineEvidenceFailureCodeV1.MISSING_MARK_PRICE.value + ":BASELINE")

    typed_vol = dict(payload.get("typed_volatility_baseline") or {})
    if instrument["instId"] not in typed_vol:
        raise FixtureError(
            OfflineEvidenceFailureCodeV1.MISSING_TYPED_VOLATILITY.value + ":BASELINE"
        )
    tv = typed_vol[instrument["instId"]]
    if not isinstance(tv, Mapping) or not bool(tv.get("presence")):
        raise FixtureError(OfflineEvidenceFailureCodeV1.MISSING_TYPED_VOLATILITY.value)

    checkpoint = int(payload.get("checkpoint_after_observation_index") or 0)
    if checkpoint < 1:
        raise FixtureError(OfflineEvidenceFailureCodeV1.FIXTURE_INVALID.value + ":CHECKPOINT")

    return OfflineMarketDataFixtureV1(
        fixture_version=version,
        fixture_id=str(payload.get("fixture_id") or ""),
        seed_policy=str(payload.get("seed_policy") or ""),
        seed=str(payload.get("seed") or ""),
        instrument_metadata=instrument,
        companion_instruments=tuple(dict(x) for x in (payload.get("companion_instruments") or [])),
        mark_price_baseline=marks,
        typed_volatility_baseline=typed_vol,
        checkpoint_after_observation_index=checkpoint,
        observations=observations,
        required_sequence_roles=required,
        notes=tuple(str(x) for x in (payload.get("notes") or [])),
        source_path=str(fixture_path.relative_to(_repo_root())),
        raw_bytes=raw,
    )


def load_config_digest_v1(path: Path | None = None) -> str:
    config_path = Path(path) if path is not None else _repo_root() / DEFAULT_CONFIG_RELPATH
    if not config_path.is_file():
        raise FixtureError(OfflineEvidenceFailureCodeV1.CONFIG_MISMATCH.value + ":MISSING_CONFIG")
    return sha256_hex(config_path.read_bytes())


def fixture_input_digest_v1(
    fixture: OfflineMarketDataFixtureV1,
    *,
    config_digest: str,
    repository_sha: str,
) -> str:
    return canonical_digest_v1(
        {
            "fixture_digest": fixture.fixture_digest,
            "fixture_version": fixture.fixture_version,
            "config_digest": config_digest,
            "repository_sha": repository_sha,
            "seed": fixture.seed,
            "seed_policy": fixture.seed_policy,
            "mids": fixture.replay_mids(),
            "observation_ids": [
                o.observation_id
                for o in fixture.observations
                if not o.missing and not o.duplicate_of
            ],
        }
    )


def universe_rows_from_fixture_v1(
    fixture: OfflineMarketDataFixtureV1,
) -> list[dict[str, Any]]:
    rows = [dict(fixture.instrument_metadata)]
    rows.extend(dict(x) for x in fixture.companion_instruments)
    return rows


def assert_no_http_network_imports_in_entrypoint_source_v1(source: str) -> None:
    forbidden = (
        "requests.",
        "urllib.request",
        "http.client",
        "aiohttp",
        "websocket",
        "websockets",
        "socket.create_connection",
    )
    lowered = source.lower()
    for token in forbidden:
        if token.lower() in lowered and "no_" + token.lower() not in lowered:
            # Allow comments mentioning forbidden tokens only if clearly negated.
            if f"# no {token.lower()}" in lowered or f"# forbid {token.lower()}" in lowered:
                continue
            raise FixtureError(
                OfflineEvidenceFailureCodeV1.NETWORK_ACCESS_ATTEMPTED.value + f":{token}"
            )


__all__ = [
    "FixtureError",
    "MarketObservationV1",
    "OfflineMarketDataFixtureV1",
    "assert_no_http_network_imports_in_entrypoint_source_v1",
    "fixture_input_digest_v1",
    "load_config_digest_v1",
    "load_offline_market_data_fixture_v1",
    "universe_rows_from_fixture_v1",
]
