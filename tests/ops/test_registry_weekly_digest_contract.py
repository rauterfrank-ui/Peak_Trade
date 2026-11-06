from scripts.ops.registry_weekly_digest import weekly_digest


def test_weekly_digest_computes_rates() -> None:
    rows = [
        {
            "ops_status_exit": 0,
            "prbi_decision": "READY_FOR_LIVE_PILOT",
            "prbg_status": "OK",
            "prbg_error_count": 0,
            "prbg_sample_size": 100,
        },
        {
            "ops_status_exit": 2,
            "prbi_decision": "CONTINUE_TESTNET",
            "prbg_status": "OK",
            "prbg_error_count": 1,
            "prbg_sample_size": 50,
        },
    ]
    d = weekly_digest(rows, days=0)
    assert d["rows_total"] == 2
    assert d["ops_ok"] == 1
    assert d["prbi_ready"] == 1
    assert d["prbg_ok"] == 2
    assert d["prbg_err_free"] == 1
    assert d["prbg_sample_size_min"] == 50
    assert d["prbg_sample_size_max"] == 100
