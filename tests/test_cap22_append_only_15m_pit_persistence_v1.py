"""Bounded tests for Cap 2.2 WP1 append-only 15m PIT persistence contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.cap22_append_only_15m_pit_persistence_v1.anchor_v1 import (
    Cap22AppendOnlyPitPersistenceError,
    canonical_path_key_for_anchor,
    parse_canonical_15m_anchor_utc,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.archive_v1 import (
    bind_economic_md_to_cap21_at_exact_t_v1,
    canonical_cap21_path,
    canonical_economic_md_path,
    load_cap21_universe_at_t_v1,
    persist_cap21_universe_at_t_v1,
    persist_economic_md_at_t_v1,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED,
    CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED,
    CAP21_SNAPSHOT_FILENAME,
    CAP22_90D_EVIDENCE_CLOCK_STARTED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED,
    CAP22_PROSPECTIVE_COLLECTION_STARTED,
    COLLECTION_CADENCE_ID,
    COLLECTION_NETWORK_AUTHORIZED,
    COLLECTION_SCHEDULER_ENABLED,
    CONTRACT_ID,
    ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED,
    ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED,
    ECONOMIC_RANK_ACTIVATED,
    EXACT_T_BINDING_REQUIRED,
    FORWARD_LABEL_EXECUTION_IMPLEMENTED,
    HISTORICAL_EVIDENCE_GENERATED,
    NEXT_CAP22_DEPENDENCY,
    PDF_STEP_5_STATUS,
    PDF_STEP_7_STATUS,
    POLICY_RATIFICATION_JUSTIFIED,
    PROSPECTIVE_COLLECTION_STARTED,
    RUNTIME_AUTHORITY_GRANTED,
    WALK_FORWARD_EXECUTION_IMPLEMENTED,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.contract_v1 import (
    classify_cap22_append_only_15m_pit_persistence_v1,
    classify_preserved_program_invariants_v1,
    validate_cap22_append_only_15m_pit_persistence_declaration_v1,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.reason_codes_v1 import (
    Cap22AppendOnlyPitPersistenceFailureCodeV1 as Code,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import MINIMUM_FINALIZED_PT1M_MARKS
from src.ops.economic_md_input_producer_v1.producer_v1 import produce_economic_md_input_snapshot_v1
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import SNAPSHOT_FILENAME
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    persist_universe_bundle_atomic_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    GovernedUniverseSingleWriterV1,
)

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "src/ops/cap22_append_only_15m_pit_persistence_v1"
SPEC = REPO / "docs/ops/specs/CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1.md"
RUNBOOK = REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
TIME_SPEC = REPO / "docs/ops/specs/CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1.md"
ANCHOR = "2026-09-12T00:00:00Z"
REPO_SHA = "b31c0398b71a9898ed73cf3bfde9cd3e113caa3b"
BASE_TS_MS = 1_757_631_540_000
CAPTURE_TS = "1757635260000"


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "append_only": True,
        "cap21_append_only_at_t_persistence_implemented": True,
        "cap21_existing_producer_authority_preserved": True,
        "cap22_membership_authority_added": False,
        "cap22_productive_economic_runtime_wired": False,
        "cap22_prospective_collection_contracts_implemented": True,
        "cap22_prospective_collection_started": False,
        "cap22_selection_authority_added": False,
        "cap22_90d_evidence_clock_started": False,
        "collection_cadence_id": COLLECTION_CADENCE_ID,
        "collection_network_authorized": False,
        "collection_scheduler_enabled": False,
        "conflicting_overwrite_forbidden": True,
        "downstream_execution_must_not_re_rank": True,
        "economic_md_append_only_at_t_persistence_implemented": True,
        "economic_md_existing_producer_authority_preserved": True,
        "economic_md_producer_may_rank": False,
        "economic_md_producer_may_select": False,
        "economic_md_producer_productively_scheduled": False,
        "economic_rank_activated": False,
        "exact_t_binding_required": True,
        "forward_label_execution_implemented": False,
        "historical_evidence_generated": False,
        "identical_duplicate_idempotent": True,
        "multi_future_runtime_authorized": False,
        "next_cap22_dependency": NEXT_CAP22_DEPENDENCY,
        "no_as_of_guessing": True,
        "no_implicit_fill": True,
        "no_nearest_latest_fallback": True,
        "no_today_universe_membership_retroactive": True,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_ratification_justified": False,
        "productive_mf_host_join": False,
        "prospective_collection_started": False,
        "runtime_authority_granted": False,
        "walk_forward_execution_implemented": False,
    }
    payload.update(overrides)
    return payload


def _perp() -> dict:
    return {
        "instId": "ETH-USDT-SWAP",
        "instType": "SWAP",
        "state": "live",
        "baseCcy": "ETH",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": "ETH",
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": "ETH-USDT",
        "expTime": "",
    }


def _universe_snapshot(*, event_time: str = ANCHOR) -> dict:
    observed = datetime(2026, 9, 12, 0, 1, tzinfo=timezone.utc).timestamp()
    return produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": [_perp()]},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": "ETH-USDT-SWAP", "markPx": "100.5"}],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=observed,
        source_event_time=event_time,
    ).snapshot.to_dict()


def _marks() -> tuple[RawMarkCandleV1, ...]:
    rows: list[RawMarkCandleV1] = []
    for i in range(MINIMUM_FINALIZED_PT1M_MARKS):
        rows.append(
            RawMarkCandleV1(
                venue_native_id="ETH-USDT-SWAP",
                ts_ms=str(BASE_TS_MS + i * 60_000),
                mark_px=str(100 + i),
                confirm="1",
                receive_or_capture_timestamp=CAPTURE_TS,
            )
        )
    return tuple(rows)


def _economic_md_snapshot(universe: dict) -> dict:
    started = datetime(2026, 9, 12, 0, 0, 1, tzinfo=timezone.utc).timestamp()
    completed = datetime(2026, 9, 12, 0, 0, 20, tzinfo=timezone.utc).timestamp()
    source = InjectedEconomicMdPublicSourceV1(
        bundles={
            "ETH-USDT-SWAP": InstrumentPublicMdBundleV1(
                venue_native_id="ETH-USDT-SWAP",
                marks=_marks(),
                ticker=RawTickerQuoteV1(
                    venue_native_id="ETH-USDT-SWAP",
                    bid_px="100.1",
                    ask_px="100.3",
                    ticker_event_timestamp="1757635259000",
                    capture_or_receive_timestamp=CAPTURE_TS,
                ),
            )
        }
    )
    return produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe,
        public_md_source=source,
        collection_started_at_unix=started,
        collection_completed_at_unix=completed,
    ).snapshot.to_dict()


def test_valid_utc_15m_anchor_accepted_and_non_15m_rejected() -> None:
    assert parse_canonical_15m_anchor_utc(ANCHOR) == ANCHOR
    assert parse_canonical_15m_anchor_utc("2026-09-12T00:15:00Z") == "2026-09-12T00:15:00Z"
    assert canonical_path_key_for_anchor(ANCHOR) == "2026-09-12T000000Z"
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as invalid:
        parse_canonical_15m_anchor_utc("2026-09-12T00:07:00Z")
    assert invalid.value.failure_code == Code.INVALID_ANCHOR.value
    with pytest.raises(Cap22AppendOnlyPitPersistenceError):
        parse_canonical_15m_anchor_utc("2026-09-12T00:00:01Z")
    with pytest.raises(Cap22AppendOnlyPitPersistenceError):
        parse_canonical_15m_anchor_utc("2026-09-12T00:00:00+00:00")
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as missing:
        parse_canonical_15m_anchor_utc("")
    assert missing.value.failure_code == Code.EVENT_TIME_MISSING.value


def test_contract_flags_remain_fail_closed() -> None:
    assert CONTRACT_ID == "CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1"
    assert COLLECTION_CADENCE_ID == "PT1M_15_MINUTE_ANCHORS_V1"
    assert COLLECTION_NETWORK_AUTHORIZED is False
    assert COLLECTION_SCHEDULER_ENABLED is False
    assert PROSPECTIVE_COLLECTION_STARTED is False
    assert CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED is True
    assert CAP22_PROSPECTIVE_COLLECTION_STARTED is False
    assert CAP22_90D_EVIDENCE_CLOCK_STARTED is False
    assert CAP21_EXISTING_PRODUCER_AUTHORITY_PRESERVED is True
    assert CAP21_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED is True
    assert ECONOMIC_MD_EXISTING_PRODUCER_AUTHORITY_PRESERVED is True
    assert ECONOMIC_MD_APPEND_ONLY_AT_T_PERSISTENCE_IMPLEMENTED is True
    assert EXACT_T_BINDING_REQUIRED is True
    assert HISTORICAL_EVIDENCE_GENERATED is False
    assert FORWARD_LABEL_EXECUTION_IMPLEMENTED is False
    assert WALK_FORWARD_EXECUTION_IMPLEMENTED is False
    assert POLICY_RATIFICATION_JUSTIFIED is False
    assert ECONOMIC_RANK_ACTIVATED is False
    assert CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED is False
    assert PDF_STEP_5_STATUS == "UNRESOLVED"
    assert PDF_STEP_7_STATUS == "FORBIDDEN"
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert NEXT_CAP22_DEPENDENCY == (
        "SEPARATE_OWNER_GO_REQUIRED_FOR_PROSPECTIVE_15M_CAP21_AND_ECONOMIC_MD_COLLECTION"
    )
    assert AUTHORITY_EFFECT == "OFFLINE_APPEND_ONLY_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_ONLY"


def test_declaration_validator_accepts_bound_flags() -> None:
    result = validate_cap22_append_only_15m_pit_persistence_declaration_v1(_valid_payload())
    assert result["valid"] is True
    assert result["collection_cadence_id"] == COLLECTION_CADENCE_ID


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("collection_scheduler_enabled", True),
        ("collection_network_authorized", True),
        ("prospective_collection_started", True),
        ("cap22_prospective_collection_started", True),
        ("cap22_90d_evidence_clock_started", True),
        ("economic_rank_activated", True),
        ("runtime_authority_granted", True),
        ("historical_evidence_generated", True),
        ("walk_forward_execution_implemented", True),
        ("pdf_step_5_status", "CLOSED"),
        ("pdf_step_7_status", "ALLOWED"),
        ("collection_cadence_id", "PT5M"),
        ("append_only", False),
        ("exact_t_binding_required", False),
    ],
)
def test_declaration_validator_rejects_authority_leak(key: str, value: object) -> None:
    with pytest.raises(Cap22AppendOnlyPitPersistenceError):
        validate_cap22_append_only_15m_pit_persistence_declaration_v1(
            _valid_payload(**{key: value})
        )


def test_classifiers_preserve_non_activation() -> None:
    classified = classify_cap22_append_only_15m_pit_persistence_v1()
    assert classified["collection_scheduler_enabled"] is False
    assert classified["collection_network_authorized"] is False
    preserved = classify_preserved_program_invariants_v1()
    assert preserved["pdf_step_5_status"] == "UNRESOLVED"
    assert preserved["historical_evidence_generated"] is False
    assert preserved["next_cap22_dependency"].endswith("ECONOMIC_MD_COLLECTION")


def test_deterministic_path_and_cap21_idempotent_replay(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    first = persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    expected = canonical_cap21_path(tmp_path, ANCHOR)
    assert first.ok is True
    assert first.idempotent is False
    assert first.path == str(expected)
    assert expected.is_file()
    second = persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    assert second.idempotent is True
    assert second.payload_digest == first.payload_digest
    loaded = load_cap21_universe_at_t_v1(tmp_path, anchor=ANCHOR)
    assert loaded.payload_digest == first.payload_digest
    assert loaded.generated_at_event_time == ANCHOR
    assert loaded.snapshot_id == universe["snapshot_id"]


def test_cap21_event_time_mismatch_and_invalid_anchor_rejected(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as mismatch:
        persist_cap21_universe_at_t_v1(
            archive_root=tmp_path,
            anchor="2026-09-12T00:15:00Z",
            snapshot=universe,
        )
    assert mismatch.value.failure_code == Code.EVENT_TIME_MISMATCH.value
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as invalid:
        persist_cap21_universe_at_t_v1(
            archive_root=tmp_path,
            anchor="2026-09-12T00:01:00Z",
            snapshot=universe,
        )
    assert invalid.value.failure_code == Code.INVALID_ANCHOR.value


def test_conflicting_cap21_duplicate_fail_closed(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    conflicted = dict(universe)
    conflicted["snapshot_id"] = "other_snapshot"
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as exc:
        persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=conflicted)
    assert exc.value.failure_code in {
        Code.CONFLICTING_DUPLICATE.value,
        Code.DIGEST_OR_SCHEMA_ERROR.value,
    }
    loaded = load_cap21_universe_at_t_v1(tmp_path, anchor=ANCHOR)
    assert loaded.snapshot_id == universe["snapshot_id"]


def test_corrupted_cap21_digest_rejected(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    path = canonical_cap21_path(tmp_path, ANCHOR)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["payload_digest"] = "0" * 64
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as exc:
        load_cap21_universe_at_t_v1(tmp_path, anchor=ANCHOR)
    assert exc.value.failure_code in {
        Code.DIGEST_OR_SCHEMA_ERROR.value,
        Code.CORRUPT_PERSISTED_SNAPSHOT.value,
    }


def test_exact_t_binding_and_missing_cap21_rejected(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    economic = _economic_md_snapshot(universe)
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as missing:
        persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=economic)
    assert missing.value.failure_code == Code.MISSING_CAP21_BINDING.value
    persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    stored = persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=economic)
    assert stored.ok is True
    assert stored.idempotent is False
    assert Path(stored.path) == canonical_economic_md_path(tmp_path, ANCHOR)
    again = persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=economic)
    assert again.idempotent is True
    binding = bind_economic_md_to_cap21_at_exact_t_v1(tmp_path, anchor=ANCHOR)
    assert binding.anchor == ANCHOR
    assert binding.cap21_snapshot_id == universe["snapshot_id"]
    assert binding.cap21_payload_digest == universe["payload_digest"]
    assert binding.economic_md_payload_digest == economic["payload_digest"]


def test_economic_md_binding_mismatch_and_incomplete_snapshot_rejected(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    economic = _economic_md_snapshot(universe)
    broken_ref = dict(economic)
    reference = dict(broken_ref["universe_snapshot_reference"])
    reference["snapshot_id"] = "not-the-cap21-id"
    broken_ref["universe_snapshot_reference"] = reference
    broken_ref.pop("payload_digest", None)
    from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1

    rebound = EconomicMdInputSnapshotV1.from_dict(broken_ref).with_payload_digest()
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as mismatch:
        persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=rebound)
    assert mismatch.value.failure_code == Code.CAP21_BINDING_MISMATCH.value
    incomplete = dict(economic)
    incomplete["economic_input_snapshot_id"] = ""
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as incomplete_exc:
        persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=incomplete)
    assert incomplete_exc.value.failure_code in {
        Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT.value,
        Code.DIGEST_OR_SCHEMA_ERROR.value,
    }


def test_conflicting_economic_md_duplicate_fail_closed(tmp_path: Path) -> None:
    universe = _universe_snapshot()
    persist_cap21_universe_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=universe)
    economic = _economic_md_snapshot(universe)
    persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=economic)
    other = dict(economic)
    other["collection_cycle_identity"] = "other-cycle"
    from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1

    mutated = EconomicMdInputSnapshotV1.from_dict(other).with_payload_digest()
    with pytest.raises(Cap22AppendOnlyPitPersistenceError) as exc:
        persist_economic_md_at_t_v1(archive_root=tmp_path, anchor=ANCHOR, snapshot=mutated)
    assert exc.value.failure_code == Code.CONFLICTING_DUPLICATE.value


def test_latest_state_cap21_persistence_unchanged(tmp_path: Path) -> None:
    latest_root = tmp_path / "latest"
    archive_root = tmp_path / "archive"
    universe = _universe_snapshot()
    from src.ops.governed_futures_universe_producer_v1.models_v1 import (
        GovernedFuturesUniverseSnapshotV1,
    )

    snapshot = GovernedFuturesUniverseSnapshotV1.from_dict(universe)
    writer = GovernedUniverseSingleWriterV1(state_root=latest_root, session_id="latest")
    writer.acquire(now_unix=datetime(2026, 9, 12, 0, 1, tzinfo=timezone.utc).timestamp())
    persist_universe_bundle_atomic_v1(
        state_root=latest_root,
        writer=writer,
        snapshot=snapshot,
        evidence={"capability_id": snapshot.capability_id},
    )
    writer.release()
    assert (latest_root / SNAPSHOT_FILENAME).is_file()
    persist_cap21_universe_at_t_v1(archive_root=archive_root, anchor=ANCHOR, snapshot=universe)
    assert not (latest_root / "cap21_universe_at_t").exists()
    assert (latest_root / SNAPSHOT_FILENAME).is_file()
    assert canonical_cap21_path(archive_root, ANCHOR).is_file()
    assert SNAPSHOT_FILENAME == CAP21_SNAPSHOT_FILENAME


def test_package_has_no_network_scheduler_ranking_or_runtime_wire() -> None:
    combined = ""
    for path in PACKAGE.glob("*.py"):
        combined += path.read_text(encoding="utf-8")
    assert "www.okx.com" not in combined
    assert "/api/v5/" not in combined
    assert "urllib" not in combined
    assert "schedule" not in combined.lower() or "COLLECTION_SCHEDULER_ENABLED" in combined
    assert "src.ops.cap22_offline_mvr_evidence_harness_v1" not in combined
    assert "src.ops.productive_futures_ranking_producer_v1" not in combined
    assert "src.execution" not in combined
    assert "evaluate_challenger" not in combined
    assert "time.sleep" not in combined
    assert "Threading" not in combined
    assert COLLECTION_SCHEDULER_ENABLED is False
    assert COLLECTION_NETWORK_AUTHORIZED is False


def test_spec_and_runbook_persist_this_decision() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    time_spec = TIME_SPEC.read_text(encoding="utf-8")
    assert (
        _docs_token_marker(
            "DOCS_TOKEN_CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1"
        )
        in spec
    )
    assert "COLLECTION_CADENCE_ID=PT1M_15_MINUTE_ANCHORS_V1" in spec
    assert "COLLECTION_SCHEDULER_ENABLED=false" in spec
    assert "PROSPECTIVE_COLLECTION_STARTED=false" in spec
    assert "CAP22_90D_EVIDENCE_CLOCK_STARTED=false" in spec
    assert "### 4.5.13 Cap 2.2 append-only 15m PIT persistence" in runbook
    assert "CAP22_PROSPECTIVE_COLLECTION_CONTRACTS_IMPLEMENTED=true" in runbook
    assert "CAP22_PROSPECTIVE_COLLECTION_STARTED=false" in runbook
    assert (
        "SEPARATE_OWNER_GO_REQUIRED_FOR_PROSPECTIVE_15M_CAP21_AND_ECONOMIC_MD_COLLECTION" in runbook
    )
    assert "CAP22_APPEND_ONLY_15M_PIT_PERSISTENCE_AND_COLLECTION_CONTRACTS_V1.md" in mot
    assert "PT1M_15_MINUTE_ANCHORS_V1" in time_spec
    assert "ECONOMIC_RANK_ACTIVATED=true" not in spec
    source = (PACKAGE / "archive_v1.py").read_text(encoding="utf-8")
    assert "evaluate_challenger" not in source
