#!/usr/bin/env python3
"""Emit a temporary scheduler jobs.toml with one job enabled and an absolute outdir.

Planner-only / CI: does not run the scheduler or any paper runtime.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # pragma: no cover - py<3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef,import-untyped]

USAGE_EXIT = 2


def _toml_escape_basic(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _split_job_block_ranges(lines: list[str]) -> list[tuple[int, int]]:
    starts = [i for i, line in enumerate(lines) if line.strip() == "[[job]]"]
    ranges: list[tuple[int, int]] = []
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        ranges.append((start, end))
    return ranges


def _job_name_in_block(block: str) -> str | None:
    m = re.search(r"(?m)^name\s*=\s*\"([^\"]*)\"\s*$", block)
    return m.group(1) if m else None


def _find_target_block_range(lines: list[str], job_name: str) -> tuple[int, int]:
    ranges = _split_job_block_ranges(lines)
    hits: list[int] = []
    for idx, (start, end) in enumerate(ranges):
        block = "".join(lines[start:end])
        name = _job_name_in_block(block)
        if name == job_name:
            hits.append(idx)
    if not hits:
        raise ValueError(f"Kein Job mit name={job_name!r} gefunden")
    if len(hits) > 1:
        raise ValueError(f"Mehrdeutig: {len(hits)} Blöcke mit name={job_name!r}")
    return ranges[hits[0]]


def _patch_job_block(block: str, absolute_outdir: str) -> str:
    esc = _toml_escape_basic(absolute_outdir)
    out_lines: list[str] = []
    enabled_ok = False
    outdir_ok = False

    for line in block.splitlines(keepends=True):
        if re.match(r"^\s*enabled\s*=\s*false\s*$", line):
            out_lines.append(re.sub(r"\bfalse\b", "true", line, count=1))
            enabled_ok = True
        elif re.match(r"^\s*enabled\s*=\s*true\s*$", line):
            out_lines.append(line)
            enabled_ok = True
        elif re.match(r"^\s*outdir\s*=\s*\"[^\"]*\"\s*$", line):
            indent_m = re.match(r"^(\s*)", line)
            indent = indent_m.group(1) if indent_m else ""
            out_lines.append(f'{indent}outdir = "{esc}"\n')
            outdir_ok = True
        elif "args" in line and "{" in line and "outdir" in line:
            new_line, n = re.subn(r"outdir\s*=\s*\"[^\"]*\"", f'outdir = "{esc}"', line, count=1)
            if n:
                outdir_ok = True
            out_lines.append(new_line)
        else:
            out_lines.append(line)

    if not enabled_ok:
        raise ValueError("Konnte enabled-Zeile im Job-Block nicht auf true setzen")
    if not outdir_ok:
        raise ValueError(
            "Unsupported: kein outdir als eigene Zeile und keine inline-args-Zeile mit outdir= gefunden"
        )
    return "".join(out_lines)


def _verify_target_job(data: object, job_name: str, expected_outdir: str) -> None:
    if not isinstance(data, dict):
        raise ValueError("Top-Level TOML ist kein Objekt")
    jobs = data.get("job")
    if not isinstance(jobs, list):
        raise ValueError("job ist keine Liste")
    targets = [j for j in jobs if isinstance(j, dict) and j.get("name") == job_name]
    if len(targets) != 1:
        raise ValueError(
            f"Erwarte genau einen Job {job_name!r} nach dem Parsen, habe {len(targets)}"
        )
    job = targets[0]
    if job.get("enabled") is not True:
        raise ValueError(f"Job {job_name!r} ist nach dem Patch nicht enabled=true")
    args = job.get("args")
    if not isinstance(args, dict):
        raise ValueError(f"Job {job_name!r} hat keine args-Tabelle")
    if args.get("outdir") != expected_outdir:
        raise ValueError(f"outdir mismatch: {args.get('outdir')!r} != {expected_outdir!r}")


def _consume_argv(argv: list[str] | None) -> list[str]:
    """Drop argv[0] when invoked like sys.argv (program name)."""
    if argv is None:
        return sys.argv[1:]
    if argv and not argv[0].startswith("-"):
        return list(argv[1:])
    return list(argv)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Schreibt temporäre scheduler jobs.toml mit absolutem outdir für einen Job."
    )
    parser.add_argument("--source", type=Path, required=True, help="Quell-jobs.toml")
    parser.add_argument(
        "--job",
        required=True,
        help="Exakter Job-Name, z. B. paper_shadow_247_paper_only_runtime_min_v0",
    )
    parser.add_argument(
        "--outdir",
        required=True,
        help="Absoluter Ausgabepfad für run_paper_trading_session (muss absolut sein)",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Zieldatei (Parent muss existieren)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Vorhandene output-Datei überschreiben",
    )
    args_ns = parser.parse_args(_consume_argv(argv))

    outdir_path = Path(args_ns.outdir)
    if not outdir_path.is_absolute():
        print("make_scheduler_temp_config: --outdir muss ein absoluter Pfad sein", file=sys.stderr)
        return USAGE_EXIT

    source: Path = args_ns.source
    output: Path = args_ns.output
    if not source.is_file():
        print(f"make_scheduler_temp_config: Quelle fehlt: {source}", file=sys.stderr)
        return USAGE_EXIT
    if not output.parent.is_dir():
        print(
            f"make_scheduler_temp_config: Parent von --output existiert nicht: {output.parent}",
            file=sys.stderr,
        )
        return USAGE_EXIT
    if output.exists() and not args_ns.force:
        print(
            f"make_scheduler_temp_config: --output existiert schon (nutze --force): {output}",
            file=sys.stderr,
        )
        return USAGE_EXIT

    raw = source.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    try:
        start, end = _find_target_block_range(lines, args_ns.job)
        block = "".join(lines[start:end])
        patched_block = _patch_job_block(block, str(outdir_path))
        new_text = "".join(lines[:start]) + patched_block + "".join(lines[end:])
    except ValueError as exc:
        print(f"make_scheduler_temp_config: {exc}", file=sys.stderr)
        return USAGE_EXIT

    try:
        parsed = tomllib.loads(new_text)
        _verify_target_job(parsed, args_ns.job, str(outdir_path))
    except (OSError, ValueError, TypeError) as exc:
        print(
            f"make_scheduler_temp_config: Ausgabe-TOML-Validierung fehlgeschlagen: {exc}",
            file=sys.stderr,
        )
        return USAGE_EXIT

    output.write_text(new_text, encoding="utf-8")
    print(
        "make_scheduler_temp_config: ok\n"
        f"  job={args_ns.job}\n"
        f"  outdir={outdir_path}\n"
        f"  output={output.resolve()}\n"
        f"  enabled=true (nur dieser Job in der bearbeiteten Datei)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
