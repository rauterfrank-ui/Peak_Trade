from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, Tuple


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sha256sums(bundle_root: Path, relpaths: Iterable[str]) -> Path:
    """
    Write hashes/sha256sums.txt deterministically.

    Format:
    - sorted by relpath (byte-wise on the string)
    - LF newlines
    - lines: "<sha256><two spaces><relpath>"
    """
    rel_list = sorted(dict.fromkeys(relpaths))
    out_path = bundle_root / "hashes" / "sha256sums.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for rel in rel_list:
        p = bundle_root / rel
        digest = sha256_file(p)
        lines.append(f"{digest}  {rel}")

    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")
    return out_path


def parse_sha256sums_text(s: str) -> Dict[str, str]:
    """
    Parse sha256sums.txt into {relpath: sha256}.
    """
    out: Dict[str, str] = {}
    for raw in s.splitlines():
        line = raw.strip()
        if not line:
            continue
        # sha256 + 2 spaces + relpath
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise ValueError("invalid sha256sums line (expected: '<sha256>  <path>')")
        digest, rel = parts[0].strip(), parts[1].strip()
        out[rel] = digest
    return out


def collect_files_for_hashing(bundle_root: Path) -> Tuple[str, ...]:
    """
    Collect all files under bundle_root (relative paths), excluding sha256sums.txt itself.
    """
    out = []
    for p in bundle_root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(bundle_root).as_posix()
        if rel == "hashes/sha256sums.txt":
            continue
        out.append(rel)
    return tuple(sorted(out))
