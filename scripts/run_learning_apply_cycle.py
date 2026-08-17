#!/usr/bin/env python3
"""
Learning Apply Cycle (Bridge Runner) - minimal viable
====================================================

Zweck:
  Research-/Preview-Brücke zwischen Learning Snippets (JSON/JSONL) und
  einem geplanten Override-File. Writes sind permanent fail-closed.

Inputs (tolerant):
  - Directory: reports/learning_snippets/ (default)
  - File types:
      - *.json  : { "patches": [...] } OR single patch dict OR list of patch dicts
      - *.jsonl : one patch dict per line

Patch object fields (best-effort):
  - target (required): dotted path, e.g. "portfolio.leverage"
  - new_value (required) OR value
  - old_value (optional)
  - reason/source_experiment_id/generated_at (optional; not used in override output v1)

Output:
  - Preview only. Non-dry-run write attempts are refused.
  - Historical default path (never written by this script):
      config/auto/learning.override.toml

Format (minimal + deterministic):
  [overrides]
  "a.b.c" = 1.23

  Keys are always quoted; keys are sorted lexicographically.
  Only TOML-scalar values are written (int/float/bool/string). List/dict values are skipped.

CLI:
  python3 scripts/run_learning_apply_cycle.py --dry-run
  python3 scripts/run_learning_apply_cycle.py  # write refused (preview-only)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_IN_DIR = Path("reports/learning_snippets")
DEFAULT_OUT_FILE = Path("config/auto/learning.override.toml")


def _toml_escape_string(s: str) -> str:
    # Minimal TOML string escape for double-quoted strings
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _toml_format_value(v: Any) -> Optional[str]:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        # Stable float formatting, no scientific notation surprises for common values
        return repr(float(v))
    if isinstance(v, str):
        return f'"{_toml_escape_string(v)}"'
    return None


LEARNING_APPLY_WRITE_FORBIDDEN = (
    "LEARNING_APPLY_WRITE_FORBIDDEN: scripts/run_learning_apply_cycle.py "
    "is research/preview-only and must not write override config files."
)


def _write_override_toml(path: Path, overrides: Dict[str, Any]) -> str:
    del path, overrides
    raise PermissionError(LEARNING_APPLY_WRITE_FORBIDDEN)


def _iter_input_files(in_dir: Path) -> List[Path]:
    if not in_dir.exists() or not in_dir.is_dir():
        return []

    files: List[Path] = []
    for p in in_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() in (".json", ".jsonl"):
            files.append(p)
    return files


def _select_files(files: Sequence[Path], max_files: Optional[int]) -> List[Path]:
    # Deterministic ordering: (mtime, path) ascending, so newest is processed last.
    items: List[Tuple[float, str, Path]] = []
    for p in files:
        try:
            mtime = p.stat().st_mtime
        except Exception:
            mtime = 0.0
        items.append((mtime, str(p), p))

    items.sort(key=lambda t: (t[0], t[1]))
    selected = [p for _, __, p in items]
    if max_files is not None:
        selected = selected[-max_files:]
    return selected


def _coerce_patch_obj(obj: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(obj, dict):
        return None
    return obj


def _extract_patches_from_json_payload(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        if "patches" in payload and isinstance(payload["patches"], list):
            return [
                p for p in ([_coerce_patch_obj(x) for x in payload["patches"]]) if p is not None
            ]
        patch = _coerce_patch_obj(payload)
        return [patch] if patch is not None else []
    if isinstance(payload, list):
        return [p for p in ([_coerce_patch_obj(x) for x in payload]) if p is not None]
    return []


def _read_patches_from_file(path: Path) -> List[Dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[learning_apply] WARNING: Failed to read {path}: {e}")
        return []

    if path.suffix.lower() == ".jsonl":
        patches: List[Dict[str, Any]] = []
        for idx, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                print(f"[learning_apply] WARNING: Invalid JSONL in {path}:{idx}: {e}")
                continue
            patch = _coerce_patch_obj(obj)
            if patch is None:
                print(f"[learning_apply] WARNING: Non-dict patch in {path}:{idx} (skipped)")
                continue
            patches.append(patch)
        return patches

    # .json
    try:
        payload = json.loads(text)
    except Exception as e:
        print(f"[learning_apply] WARNING: Invalid JSON in {path}: {e}")
        return []

    return _extract_patches_from_json_payload(payload)


def _patch_to_override(patch: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
    target = patch.get("target")
    if not isinstance(target, str) or not target.strip():
        return None

    if "new_value" in patch:
        new_value = patch.get("new_value")
    else:
        new_value = patch.get("value")

    # Minimal v1: only scalars
    if isinstance(new_value, (dict, list)) or new_value is None:
        return None

    # Normalize ints/floats/bools/strings; anything else skip
    if not isinstance(new_value, (bool, int, float, str)):
        return None

    return (target.strip(), new_value)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the Learning Apply Cycle (minimal bridge runner).")
    p.add_argument("--in-dir", type=Path, default=DEFAULT_IN_DIR, help="Input directory path.")
    p.add_argument("--out-file", type=Path, default=DEFAULT_OUT_FILE, help="Output TOML path.")
    p.add_argument("--dry-run", action="store_true", help="Preview only; do not write files.")
    p.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="If set: only use the N newest files by mtime.",
    )
    p.add_argument(
        "--print-sources",
        action="store_true",
        help="Print the list of processed input files.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    files_seen = 0
    files_used = 0
    patches_parsed = 0
    patches_written = 0

    input_files = _iter_input_files(args.in_dir)
    files_seen = len(input_files)

    if files_seen == 0:
        print(f"[learning_apply] No input files found under: {args.in_dir}")
        print(
            f"[learning_apply] Summary: files_seen={files_seen} files_used=0 "
            f"patches_parsed=0 patches_written=0 out_file={args.out_file}"
        )
        return 0

    selected = _select_files(input_files, args.max_files)
    files_used = len(selected)

    if args.print_sources:
        print("[learning_apply] Sources (processed order; newest last):")
        for p in selected:
            print(f"  - {p}")

    overrides: Dict[str, Any] = {}
    for p in selected:
        patches = _read_patches_from_file(p)
        patches_parsed += len(patches)

        for patch in patches:
            item = _patch_to_override(patch)
            if item is None:
                # Optional: warn only for clearly intended objects
                continue
            k, v = item
            if isinstance(v, (dict, list)):
                continue
            overrides[k] = v  # last write wins (deterministic due to processing order)

    # Filter to TOML scalars only
    scalar_overrides = {k: v for k, v in overrides.items() if _toml_format_value(v) is not None}
    patches_written = len(scalar_overrides)

    if args.dry_run:
        print("[learning_apply] Dry-run: planned overrides (sorted):")
        for k in sorted(scalar_overrides.keys()):
            print(f"  - {k} = {scalar_overrides[k]!r}")
        print(
            f"[learning_apply] Summary: files_seen={files_seen} files_used={files_used} "
            f"patches_parsed={patches_parsed} patches_written={patches_written} out_file={args.out_file}"
        )
        return 0

    print(f"[learning_apply] REFUSED: {LEARNING_APPLY_WRITE_FORBIDDEN}")
    print(
        f"[learning_apply] Summary: files_seen={files_seen} files_used={files_used} "
        f"patches_parsed={patches_parsed} patches_written=0 write_forbidden=true "
        f"out_file={args.out_file}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
