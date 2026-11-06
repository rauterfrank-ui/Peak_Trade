"""Focused contract tests for OKX history-depth probe (mocked network)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.longer_chronological_pit_acquisition_v1 import (
    ENV_ARCHIVE_ROOT,
    TARGET_PERIOD_START,
)
from src.research.longer_chronological_pit_acquisition_v1.history_depth_probe import (
    AuthRequiredError,
    HistoryDepthProbeError,
    NetworkProbeDisabledError,
    RequestBudget,
    RequestBudgetExceeded,
    SchemaDriftError,
    default_probe_universe_sample,
    evaluate_lifecycle_clipping,
    evaluate_three_year_depth,
    parse_history_candles_payload,
    run_history_depth_probe,
    select_probe_instruments,
)
from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
    InstrumentLifecycleV1,
    PartitionPlanError,
)


def _candle_body(timestamps: list[int]) -> bytes:
    rows = [[str(ts), "1", "2", "0.5", "1.5", "10", "10", "10", "1"] for ts in timestamps]
    return json.dumps({"code": "0", "msg": "", "data": rows}).encode("utf-8")


def test_request_budget_fail_closed() -> None:
    budget = RequestBudget(2)
    budget.consume(1)
    budget.consume(1)
    with pytest.raises(RequestBudgetExceeded):
        budget.consume(1)


def test_network_disabled_without_explicit_freigabe() -> None:
    with pytest.raises(HistoryDepthProbeError, match="REQUEST_BUDGET_REQUIRED"):
        run_history_depth_probe(allow_network_probe=True, request_budget=None)

    summary = run_history_depth_probe(allow_network_probe=False)
    assert summary["network_probe_executed"] is False
    assert summary["requests_used"] == 0
    assert all(r["status"] == "DRY_RUN_NO_NETWORK" for r in summary["instrument_results"])


def test_write_disabled_without_explicit_freigabe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    summary = run_history_depth_probe(allow_write_probe=False, archive_root=None)
    assert summary["allow_write_probe"] is False
    assert summary["written_artifacts"] == {}

    with pytest.raises(Exception, match="MISSING_"):
        run_history_depth_probe(
            allow_write_probe=True,
            archive_root=None,
            env={},
        )


def test_external_archive_root_required_for_write(tmp_path: Path) -> None:
    root = tmp_path / "ext_probe_archive"
    root.mkdir()
    calls: list[str] = []

    def fetcher(url: str) -> bytes:
        calls.append(url)
        # newest then older pages
        if "after=" not in url:
            return _candle_body([1_725_000_000_000, 1_724_996_400_000])
        after = int(url.split("after=")[1].split("&")[0])
        if after > 1_630_000_000_000:
            return _candle_body([1_630_454_400_000, 1_630_450_800_000])
        if after > 1_575_000_000_000:
            return _candle_body([1_575_158_400_000, 1_575_162_000_000])
        return _candle_body([])

    summary = run_history_depth_probe(
        default_probe_universe_sample()[:3],
        allow_network_probe=True,
        allow_write_probe=True,
        request_budget=25,
        archive_root=root,
        max_instruments=2,
        fetcher=fetcher,
        sleep=lambda _s: None,
        backoff_seconds=0.0,
    )
    assert summary["written_artifacts"]
    assert "history_depth_probe_manifest.json" in summary["external_artifact_hashes"]
    assert "resume_state.json" in summary["external_artifact_hashes"]
    # nothing under repo
    repo = Path(__file__).resolve().parents[2]
    assert not (repo / "longer_chronological_pit").exists()


def test_btc_and_spot_excluded_from_probe_sample() -> None:
    mixed = default_probe_universe_sample() + [
        InstrumentLifecycleV1(
            instrument_id="okx:linear_perpetual:BTC:USDT:USDT:perp",
            native_instrument_id="BTC-USDT-SWAP",
            base_asset="BTC",
            quote_asset="USDT",
            market_type="linear_usdt_perpetual",
            listing_time="2019-01-01T00:00:00Z",
            delisting_time=None,
        ),
        InstrumentLifecycleV1(
            instrument_id="okx:spot:ETH:USDT",
            native_instrument_id="ETH-USDT",
            base_asset="ETH",
            quote_asset="USDT",
            market_type="spot",
            listing_time="2019-01-01T00:00:00Z",
            delisting_time=None,
        ),
    ]
    sel = select_probe_instruments(mixed, max_instruments=5, seed=0)
    natives = sel["native_ids"]
    assert all("BTC" not in n for n in natives)
    assert all(n.endswith("-SWAP") for n in natives)
    assert any(e["reason"].startswith("BTC_EXCLUDED") for e in sel["excluded"])
    assert any(e["reason"].startswith("SPOT_EXCLUDED") for e in sel["excluded"])


def test_deterministic_sample_selection() -> None:
    a = select_probe_instruments(default_probe_universe_sample(), max_instruments=5, seed=0)
    b = select_probe_instruments(default_probe_universe_sample(), max_instruments=5, seed=0)
    assert a["native_ids"] == b["native_ids"]
    assert a["roles"] == b["roles"]
    assert len(a["native_ids"]) <= 5
    assert "ETH-USDT-SWAP" in a["native_ids"]  # oldest


def test_pagination_end_condition() -> None:
    pages = {
        "latest": _candle_body([1_725_000_000_000]),
        "empty": _candle_body([]),
    }

    def fetcher(url: str) -> bytes:
        if "after=" not in url:
            return pages["latest"]
        return pages["empty"]

    summary = run_history_depth_probe(
        [
            InstrumentLifecycleV1(
                instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
                native_instrument_id="ETH-USDT-SWAP",
                base_asset="ETH",
                quote_asset="USDT",
                market_type="linear_usdt_perpetual",
                listing_time="2019-12-01T00:00:00Z",
                delisting_time=None,
            )
        ],
        allow_network_probe=True,
        request_budget=10,
        max_instruments=1,
        fetcher=fetcher,
        sleep=lambda _s: None,
        backoff_seconds=0.0,
    )
    result = summary["instrument_results"][0]
    assert result["pagination_end_reached"] is True


def test_lifecycle_clipping_evaluation() -> None:
    listing_ms = 1_600_000_000_000
    good = evaluate_lifecycle_clipping(
        earliest_ms=listing_ms + 3_600_000,
        listing_ms=listing_ms,
        delisting_ms=None,
        latest_ms=listing_ms + 10_000_000,
        planned_start="2021-09-01T00:00:00Z",
        planned_end="2021-10-01T00:00:00Z",
    )
    assert good["valid"] is True

    bad = evaluate_lifecycle_clipping(
        earliest_ms=listing_ms - 10_000_000,
        listing_ms=listing_ms,
        delisting_ms=None,
        latest_ms=listing_ms + 10_000_000,
        planned_start="2020-01-01T00:00:00Z",
        planned_end="2020-02-01T00:00:00Z",
    )
    assert bad["valid"] is False
    assert "PUBLIC_HISTORY_BEFORE_LISTING" in bad["reasons"]


def test_timeout_retry_bounds() -> None:
    attempts = {"n": 0}

    def flaky(_url: str) -> bytes:
        attempts["n"] += 1
        raise HistoryDepthProbeError("RATE_LIMIT_HTTP_429")

    sleeps: list[float] = []
    summary = run_history_depth_probe(
        default_probe_universe_sample()[:1],
        allow_network_probe=True,
        request_budget=5,
        max_instruments=1,
        fetcher=flaky,
        max_retries=2,
        backoff_seconds=0.01,
        sleep=lambda s: sleeps.append(s),
    )
    # 1 initial + 2 retries = 3 attempts for the first GET
    assert attempts["n"] == 3
    assert len(sleeps) >= 2
    assert summary["instrument_results"][0]["status"] == "FAILED"
    assert "FETCH_FAILED" in str(summary["instrument_results"][0].get("error", ""))


def test_schema_drift_fail_closed() -> None:
    with pytest.raises(SchemaDriftError):
        parse_history_candles_payload(b'{"code":"0","data":"nope"}')
    with pytest.raises(SchemaDriftError):
        parse_history_candles_payload(b'{"code":"0","data":[["x","1","2","3","4"]]}')
    with pytest.raises(AuthRequiredError):
        parse_history_candles_payload(b'{"code":"50111","msg":"Invalid API key","data":[]}')


def test_three_year_depth_classification() -> None:
    target = int(
        __import__("datetime")
        .datetime(2021, 9, 1, tzinfo=__import__("datetime").timezone.utc)
        .timestamp()
        * 1000
    )
    assert (
        evaluate_three_year_depth(
            earliest_ms=target - 1000,
            listing_ms=target - 10_000_000,
            target_start_ms=target,
            pagination_exhausted=True,
        )
        == "YES"
    )
    assert (
        evaluate_three_year_depth(
            earliest_ms=target + 10_000_000,
            listing_ms=target - 10_000_000,
            target_start_ms=target,
            pagination_exhausted=True,
        )
        == "NO"
    )
    assert (
        evaluate_three_year_depth(
            earliest_ms=target + 10_000_000,
            listing_ms=target - 10_000_000,
            target_start_ms=target,
            pagination_exhausted=False,
        )
        == "INCONCLUSIVE"
    )


def test_no_archive_files_in_git_tree_after_probe(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    before = {p for p in repo.rglob("history_depth_probe_summary.json")}
    root = tmp_path / "archive_only"
    root.mkdir()

    def fetcher(url: str) -> bytes:
        if "after=" not in url:
            return _candle_body([1_700_000_000_000])
        return _candle_body([])

    run_history_depth_probe(
        default_probe_universe_sample()[:1],
        allow_network_probe=True,
        allow_write_probe=True,
        request_budget=10,
        archive_root=root,
        max_instruments=1,
        fetcher=fetcher,
        sleep=lambda _s: None,
        backoff_seconds=0.0,
    )
    after = {p for p in repo.rglob("history_depth_probe_summary.json")}
    assert before == after
    assert list((root / "longer_chronological_pit").rglob("*.json"))


def test_cli_history_depth_probe_default_no_network(capsys: pytest.CaptureFixture[str]) -> None:
    from src.research.longer_chronological_pit_acquisition_v1.cli import main

    rc = main(["history-depth-probe", "--max-instruments", "2"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["network_probe_executed"] is False
    assert out["credentials_used"] is False
    assert out["mass_download_started"] is False
    assert out["economic_gate_opened"] is False


def test_network_probe_disabled_error_on_client() -> None:
    from src.research.longer_chronological_pit_acquisition_v1.history_depth_probe import (
        ProbeHttpClient,
    )

    client = ProbeHttpClient(allow_network=False, budget=RequestBudget(5))
    with pytest.raises(NetworkProbeDisabledError):
        client.get("https://www.okx.com/api/v5/market/history-candles?instId=ETH-USDT-SWAP&bar=1H")


def test_btc_raises_in_planner_still() -> None:
    from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
        plan_partitions_for_instrument,
    )

    with pytest.raises(PartitionPlanError, match="BTC_EXCLUDED"):
        plan_partitions_for_instrument(
            InstrumentLifecycleV1(
                instrument_id="x",
                native_instrument_id="BTC-USDT-SWAP",
                base_asset="BTC",
                quote_asset="USDT",
                market_type="linear_usdt_perpetual",
                listing_time="2020-01-01T00:00:00Z",
                delisting_time=None,
            )
        )


def test_target_period_constant_aligned() -> None:
    assert TARGET_PERIOD_START == "2021-09-01T00:00:00Z"
