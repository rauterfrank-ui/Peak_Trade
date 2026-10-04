#!/usr/bin/env python3
"""Emit canonical Run-001 settings manifest + digest for CURRENT repo (stdout JSON)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
        load_paper_shadow_run_contract_v1,
    )
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_settings_manifest_v1 import (
        build_run_settings_manifest_v1,
    )

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--settings-digest", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    contract = load_paper_shadow_run_contract_v1(
        contract_path=args.contract,
        settings_digest_path=args.settings_digest,
    )
    manifest = build_run_settings_manifest_v1(repo_root=_REPO, contract=contract)
    text = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
