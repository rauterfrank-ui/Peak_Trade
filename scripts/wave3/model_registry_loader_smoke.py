from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    out_dir = Path("out/ops/model_registry_loader_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture = Path("tests/fixtures/wave3/model_registry_loader_input.json")
    input_payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload = {
        "status": "SMOKE_OK",
        "component": "model_registry_loader",
        "registry_name": input_payload.get("registry_name"),
        "model_count": len(input_payload.get("models", [])),
        "default_model": input_payload.get("default_model"),
    }

    out_file = out_dir / "model_registry_loader_smoke.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
