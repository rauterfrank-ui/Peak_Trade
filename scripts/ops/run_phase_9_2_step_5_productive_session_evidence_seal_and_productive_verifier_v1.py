#!/usr/bin/env python3
"""CLI for Step-5 productive session evidence seal + productive verifier.

Commands:
  verify-productive-session
  seal-productive-session
  materialize-evidence

No network session. No authorization/token issuance or consumption.
Does not rewrite raw productive session evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.constants_v1 import (  # noqa: E402
    CANONICAL_SESSION_RELATIVE_PATH,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.evidence_v1 import (  # noqa: E402
    materialize_seal_evidence_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.productive_session_verifier_v1 import (  # noqa: E402
    verify_productive_session_evidence_v1,
)
from src.ops.phase_9_2_step_5_productive_session_evidence_seal_and_productive_verifier_v1.seal_v1 import (  # noqa: E402
    seal_productive_session_evidence_v1,
)


def _repo_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "verify-productive-session",
            "seal-productive-session",
            "materialize-evidence",
        ),
    )
    p.add_argument(
        "--session-root",
        type=Path,
        default=None,
        help="Productive session evidence root (default: canonical Step-5 session)",
    )
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--seal-output", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sha = args.expected_repository_sha or _repo_sha()
    session = (
        Path(args.session_root)
        if args.session_root
        else (_REPO_ROOT / CANONICAL_SESSION_RELATIVE_PATH)
    )

    if args.command == "verify-productive-session":
        result = verify_productive_session_evidence_v1(
            session,
            expected_repository_sha=sha,
            repo_root=_REPO_ROOT,
        )
    elif args.command == "seal-productive-session":
        out = args.seal_output or (
            (args.evidence_root or (_REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME))
            / "fixtures"
            / "productive_session_evidence_seal_v1.json"
        )
        result = seal_productive_session_evidence_v1(
            session_root=session,
            expected_repository_sha=sha,
            seal_output_path=out,
            repo_root=_REPO_ROOT,
        )
    else:
        result = materialize_seal_evidence_v1(
            repository_sha=sha,
            session_root=session,
            evidence_root=args.evidence_root,
            repo_root=_REPO_ROOT,
        )

    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        ok = bool(result.get("ok") or result.get("PRODUCTIVE_EVIDENCE_SEALED"))
        print(f"CAPABILITY_ID={CAPABILITY_ID}")
        print(f"OK={ok}")
        if "VERIFIER_RESULT" in result:
            print(f"VERIFIER_RESULT={result.get('VERIFIER_RESULT')}")
        if "PRODUCTIVE_VERIFIER_RESULT" in result:
            print(f"PRODUCTIVE_VERIFIER_RESULT={result.get('PRODUCTIVE_VERIFIER_RESULT')}")
        if result.get("blockers"):
            print("BLOCKERS=" + ",".join(str(b) for b in result["blockers"]))
        if result.get("seal_digest"):
            print(f"SEAL_DIGEST={result.get('seal_digest')}")
        if result.get("productive_evidence_seal_digest"):
            print(f"SEAL_DIGEST={result.get('productive_evidence_seal_digest')}")
    return 0 if bool(result.get("ok") or result.get("PRODUCTIVE_EVIDENCE_SEALED")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
