"""Contract tests for run_venue_capability_snapshot_v1 script."""

from __future__ import annotations

import json

import pytest

pytest_plugins = [
    "tests.meta.venue_capability_snapshot_v1_fixtures",
]

from scripts.run_venue_capability_snapshot_v1 import EXIT_OK, EXIT_USAGE_ERROR, main
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps
from tests.meta.venue_capability_snapshot_v1_fixtures import (
    build_valid_venue_capability_input,
    produce_venue_capability_snapshot_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.venue_capability_snapshot_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path, name: str = "script_venue_capability") -> str:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return str(root / name)


def test_script_happy_path(tmp_path, capsys) -> None:
    input_data = build_valid_venue_capability_input()
    input_path = tmp_path / "input.json"
    input_path.write_text(
        deterministic_json_dumps(
            {
                "contract_name": input_data.contract_name,
                "contract_version": input_data.contract_version,
                "snapshot_id": input_data.snapshot_id,
                "venue": input_data.venue,
                "account_scope": input_data.account_scope,
                "instrument": input_data.instrument,
                "market_type": input_data.market_type,
                "contract_type": input_data.contract_type,
                "contract_multiplier": input_data.contract_multiplier,
                "tick_size": input_data.tick_size,
                "lot_size": input_data.lot_size,
                "minimum_notional": input_data.minimum_notional,
                "maximum_order_size": input_data.maximum_order_size,
                "position_mode": input_data.position_mode,
                "margin_mode": input_data.margin_mode,
                "leverage_cap": input_data.leverage_cap,
                "supported_order_types": list(input_data.supported_order_types),
                "supported_time_in_force": list(input_data.supported_time_in_force),
                "reduce_only_semantics": input_data.reduce_only_semantics,
                "source_ref": input_data.source_ref,
                "source_digest": input_data.source_digest,
                "source_timestamp": input_data.source_timestamp,
                "builder_version": input_data.builder_version,
            }
        ),
        encoding="utf-8",
    )
    out = _durable_output(tmp_path)
    rc = main(["--input-json", str(input_path), "--output-dir", out])
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["snapshot_status"] == "VENUE_CAPABILITY_SNAPSHOT_VALID"


def test_script_missing_input(tmp_path) -> None:
    out = _durable_output(tmp_path)
    rc = main(["--input-json", str(tmp_path / "missing.json"), "--output-dir", out])
    assert rc == EXIT_USAGE_ERROR


def test_script_drift_mode(tmp_path, capsys) -> None:
    fixture = produce_venue_capability_snapshot_fixture(
        tmp_path,
        tmp_path / "evidence_root",
        produce_output=True,
        snapshot_name="baseline_snapshot",
    )
    assert fixture.snapshot_bundle_dir is not None
    baseline_path = fixture.snapshot_bundle_dir / "venue_capability_snapshot_v1.json"
    input_path = tmp_path / "candidate_input.json"
    input_path.write_text(
        deterministic_json_dumps(
            {
                **{
                    key: getattr(fixture.input_data, key)
                    for key in (
                        "contract_name",
                        "contract_version",
                        "snapshot_id",
                        "venue",
                        "account_scope",
                        "instrument",
                        "market_type",
                        "contract_type",
                        "contract_multiplier",
                        "tick_size",
                        "lot_size",
                        "minimum_notional",
                        "maximum_order_size",
                        "position_mode",
                        "margin_mode",
                        "leverage_cap",
                        "reduce_only_semantics",
                        "source_ref",
                        "source_digest",
                        "source_timestamp",
                        "builder_version",
                    )
                },
                "supported_order_types": list(fixture.input_data.supported_order_types),
                "supported_time_in_force": list(fixture.input_data.supported_time_in_force),
            }
        ),
        encoding="utf-8",
    )
    out = _durable_output(tmp_path, "candidate_snapshot")
    drift_out = tmp_path / "drift.json"
    rc = main(
        [
            "--input-json",
            str(input_path),
            "--output-dir",
            out,
            "--baseline-snapshot-json",
            str(baseline_path),
            "--drift-output-json",
            str(drift_out),
        ]
    )
    assert rc == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["drift_classification"] == "NO_DRIFT"
    assert drift_out.is_file()
