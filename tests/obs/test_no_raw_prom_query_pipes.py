from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALLOW_MARKER = "ALLOW_RAW_PROM_QUERY_PIPE"


def test_no_raw_curl_python_pipe_for_prom_query_in_obs_scripts() -> None:
    """
    Regression lock:
    Forbid the brittle pattern in scripts/obs:
      curl .../api/v1/query ... | python ... json.load(sys.stdin)

    Allowed only if the file contains:
      ALLOW_RAW_PROM_QUERY_PIPE: <reason>
    """

    scripts_dir = PROJECT_ROOT / "scripts" / "obs"
    assert scripts_dir.is_dir()

    offenders: list[str] = []
    pipe_re = re.compile(
        r"curl[^\n]*api/v1/query[^\n]*\|[^\n]*python[^\n]*json\.load\(sys\.stdin\)", re.I
    )

    for p in sorted(scripts_dir.glob("*.sh")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        if ALLOW_MARKER in txt:
            continue
        if pipe_re.search(txt):
            offenders.append(str(p.relative_to(PROJECT_ROOT)))

    assert offenders == [], "raw prom query curl|python json.load pipeline found in: " + ", ".join(
        offenders
    )
