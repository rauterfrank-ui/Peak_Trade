from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure repo root on path when run as script
_repo = Path(__file__).resolve().parent.parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from scripts.ops.registry_trend_report import compute_alerts


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        rows.append(json.loads(s))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--registry",
        default="out/ops/registry/morning_one_shot_done_registry.jsonl",
        help="Input JSONL registry (untracked)",
    )
    ap.add_argument(
        "--out",
        default="out/ops/registry/reports/alerts_latest.txt",
        help="Alerts output file (untracked)",
    )
    args = ap.parse_args()

    rows = _read_jsonl(Path(args.registry))
    alerts = compute_alerts(rows)

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(alerts) + ("\n" if alerts else ""), encoding="utf-8")

    if alerts:
        print("ALERTS_PRESENT")
        for a in alerts:
            print(a)
        return 2

    print("ALERTS_NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
