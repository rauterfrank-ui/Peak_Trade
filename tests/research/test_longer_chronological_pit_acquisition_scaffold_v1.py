"""Focused tests for longer chronological PIT acquisition scaffold v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    ENV_ARCHIVE_ROOT,
    MANIFEST_SCHEMA_VERSION,
)
from src.research.longer_chronological_pit_acquisition_v1.adapter import (
    NetworkDisabledError,
    OkxPublicHistoryAdapterV1,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    resolve_archive_root,
    validate_archive_root,
)
from src.research.longer_chronological_pit_acquisition_v1.manifest import (
    build_acquisition_manifest,
    build_partition_manifest_row,
    manifest_digest,
    write_manifest_atomic,
)
from src.research.longer_chronological_pit_acquisition_v1.partition_planner import (
    InstrumentLifecycleV1,
    PartitionPlanError,
    partition_id_for,
    plan_partitions,
    plan_partitions_for_instrument,
)
from src.research.longer_chronological_pit_acquisition_v1.qualification import (
    run_qualification_dry_run,
)
from src.research.longer_chronological_pit_acquisition_v1.resume_state import (
    StateTransitionError,
    assert_transition,
    new_state_store,
    should_skip_verified,
    transition,
    write_immutable_partition_bytes,
)

ETH = InstrumentLifecycleV1(
    instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp",
    native_instrument_id="ETH-USDT-SWAP",
    base_asset="ETH",
    quote_asset="USDT",
    market_type="linear_usdt_perpetual",
    listing_time="2021-01-01T00:00:00Z",
    delisting_time=None,
    state="KNOWN",
)


def test_missing_archive_root_blocks_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    with pytest.raises(ArchiveRootError, match="MISSING_"):
        resolve_archive_root(require_for_write=True)
    # read-only plan ok without root
    assert resolve_archive_root(require_for_write=False) is None


def test_repo_path_as_archive_root_blocked(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    with pytest.raises(ArchiveRootError, match="INSIDE_GIT_REPO"):
        validate_archive_root(repo)
    with pytest.raises(ArchiveRootError, match="FILESYSTEM_ROOT"):
        validate_archive_root(Path("/"))
    with pytest.raises(ArchiveRootError, match="HOME"):
        validate_archive_root(Path.home())


def test_btc_and_spot_excluded() -> None:
    btc = InstrumentLifecycleV1(
        instrument_id="okx:linear_perpetual:BTC:USDT:USDT:perp",
        native_instrument_id="BTC-USDT-SWAP",
        base_asset="BTC",
        quote_asset="USDT",
        market_type="linear_usdt_perpetual",
        listing_time="2020-01-01T00:00:00Z",
        delisting_time=None,
    )
    spot = InstrumentLifecycleV1(
        instrument_id="okx:spot:ETH:USDT",
        native_instrument_id="ETH-USDT",
        base_asset="ETH",
        quote_asset="USDT",
        market_type="spot",
        listing_time="2020-01-01T00:00:00Z",
        delisting_time=None,
    )
    with pytest.raises(PartitionPlanError, match="BTC_EXCLUDED"):
        plan_partitions_for_instrument(btc)
    with pytest.raises(PartitionPlanError, match="SPOT_EXCLUDED"):
        plan_partitions_for_instrument(spot)


def test_partitions_respect_listing_delisting() -> None:
    inst = InstrumentLifecycleV1(
        instrument_id="okx:linear_perpetual:AAA:USDT:USDT:perp",
        native_instrument_id="AAA-USDT-SWAP",
        base_asset="AAA",
        quote_asset="USDT",
        market_type="linear_usdt_perpetual",
        listing_time="2022-03-15T00:00:00Z",
        delisting_time="2022-05-10T00:00:00Z",
        state="KNOWN",
    )
    rows = plan_partitions_for_instrument(
        inst,
        period_start="2022-01-01T00:00:00Z",
        period_end="2022-07-01T00:00:00Z",
    )
    assert rows
    assert all(r["period_start"] >= "2022-03-15T00:00:00Z" for r in rows)
    assert all(r["period_end"] <= "2022-05-10T00:00:00Z" for r in rows)
    # no January/February or June partitions
    assert not any(r["period_start"].startswith("2022-01") for r in rows)
    assert not any(r["period_start"].startswith("2022-06") for r in rows)


def test_stable_partition_ids() -> None:
    a = partition_id_for(
        instrument_id=ETH.instrument_id,
        period_start="2021-09-01T00:00:00Z",
        period_end="2021-10-01T00:00:00Z",
    )
    b = partition_id_for(
        instrument_id=ETH.instrument_id,
        period_start="2021-09-01T00:00:00Z",
        period_end="2021-10-01T00:00:00Z",
    )
    assert a == b


def test_deterministic_manifest() -> None:
    plan = plan_partitions(
        [ETH],
        period_start="2021-09-01T00:00:00Z",
        period_end="2021-11-01T00:00:00Z",
    )
    m1 = build_acquisition_manifest(plan["partitions"], created_at="2026-07-20T00:00:00Z")
    m2 = build_acquisition_manifest(plan["partitions"], created_at="2026-07-20T00:00:00Z")
    assert m1["manifest_digest"] == m2["manifest_digest"]
    assert m1["manifest_digest"] == manifest_digest(m1)
    assert m1["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert m1["dataset_id"] == DATASET_ID


def test_no_overwrite_immutable_partition(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    write_immutable_partition_bytes(
        archive_root=root, relative_path="raw/x/p1.json", payload=b"abc"
    )
    with pytest.raises(ArchiveRootError, match="NO_OVERWRITE"):
        write_immutable_partition_bytes(
            archive_root=root, relative_path="raw/x/p1.json", payload=b"def"
        )


def test_state_transitions_allowed_and_forbidden() -> None:
    assert_transition("PLANNED", "DISCOVERED")
    with pytest.raises(StateTransitionError):
        assert_transition("PLANNED", "QUALIFIED")
    store = new_state_store()
    transition(store, "p1", "DISCOVERED")
    transition(store, "p1", "ACQUIRING")
    transition(store, "p1", "ACQUIRED")
    transition(store, "p1", "CHECKSUM_VERIFIED")
    assert should_skip_verified(store, "p1") is True


def test_dry_run_creates_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ARCHIVE_ROOT, raising=False)
    before = set(tmp_path.rglob("*"))
    report = run_qualification_dry_run(
        [ETH],
        period_start="2021-09-01T00:00:00Z",
        period_end="2021-12-01T00:00:00Z",
        write_manifest=False,
    )
    after = set(tmp_path.rglob("*"))
    assert before == after
    assert report["network_used"] is False
    assert report["writes_enabled"] is False
    assert report["economic_gate_opened"] is False


def test_network_blocked_without_flag() -> None:
    adapter = OkxPublicHistoryAdapterV1(fetcher=lambda _url: b"{}")
    with pytest.raises(NetworkDisabledError):
        adapter.acquire_partition(
            {
                "partition_id": "p",
                "native_instrument_id": "ETH-USDT-SWAP",
                "period_start": "2021-09-01T00:00:00Z",
                "period_end": "2021-10-01T00:00:00Z",
                "instrument_id": "eth",
            },
            allow_network=False,
            archive_root=None,
            write=False,
            source_locator="https://example.invalid",
        )


def test_probe_limit_max_partitions() -> None:
    plan = plan_partitions(
        [ETH],
        period_start="2021-09-01T00:00:00Z",
        period_end="2022-09-01T00:00:00Z",
        max_partitions=1,
    )
    assert plan["partition_count"] == 1
    assert plan["truncated"] is True


def test_quarantine_on_checksum_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "archive"
    root.mkdir()
    adapter = OkxPublicHistoryAdapterV1(fetcher=lambda _url: b"payload-bytes")
    part = {
        "partition_id": "part1",
        "instrument_id": ETH.instrument_id,
        "native_instrument_id": ETH.native_instrument_id,
        "period_start": "2021-09-01T00:00:00Z",
        "period_end": "2021-10-01T00:00:00Z",
        "kind": "ohlcv_pt1h",
    }
    row = build_partition_manifest_row(part)
    result = adapter.acquire_partition(
        {**part, **row},
        allow_network=True,
        archive_root=root,
        write=True,
        source_locator=row["source_locator"],
        expected_checksum="deadbeef",
    )
    assert result["status"] == "QUARANTINED"
    assert result["error_code"] == "CHECKSUM_MISMATCH"
    qfiles = list((root / "longer_chronological_pit" / "chrono_3y_v1" / "quarantine").glob("*"))
    assert qfiles


def test_resume_skips_verified_partitions() -> None:
    store = new_state_store()
    transition(store, "p1", "DISCOVERED")
    transition(store, "p1", "ACQUIRING")
    transition(store, "p1", "ACQUIRED")
    transition(store, "p1", "CHECKSUM_VERIFIED")
    assert should_skip_verified(store, "p1") is True
    assert should_skip_verified(store, "p2") is False


def test_unknown_instrument_state_fail_closed() -> None:
    unknown = InstrumentLifecycleV1(
        instrument_id="x",
        native_instrument_id="FOO-USDT-SWAP",
        base_asset="FOO",
        quote_asset="USDT",
        market_type="linear_usdt_perpetual",
        listing_time="2021-01-01T00:00:00Z",
        delisting_time=None,
        state="UNKNOWN",
    )
    with pytest.raises(PartitionPlanError, match="UNKNOWN_INSTRUMENT_STATE"):
        plan_partitions_for_instrument(unknown)


def test_write_manifest_requires_external_root(tmp_path: Path) -> None:
    root = tmp_path / "ext_archive"
    root.mkdir()
    plan = plan_partitions(
        [ETH],
        period_start="2021-09-01T00:00:00Z",
        period_end="2021-11-01T00:00:00Z",
    )
    manifest = build_acquisition_manifest(plan["partitions"], created_at="2026-07-20T00:00:00Z")
    path = write_manifest_atomic(manifest, archive_root=root)
    assert path.exists()
    with pytest.raises(ArchiveRootError, match="NO_OVERWRITE"):
        write_manifest_atomic(manifest, archive_root=root)


def test_cli_plan_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    from src.research.longer_chronological_pit_acquisition_v1.cli import main

    rc = main(["plan", "--max-partitions", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY_RUN" in out or "MODE=DRY_RUN" in out
    assert "NETWORK_USED=False" in out
