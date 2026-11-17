#!/usr/bin/env python3
"""Verify the accepted Double Play and occupied N1 runtime source offline."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


MANIFEST = "docs/ops/specs/N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.json"
POLICY = "docs/ops/specs/N1_DOUBLE_PLAY_RUNTIME_SEAL_V1.md"
CHECKER = "scripts/ops/check_n1_double_play_runtime_seal_v1.py"
LINT_WORKFLOW = ".github/workflows/lint_gate.yml"
REFERENCE_WORKFLOW = ".github/workflows/map_currency_gate_v1.yml"
LINT_STEP = "      - name: Verify sealed N1 Double Play source"
CONTROL_PATHS = (MANIFEST, POLICY, CHECKER, REFERENCE_WORKFLOW)


def _git(root, *args):
    return subprocess.check_output(["git", "--literal-pathspecs", *args], cwd=root)


def _safe_path(value):
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value
    )


def _load_manifest(raw):
    data = json.loads(raw)
    if (
        set(data) != {"schema", "state", "runtime_authorization_effect", "directories", "files"}
        or data["schema"] != "peaktrade.n1_double_play_runtime_seal.v1"
        or data["state"] != "SEALED"
        or data["runtime_authorization_effect"] != "NONE"
        or not isinstance(data["directories"], list)
        or not data["directories"]
        or not all(_safe_path(path) for path in data["directories"])
        or not isinstance(data["files"], dict)
        or not data["files"]
        or not all(
            _safe_path(path) and isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
            for path, digest in data["files"].items()
        )
        or not all(
            any(path.startswith(directory + "/") for path in data["files"])
            for directory in data["directories"]
        )
    ):
        raise ValueError("invalid seal manifest")
    return data


def verify_content(root):
    """Check the frozen bytes and the Python membership of sealed packages."""
    seal = _load_manifest((root / MANIFEST).read_bytes())
    errors = []
    for rel, digest in seal["files"].items():
        path = root / rel
        if path.resolve() != path or not path.is_file():
            errors.append(f"sealed file missing or replaced: {rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"sealed file changed: {rel}")
    for directory in seal["directories"]:
        for path in (root / directory).rglob("*.py"):
            rel = path.relative_to(root).as_posix()
            if rel not in seal["files"]:
                errors.append(f"new source in sealed package: {rel}")
    return errors


def _lint_step(raw):
    lines = raw.decode().splitlines()
    if lines.count(LINT_STEP) != 1:
        return ()
    start = lines.index(LINT_STEP)
    end = next(
        (idx for idx in range(start + 1, len(lines)) if lines[idx].startswith("      - ")),
        len(lines),
    )
    return tuple(lines[start:end])


def verify_base_policy(root, base):
    """Apply the protected path policy from the target branch, including its control files."""
    base_commit = _git(root, "rev-parse", "--verify", base + "^{commit}").decode().strip()
    if not _git(root, "ls-tree", base_commit, "--", MANIFEST):
        # The first introduction is checked by the separate content gate.
        if not _lint_step((root / LINT_WORKFLOW).read_bytes()):
            return ["initial seal requires its Lint Gate integration"]
        return []
    seal = _load_manifest(_git(root, "show", f"{base_commit}:{MANIFEST}"))
    paths = [*CONTROL_PATHS, *seal["files"], *seal["directories"]]
    changed = _git(root, "diff", "--name-only", "--no-renames", "-z", base_commit, "--", *paths)
    errors = [
        f"protected path changed against {base_commit[:12]}: {p.decode()}"
        for p in changed.split(b"\0")
        if p
    ]
    previous_step = _lint_step(_git(root, "show", f"{base_commit}:{LINT_WORKFLOW}"))
    lint = root / LINT_WORKFLOW
    if not lint.is_file() or not previous_step or _lint_step(lint.read_bytes()) != previous_step:
        errors.append(f"protected seal step changed: {LINT_WORKFLOW}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--base", help="Check protected paths against the trusted target commit")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        errors = verify_base_policy(root, args.base) if args.base else verify_content(root)
    except (OSError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        errors = [str(exc)]
    if errors:
        print("N1_DOUBLE_PLAY_RUNTIME_SEAL_V1=FAIL")
        for error in errors:
            print(error)
        print(f"The accepted Double Play / N1 configuration is sealed. See {POLICY}.")
        return 1
    print("N1_DOUBLE_PLAY_RUNTIME_SEAL_V1=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
