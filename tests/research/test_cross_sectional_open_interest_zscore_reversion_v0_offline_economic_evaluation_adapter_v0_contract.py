"""Contract tests for cross_sectional_open_interest_zscore_reversion/v0 offline evaluation adapter v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN,
    RUNTIME_EFFECT,
    adapter_result_to_dict,
    materialize_adapter_contract_v0,
    run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_execution_v0 import (
    ADAPTER_GO_TOKEN,
    CANONICAL_EVALUATION_CALLABLE,
    LoadedBoundOpenInterestPanelV0,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_EXPANDED_UNIVERSE,
    REASON_GO_TOKEN_INVALID,
    REASON_INSUFFICIENT_PANEL_HISTORY,
    REASON_NON_ALIGNED_PANEL,
    REASON_SUBSTITUTED_INSTRUMENT,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    load_bound_open_interest_panel_from_materialization_root_v0,
    run_offline_evaluation_adapter_precheck_v0,
    validate_bound_panel_contract_v0,
    verify_offline_and_go_gates_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0 import (
    RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    RATIFIED_PANEL_DATASET_DIGEST,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    OPEN_INTEREST_UNIT,
    compute_panel_open_interest_digest_v1,
    serialize_panel_bar_v1,
)
from src.research.okx_historical_open_interest_public_fetch_v0 import (
    compute_availability_time_utc_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_pit_semantics_contract_v0 import (
    SIGNAL_LAG_BARS,
    SOURCE_SCHEMA_VERSION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LATEST_PANEL_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_zscore_reversion_v0_historical_panel_depth_extension_"
    "and_rematerialization_implementation_v0_20260712T004937Z/materialization/run_a"
)
ADAPTER_MODULE = (
    REPO_ROOT
    / "src/research/cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_"
    "adapter_v0.py"
)
RUNNER_MODULE = (
    REPO_ROOT
    / "scripts/ops/run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_"
    "adapter_v0.py"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)

PANEL_TIMESTAMPS = (
    "2026-07-11T18:00:00Z",
    "2026-07-11T19:00:00Z",
    "2026-07-11T20:00:00Z",
    "2026-07-11T21:00:00Z",
    "2026-07-11T22:00:00Z",
    "2026-07-11T23:00:00Z",
)


def _make_bar(instrument_id: str, native_id: str, ts: str, oi: str = "1000.0") -> dict[str, object]:
    from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import PanelBarWithOpenInterestV1

    bar = PanelBarWithOpenInterestV1(
        instrument_id=instrument_id,
        native_instrument_id=native_id,
        timestamp_utc=ts,
        open_interest=oi,
        open_interest_unit=OPEN_INTEREST_UNIT,
        availability_time_utc=compute_availability_time_utc_v0(ts, signal_lag_bars=SIGNAL_LAG_BARS),
        is_final=True,
        data_quality_status="OK",
        stale_flag=False,
        missing_flag=False,
        universe_membership_status="ELIGIBLE",
        source_schema_version=SOURCE_SCHEMA_VERSION,
    )
    return serialize_panel_bar_v1(bar)


def _write_valid_panel_fixture(root: Path) -> Path:
    panel_dir = root / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for inst_id, native_id in CANONICAL_UNIVERSE_BINDING:
        for idx, ts in enumerate(PANEL_TIMESTAMPS):
            rows.append(_make_bar(inst_id, native_id, ts, oi=str(1000 + idx)))
    rows.sort(key=lambda row: (str(row["instrument_id"]), str(row["timestamp_utc"])))
    digest = compute_panel_open_interest_digest_v1(rows)
    (panel_dir / "normalized_panel_bars_with_open_interest.json").write_text(
        json.dumps({"bars": rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "pit_okx_pt1h_panel_open_interest_dataset_manifest_v1",
        "panel_id": "pit_okx_linear_usdt_non_bitcoin_self_accumulated_open_interest_panel",
        "dataset_id": "pit_okx_linear_usdt_non_bitcoin_self_accumulated_open_interest_panel/v0",
        "dataset_extension": "self_accumulated_forward_accrual_v0",
        "panel_dataset_schema": "pit_okx_pt1h_panel_open_interest_dataset_manifest_v1",
        "instrument_ids": [inst for inst, _ in CANONICAL_UNIVERSE_BINDING],
        "native_instrument_ids": [native for _, native in CANONICAL_UNIVERSE_BINDING],
        "panel_calendar_timestamps_utc": list(PANEL_TIMESTAMPS),
        "open_interest_panel_digest": digest,
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
        "row_count_total": len(rows),
    }
    (panel_dir / "panel_open_interest_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="valid_panel_root")
def fixture_valid_panel_root() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_oi_zscore_reversion_adapter_v0_"))
    return _write_valid_panel_fixture(tmp)


def test_exact_five_instrument_binding_accepted(
    complete_binding: dict,
) -> None:
    if not LATEST_PANEL_ROOT.is_dir():
        pytest.skip("latest panel evidence unavailable")
    result = run_offline_evaluation_adapter_precheck_v0(
        repo_root=REPO_ROOT,
        materialization_root=LATEST_PANEL_ROOT,
        go_token=ADAPTER_GO_TOKEN,
        versioned_binding=complete_binding,
    )
    assert result.precheck_passed is True
    assert result.instrument_count == 5


def test_substituted_instrument_rejected(valid_panel_root: Path) -> None:
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest=loaded.panel_dataset_digest,
        expected_universe_digest=loaded.instrument_universe_digest,
        expected_instrument_ids=[
            "okx:linear_perpetual:BTC:USDT:USDT:perp",
            *[inst for inst, _ in CANONICAL_UNIVERSE_BINDING[1:]],
        ],
    )
    assert ok is False
    assert REASON_SUBSTITUTED_INSTRUMENT in reasons or "INSTRUMENT_SET_MISMATCH" in reasons


def test_wrong_universe_digest_rejected(valid_panel_root: Path) -> None:
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest=loaded.panel_dataset_digest,
        expected_universe_digest="0" * 64,
    )
    assert ok is False
    assert REASON_UNIVERSE_DIGEST_MISMATCH in reasons


def test_wrong_dataset_digest_rejected(valid_panel_root: Path) -> None:
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest="0" * 64,
        expected_universe_digest=loaded.instrument_universe_digest,
    )
    assert ok is False
    assert REASON_DATASET_DIGEST_MISMATCH in reasons


def test_insufficient_panel_history_rejected(valid_panel_root: Path) -> None:
    panel_dir = valid_panel_root / "panel"
    manifest = json.loads(
        (panel_dir / "panel_open_interest_dataset_manifest.json").read_text(encoding="utf-8")
    )
    manifest["panel_calendar_timestamps_utc"] = list(PANEL_TIMESTAMPS[:3])
    (panel_dir / "panel_open_interest_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest=loaded.panel_dataset_digest,
        expected_universe_digest=loaded.instrument_universe_digest,
    )
    assert ok is False
    assert REASON_INSUFFICIENT_PANEL_HISTORY in reasons


def test_expanded_universe_rejected(valid_panel_root: Path) -> None:
    panel_dir = valid_panel_root / "panel"
    manifest = json.loads(
        (panel_dir / "panel_open_interest_dataset_manifest.json").read_text(encoding="utf-8")
    )
    manifest["instrument_ids"] = list(manifest["instrument_ids"]) + [
        "okx:linear_perpetual:BTC:USDT:USDT:perp"
    ]
    manifest["native_instrument_ids"] = list(manifest["native_instrument_ids"]) + ["BTC-USDT-SWAP"]
    (panel_dir / "panel_open_interest_dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    payload = json.loads(
        (panel_dir / "normalized_panel_bars_with_open_interest.json").read_text(encoding="utf-8")
    )
    for ts in PANEL_TIMESTAMPS:
        payload["bars"].append(
            _make_bar("okx:linear_perpetual:BTC:USDT:USDT:perp", "BTC-USDT-SWAP", ts, "500.0")
        )
    payload["bars"].sort(key=lambda row: (str(row["instrument_id"]), str(row["timestamp_utc"])))
    (panel_dir / "normalized_panel_bars_with_open_interest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest=loaded.panel_dataset_digest,
        expected_universe_digest=loaded.instrument_universe_digest,
    )
    assert ok is False
    assert REASON_EXPANDED_UNIVERSE in reasons


def test_non_aligned_panel_rejected(valid_panel_root: Path) -> None:
    panel_dir = valid_panel_root / "panel"
    payload = json.loads(
        (panel_dir / "normalized_panel_bars_with_open_interest.json").read_text(encoding="utf-8")
    )
    payload["bars"] = [
        row
        for row in payload["bars"]
        if not (
            row["instrument_id"] == CANONICAL_UNIVERSE_BINDING[0][0]
            and row["timestamp_utc"] == PANEL_TIMESTAMPS[-1]
        )
    ]
    (panel_dir / "normalized_panel_bars_with_open_interest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    loaded = load_bound_open_interest_panel_from_materialization_root_v0(valid_panel_root)
    ok, reasons = validate_bound_panel_contract_v0(
        loaded_panel=loaded,
        expected_panel_dataset_digest=loaded.panel_dataset_digest,
        expected_universe_digest=loaded.instrument_universe_digest,
    )
    assert ok is False
    assert REASON_NON_ALIGNED_PANEL in reasons


def test_canonical_callable_invoked_once(
    complete_binding: dict,
    valid_panel_root: Path,
) -> None:
    with patch(
        "src.research.cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0.run_offline_evaluation_adapter_precheck_v0",
        wraps=run_offline_evaluation_adapter_precheck_v0,
    ) as mocked:
        run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0(
            repo_root=REPO_ROOT,
            materialization_root=valid_panel_root,
            evidence_root=valid_panel_root / "evidence",
            go_token=ADAPTER_GO_TOKEN,
            versioned_binding=complete_binding,
        )
        mocked.assert_called_once()


def test_offline_gate_required() -> None:
    ok, reasons = verify_offline_and_go_gates_v0(
        go_token=ADAPTER_GO_TOKEN,
        offline_only=False,
    )
    assert ok is False
    assert "OFFLINE_GATE_VIOLATION" in reasons


def test_explicit_go_required() -> None:
    ok, reasons = verify_offline_and_go_gates_v0(go_token="INVALID_GO")
    assert ok is False
    assert REASON_GO_TOKEN_INVALID in reasons


def test_no_runtime_import_boundary() -> None:
    for path in (ADAPTER_MODULE, RUNNER_MODULE):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_IMPORT_PREFIXES:
            assert token not in source


def test_no_order_adapter_import_boundary() -> None:
    source = ADAPTER_MODULE.read_text(encoding="utf-8")
    for token in ("order_adapter", "src.orders", "src.trading.orders"):
        assert token not in source


def test_no_scheduler_import_boundary() -> None:
    source = ADAPTER_MODULE.read_text(encoding="utf-8")
    assert "src.scheduler" not in source


def test_no_economic_execution_in_implementation_scope(
    complete_binding: dict,
    valid_panel_root: Path,
) -> None:
    result = run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0(
        repo_root=REPO_ROOT,
        materialization_root=valid_panel_root,
        evidence_root=valid_panel_root / "evidence2",
        go_token=ADAPTER_GO_TOKEN,
        versioned_binding=complete_binding,
    )
    assert result.economic_evaluation_executed is False
    assert result.precheck.economic_evaluation_executed is False
    payload = adapter_result_to_dict(result)
    assert payload["economic_evaluation_executed"] is False


def test_deterministic_adapter_binding(
    complete_binding: dict,
    valid_panel_root: Path,
) -> None:
    first = run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0(
        repo_root=REPO_ROOT,
        materialization_root=valid_panel_root,
        evidence_root=valid_panel_root / "evidence3a",
        go_token=ADAPTER_GO_TOKEN,
        versioned_binding=complete_binding,
    )
    second = run_cross_sectional_open_interest_zscore_reversion_v0_offline_economic_evaluation_adapter_v0(
        repo_root=REPO_ROOT,
        materialization_root=valid_panel_root,
        evidence_root=valid_panel_root / "evidence3b",
        go_token=ADAPTER_GO_TOKEN,
        versioned_binding=complete_binding,
    )
    assert first.adapter_digest == second.adapter_digest


def test_authority_effect_none() -> None:
    assert AUTHORITY_EFFECT == "NONE"


def test_runtime_effect_none() -> None:
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_hypothesis_binding_v0()
    assert result.validation_verdict.value == "ACCEPTED_COMPLETE"


def test_go_token_constant() -> None:
    assert GO_TOKEN == ADAPTER_GO_TOKEN


def test_canonical_callable_constant() -> None:
    assert CANONICAL_EVALUATION_CALLABLE == "run_offline_evaluation_adapter_precheck_v0"


def test_adapter_contract_materialization() -> None:
    contract = materialize_adapter_contract_v0()
    assert contract["economic_evaluation_executed"] is False
    assert contract["offline_only"] is True


@pytest.mark.skipif(not LATEST_PANEL_ROOT.is_dir(), reason="latest panel evidence unavailable")
def test_latest_execution_panel_accepted(complete_binding: dict) -> None:
    result = run_offline_evaluation_adapter_precheck_v0(
        repo_root=REPO_ROOT,
        materialization_root=LATEST_PANEL_ROOT,
        go_token=ADAPTER_GO_TOKEN,
        versioned_binding=complete_binding,
    )
    assert result.precheck_passed is True
    assert result.panel_dataset_digest == RATIFIED_PANEL_DATASET_DIGEST
    assert result.instrument_universe_digest == RATIFIED_INSTRUMENT_UNIVERSE_DIGEST
