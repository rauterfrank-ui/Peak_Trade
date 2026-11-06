from pathlib import Path

from scripts.ops.registry_trend_report import compute_alerts, render_md


def test_trend_report_alerts_and_md_render() -> None:
    rows = [
        {
            "ts_utc": "20260304T000000Z",
            "ops_status_exit": 0,
            "prbi_decision": "READY_FOR_LIVE_PILOT",
            "prbi_score": 100,
            "prbg_status": "OK",
            "prbg_sample_size": 150,
            "prbg_anomaly_count": 0,
            "prbg_error_count": 0,
            "sha256_ok": True,
        },
        {
            "ts_utc": "20260305T000000Z",
            "ops_status_exit": 2,
            "prbi_decision": "CONTINUE_TESTNET",
            "prbi_score": 85,
            "prbg_status": "OK",
            "prbg_sample_size": 40,
            "prbg_anomaly_count": 0,
            "prbg_error_count": 1,
            "sha256_ok": True,
        },
    ]
    alerts = compute_alerts(rows)
    assert "OPS_STATUS_FAIL: ops_status_exit != 0" in alerts
    assert "PRBI_NOT_READY: prbi_decision != READY_FOR_LIVE_PILOT" in alerts
    assert "PRBG_ERRORS_PRESENT: prbg_error_count > 0" in alerts

    md = render_md(rows, alerts, limit=30, generated_at="2026-03-05T00:00:00Z")
    assert "# DONE Registry Trend Report" in md
    assert "| 20260305T000000Z | 2 |" in md
