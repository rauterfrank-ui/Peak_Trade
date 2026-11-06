from pathlib import Path


def test_files_exist():
    must = [
        "src/execution/networked/limits/clock_v1.py",
        "src/execution/networked/limits/rate_limiter_v1.py",
        "src/execution/networked/limits/backoff_v1.py",
        "docs/analysis/p133/README.md",
    ]
    for m in must:
        assert Path(m).exists(), m
