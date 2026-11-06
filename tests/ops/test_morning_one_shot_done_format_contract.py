from pathlib import Path


def test_done_token_fields_present_and_formatted():
    s = Path("scripts/ops/run_morning_one_shot.sh").read_text(encoding="utf-8")
    for key in [
        "ts_utc:",
        "ops_status_exit:",
        "prbi_decision:",
        "prbi_score:",
        "prbg_status:",
        "prbg_sample_size:",
        "prbg_anomaly_count:",
        "prbg_error_count:",
        "evidence_dir:",
    ]:
        assert key in s
