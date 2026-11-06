from pathlib import Path


def test_no_broken_double_backticks_in_pr_final_reports():
    reports = sorted(Path("docs/ops").glob("PR_*_FINAL_REPORT.md"))
    if not reports:
        return
    bad = []
    for p in reports:
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, start=1):
            if line.startswith("- ``"):
                bad.append(f"{p}:{i}: {line}")
            if line.startswith("- `src/") and not line.endswith("`"):
                bad.append(f"{p}:{i}: {line}")
    assert not bad, "Broken PR final report formatting found:\n" + "\n".join(bad)
