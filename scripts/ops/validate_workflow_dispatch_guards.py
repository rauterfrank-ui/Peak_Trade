#!/usr/bin/env python3
"""
Workflow Dispatch Guard (stdlib-only)

Checks GitHub Actions workflow YAML files for common workflow_dispatch regressions:
- Using github.event.inputs.<name> without defining <name> under on.workflow_dispatch.inputs
- Referencing github.event.inputs in workflows that do NOT include workflow_dispatch
- Accidental use of inputs.<name> (workflow_call context) inside workflow_dispatch workflows
- Provides file:line diagnostics and actionable hints

Design goal: low false positives, no external deps.
Limitations: Inline YAML forms (on: {workflow_dispatch: ...}) are detected but inputs may be "unknown".
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple


INPUT_REF_DOT_RE = re.compile(r"github\.event\.inputs\.([A-Za-z0-9_-]+)")
INPUT_REF_BRACKET_RE = re.compile(r"github\.event\.inputs\[\s*[\"']([A-Za-z0-9_-]+)[\"']\s*\]")
# Common footgun: using "inputs.<name>" which is for workflow_call / reusable workflows, not workflow_dispatch.
MISUSED_INPUTS_DOT_RE = re.compile(r"(?<!github\.event\.)\binputs\.([A-Za-z0-9_-]+)\b")

INLINE_ON_DISPATCH_RE = re.compile(
    r"^\s*[\"']?on[\"']?\s*:\s*(\[[^\]]*\bworkflow_dispatch\b[^\]]*\]|workflow_dispatch\b|{.*\bworkflow_dispatch\b.*})\s*$"
)
# Match both "on": and on: (YAML allows quoting keys; "on" is needed to avoid parsing as boolean)
ON_BLOCK_RE = re.compile(r"^\s*[\"']?on[\"']?\s*:\s*$")
WORKFLOW_DISPATCH_KEY_RE = re.compile(r"^\s*workflow_dispatch:\s*$")
INPUTS_KEY_RE = re.compile(r"^\s*inputs:\s*$")
# Captures YAML keys like:  foo_bar-1:
YAML_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_-]+):\s*(#.*)?$")


@dataclass(frozen=True)
class Finding:
    level: str  # "ERROR" | "WARN"
    path: Path
    line: int
    message: str


@dataclass(frozen=True)
class DispatchInfo:
    has_dispatch: bool
    inputs: Set[str]
    inputs_known: (
        bool  # false when we detect dispatch but can't reliably parse inputs (inline on: {...})
    )


def _read_lines(path: Path) -> List[str]:
    # keep line endings normalized for stable scanning
    return path.read_text(encoding="utf-8").splitlines()


def _indent(s: str) -> int:
    return len(s) - len(s.lstrip(" "))


def _detect_dispatch_and_inputs(lines: List[str]) -> DispatchInfo:
    """
    Heuristic YAML scan:
    - Detects workflow_dispatch presence (block or inline)
    - Extracts input keys under: on: workflow_dispatch: inputs:
    """
    has_dispatch = False
    inputs: Set[str] = set()
    inputs_known = True

    # Fast inline detection: "on: workflow_dispatch" / "on: [workflow_dispatch]" / "on: {workflow_dispatch: ...}"
    for ln in lines:
        if INLINE_ON_DISPATCH_RE.match(ln):
            has_dispatch = True
            # Inline map/list makes stable input extraction unreliable; mark unknown.
            if "{" in ln or "[" in ln:
                inputs_known = False
            break

    # Block-style extraction
    for i, ln in enumerate(lines):
        if not ON_BLOCK_RE.match(ln):
            continue

        on_indent = _indent(ln)
        # Scan until indent <= on_indent (end of on: block)
        j = i + 1
        while j < len(lines):
            cur = lines[j]
            if cur.strip() == "" or cur.lstrip().startswith("#"):
                j += 1
                continue
            if _indent(cur) <= on_indent:
                break

            # Look for workflow_dispatch:
            if WORKFLOW_DISPATCH_KEY_RE.match(cur) and _indent(cur) > on_indent:
                has_dispatch = True
                wd_indent = _indent(cur)

                # Scan inside workflow_dispatch block for inputs:
                k = j + 1
                while k < len(lines):
                    cur2 = lines[k]
                    if cur2.strip() == "" or cur2.lstrip().startswith("#"):
                        k += 1
                        continue
                    if _indent(cur2) <= wd_indent:
                        break

                    if INPUTS_KEY_RE.match(cur2) and _indent(cur2) > wd_indent:
                        inputs_indent = _indent(cur2)
                        # Next-level keys under inputs:
                        m = k + 1
                        while m < len(lines):
                            cur3 = lines[m]
                            if cur3.strip() == "" or cur3.lstrip().startswith("#"):
                                m += 1
                                continue
                            if _indent(cur3) <= inputs_indent:
                                break
                            # key: ...
                            mm = YAML_KEY_RE.match(cur3)
                            if mm and _indent(cur3) > inputs_indent:
                                inputs.add(mm.group(1))
                            m += 1
                    k += 1
            j += 1

    return DispatchInfo(has_dispatch=has_dispatch, inputs=inputs, inputs_known=inputs_known)


def _find_referenced_inputs(lines: List[str]) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for idx, ln in enumerate(lines, start=1):
        for m in INPUT_REF_DOT_RE.finditer(ln):
            out.append((m.group(1), idx))
        for m in INPUT_REF_BRACKET_RE.finditer(ln):
            out.append((m.group(1), idx))
    return out


def _find_misused_inputs_dot(lines: List[str]) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    for idx, ln in enumerate(lines, start=1):
        for m in MISUSED_INPUTS_DOT_RE.finditer(ln):
            out.append((m.group(1), idx))
    return out


def _iter_workflow_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".yml", ".yaml"}:
            yield p


def validate_file(path: Path) -> List[Finding]:
    lines = _read_lines(path)
    info = _detect_dispatch_and_inputs(lines)
    referenced = _find_referenced_inputs(lines)
    misused_inputs = _find_misused_inputs_dot(lines)

    findings: List[Finding] = []

    # If workflow references github.event.inputs but has no workflow_dispatch => error
    if referenced and not info.has_dispatch:
        for name, line in referenced:
            findings.append(
                Finding(
                    level="ERROR",
                    path=path,
                    line=line,
                    message=(
                        f"Referenziert github.event.inputs.{name}, aber Workflow hat kein 'on: workflow_dispatch'. "
                        "Entweder workflow_dispatch aktivieren oder Input-Referenz entfernen/absichern."
                    ),
                )
            )

    # If workflow has workflow_dispatch and inputs are known: verify referenced names exist
    if referenced and info.has_dispatch:
        if info.inputs_known and info.inputs:
            declared = info.inputs
            for name, line in referenced:
                if name not in declared:
                    findings.append(
                        Finding(
                            level="ERROR",
                            path=path,
                            line=line,
                            message=(
                                f"Referenziert github.event.inputs.{name}, aber Input ist nicht unter "
                                "on.workflow_dispatch.inputs definiert. "
                                f"Definiert sind: {sorted(declared)}"
                            ),
                        )
                    )
        elif not info.inputs_known:
            # Dispatch detected but inline; can't reliably know declared inputs => warn only
            for name, line in referenced:
                findings.append(
                    Finding(
                        level="WARN",
                        path=path,
                        line=line,
                        message=(
                            f"workflow_dispatch erkannt (inline 'on:' Form), aber Inputs nicht zuverlässig parsbar. "
                            f"Bitte sicherstellen, dass Input '{name}' in on.workflow_dispatch.inputs definiert ist "
                            "oder 'on:' in block-style schreiben."
                        ),
                    )
                )
        else:
            # Dispatch present but no inputs parsed; if references exist => error (very likely missing inputs section)
            for name, line in referenced:
                findings.append(
                    Finding(
                        level="ERROR",
                        path=path,
                        line=line,
                        message=(
                            f"Referenziert github.event.inputs.{name}, aber keine Inputs unter "
                            "on.workflow_dispatch.inputs gefunden. "
                            "Füge on.workflow_dispatch.inputs.<name> hinzu."
                        ),
                    )
                )

    # Misused "inputs.<name>" inside workflows that have workflow_dispatch is a common confusion (workflow_call vs dispatch).
    if misused_inputs and info.has_dispatch:
        for name, line in misused_inputs:
            findings.append(
                Finding(
                    level="ERROR",
                    path=path,
                    line=line,
                    message=(
                        f"Verdächtig: 'inputs.{name}' gefunden. Für workflow_dispatch bitte "
                        f"'github.event.inputs.{name}' verwenden. "
                        "Wenn es ein reusable workflow (workflow_call) ist, dann ist workflow_dispatch wahrscheinlich falsch."
                    ),
                )
            )

    return findings


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Validate GitHub Actions workflow_dispatch guards.")
    ap.add_argument(
        "--paths",
        nargs="+",
        default=[".github/workflows"],
        help="Paths to scan (files or directories). Default: .github/workflows",
    )
    ap.add_argument("--fail-on-warn", action="store_true", help="Treat WARN as failure.")
    ap.add_argument(
        "--print-ok", action="store_true", help="Print OK lines for files without findings."
    )
    args = ap.parse_args(argv)

    all_findings: List[Finding] = []
    scanned_files: List[Path] = []

    for p_str in args.paths:
        p = Path(p_str)
        if not p.exists():
            continue
        for wf in _iter_workflow_files(p):
            # Only scan .github/workflows by default; allow explicit file paths
            scanned_files.append(wf)
            all_findings.extend(validate_file(wf))

    if not scanned_files:
        print("No workflow files found to scan.", file=sys.stderr)
        return 0

    # Report
    by_file: dict[Path, List[Finding]] = {}
    for f in all_findings:
        by_file.setdefault(f.path, []).append(f)

    exit_code = 0

    for wf in sorted(scanned_files):
        findings = by_file.get(wf, [])
        if not findings and args.print_ok:
            print(f"OK {wf}")
            continue
        for f in sorted(findings, key=lambda x: (x.line, x.level)):
            print(f"{f.level} {f.path}:{f.line} {f.message}")
            if f.level == "ERROR":
                exit_code = 2
            elif f.level == "WARN" and args.fail_on_warn:
                exit_code = max(exit_code, 1)

    if exit_code == 0:
        print(f"OK: scanned {len(scanned_files)} workflow file(s), no findings.")
    else:
        print(
            f"FAILED: scanned {len(scanned_files)} workflow file(s), findings={len(all_findings)}.",
            file=sys.stderr,
        )

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
