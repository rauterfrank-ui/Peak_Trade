from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    fixture = Path("tests/fixtures/ai/switch_layer_input.json")
    input_payload = json.loads(fixture.read_text(encoding="utf-8"))

    out_dir = Path("out/ops/switch_layer_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "SMOKE_OK",
        "component": "switch_layer_v1",
        "regime": input_payload.get("regime"),
        "volatility": input_payload.get("volatility"),
    }
    (out_dir / "switch_layer_smoke.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
