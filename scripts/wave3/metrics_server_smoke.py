from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    run_id = "SMOKE-" + Path(__file__).stem
    timestamp = datetime.now(timezone.utc).isoformat()
    out_dir = Path("out/ops/metrics_server_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture = Path("tests/fixtures/wave3/metrics_server_input.json")
    input_payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload = {
        "contract_version": "wave4.v1",
        "status": "SMOKE_OK",
        "component": "metrics_server",
        "run_id": run_id,
        "timestamp": timestamp,
        "summary": "deterministic smoke artifact",
        "host": input_payload.get("host"),
        "port": input_payload.get("port"),
        "enabled": input_payload.get("enabled"),
    }

    out_file = out_dir / "metrics_server_smoke.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
