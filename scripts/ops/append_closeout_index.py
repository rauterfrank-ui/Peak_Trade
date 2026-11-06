import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys


def _head() -> str:
    override = os.environ.get("PT_HEAD")
    if override:
        return override
    return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()


def main() -> int:
    evidence_dir = os.environ.get("PT_EVIDENCE_DIR")
    kind = os.environ.get("PT_CLOSEOUT_KIND", "CLOSEOUT")
    notes = os.environ.get("PT_CLOSEOUT_NOTES", "")
    index_path = Path(
        os.environ.get("PT_CLOSEOUT_INDEX", "out/ops/index_post_merge_closeouts.jsonl")
    )

    if not evidence_dir:
        print("ERROR: PT_EVIDENCE_DIR env var required", file=sys.stderr)
        return 2

    index_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "kind": kind,
        "evidence_dir": evidence_dir,
        "head": _head(),
        "notes": notes,
    }

    with index_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"APPENDED {index_path} <- {entry['kind']} {entry['evidence_dir']} {entry['head']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
