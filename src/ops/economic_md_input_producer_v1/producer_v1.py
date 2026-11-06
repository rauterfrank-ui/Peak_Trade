"""Economic-MD MVR raw-input producer.

Standalone/offline invokable. Not productively scheduled. Does not rank,
select, define TOP20, apply Policy A, or trigger execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    CALL_GRAPH,
    CAPABILITY_ID,
    MARK_SOURCE_CLASS,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    TICKER_SOURCE_CLASS,
)
from src.ops.economic_md_input_producer_v1.models_v1 import (
    EconomicMdInputSnapshotV1,
    EconomicMdInstrumentRawInputV1,
    EconomicMdProduceResultV1,
    authority_block,
    compute_collection_cycle_identity_v1,
    compute_economic_input_snapshot_id_v1,
)
from src.ops.economic_md_input_producer_v1.persistence_v1 import (
    EconomicMdPersistenceError,
    evidence_digest_v1,
    load_and_validate_economic_md_snapshot_v1,
    persist_economic_md_bundle_atomic_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    EconomicMdPublicSourceV1,
    InjectedEconomicMdPublicSourceV1,
)
from src.ops.economic_md_input_producer_v1.reason_codes_v1 import EconomicMdFailureCodeV1
from src.ops.economic_md_input_producer_v1.single_writer_v1 import (
    DuplicateEconomicMdWriterError,
    EconomicMdInputSingleWriterV1,
)
from src.ops.economic_md_input_producer_v1.universe_gate_v1 import (
    load_cap21_eligible_instruments_v1,
)
from src.ops.economic_md_input_producer_v1.validation_v1 import (
    classify_unresolved_validity_v1,
    select_finalized_contiguous_pt1m_marks_v1,
    validate_ticker_quotes_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)


def _rfc3339(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decimal_or_none(raw: str | None) -> Decimal | None:
    if raw in (None, ""):
        return None
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, ValueError, ArithmeticError):
        return None


def _reject_forbidden_authority_payloads(
    *,
    dashboard_payload: Mapping[str, Any] | None,
    ranking_payload: Mapping[str, Any] | None,
    extra_instrument_ids: SequenceLike | None,
) -> tuple[str, ...]:
    codes: list[str] = []
    if dashboard_payload is not None:
        codes.append(EconomicMdFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value)
    if ranking_payload is not None:
        codes.append(EconomicMdFailureCodeV1.RANKING_OUTPUT_FORBIDDEN.value)
    if extra_instrument_ids:
        codes.append(EconomicMdFailureCodeV1.INSTRUMENT_NOT_IN_CAP21_ELIGIBLE_SET.value)
    return tuple(codes)


SequenceLike = tuple[str, ...] | list[str]


def produce_economic_md_input_snapshot_v1(
    *,
    universe_snapshot: Mapping[str, Any] | None,
    public_md_source: EconomicMdPublicSourceV1,
    collection_started_at_unix: float,
    collection_completed_at_unix: float,
    dashboard_payload: Mapping[str, Any] | None = None,
    ranking_payload: Mapping[str, Any] | None = None,
    extra_instrument_ids: SequenceLike | None = None,
) -> EconomicMdProduceResultV1:
    started = _rfc3339(collection_started_at_unix)
    completed = _rfc3339(collection_completed_at_unix)
    forbidden = _reject_forbidden_authority_payloads(
        dashboard_payload=dashboard_payload,
        ranking_payload=ranking_payload,
        extra_instrument_ids=extra_instrument_ids,
    )
    gate = load_cap21_eligible_instruments_v1(universe_snapshot)
    if forbidden or not gate.ok:
        cycle = compute_collection_cycle_identity_v1(
            universe_snapshot_id=str(
                (gate.universe_snapshot_reference or {}).get("snapshot_id") or "missing"
            ),
            collection_started_at=started,
            collection_completed_at=completed,
        )
        snapshot_id = compute_economic_input_snapshot_id_v1(
            universe_snapshot_id=str(
                (gate.universe_snapshot_reference or {}).get("snapshot_id") or "missing"
            ),
            universe_payload_digest=str(
                (gate.universe_snapshot_reference or {}).get("payload_digest") or "missing"
            ),
            collection_cycle_identity=cycle,
            instrument_raw_digests=(),
        )
        codes = tuple(sorted(set(forbidden + gate.failure_codes)))
        snap = EconomicMdInputSnapshotV1(
            schema_version=SCHEMA_VERSION,
            producer_version=PRODUCER_VERSION,
            capability_id=CAPABILITY_ID,
            economic_input_snapshot_id=snapshot_id,
            universe_snapshot_reference=dict(gate.universe_snapshot_reference),
            collection_cycle_identity=cycle,
            collection_started_at=started,
            collection_completed_at=completed,
            instrument_count_requested=0,
            instrument_count_rankable_raw_input=0,
            payload_digest="",
            provenance=_snapshot_provenance(network_used=False),
            instruments=(),
            authority=authority_block(),
            call_graph=CALL_GRAPH,
            failure_codes=codes,
        ).with_payload_digest()
        return EconomicMdProduceResultV1(snap, False, True, snap.failure_codes)

    instruments: list[EconomicMdInstrumentRawInputV1] = []
    for candidate in gate.eligible:
        bundle = public_md_source.collect_instrument_raw_input_v1(
            venue_native_id=candidate.venue_native_id
        )
        reasons: list[str] = list(bundle.failure_codes)
        marks, mark_codes = select_finalized_contiguous_pt1m_marks_v1(bundle.marks)
        reasons.extend(mark_codes)
        ticker, ticker_codes = validate_ticker_quotes_v1(bundle)
        reasons.extend(ticker_codes)
        bid = _decimal_or_none(None if ticker is None else ticker.bid_px)
        ask = _decimal_or_none(None if ticker is None else ticker.ask_px)
        unresolved = classify_unresolved_validity_v1(bid=bid, ask=ask)
        unique_reasons = tuple(sorted(set(reasons)))
        eligible = not unique_reasons
        provenance = {
            "canonical_instrument_id": candidate.canonical_instrument_id,
            "mark_source_class": MARK_SOURCE_CLASS,
            "ticker_source_class": TICKER_SOURCE_CLASS,
            "venue_native_id": candidate.venue_native_id,
        }
        row = EconomicMdInstrumentRawInputV1(
            canonical_instrument_id=candidate.canonical_instrument_id,
            venue_native_id=candidate.venue_native_id,
            raw_input_eligible=eligible,
            exclusion_reason_codes=unique_reasons,
            finalized_pt1m_marks=marks,
            ticker=ticker,
            unresolved_validity_dimensions=unresolved,
            raw_input_digest="",
            provenance=provenance,
        )
        if eligible and not row.compute_raw_input_digest():
            row = EconomicMdInstrumentRawInputV1(
                canonical_instrument_id=row.canonical_instrument_id,
                venue_native_id=row.venue_native_id,
                raw_input_eligible=False,
                exclusion_reason_codes=(
                    EconomicMdFailureCodeV1.PROVENANCE_DIGEST_UNAVAILABLE.value,
                ),
                finalized_pt1m_marks=(),
                ticker=row.ticker,
                unresolved_validity_dimensions=row.unresolved_validity_dimensions,
                raw_input_digest="",
                provenance=row.provenance,
            )
        instruments.append(row.with_raw_input_digest())

    instruments.sort(key=lambda row: (row.canonical_instrument_id, row.venue_native_id))
    rankable = tuple(row for row in instruments if row.raw_input_eligible)
    cycle = compute_collection_cycle_identity_v1(
        universe_snapshot_id=str(gate.universe_snapshot_reference["snapshot_id"]),
        collection_started_at=started,
        collection_completed_at=completed,
    )
    snapshot_id = compute_economic_input_snapshot_id_v1(
        universe_snapshot_id=str(gate.universe_snapshot_reference["snapshot_id"]),
        universe_payload_digest=str(gate.universe_snapshot_reference["payload_digest"]),
        collection_cycle_identity=cycle,
        instrument_raw_digests=tuple(row.raw_input_digest for row in instruments),
    )
    snap = EconomicMdInputSnapshotV1(
        schema_version=SCHEMA_VERSION,
        producer_version=PRODUCER_VERSION,
        capability_id=CAPABILITY_ID,
        economic_input_snapshot_id=snapshot_id,
        universe_snapshot_reference=dict(gate.universe_snapshot_reference),
        collection_cycle_identity=cycle,
        collection_started_at=started,
        collection_completed_at=completed,
        instrument_count_requested=len(gate.eligible),
        instrument_count_rankable_raw_input=len(rankable),
        payload_digest="",
        provenance=_snapshot_provenance(network_used=False),
        instruments=tuple(instruments),
        authority=authority_block(),
        call_graph=CALL_GRAPH,
        failure_codes=(),
    ).with_payload_digest()
    if not snap.payload_digest:
        snap = EconomicMdInputSnapshotV1(
            schema_version=snap.schema_version,
            producer_version=snap.producer_version,
            capability_id=snap.capability_id,
            economic_input_snapshot_id=snap.economic_input_snapshot_id,
            universe_snapshot_reference=dict(snap.universe_snapshot_reference),
            collection_cycle_identity=snap.collection_cycle_identity,
            collection_started_at=snap.collection_started_at,
            collection_completed_at=snap.collection_completed_at,
            instrument_count_requested=snap.instrument_count_requested,
            instrument_count_rankable_raw_input=0,
            payload_digest="",
            provenance=dict(snap.provenance),
            instruments=(),
            authority=authority_block(),
            call_graph=CALL_GRAPH,
            failure_codes=(EconomicMdFailureCodeV1.PROVENANCE_DIGEST_UNAVAILABLE.value,),
        ).with_payload_digest()
        return EconomicMdProduceResultV1(snap, False, True, snap.failure_codes)
    return EconomicMdProduceResultV1(snap, True, False, ())


def _snapshot_provenance(*, network_used: bool) -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "library_reuse_authority_transfer": False,
        "mark_source_class": MARK_SOURCE_CLASS,
        "network_used": bool(network_used),
        "producer_version": PRODUCER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "ticker_source_class": TICKER_SOURCE_CLASS,
    }


def build_economic_md_evidence_v1(
    *,
    produced: EconomicMdProduceResultV1,
    persistence_path: str,
    persistence_verification: Mapping[str, Any] | None,
    replay_verification: Mapping[str, Any] | None,
    extra_failure_codes: tuple[str, ...] = (),
) -> dict[str, Any]:
    evidence = {
        "authority": authority_block(),
        "call_graph": list(CALL_GRAPH),
        "capability_id": CAPABILITY_ID,
        "economic_input_snapshot_id": produced.snapshot.economic_input_snapshot_id,
        "failure_codes": list(sorted(set(produced.failure_codes + extra_failure_codes))),
        "instrument_count_rankable_raw_input": (
            produced.snapshot.instrument_count_rankable_raw_input
        ),
        "instrument_count_requested": produced.snapshot.instrument_count_requested,
        "ok": produced.ok,
        "payload_digest": produced.snapshot.payload_digest,
        "persistence_path": persistence_path,
        "persistence_verification": dict(persistence_verification or {}),
        "producer_version": PRODUCER_VERSION,
        "replay_verification": dict(replay_verification or {}),
        "schema_version": SCHEMA_VERSION,
    }
    evidence["evidence_digest"] = evidence_digest_v1(evidence)
    return evidence


def replay_economic_md_snapshot_v1(state_root: Path) -> dict[str, Any]:
    """Reconstruct and verify a snapshot from persisted raw input. No network."""
    loaded = load_and_validate_economic_md_snapshot_v1(Path(state_root))
    if not loaded.ok or loaded.snapshot is None:
        return {
            "network_read": False,
            "ok": False,
            "failure_codes": loaded.failure_codes,
            "detail": loaded.detail,
            "snapshot": None,
        }
    round_trip = EconomicMdInputSnapshotV1.from_dict(loaded.snapshot.to_dict())
    digest_ok = round_trip.compute_payload_digest() == loaded.snapshot.payload_digest
    return {
        "network_read": False,
        "ok": digest_ok,
        "failure_codes": ()
        if digest_ok
        else (EconomicMdFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
        "payload_digest": loaded.snapshot.payload_digest,
        "snapshot": loaded.snapshot.to_dict(),
        "snapshot_id": loaded.snapshot.economic_input_snapshot_id,
    }


def run_economic_md_input_producer_v1(
    *,
    state_root: Path,
    universe_snapshot: Mapping[str, Any] | None = None,
    universe_state_root: Path | None = None,
    public_md_source: EconomicMdPublicSourceV1 | None = None,
    injected_bundles: Mapping[str, Any] | None = None,
    collection_started_at_unix: float,
    collection_completed_at_unix: float,
    session_id: str = "default",
    release_writer: bool = True,
) -> dict[str, Any]:
    """Standalone produce → persist → replay. Not a productive host join."""
    if universe_snapshot is None and universe_state_root is not None:
        loaded = load_and_validate_universe_snapshot_v1(Path(universe_state_root))
        universe_snapshot = None if loaded.snapshot is None else loaded.snapshot.to_dict()
        if not loaded.ok:
            produced = produce_economic_md_input_snapshot_v1(
                universe_snapshot=None,
                public_md_source=InjectedEconomicMdPublicSourceV1({}),
                collection_started_at_unix=collection_started_at_unix,
                collection_completed_at_unix=collection_completed_at_unix,
            )
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": produced.failure_codes,
                "snapshot": produced.snapshot.to_dict(),
                "persistence": None,
                "replay": None,
                "evidence": build_economic_md_evidence_v1(
                    produced=produced,
                    persistence_path=str(state_root),
                    persistence_verification=None,
                    replay_verification=None,
                ),
            }
    source = public_md_source
    if source is None:
        from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
            InstrumentPublicMdBundleV1,
        )

        bundles = {}
        for venue_id, payload in dict(injected_bundles or {}).items():
            if isinstance(payload, InstrumentPublicMdBundleV1):
                bundles[str(venue_id)] = payload
        source = InjectedEconomicMdPublicSourceV1(bundles)

    writer = EconomicMdInputSingleWriterV1(state_root=Path(state_root), session_id=session_id)
    try:
        writer.acquire(now_unix=collection_started_at_unix)
    except DuplicateEconomicMdWriterError as exc:
        return {
            "ok": False,
            "hard_stop": True,
            "failure_codes": (exc.failure_code,),
            "snapshot": None,
            "persistence": None,
            "replay": None,
            "evidence": {
                "capability_id": CAPABILITY_ID,
                "duplicate_writer_rejected": True,
                "failure_codes": [exc.failure_code],
            },
        }
    try:
        produced = produce_economic_md_input_snapshot_v1(
            universe_snapshot=universe_snapshot,
            public_md_source=source,
            collection_started_at_unix=collection_started_at_unix,
            collection_completed_at_unix=collection_completed_at_unix,
        )
        evidence = build_economic_md_evidence_v1(
            produced=produced,
            persistence_path=str(Path(state_root)),
            persistence_verification=None,
            replay_verification=None,
        )
        try:
            persistence = persist_economic_md_bundle_atomic_v1(
                state_root=Path(state_root),
                writer=writer,
                snapshot=produced.snapshot,
                evidence=evidence,
            )
        except EconomicMdPersistenceError as exc:
            evidence = build_economic_md_evidence_v1(
                produced=produced,
                persistence_path=str(Path(state_root)),
                persistence_verification={"ok": False, "failure_code": exc.failure_code},
                replay_verification=None,
                extra_failure_codes=(exc.failure_code,),
            )
            return {
                "ok": False,
                "hard_stop": True,
                "failure_codes": tuple(sorted(set(produced.failure_codes + (exc.failure_code,)))),
                "snapshot": produced.snapshot.to_dict(),
                "persistence": {"ok": False, "failure_code": exc.failure_code},
                "replay": None,
                "evidence": evidence,
            }
        replay = replay_economic_md_snapshot_v1(Path(state_root))
        evidence = build_economic_md_evidence_v1(
            produced=produced,
            persistence_path=persistence["persistence_path"],
            persistence_verification=persistence,
            replay_verification=replay,
        )
        persist_economic_md_bundle_atomic_v1(
            state_root=Path(state_root),
            writer=writer,
            snapshot=produced.snapshot,
            evidence=evidence,
        )
        return {
            "ok": produced.ok and bool(persistence.get("ok")) and bool(replay.get("ok")),
            "hard_stop": produced.hard_stop or not replay.get("ok"),
            "failure_codes": produced.failure_codes,
            "snapshot": produced.snapshot.to_dict(),
            "persistence": persistence,
            "replay": replay,
            "evidence": evidence,
        }
    finally:
        if release_writer:
            writer.release()
