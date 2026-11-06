from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


SUMMARY_PATH = Path("out/ops/shared_smoke_summary/shared_smoke_summary.json")
REGISTRY_DIR = Path("out/ops/evidence_registry")
MANIFEST_PATH = REGISTRY_DIR / "manifest.json"
INDEX_PATH = REGISTRY_DIR / "index.jsonl"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not SUMMARY_PATH.exists():
        raise SystemExit(f"missing input summary: {SUMMARY_PATH}")

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    ts = datetime.now(timezone.utc).isoformat()
    digest = sha256_file(SUMMARY_PATH)

    manifest = {
        "contract_version": "wave6.evidence.v1",
        "status": "SMOKE_OK",
        "component": "evidence_registry_hook",
        "run_id": "SMOKE-write_evidence_registry_hook",
        "timestamp": ts,
        "summary": "local evidence manifest for shared smoke summary",
        "source_artifact": str(SUMMARY_PATH),
        "source_contract_version": summary.get("contract_version"),
        "source_component": summary.get("component"),
        "source_status": summary.get("status"),
        "source_sha256": digest,
        "component_count": summary.get("component_count"),
        "missing_count": summary.get("missing_count"),
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    index_entry = {
        "timestamp": ts,
        "manifest_path": str(MANIFEST_PATH),
        "source_artifact": str(SUMMARY_PATH),
        "source_sha256": digest,
        "component": "evidence_registry_hook",
        "status": "SMOKE_OK",
    }
    with INDEX_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(index_entry) + "\n")

    print(json.dumps(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
