from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    fixture = Path("tests/fixtures/ai/policy_audit_input.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    out_dir = Path("out/ops/policy_audit_smoke")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "status": "SMOKE_OK",
        "component": "ai_model_policy_audit_v1",
        "mode": payload.get("mode"),
        "enabled_count": len(payload.get("enabled", [])),
        "blocked_count": len(payload.get("blocked", [])),
    }

    out_file = out_dir / "policy_audit_smoke.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
