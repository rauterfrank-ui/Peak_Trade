#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

P7_DIR="${1:-}"
if [[ -z "${P7_DIR}" ]]; then
  echo "USAGE: $0 <p7_dir>" >&2
  echo "Example: $0 out/ops/p7_step6_smoke_20260211T144454Z" >&2
  exit 2
fi

python3 - <<'PY' "${P7_DIR}"
import json
import sys
from pathlib import Path

from src.aiops.p7.reconciliation import reconcile_p7_outdir

p7_dir = Path(sys.argv[1])
res = reconcile_p7_outdir(p7_dir)

print(
    json.dumps(
        {
            "ok": res.ok,
            "metrics": res.metrics,
            "issues": [
                {"code": i.code, "path": i.path, "detail": i.detail}
                for i in res.issues
            ],
        },
        indent=2,
        sort_keys=True,
    )
)

sys.exit(0 if res.ok else 3)
PY
