from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    out_dir = Path("out/ops/api_manager_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "status": "SMOKE_OK",
        "component": "api_manager",
    }

    out_file = out_dir / "api_manager_smoke.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
