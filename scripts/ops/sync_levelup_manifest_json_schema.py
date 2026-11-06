#!/usr/bin/env python3
"""
Regenerate the committed JSON Schema for LevelUpManifestV0.

Uses the same source as ``python -m src.levelup.cli export-json-schema`` (Pydantic
``model_json_schema`` on ``LevelUpManifestV0``). Run after changing v0 models.

Exit codes:
  0 — file written
  2 — unexpected error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.levelup.v0_models import levelup_manifest_v0_json_schema  # noqa: E402

_OUT = _REPO_ROOT / "schemas" / "levelup" / "levelup_manifest_v0.schema.json"


def main() -> int:
    try:
        schema = levelup_manifest_v0_json_schema()
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        _OUT.write_text(text, encoding="utf-8")
    except OSError as exc:
        print(f"sync_levelup_manifest_json_schema: write failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
