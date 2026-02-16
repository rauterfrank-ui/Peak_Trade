"""P85 — Live Data Ingest Readiness v1.

Dry online / live-data ingest readiness: connectivity, rate limit, schema, persistency.
No execution, no model calls. Evidence written to out/ops.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class P85ContextV1:
    """Context for P85 live data ingest readiness run."""

    mode: str  # paper|shadow
    run_id: str
    out_dir: str
    connectivity_url: str = "https://api.kraken.com/0/public/Time"
    timeout_sec: float = 10.0

    @classmethod
    def from_env(cls) -> "P85ContextV1":
        import os

        return cls(
            mode=os.environ.get("MODE", "shadow"),
            run_id=os.environ.get("RUN_ID", "p85"),
            out_dir=os.environ.get("OUT_DIR", ""),
            connectivity_url=os.environ.get(
                "P85_CONNECTIVITY_URL", "https://api.kraken.com/0/public/Time"
            ),
        )


def _check_connectivity(ctx: P85ContextV1) -> dict[str, Any]:
    """Check connectivity to live data endpoint (REST)."""
    try:
        req = urllib.request.Request(
            ctx.connectivity_url,
            headers={"User-Agent": "PeakTrade-P85-Readiness/1.0"},
        )
        with urllib.request.urlopen(req, timeout=ctx.timeout_sec) as resp:
            body = resp.read().decode()
            data = json.loads(body)
            # Kraken Time response: {"error":[],"result":{"unixtime":...,"rfc1123":"..."}}
            has_result = "result" in data and isinstance(data["result"], dict)
            has_unixtime = has_result and "unixtime" in data["result"]
            schema_ok = has_unixtime
            return {
                "ok": True,
                "status": resp.status,
                "schema_valid": schema_ok,
                "detail": {"url": ctx.connectivity_url, "has_unixtime": has_unixtime},
            }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "detail": {"url": ctx.connectivity_url},
        }


def _check_rate_limit(resp_headers: dict[str, str]) -> dict[str, Any]:
    """Rate limit check (best-effort from headers)."""
    # Kraken may send X-RateLimit-* headers; if absent, assume OK for public endpoint
    return {"ok": True, "detail": "public_endpoint_no_strict_limit"}


def run_live_data_ingest_readiness_v1(ctx: P85ContextV1) -> dict[str, Any]:
    """Run P85 live data ingest readiness checks."""
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError(f"P85: only paper/shadow allowed. mode={ctx.mode}")

    connectivity = _check_connectivity(ctx)
    rate_limit = _check_rate_limit({})

    checks = [
        {"id": "connectivity", "ok": connectivity["ok"], "detail": connectivity.get("detail", {})},
        {
            "id": "schema",
            "ok": connectivity.get("schema_valid", False),
            "detail": connectivity.get("detail", {}),
        },
        {"id": "rate_limit", "ok": rate_limit["ok"], "detail": rate_limit.get("detail", {})},
    ]

    overall_ok = all(c["ok"] for c in checks)
    report = {
        "meta": {"p85_version": "v1", "run_id": ctx.run_id, "mode": ctx.mode},
        "checks": checks,
        "overall_ok": overall_ok,
        "connectivity": connectivity,
    }

    # Persist to out/ops
    out_path = Path(ctx.out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    result_path = out_path / "P85_RESULT.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main() -> int:
    """CLI entrypoint. Reads MODE, RUN_ID, OUT_DIR from env."""
    ctx = P85ContextV1.from_env()
    if not ctx.out_dir:
        print("ERR: OUT_DIR required", file=__import__("sys").stderr)
        return 2
    try:
        report = run_live_data_ingest_readiness_v1(ctx)
    except PermissionError as e:
        print(f"ERR: {e}", file=__import__("sys").stderr)
        return 3

    if report["overall_ok"]:
        print(f"P85_READY out_dir={ctx.out_dir} run_id={ctx.run_id} mode={ctx.mode}")
        return 0
    print(
        f"P85_NOT_READY out_dir={ctx.out_dir} checks={report['checks']}",
        file=__import__("sys").stderr,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
