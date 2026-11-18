#!/usr/bin/env python3
"""Verify the frozen offline Master V2 Double Play instrument-card adapter."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

MANIFEST = "docs/ops/specs/MASTER_V2_INSTRUMENT_CARDS_SEAL_V1.json"
CHECKER = "scripts/ops/check_master_v2_instrument_cards_seal_v1.py"
WORKFLOW = ".github/workflows/lint_gate.yml"
STEP = "      - name: Verify sealed Master V2 instrument cards"
SOURCE_FILES = frozenset(
    {
        "src/ops/master_v2_double_play_instrument_cards_v1.py",
        "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/offline_candidate_cards_v1.py",
    }
)


def _git(root, *args):
    return subprocess.check_output(["git", "--literal-pathspecs", *args], cwd=root)


def _load(raw):
    manifest = json.loads(raw)
    if (
        manifest.get("schema") != "peaktrade.master_v2_instrument_cards_seal.v1"
        or manifest.get("state") != "SEALED"
        or manifest.get("owner_universe") != "Master V2 Double Play"
        or manifest.get("runtime_authorization_effect") != "NONE"
        or set(manifest.get("files", {})) != SOURCE_FILES
        or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in manifest["files"].values())
    ):
        raise ValueError("invalid instrument-card seal manifest")
    return manifest


def _step(raw):
    lines = raw.decode().splitlines()
    if lines.count(STEP) != 1:
        return ()
    start = lines.index(STEP)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("      - ")), len(lines)
    )
    return tuple(lines[start:end])


def verify(root, base=None):
    manifest = _load((root / MANIFEST).read_bytes())
    errors = []
    for name, digest in manifest["files"].items():
        path = root / name
        if path.resolve() != path or not path.is_file():
            errors.append("sealed file missing or replaced: " + name)
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append("sealed file changed: " + name)
    if not _step((root / WORKFLOW).read_bytes()):
        errors.append("instrument-card seal CI step missing")
    if base is not None and _git(root, "ls-tree", base, "--", MANIFEST):
        prior = _load(_git(root, "show", base + ":" + MANIFEST))
        changed = _git(
            root,
            "diff",
            "--name-only",
            "--no-renames",
            base,
            "--",
            MANIFEST,
            CHECKER,
            *sorted(prior["files"]),
        )
        errors.extend(
            "protected instrument-card path changed: " + name
            for name in changed.decode().splitlines()
        )
        if _step((root / WORKFLOW).read_bytes()) != _step(
            _git(root, "show", base + ":" + WORKFLOW)
        ):
            errors.append("instrument-card seal CI step changed")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base")
    args = parser.parse_args()
    try:
        errors = verify(args.root.resolve(), args.base)
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        errors = [str(exc)]
    print("MASTER_V2_INSTRUMENT_CARDS_SEAL_V1=" + ("FAIL" if errors else "PASS"))
    for error in errors:
        print(error)
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
