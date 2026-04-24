def test_generate_live_status_report_help_subprocess_smoke():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "generate_live_status_report.py"

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    combined_output = result.stdout + result.stderr
    assert "usage:" in combined_output.lower()
    assert "live" in combined_output.lower()
    assert "status" in combined_output.lower()
