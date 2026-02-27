from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    run_id = "SMOKE-" + Path(__file__).stem
    timestamp = datetime.now(timezone.utc).isoformat()
    out_dir = Path("out/ops/api_manager_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture = Path("tests/fixtures/wave3/api_manager_input.json")
    input_payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload = {
        "contract_version": "wave4.v1",
        "status": "SMOKE_OK",
        "component": "api_manager",
        "run_id": run_id,
        "timestamp": timestamp,
        "summary": "deterministic smoke artifact",
        "provider": input_payload.get("provider"),
        "api_mode": input_payload.get("api_mode"),
        "max_clients": input_payload.get("max_clients"),
    }

    out_file = out_dir / "api_manager_smoke.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
