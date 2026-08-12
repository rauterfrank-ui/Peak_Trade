#!/usr/bin/env python3
"""Verify §11.13.5 authoring/forensic evidence root."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.verifier_v1 import (  # noqa: E402
    LiveCanaryVerifierError,
    verify_live_canary_authoring_evidence_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify §11.13.5 canary authoring evidence.")
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_live_canary_authoring_evidence_v1(args.evidence_root)
    except LiveCanaryVerifierError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
