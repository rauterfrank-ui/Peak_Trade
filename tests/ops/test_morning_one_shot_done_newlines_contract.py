from pathlib import Path


def test_done_token_heredoc_has_newlines_between_keys():
    s = Path("scripts/ops/run_morning_one_shot.sh").read_text(encoding="utf-8")
    assert 'cat > "$DONE" <<EOF' in s
    # Require at least a few critical newline-separated lines inside heredoc
    assert "DONE: morning_one_shot\n" in s
    assert "ts_utc: ${TS}\n" in s
    assert "ops_status_exit: ${OPS_EXIT}\n" in s
    assert "prbi_decision: ${PRBI_DECISION}\n" in s
    assert "prbg_sample_size: ${PRBG_SAMPLE_SIZE}\n" in s
    assert "evidence_dir: ${OUT}" in s
