from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


INPUTS = [
    ("policy_audit", Path("out/ops/policy_audit_smoke/policy_audit_smoke.json")),
    ("switch_layer", Path("out/ops/switch_layer_smoke/switch_layer_smoke.json")),
    (
        "model_registry_loader",
        Path("out/ops/model_registry_loader_smoke/model_registry_loader_smoke.json"),
    ),
    ("metrics_server", Path("out/ops/metrics_server_smoke/metrics_server_smoke.json")),
    ("api_manager", Path("out/ops/api_manager_smoke/api_manager_smoke.json")),
    ("new_listings_ai_bridge", Path("out/ops/new_listings_ai_bridge/new_listings_ai_bridge.json")),
]


def main() -> int:
    components: list[dict] = []
    missing: list[str] = []

    for alias, path in INPUTS:
        if not path.exists():
            missing.append(alias)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        components.append(
            {
                "alias": alias,
                "component": payload.get("component"),
                "status": payload.get("status"),
                "contract_version": payload.get("contract_version"),
                "run_id": payload.get("run_id"),
                "timestamp": payload.get("timestamp"),
            }
        )

    out_dir = Path("out/ops/shared_smoke_summary")
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "contract_version": "wave4.summary.v1",
        "status": "SMOKE_OK" if not missing else "PARTIAL",
        "component": "shared_smoke_summary",
        "run_id": "SMOKE-aggregate_smoke_contracts",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": "aggregated smoke contract summary",
        "component_count": len(components),
        "missing_count": len(missing),
        "components": components,
        "missing": missing,
    }

    out_file = out_dir / "shared_smoke_summary.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
