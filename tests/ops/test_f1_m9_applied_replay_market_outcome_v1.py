import json
import math
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.ops.f1_m9_applied_replay_market_outcome_v1 import (
    declare_f1_m9_applied_replay_market_outcome_v1,
    measure_f1_m9_applied_replay_market_outcome_v1,
    read_f1_m9_applied_replay_market_outcome_v1,
)
from tests.learning.test_offline_recorded_market_replay_v1 import (
    market_request,
    utc,
    write_archive,
)
from tests.ops.test_f1_m9_applied_offline_replay_v1 import EVALUATED_AT, _run
from tests.ops.test_f1_m9_applied_offline_replay_v1 import owner_state as owner_state

ROOT = Path(__file__).resolve().parents[2]
HORIZON_START = datetime(2026, 11, 12, 8, tzinfo=timezone.utc)
RECEIVED = HORIZON_START + timedelta(hours=2, minutes=1)


def test_recorded_later_mark_window_binds_the_applied_host_and_reads_back(owner_state, tmp_path):
    host_path, host_digest = _run(owner_state, tmp_path / "host")
    store = tmp_path / "outcomes"
    plan = declare_f1_m9_applied_replay_market_outcome_v1(
        store_root=store,
        host_evidence_path=host_path,
        host_evidence_sha256=host_digest,
        market_request=market_request(HORIZON_START),
        declared_at_utc=utc(EVALUATED_AT),
    )
    plan_digest = plan["exact_content_digest"]
    assert plan["host_evidence_sha256"] == host_digest
    assert plan["host_configuration_digest"] == owner_state[3]["configuration_digest"]
    assert plan["market_target"]["return_start_close_time_utc"] == "2026-11-12T09:00:00Z"
    assert plan["market_target"]["return_end_close_time_utc"] == "2026-11-12T10:00:00Z"
    assert not (store / plan_digest / "measurement.json").exists()

    archive = write_archive(
        tmp_path / "recorded", opened=HORIZON_START, received=RECEIVED, closes=(101, 102)
    )
    before = archive.raw_path.read_bytes()
    kwargs = dict(
        store_root=store,
        plan_digest=plan_digest,
        host_evidence_path=host_path,
        archive=archive,
    )
    with pytest.raises(ValueError, match="ARCHIVE_RESPONSE_NOT_YET_AVAILABLE"):
        measure_f1_m9_applied_replay_market_outcome_v1(
            **kwargs, evaluated_at_utc=utc(RECEIVED - timedelta(seconds=1))
        )
    assert not (store / plan_digest / "measurement.json").exists()

    result = measure_f1_m9_applied_replay_market_outcome_v1(
        **kwargs, evaluated_at_utc=utc(RECEIVED)
    )
    assert result == measure_f1_m9_applied_replay_market_outcome_v1(
        **kwargs, evaluated_at_utc=utc(RECEIVED)
    )
    assert result["market_observation"]["measurement"]["log_return"] == pytest.approx(
        math.log(102 / 101)
    )
    assert result["plan_digest"] == plan_digest
    assert result["economic_application_effect"] is None
    assert result["comparison_status"] == "COMPARABLE_EXECUTION_EVIDENCE_REQUIRED"
    assert archive.raw_path.read_bytes() == before

    changed = write_archive(
        tmp_path / "alternate", opened=HORIZON_START, received=RECEIVED, closes=(101, 103)
    )
    with pytest.raises(ValueError, match="F1_M9_MARKET_OUTCOME_RECORD_CONFLICT"):
        measure_f1_m9_applied_replay_market_outcome_v1(
            **{**kwargs, "archive": changed}, evaluated_at_utc=utc(RECEIVED)
        )
    digest = result["exact_content_digest"]
    code = """
import json, sys
from pathlib import Path
from src.ops.f1_m9_applied_replay_market_outcome_v1 import read_f1_m9_applied_replay_market_outcome_v1
print(json.dumps(read_f1_m9_applied_replay_market_outcome_v1(
    store_root=Path(sys.argv[1]), plan_digest=sys.argv[2],
    host_evidence_path=Path(sys.argv[3]), expected_measurement_digest=sys.argv[4]
)))
"""
    cold = subprocess.run(
        ["./scripts/pt", "-c", code, str(store), plan_digest, str(host_path), digest],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    assert json.loads(cold.stdout.splitlines()[-1]) == result
    path = store / plan_digest / "measurement.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="INTEGRATION_SCHEMA_MISMATCH"):
        read_f1_m9_applied_replay_market_outcome_v1(
            store_root=store,
            plan_digest=plan_digest,
            host_evidence_path=host_path,
            expected_measurement_digest=digest,
        )


def test_plan_rejects_wrong_instrument_and_late_declaration(owner_state, tmp_path):
    host_path, host_digest = _run(owner_state, tmp_path / "host")
    store = tmp_path / "outcomes"
    kwargs = dict(
        store_root=store,
        host_evidence_path=host_path,
        host_evidence_sha256=host_digest,
    )
    market = market_request(HORIZON_START)
    with pytest.raises(ValueError, match="F1_M9_MARKET_OUTCOME_DECLARATION_TIME_MISMATCH"):
        declare_f1_m9_applied_replay_market_outcome_v1(
            **kwargs,
            market_request=market,
            declared_at_utc=utc(HORIZON_START + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="F1_M9_MARKET_OUTCOME_DECLARATION_TIME_MISMATCH"):
        declare_f1_m9_applied_replay_market_outcome_v1(
            **kwargs,
            market_request=market,
            declared_at_utc=utc(EVALUATED_AT - timedelta(seconds=1)),
        )
    market["market_identity"]["instrument_ref"] = "inst-btc-usdt-perp"
    with pytest.raises(ValueError, match="F1_M9_MARKET_OUTCOME_INSTRUMENT_MISMATCH"):
        declare_f1_m9_applied_replay_market_outcome_v1(
            **kwargs, market_request=market, declared_at_utc=utc(EVALUATED_AT)
        )
    assert not store.exists()
