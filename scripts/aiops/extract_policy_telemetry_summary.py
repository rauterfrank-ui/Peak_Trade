"""Extract policy telemetry summary from evidence/manifest JSON (deterministic)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_from_evidence_manifest(manifest_path: Path) -> dict[str, Any]:
    """
    Deterministic best-effort extractor.
    Input: evidence_manifest.json or manifest.json written by paper session/audit runner.
    Output: telemetry_summary dict with stable keys.
    """
    m = _read_json(manifest_path)
    out: dict[str, Any] = {
        "source": "evidence_manifest",
        "manifest_path": str(manifest_path),
        "policy": {},
        "policy_enforce": {},
    }

    decision = None
    if isinstance(m, dict):
        decision = m.get("decision") or m.get("decision_context") or None

    if isinstance(decision, dict):
        policy = decision.get("policy") or {}
        out["policy"] = {
            "action": policy.get("action"),
            "reason_codes": policy.get("reason_codes") or [],
            "metadata": policy.get("metadata") or {},
        }
        pe = decision.get("policy_enforce") or {}
        out["policy_enforce"] = {
            "allowed": pe.get("allowed"),
            "reason_code": pe.get("reason_code"),
            "env": pe.get("env"),
        }

    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--manifest", required=True, help="Path to evidence_manifest.json or manifest.json"
    )
    ap.add_argument("--out", required=True, help="Path to write telemetry_summary.json")
    ap.add_argument(
        "--fallback-policy-json",
        default=None,
        help="Optional JSON file with policy dict when manifest has no decision.",
    )
    ns = ap.parse_args()

    manifest = Path(ns.manifest)
    outp = Path(ns.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    summary = extract_from_evidence_manifest(manifest)

    # Phase K: optional fallback policy when manifest lacks decision context
    if (not summary.get("policy")) and ns.fallback_policy_json:
        fp = Path(ns.fallback_policy_json)
        if fp.exists():
            try:
                fb = json.loads(fp.read_text(encoding="utf-8"))
                if isinstance(fb, dict) and fb:
                    fb.setdefault("reason_codes", [])
                    summary["policy"] = fb
            except Exception:
                pass

    # Normalize policy shape
    if "policy" not in summary or summary["policy"] is None:
        summary["policy"] = {}
    if isinstance(summary["policy"], dict):
        summary["policy"].setdefault("reason_codes", [])

    outp.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
