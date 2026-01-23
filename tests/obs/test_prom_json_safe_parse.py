import subprocess


def _run_parser(stdin: bytes) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/obs/prom_json_safe_parse.py"],
        input=stdin.decode("utf-8", errors="replace"),
        text=True,
        capture_output=True,
        check=False,
    )


def test_prom_json_safe_parse_valid_success_json_passes_through() -> None:
    proc = _run_parser(b'{"status":"success","data":{"resultType":"vector","result":[]}}')
    assert proc.returncode == 0
    assert '"status":"success"' in proc.stdout
    assert proc.stderr.strip() == ""


def test_prom_json_safe_parse_empty_body_fails_with_diagnostics() -> None:
    proc = _run_parser(b"")
    assert proc.returncode != 0
    assert "prom_json_parse_error=" in proc.stderr
    assert "prom_body_first_200_bytes" in proc.stderr


def test_prom_json_safe_parse_non_json_body_fails_with_diagnostics() -> None:
    proc = _run_parser(b"<html>not json</html>")
    assert proc.returncode != 0
    assert "prom_json_parse_error=" in proc.stderr
    assert "not json" in proc.stderr
