"""CURRENT_PRODUCTIVE G17 typed-vol mark-history checkpoint lifecycle tests."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
    ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    FullCoreG17Pt1mMarkIngestFieldsV1,
    extract_full_core_g17_pt1m_mark_ingest_fields_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    ARTIFACT_ID,
    CHECKPOINT_FILENAME,
    CHECKPOINT_OWNER,
    CHECKPOINT_PER_RUN_DIRNAME,
    CMC_BINDING_PERFORMED,
    DISPOSITION_FAIL_CLOSED_CORRUPT,
    DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH,
    DISPOSITION_MISSING_CREATED,
    DISPOSITION_RESTORED,
    ECONOMIC_MD_OWNER,
    ESTIMATE_REMATERIALIZED_ON_RESTORE,
    GLOBAL_SINGLETON,
    HARDENING_SESSION_OWNER,
    PACKAGE_MARKER,
    PRESENCE_GATE_MUTATED,
    SIDESTATE_CURSOR_OWNER,
    apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1,
    assert_checkpoint_is_sibling_to_sidestate_cursor_v1,
    current_productive_g17_checkpoint_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
)
from trading.master_v2.canonical_volatility_runtime_mark_history_v1 import (
    HISTORY_SCHEMA_VERSION,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    V5_HOST,
)
from tests.trading.master_v2.test_canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    test_duplicate_noop_preserves_history_and_estimate_digests,
    test_gap_exceeds_pt1m_rejects_estimate,
    test_out_of_order_rejected_fail_closed,
    test_produced_exactly_61_prices_matches_materializer_fixture,
    test_warmup_exactly_60_prices_no_estimate,
)

REPO = Path(__file__).resolve().parents[2]
CHECKPOINT_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_typed_vol_mark_history_checkpoint_v1.py"
)
ADAPTER_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_pt1m_mark_sample_adapter_v1.py"
)
BASE_TS_MS = 1_700_000_000_000
CAPTURE_TS = "1700000061000"
CANON = "BTC-USDT-SWAP-CANON"
NATIVE = "BTC-USDT-SWAP"
VENUE = DEFAULT_VENUE


def _mark_row(index: int, *, confirm: str = "1", px: str | None = None) -> list[str]:
    ts = str(BASE_TS_MS + index * 60_000)
    price = px if px is not None else str(100 + index)
    return [ts, price, price, price, price, confirm]


def _sixty_one_samples(
    *,
    canonical_instrument_id: str = CANON,
    venue_instrument_id: str = NATIVE,
) -> tuple[FullCoreG17Pt1mMarkIngestFieldsV1, ...]:
    rows = list(reversed([_mark_row(i) for i in range(61)]))
    extracted = extract_full_core_g17_pt1m_mark_ingest_fields_v1(
        {"code": "0", "msg": "", "data": rows},
        venue=VENUE,
        canonical_instrument_id=canonical_instrument_id,
        venue_instrument_id=venue_instrument_id,
        receive_or_capture_timestamp=CAPTURE_TS,
        source_endpoint=ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
    )
    assert len(extracted.samples) == 61
    return extracted.samples


def _apply(tmp_path: Path, samples=(), **kwargs):
    return apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1(
        store_root=tmp_path,
        venue=kwargs.get("venue", VENUE),
        canonical_instrument_id=kwargs.get("canonical_instrument_id", CANON),
        venue_instrument_id=kwargs.get("venue_instrument_id", NATIVE),
        samples=samples,
        extra_persist_roots=kwargs.get("extra_persist_roots", ()),
    )


def test_package_marker_and_authority_non_transfer() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert ARTIFACT_ID == "CURRENT_PRODUCTIVE_G17_TYPED_VOL_MARK_HISTORY_CHECKPOINT_V1"
    assert CHECKPOINT_OWNER.endswith("current_productive_g17_typed_vol_mark_history_checkpoint_v1")
    assert CMC_BINDING_PERFORMED is False
    assert PRESENCE_GATE_MUTATED is False
    assert HARDENING_SESSION_OWNER is False
    assert SIDESTATE_CURSOR_OWNER is False
    assert ECONOMIC_MD_OWNER is False
    assert GLOBAL_SINGLETON is False
    assert ESTIMATE_REMATERIALIZED_ON_RESTORE is False
    assert VENUE == "OKX"


def test_checkpoint_path_is_sibling_to_sidestate_cursor() -> None:
    assert_checkpoint_is_sibling_to_sidestate_cursor_v1()
    assert CHECKPOINT_FILENAME != CURSOR_FILENAME
    assert CHECKPOINT_PER_RUN_DIRNAME != "cursor"
    assert CHECKPOINT_FILENAME.endswith(".json")
    v5 = V5_HOST.read_text(encoding="utf-8")
    assert "CURRENT_G17_CHECKPOINT_STORE_RELPATH" in v5
    assert "CURRENT_CURSOR_STORE_RELPATH" in v5
    assert CHECKPOINT_FILENAME not in CURSOR_FILENAME
    cursor_src = (
        REPO
        / "src/ops/full_core_live_path_composition_root_v1"
        / "current_productive_sidestate_confirmation_cursor_v1.py"
    ).read_text(encoding="utf-8")
    assert CHECKPOINT_FILENAME not in cursor_src
    assert "g17_typed_vol_mark_history" not in cursor_src


def test_missing_creates_empty_host_ingests_61_and_produces(tmp_path: Path) -> None:
    samples = _sixty_one_samples()
    result = _apply(tmp_path, samples=samples)
    path = current_productive_g17_checkpoint_path_v1(tmp_path)
    assert result.disposition == DISPOSITION_MISSING_CREATED
    assert result.fail_closed is False
    assert result.last_outcome == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    assert result.observation_count_prices == 61
    assert result.estimate_present is True
    assert path.is_file()
    assert result.history_digest
    digest = result.history_digest
    again = _apply(tmp_path, samples=())
    assert again.history_digest == digest
    assert again.observation_count_prices == 61


def test_restore_history_without_estimate(tmp_path: Path) -> None:
    samples = _sixty_one_samples()
    created = _apply(tmp_path, samples=samples)
    restored = _apply(tmp_path, samples=())
    assert restored.disposition == DISPOSITION_RESTORED
    assert restored.fail_closed is False
    assert restored.history_digest == created.history_digest
    assert restored.observation_count_prices == 61
    assert restored.estimate_present is False
    assert restored.producer is not None
    assert restored.producer.output_port_v1().estimate is None
    assert restored.producer.history.acceptance_state is not None
    assert restored.producer.history.last_accepted_event_time is not None


def test_restore_duplicate_last_sample_is_canonical_noop(tmp_path: Path) -> None:
    samples = _sixty_one_samples()
    created = _apply(tmp_path, samples=samples)
    restored = _apply(tmp_path, samples=(samples[-1],))
    assert restored.disposition == DISPOSITION_RESTORED
    assert restored.last_outcome == TypedRuntimeProducerOutcomeV1.DUPLICATE_NOOP.value
    assert restored.history_digest == created.history_digest
    assert restored.observation_count_prices == 61
    assert restored.estimate_present is False


def test_restore_newer_distinct_advances_and_persists(tmp_path: Path) -> None:
    samples = _sixty_one_samples()
    created = _apply(tmp_path, samples=samples)
    newer = FullCoreG17Pt1mMarkIngestFieldsV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
        event_time_unix_seconds=samples[-1].event_time_unix_seconds + 60.0,
        mark_price=float(samples[-1].mark_price) + 1.0,
        is_final=True,
    )
    advanced = _apply(tmp_path, samples=(newer,))
    assert advanced.disposition == DISPOSITION_RESTORED
    assert advanced.last_outcome == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    assert advanced.observation_count_prices == 62
    assert advanced.history_digest != created.history_digest
    assert Path(advanced.persistence_path).is_file()


def test_corrupt_json_fail_closed_no_empty_create_or_rewrite(tmp_path: Path) -> None:
    path = current_productive_g17_checkpoint_path_v1(tmp_path)
    path.write_text("{not-json", encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    result = _apply(tmp_path, samples=_sixty_one_samples())
    assert result.disposition == DISPOSITION_FAIL_CLOSED_CORRUPT
    assert result.fail_closed is True
    assert result.producer is None
    assert path.read_text(encoding="utf-8") == before
    assert "{not-json" in before


def test_incompatible_schema_fail_closed_no_rewrite(tmp_path: Path) -> None:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    path = Path(created.persistence_path)
    text = path.read_text(encoding="utf-8")
    mutated = text.replace(
        HISTORY_SCHEMA_VERSION,
        "canonical_volatility_runtime_mark_history/v0-incompatible",
        1,
    )
    path.write_text(mutated, encoding="utf-8")
    result = _apply(tmp_path, samples=())
    assert result.disposition == DISPOSITION_FAIL_CLOSED_CORRUPT
    assert result.fail_closed is True
    assert result.producer is None
    assert path.read_text(encoding="utf-8") == mutated


def test_restored_identity_mismatch_fail_closed(tmp_path: Path) -> None:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    path = Path(created.persistence_path)
    before = path.read_text(encoding="utf-8")
    result = _apply(
        tmp_path,
        samples=(),
        canonical_instrument_id="ETH-USDT-SWAP-CANON",
        venue_instrument_id="ETH-USDT-SWAP",
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED_IDENTITY_MISMATCH
    assert result.fail_closed is True
    assert result.producer is None
    assert path.read_text(encoding="utf-8") == before


def test_extra_persist_root_mirrors_after_distinct(tmp_path: Path) -> None:
    extra = tmp_path / "standing"
    result = _apply(
        tmp_path / "per_run",
        samples=_sixty_one_samples(),
        extra_persist_roots=(extra,),
    )
    assert result.fail_closed is False
    extra_path = current_productive_g17_checkpoint_path_v1(extra)
    assert extra_path.is_file()
    assert extra_path.read_text(encoding="utf-8") == Path(result.persistence_path).read_text(
        encoding="utf-8"
    )


def test_v5_has_no_inline_ingest_missing_gate_or_cmc_bind() -> None:
    host = V5_HOST.read_text(encoding="utf-8")
    assert "ingest_finalized_pt1m_mark_sample_v1" not in host
    assert 'missing.append("G17' not in host
    assert "bind_typed_canonical_volatility_estimate" not in host
    assert "apply_current_productive_g17_typed_vol_mark_history_checkpoint_v1" in host
    assert "CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1" not in host
    adapter = ADAPTER_SRC.read_text(encoding="utf-8")
    assert "TYPED_VOL_HOST_PERSISTENCE_PERFORMED = False" in adapter
    checkpoint = CHECKPOINT_SRC.read_text(encoding="utf-8")
    assert "HardenedBridgeSessionStateV2" not in checkpoint
    assert "evaluate_double_play_runtime_typed_volatility_presence_gate_v1" not in checkpoint
    assert "run_economic_md_input_producer_v1" not in checkpoint


def test_reuse_existing_g17_warmup_produced_duplicate_out_of_order_and_gap() -> None:
    test_warmup_exactly_60_prices_no_estimate()
    test_produced_exactly_61_prices_matches_materializer_fixture()
    test_duplicate_noop_preserves_history_and_estimate_digests()
    test_out_of_order_rejected_fail_closed()
    test_gap_exceeds_pt1m_rejects_estimate()
