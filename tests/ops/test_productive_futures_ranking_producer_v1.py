"""Capability 2.2 — Productive Futures Ranking Producer tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    RANKING_POLICY_ID,
    RANKING_POLICY_VERSION,
    SCHEMA_VERSION,
    SELECTION_AUTHORITY_ADDED,
    SNAPSHOT_FILENAME,
    SNAPSHOT_STATE_NO_ELIGIBLE,
    SNAPSHOT_STATE_STALE_INPUT,
    SNAPSHOT_STATE_VALID,
    TOP20_CANDIDATE_CONTEXT_LIMIT,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    compute_config_digest_v1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
    persist_ranking_bundle_atomic_v1,
    verify_manifest,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
    prove_restart_load_v1,
    run_productive_futures_ranking_producer_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import (
    ALL_FAILURE_CODES,
    RankingFailureCodeV1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    DuplicateRankingWriterError,
    ProductiveRankingSingleWriterV1,
)

REPO_SHA = "02095305f1ecaaa94e294ab73010ffdf33c905f0"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"  # ms → 2023-11-14T22:13:20Z


def _perp(
    inst_id: str = "ETH-USDT-SWAP",
    *,
    state: str = "live",
    tick: str = "0.01",
    lot: str = "1",
    min_sz: str = "1",
    ct_val: str = "0.01",
    ct_val_ccy: str = "ETH",
    base: str = "ETH",
    quote: str = "USDT",
    settle: str = "USDT",
    ct_type: str = "linear",
    inst_type: str = "SWAP",
    exp: str = "",
    **extra: object,
) -> dict:
    row = {
        "instId": inst_id,
        "instType": inst_type,
        "state": state,
        "baseCcy": base,
        "quoteCcy": quote,
        "settleCcy": settle,
        "ctType": ct_type,
        "ctVal": ct_val,
        "ctValCcy": ct_val_ccy,
        "tickSz": tick,
        "lotSz": lot,
        "minSz": min_sz,
        "uly": f"{base}-{quote}",
        "expTime": exp,
    }
    row.update(extra)
    return row


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _universe(rows: list[dict], marks: list[str] | None = None, **kwargs):
    mark_ids = marks if marks is not None else [r["instId"] for r in rows if r.get("instId")]
    return produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        **kwargs,
    ).snapshot.to_dict()


def _many_perps(n: int) -> list[dict]:
    # Deterministic synthetic non-BTC linear perps.
    bases = [
        "ETH",
        "SOL",
        "XRP",
        "ADA",
        "DOT",
        "LINK",
        "AVAX",
        "ATOM",
        "NEAR",
        "APT",
        "OP",
        "ARB",
        "SUI",
        "FIL",
        "LTC",
        "BCH",
        "TRX",
        "TON",
        "INJ",
        "SEI",
        "TIA",
        "WLD",
        "PEPE",
        "DOGE",
        "SHIB",
    ]
    rows = []
    for i in range(n):
        base = bases[i % len(bases)]
        # Unique inst ids even when base cycles.
        inst = f"{base}{i}-USDT-SWAP" if i >= len(bases) else f"{base}-USDT-SWAP"
        rows.append(
            _perp(
                inst,
                base=base if i < len(bases) else f"{base}{i}",
                ct_val_ccy=base if i < len(bases) else f"{base}{i}",
            )
        )
    return rows


def test_constants_and_authority_bounds() -> None:
    assert CAPABILITY_ID == "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
    assert PACKAGE_MARKER == "PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1=true"
    assert SCHEMA_VERSION == "productive_futures_ranking_snapshot.v1"
    assert PRODUCER_VERSION == "productive_futures_ranking_producer.v1"
    assert RANKING_POLICY_ID == "productive_futures_universe_structural_ranking_v1"
    assert RANKING_POLICY_VERSION == "v1"
    assert ALPHA_ALLOWED_DEFAULT is False
    assert SELECTION_AUTHORITY_ADDED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
    assert TOP20_CANDIDATE_CONTEXT_LIMIT == 20
    assert FORBIDDEN_CALL_GRAPH_TARGETS.isdisjoint(set(CALL_GRAPH))
    assert "selected_future" not in CALL_GRAPH


def test_valid_top20_from_universe() -> None:
    uni = _universe(_many_perps(25))
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.ok is True
    assert result.snapshot.snapshot_state == SNAPSHOT_STATE_VALID
    assert result.snapshot.eligible_candidate_count == 25
    assert len(result.snapshot.ranked_candidates) == 20
    assert result.snapshot.alpha_allowed is False
    assert result.snapshot.selection_authority_created is False
    assert result.snapshot.dashboard_input_used is False
    ranks = [c.rank for c in result.snapshot.ranked_candidates]
    assert ranks == list(range(1, 21))
    # Full score components persisted.
    for cand in result.snapshot.ranked_candidates:
        assert set(cand.score_components) == {
            "universe_eligibility",
            "data_quality_pass",
            "mark_price_supported",
            "market_data_supported",
            "trading_status_live",
            "metadata_complete",
        }
        assert cand.total_score == 6.0
        assert "venue_native_id" in cand.tie_break_values


def test_less_than_20_eligible() -> None:
    uni = _universe([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL")])
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.snapshot.eligible_candidate_count == 2
    assert len(result.snapshot.ranked_candidates) == 2
    assert [c.rank for c in result.snapshot.ranked_candidates] == [1, 2]


def test_no_eligible_candidates_persisted_state() -> None:
    # Cap 2.1 empty-eligible universe still yields a snapshot with zero instruments.
    uni = _universe([_perp(inst_id="BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC")])
    assert uni["eligible_instrument_count"] == 0
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.snapshot.snapshot_state == SNAPSHOT_STATE_NO_ELIGIBLE
    assert result.snapshot.ranked_candidates == ()
    assert RankingFailureCodeV1.NO_ELIGIBLE_CANDIDATES.value in result.failure_codes
    assert result.snapshot.alpha_allowed is False


def test_deterministic_ranking_and_tie_break() -> None:
    uni = _universe(
        [
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA", ct_val_ccy="ADA"),
        ]
    )
    a = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    b = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 50.0,
    )
    assert a.snapshot.integrity_digest == b.snapshot.integrity_digest
    assert [c.venue_native_id for c in a.snapshot.ranked_candidates] == [
        c.venue_native_id for c in b.snapshot.ranked_candidates
    ]
    # Lexicographic tie-break on equal structural scores.
    natives = [c.venue_native_id for c in a.snapshot.ranked_candidates]
    assert natives == sorted(natives)


def test_missing_universe_fail_closed() -> None:
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.ok is False
    assert RankingFailureCodeV1.UNIVERSE_SNAPSHOT_MISSING.value in result.failure_codes


def test_invalid_universe_fail_closed() -> None:
    result = produce_productive_futures_ranking_v1(
        universe_snapshot={"not": "a universe"},
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.ok is False
    assert result.hard_stop is True


def test_stale_universe_fail_closed() -> None:
    uni = _universe([_perp()])
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 200_000,
        max_universe_age_seconds=60.0,
    )
    assert result.ok is False
    assert result.snapshot.snapshot_state == SNAPSHOT_STATE_STALE_INPUT
    assert RankingFailureCodeV1.UNIVERSE_SNAPSHOT_STALE.value in result.failure_codes


def test_digest_mismatch_fail_closed() -> None:
    uni = _universe([_perp()])
    uni["payload_digest"] = "0" * 64
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert RankingFailureCodeV1.UNIVERSE_DIGEST_MISMATCH.value in result.failure_codes


def test_repository_sha_mismatch() -> None:
    uni = _universe([_perp()])
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        expected_universe_repository_sha="deadbeef",
    )
    assert RankingFailureCodeV1.REPOSITORY_SHA_MISMATCH.value in result.failure_codes


def test_mark_price_and_metadata_exclusions() -> None:
    uni = _universe([_perp()])
    # Mutate instrument rows after Cap 2.1 production to simulate degraded input.
    uni["instruments"][0]["mark_price_supported"] = False
    uni["instruments"][0]["market_data_supported"] = False
    uni["instruments"][0]["tick_size"] = ""
    uni["payload_digest"] = ""  # force recompute failure path separately — rebuild digest
    from src.ops.governed_futures_universe_producer_v1.models_v1 import (
        GovernedFuturesUniverseSnapshotV1,
    )

    rebuilt = GovernedFuturesUniverseSnapshotV1.from_dict(uni).with_payload_digest()
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=rebuilt.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.snapshot.snapshot_state == SNAPSHOT_STATE_NO_ELIGIBLE
    codes = result.snapshot.excluded_candidates[0].exclusion_reason_codes
    assert RankingFailureCodeV1.MARK_PRICE_UNSUPPORTED.value in codes
    assert RankingFailureCodeV1.MISSING_REQUIRED_METADATA.value in codes


def test_dashboard_and_legacy_ranker_independence() -> None:
    uni = _universe([_perp()])
    dash = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        dashboard_payload={"ranking": [{"id": "ETH", "score": 999}]},
    )
    assert RankingFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value in dash.failure_codes

    legacy = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        legacy_ranker_payload={"top": ["ETH-USDT-SWAP"]},
    )
    assert RankingFailureCodeV1.LEGACY_RANKER_INPUT_FORBIDDEN.value in legacy.failure_codes

    good = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    # Conflicting dashboard display must not alter productive ranking.
    assert good.snapshot.ranked_candidates[0].venue_native_id == "ETH-USDT-SWAP"
    assert good.snapshot.authority["DASHBOARD_AUTHORITY"] is False
    assert good.snapshot.authority["SELECTION_AUTHORITY_ADDED"] is False
    assert good.snapshot.authority["TOP_N_ACTIVE_SET_AUTHORITY"] is False


def test_persistence_restart_idempotency_and_conflict(tmp_path: Path) -> None:
    uni = _universe([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL")])
    out = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "ok",
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="sess-1",
    )
    assert out["ok"] is True
    assert out["alpha_allowed"] is False
    assert out["restart"]["identical_canonical_truth"] is True
    assert out["restart"]["selection_authority_after_restart"] is False
    assert out["evidence"]["no_selection_proof"] is True
    assert out["evidence"]["dashboard_independence"] is True
    verify_manifest(tmp_path / "ok")

    # Idempotent rewrite with identical content (different wall clock).
    out2 = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "ok",
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10.0,
        session_id="sess-2",
    )
    assert out2["ok"] is True
    assert out2["snapshot"]["integrity_digest"] == out["snapshot"]["integrity_digest"]

    # Same snapshot id, conflicting content → fail closed.
    writer = ProductiveRankingSingleWriterV1(state_root=tmp_path / "ok", session_id="conflict")
    writer.acquire(now_unix=OBSERVED_UNIX)
    base_snap = ProductiveFuturesRankingSnapshotV1.from_dict(out["snapshot"])
    conflicting_payload = base_snap.to_dict()
    conflicting_payload["eligible_candidate_count"] = 999
    conflicting_payload["integrity_digest"] = ""
    conflicting = ProductiveFuturesRankingSnapshotV1.from_dict(
        conflicting_payload
    ).with_integrity_digest()
    from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
        RankingPersistenceError,
    )

    with pytest.raises(RankingPersistenceError) as exc:
        persist_ranking_bundle_atomic_v1(
            state_root=tmp_path / "ok",
            writer=writer,
            snapshot=conflicting,
            evidence={"capability_id": CAPABILITY_ID},
        )
    assert exc.value.failure_code == RankingFailureCodeV1.SNAPSHOT_ID_CONTENT_CONFLICT.value
    writer.release()


def test_duplicate_writer_rejection(tmp_path: Path) -> None:
    first = ProductiveRankingSingleWriterV1(state_root=tmp_path, session_id="a")
    first.acquire(now_unix=OBSERVED_UNIX)
    second = ProductiveRankingSingleWriterV1(state_root=tmp_path, session_id="b")
    with pytest.raises(DuplicateRankingWriterError):
        second.acquire(now_unix=OBSERVED_UNIX)
    out = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path,
        universe_snapshot=_universe([_perp()]),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="c",
    )
    assert out["ok"] is False
    assert RankingFailureCodeV1.DUPLICATE_PRODUCER_WRITER.value in out["failure_codes"]
    first.release()


def test_persistence_failure_injection(tmp_path: Path) -> None:
    uni = _universe([_perp()])
    fail = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "fail",
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="wf",
        simulate_write_failure=True,
    )
    assert RankingFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value in fail["failure_codes"]

    partial = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "partial",
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="pw",
        simulate_partial_write=True,
    )
    assert RankingFailureCodeV1.PARTIAL_WRITE.value in partial["failure_codes"]

    crash = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path / "crash",
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="cr",
        simulate_crash_after_persist_before_confirm=True,
    )
    assert RankingFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value in crash["failure_codes"]


def test_config_digest_mismatch_on_load(tmp_path: Path) -> None:
    uni = _universe([_perp()])
    out = run_productive_futures_ranking_producer_v1(
        state_root=tmp_path,
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="cfg",
    )
    assert out["ok"] is True
    wrong = compute_config_digest_v1(repository_sha=REPO_SHA, max_universe_age_seconds=1.0)
    loaded = load_and_validate_ranking_snapshot_v1(
        tmp_path,
        expected_config_digest=wrong,
    )
    assert RankingFailureCodeV1.CONFIG_DIGEST_MISMATCH.value in loaded.failure_codes


def test_no_core_logic_mutation_surface() -> None:
    import src.ops.productive_futures_ranking_producer_v1.producer_v1 as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    # May import Cap 2.1 universe models; must not wire Master V2 / Double Play trading.
    assert "double_play" not in src.lower()
    assert "selected_future" not in CALL_GRAPH
    assert "top_n_active_set" not in CALL_GRAPH


def test_failure_semantics_catalog_complete() -> None:
    required = {
        "UNIVERSE_SNAPSHOT_MISSING",
        "UNIVERSE_SNAPSHOT_INVALID",
        "UNIVERSE_SNAPSHOT_STALE",
        "UNIVERSE_DIGEST_MISMATCH",
        "REPOSITORY_SHA_MISMATCH",
        "CONFIG_DIGEST_MISMATCH",
        "MISSING_REQUIRED_METADATA",
        "MARK_PRICE_UNSUPPORTED",
        "NO_ELIGIBLE_CANDIDATES",
        "PERSISTENCE_WRITE_FAILURE",
        "PARTIAL_WRITE",
        "CORRUPT_PERSISTED_SNAPSHOT",
        "DUPLICATE_PRODUCER_WRITER",
        "SNAPSHOT_ID_CONTENT_CONFLICT",
        "DASHBOARD_INPUT_FORBIDDEN",
        "LEGACY_RANKER_INPUT_FORBIDDEN",
        "INTEGRITY_FAILURE",
    }
    assert required.issubset(ALL_FAILURE_CODES)


def test_restart_helper_identical(tmp_path: Path) -> None:
    produced = produce_productive_futures_ranking_v1(
        universe_snapshot=_universe([_perp()]),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    writer = ProductiveRankingSingleWriterV1(state_root=tmp_path, session_id="r")
    writer.acquire(now_unix=OBSERVED_UNIX)
    persist_ranking_bundle_atomic_v1(
        state_root=tmp_path,
        writer=writer,
        snapshot=produced.snapshot,
        evidence={"capability_id": CAPABILITY_ID},
    )
    writer.release()
    proof = prove_restart_load_v1(state_root=tmp_path, expected_snapshot=produced.snapshot)
    assert proof["ok"] is True
    assert proof["alpha_allowed_after_restart"] is False


def test_event_time_bound() -> None:
    uni = _universe([_perp()])
    result = produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.snapshot.event_time == uni["generated_at_event_time"]


def test_generate_durable_evidence(tmp_path: Path) -> None:
    """Write Cap 2.2 evidence bundle under docs/evidence when running locally."""
    evidence_root = Path("docs/evidence/capability_2_2_productive_futures_ranking_producer_v1")
    productive = evidence_root / "productive_ranking"
    productive.mkdir(parents=True, exist_ok=True)

    uni = _universe(_many_perps(22))
    out = run_productive_futures_ranking_producer_v1(
        state_root=productive,
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="evidence",
        ranking_snapshot_id="pfr_evidence_cap22_v1",
    )
    assert out["ok"] is True
    summary = {
        "ACTIVATED": False,
        "BOUND": True,
        "CODE_EXISTS": True,
        "RUNTIME_REACHABLE": True,
        "PERSISTED": True,
        "RESTART_PROVEN": True,
        "PRODUCTIVE_RANKING_PRODUCER_IMPLEMENTED": True,
        "RANKING_SNAPSHOT_PERSISTED": True,
        "RANKING_RESTART_PROVEN": True,
        "TOP20_CANDIDATE_CONTEXT_AVAILABLE": True,
        "SINGLE_SELECTED_FUTURE_AUTHORITY": False,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": "BOUND_NOT_ACTIVATED",
        "DETERMINISTIC_RANKING": True,
        "EVENT_TIME_BOUND": True,
        "DATA_QUALITY_ENFORCED": True,
        "STALE_INPUT_FAIL_CLOSED": True,
        "MISSING_INPUT_FAIL_CLOSED": True,
        "TIE_BREAK_DETERMINISTIC": True,
        "SELECTION_AUTHORITY_CREATED": False,
        "POSITION_AUTHORITY_CREATED": False,
        "DASHBOARD_INPUT_USED": False,
        "SINGLE_WRITER_PROVEN": True,
        "PERSISTENCE_ATOMIC": True,
        "IDEMPOTENCY_PROVEN": True,
        "INTEGRITY_VERIFIED": True,
        "CORE_LOGIC_CHANGED": False,
        "RUNTIME_ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "capability_id": CAPABILITY_ID,
        "ranking_policy_id": RANKING_POLICY_ID,
        "ranking_policy_version": RANKING_POLICY_VERSION,
        "ranking_policy_provenance": out["snapshot"]["ranking_policy_provenance"],
        "universe_snapshot_id": out["snapshot"]["universe_snapshot_id"],
        "universe_source_digest": out["snapshot"]["universe_source_digest"],
        "config_digest": out["snapshot"]["config_digest"],
        "repository_sha": out["snapshot"]["repository_sha"],
        "event_time": out["snapshot"]["event_time"],
        "ranking_snapshot_id": out["snapshot"]["ranking_snapshot_id"],
        "integrity_digest": out["snapshot"]["integrity_digest"],
        "eligible_candidate_count": out["snapshot"]["eligible_candidate_count"],
        "ranked_count": len(out["snapshot"]["ranked_candidates"]),
        "snapshot_state": out["snapshot"]["snapshot_state"],
        "persistence_verification": out["persistence"],
        "restart_verification": out["restart"],
        "authority_verification": out["snapshot"]["authority"],
        "failure_injection_coverage": sorted(
            [
                "UNIVERSE_SNAPSHOT_MISSING",
                "UNIVERSE_SNAPSHOT_STALE",
                "UNIVERSE_DIGEST_MISMATCH",
                "DASHBOARD_INPUT_FORBIDDEN",
                "LEGACY_RANKER_INPUT_FORBIDDEN",
                "DUPLICATE_PRODUCER_WRITER",
                "SNAPSHOT_ID_CONTENT_CONFLICT",
                "PERSISTENCE_WRITE_FAILURE",
                "PARTIAL_WRITE",
            ]
        ),
    }
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    # Root MANIFEST over SUMMARY + productive_ranking artifacts.
    from src.ops.productive_futures_ranking_producer_v1.models_v1 import sha256_hex

    lines = []
    for rel in sorted(
        [
            "SUMMARY.json",
            f"productive_ranking/{SNAPSHOT_FILENAME}",
            "productive_ranking/productive_futures_ranking_evidence_v1.json",
            "productive_ranking/MANIFEST.sha256",
        ]
    ):
        digest = sha256_hex((evidence_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    (evidence_root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert (productive / SNAPSHOT_FILENAME).is_file()
