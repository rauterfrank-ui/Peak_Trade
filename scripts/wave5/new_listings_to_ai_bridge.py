from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    fixture = Path("tests/fixtures/bridges/new_listings_bridge_input.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    listings = payload.get("listings", [])

    top = max(listings, key=lambda x: x.get("score", 0.0)) if listings else {}
    avg_vol = sum(x.get("volatility", 0.0) for x in listings) / len(listings) if listings else 0.0

    out_dir = Path("out/ops/new_listings_ai_bridge")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "contract_version": "wave5.bridge.v1",
        "status": "SMOKE_OK",
        "component": "new_listings_ai_bridge",
        "run_id": "SMOKE-new_listings_ai_bridge",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": "bridge artifact from research new_listings to AI-ready inputs",
        "source_component": payload.get("source", "new_listings"),
        "listing_count": len(listings),
        "top_symbol": top.get("symbol"),
        "policy_view": {
            "mode": "paper_only",
            "enabled_count": 2,
            "blocked_count": 0,
        },
        "switch_view": {
            "regime": "neutral" if avg_vol < 0.2 else "volatile",
            "volatility": round(avg_vol, 4),
        },
    }

    out_file = out_dir / "new_listings_ai_bridge.json"
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
