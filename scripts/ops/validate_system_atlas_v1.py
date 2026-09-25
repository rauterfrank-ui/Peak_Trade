#!/usr/bin/env python3
"""Validate Peak_Trade System Atlas and generated-file freshness. ATLAS_AUTHORITY=NONE."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.system_atlas_v1.generate_v1 import generated_drift_v1  # noqa: E402
from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1  # noqa: E402
from scripts.ops.system_atlas_v1.validate_v1 import AtlasValidationError, validate_atlas_v1  # noqa: E402


def main() -> int:
    atlas = load_atlas_v1(repo_root=_REPO_ROOT)
    try:
        validate_atlas_v1(atlas)
    except AtlasValidationError as exc:
        print(f"ATLAS_VALIDATION_FAIL:{exc}", file=sys.stderr)
        return 2
    drift = generated_drift_v1(atlas=atlas, repo_root=_REPO_ROOT)
    if drift:
        print("ATLAS_GENERATED_DRIFT:" + ",".join(drift), file=sys.stderr)
        return 3
    print("ATLAS_VALIDATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
