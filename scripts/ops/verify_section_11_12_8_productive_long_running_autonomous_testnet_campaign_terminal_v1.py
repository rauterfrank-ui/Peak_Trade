#!/usr/bin/env python3
"""Verify §11.12.8 terminal productive campaign consumer evidence / contracts."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (  # noqa: E402
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.verifier_v1 import (  # noqa: E402
    verify_section_11_12_8_terminal_consumer_v1,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_manifest(evidence_root: Path) -> int:
    manifest = evidence_root / MANIFEST_FILENAME
    if not manifest.is_file():
        print(json.dumps({"ok": False, "error": "MANIFEST_MISSING"}))
        return 2
    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for line in lines:
        digest, _, rel = line.partition("  ")
        path = evidence_root / rel
        if not path.is_file():
            print(json.dumps({"ok": False, "error": "MANIFEST_PATH_MISSING", "path": rel}))
            return 2
        actual = _sha256_bytes(path.read_bytes())
        if actual != digest:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "MANIFEST_DIGEST_MISMATCH",
                        "path": rel,
                        "expected": digest,
                        "actual": actual,
                    }
                )
            )
            return 2
    return 0


def main() -> int:
    live = verify_section_11_12_8_terminal_consumer_v1()
    if not live.get("ok"):
        print(json.dumps({"ok": False, "error": "LIVE_VERIFIER_FAILED", "verification": live}))
        return 2

    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    if evidence_root.is_dir() and (evidence_root / MANIFEST_FILENAME).is_file():
        rc = verify_manifest(evidence_root)
        if rc != 0:
            return rc

    print(json.dumps({"ok": True, "verification": live}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
