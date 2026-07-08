"""
PR4985 post-merge runtime activation materiality classifier v0.

Read-only scanner/classifier for distinguishing true material runtime activation
from negative contract fixtures, docstring examples, and guarded execution
infrastructure. Fail-closed: ambiguous non-test/non-docstring paths remain material.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

CLASSIFIER_LAYER_VERSION = "v0"
CLASSIFIER_OWNER = "trading.master_v2.pr4985_runtime_activation_materiality_classifier_v0"
CLASSIFIER_SLICE_ID = "PR4985_RUNTIME_ACTIVATION_MATERIALITY_CLASSIFIER_V0"

AUTHORITY_TOKENS: tuple[str, ...] = (
    "LIVE_AUTHORIZED",
    "ORDERS_ALLOWED",
    "SCHEDULER_RUNTIME_ALLOWED",
    "SHADOW_AUTHORIZED",
    "PAPER_AUTHORIZED",
    "TESTNET_AUTHORIZED",
    "CANARY_AUTHORIZED",
    "FULL_AUTONOMOUS_PRODUCTION_AUTHORIZED",
)

RUNTIME_REWIRE_TOKENS: tuple[str, ...] = ("RUNTIME_ACTIVATION", "RUNTIME_REWIRE")

FINAL_FLAG_NAMES: tuple[str, ...] = (
    "FULL_CANONICAL_CHAIN_WIRED",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE",
)

EXECUTION_ACTION_NAMES: frozenset[str] = frozenset(
    {
        "activate_runtime",
        "runtime_activate",
        "activate_live",
        "arm_live",
        "enable_live",
        "submit_order",
        "place_order",
        "cancel_order",
        "send_order",
    }
)

GUARDED_INFRASTRUCTURE_PATH_PREFIXES: tuple[str, ...] = (
    "src/execution/",
    "src/exchange/dummy_client.py",
    "src/exchange/base.py",
    "src/exchange/__init__.py",
    "src/exchange/kraken_live.py",
    "src/execution/broker/adapter.py",
    "src/live/safety.py",
    "src/orders/exchange.py",
)

EXECUTION_SCAN_EXCLUDE_NAME_MARKERS: tuple[str, ...] = (
    "test",
    "contract",
    "interface",
    "protocol",
)

AuthorityClassification = Literal["negative_fixture", "material"]
ExecutionClassification = Literal[
    "docstring_example",
    "guarded_infrastructure",
    "material",
]

_AUTHORITY_TRUE_RE = re.compile(
    r"\b("
    + "|".join(re.escape(token) for token in (*AUTHORITY_TOKENS, *RUNTIME_REWIRE_TOKENS))
    + r")\s*[:=]\s*true\b",
    re.IGNORECASE,
)

_FINAL_FLAG_TRUE_RE = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in FINAL_FLAG_NAMES) + r")\s*[:=]\s*True\b",
)

_NEGATIVE_FIXTURE_LINE_RE = re.compile(
    r"review_.*evidence|guard|forbidden|not imply|does not imply|MUST_NOT|NO_|"
    r"blocked|BLOCKED|fail.closed|fail-closed|assert.*not|assert_not|must not|"
    r"must_not|forbid|literal|token|scan|grep|expected.*false|expected.*not|"
    r"NEGATIVE|negative",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClassifierHitV0:
    path: str
    line: int
    text: str
    classification: str
    reason: str


@dataclass(frozen=True)
class RuntimeActivationMaterialityResultV0:
    direct_true_flag_assignment: bool
    runtime_authority_true_material: bool
    execution_action_call_material: bool
    runtime_activation: bool
    authority_true_negative_fixture_hits: tuple[ClassifierHitV0, ...]
    authority_true_material_hits: tuple[ClassifierHitV0, ...]
    execution_docstring_example_hits: tuple[ClassifierHitV0, ...]
    execution_guarded_infrastructure_hits: tuple[ClassifierHitV0, ...]
    execution_material_activation_hits: tuple[ClassifierHitV0, ...]


def _normalize_rel_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_negative_contract_test_path(rel_path: str) -> bool:
    return rel_path.startswith("tests/ops/") and "_contract" in rel_path


def _is_guarded_infrastructure_path(rel_path: str) -> bool:
    return any(
        rel_path == prefix or rel_path.startswith(prefix)
        for prefix in GUARDED_INFRASTRUCTURE_PATH_PREFIXES
    )


def _should_scan_execution_source(rel_path: str) -> bool:
    if not rel_path.startswith("src/"):
        return False
    if "/tests/" in rel_path or rel_path.startswith("tests/"):
        return False
    name = Path(rel_path).name.lower()
    return not any(marker in name for marker in EXECUTION_SCAN_EXCLUDE_NAME_MARKERS)


def _line_in_docstring_ranges(line: int, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(start <= line <= end for start, end in ranges)


def _docstring_ranges(tree: ast.AST) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.body:
            continue
        first = node.body[0]
        if not isinstance(first, ast.Expr):
            continue
        if not isinstance(first.value, ast.Constant):
            continue
        if not isinstance(first.value.value, str):
            continue
        start = first.lineno
        end = first.end_lineno or start
        ranges.append((start, end))
    return ranges


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _line_is_doctest_example(source_lines: Sequence[str], line: int) -> bool:
    if line <= 0 or line > len(source_lines):
        return False
    return source_lines[line - 1].lstrip().startswith(">>>")


def _line_is_string_literal_fixture(source_lines: Sequence[str], line: int) -> bool:
    if line <= 0 or line > len(source_lines):
        return False
    stripped = source_lines[line - 1].strip()
    return stripped.startswith(('"', "'")) or stripped.startswith(("(", "[", "{"))


def _is_negative_guard_script_path(rel_path: str) -> bool:
    name = Path(rel_path).name
    return rel_path.startswith("scripts/ops/review_") and "evidence" in name


def _classify_authority_line(
    *,
    rel_path: str,
    line: int,
    text: str,
    source_lines: Sequence[str],
) -> AuthorityClassification:
    if rel_path.startswith("tests/"):
        return "negative_fixture"
    if _NEGATIVE_FIXTURE_LINE_RE.search(text):
        return "negative_fixture"
    if _is_negative_contract_test_path(rel_path):
        return "negative_fixture"
    if _is_negative_guard_script_path(rel_path):
        return "negative_fixture"
    if _line_is_string_literal_fixture(source_lines, line) and (
        rel_path.startswith("tests/") or rel_path.startswith("scripts/ops/")
    ):
        return "negative_fixture"
    if re.search(
        r'["\'].*\b(?:' + "|".join(AUTHORITY_TOKENS) + r")\b.*true.*[\"']",
        text,
        re.I,
    ):
        return "negative_fixture"
    if rel_path.startswith("src/") and "forbidden" in text.lower():
        return "negative_fixture"
    if rel_path.startswith("src/") and "not allowed" in text.lower():
        return "negative_fixture"
    return "material"


def _file_has_material_authority_assignment(source: str) -> bool:
    tree = ast.parse(source)
    authority_names = {token.lower() for token in AUTHORITY_TOKENS}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value_is_true = isinstance(node.value, ast.Constant) and node.value.value is True
        if not value_is_true:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.lower() in authority_names:
                return True
    return False


def _classify_execution_call(
    *,
    rel_path: str,
    line: int,
    text: str,
    docstring_ranges: Sequence[tuple[int, int]],
    source_lines: Sequence[str],
    file_has_material_authority: bool,
) -> ExecutionClassification:
    if _line_in_docstring_ranges(line, docstring_ranges) or _line_is_doctest_example(
        source_lines, line
    ):
        return "docstring_example"
    if _is_guarded_infrastructure_path(rel_path) and not file_has_material_authority:
        return "guarded_infrastructure"
    if _is_guarded_infrastructure_path(rel_path):
        return "material"
    return "material"


def _scan_authority_true_hits(
    repo_root: Path,
) -> tuple[list[ClassifierHitV0], list[ClassifierHitV0], list[dict[str, object]]]:
    negative: list[ClassifierHitV0] = []
    material: list[ClassifierHitV0] = []
    decisions: list[dict[str, object]] = []
    scan_roots = ("src", "scripts", "tests")
    for root_name in scan_roots:
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".md", ".sh"}:
                continue
            rel_path = _normalize_rel_path(path, repo_root)
            source_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line_no, line in enumerate(source_lines, start=1):
                if not _AUTHORITY_TRUE_RE.search(line):
                    continue
                classification = _classify_authority_line(
                    rel_path=rel_path,
                    line=line_no,
                    text=line,
                    source_lines=source_lines,
                )
                hit = ClassifierHitV0(
                    path=rel_path,
                    line=line_no,
                    text=line.strip(),
                    classification=classification,
                    reason=f"authority_true:{classification}",
                )
                decisions.append(
                    {
                        "path": rel_path,
                        "line": line_no,
                        "classification": classification,
                        "category": "authority_true",
                    }
                )
                if classification == "negative_fixture":
                    negative.append(hit)
                else:
                    material.append(hit)
    return negative, material, decisions


def _scan_direct_true_flag_assignment(repo_root: Path) -> bool:
    scan_roots = (repo_root / "src", repo_root / "scripts", repo_root / "docs")
    for root in scan_roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel_path = _normalize_rel_path(path, repo_root)
            if _is_negative_contract_test_path(rel_path):
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if _FINAL_FLAG_TRUE_RE.search(line):
                    return True
    return False


def _scan_execution_action_hits(
    repo_root: Path,
) -> tuple[
    list[ClassifierHitV0],
    list[ClassifierHitV0],
    list[ClassifierHitV0],
    list[dict[str, object]],
]:
    docstring_hits: list[ClassifierHitV0] = []
    guarded_hits: list[ClassifierHitV0] = []
    material_hits: list[ClassifierHitV0] = []
    decisions: list[dict[str, object]] = []

    src_root = repo_root / "src"
    if not src_root.is_dir():
        return docstring_hits, guarded_hits, material_hits, decisions

    for path in sorted(src_root.rglob("*.py")):
        rel_path = _normalize_rel_path(path, repo_root)
        if not _should_scan_execution_source(rel_path):
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        source_lines = source.splitlines()
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            for line_no, line in enumerate(source_lines, start=1):
                if not any(re.search(rf"\b{name}\s*\(", line) for name in EXECUTION_ACTION_NAMES):
                    continue
                hit = ClassifierHitV0(
                    path=rel_path,
                    line=line_no,
                    text=line.strip(),
                    classification="material",
                    reason="execution_call:syntax_error_fail_closed",
                )
                material_hits.append(hit)
                decisions.append(
                    {
                        "path": rel_path,
                        "line": line_no,
                        "classification": "material",
                        "category": "execution_call",
                        "reason": "syntax_error_fail_closed",
                    }
                )
            continue

        docstring_ranges = _docstring_ranges(tree)
        file_has_material_authority = _file_has_material_authority_assignment(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name not in EXECUTION_ACTION_NAMES:
                continue
            line_no = node.lineno
            line_text = source_lines[line_no - 1] if 0 < line_no <= len(source_lines) else ""
            classification = _classify_execution_call(
                rel_path=rel_path,
                line=line_no,
                text=line_text,
                docstring_ranges=docstring_ranges,
                source_lines=source_lines,
                file_has_material_authority=file_has_material_authority,
            )
            hit = ClassifierHitV0(
                path=rel_path,
                line=line_no,
                text=line_text.strip(),
                classification=classification,
                reason=f"execution_call:{classification}",
            )
            decisions.append(
                {
                    "path": rel_path,
                    "line": line_no,
                    "classification": classification,
                    "category": "execution_call",
                }
            )
            if classification == "docstring_example":
                docstring_hits.append(hit)
            elif classification == "guarded_infrastructure":
                guarded_hits.append(hit)
            else:
                material_hits.append(hit)

    return docstring_hits, guarded_hits, material_hits, decisions


def classify_runtime_activation_materiality_v0(
    repo_root: Path,
) -> RuntimeActivationMaterialityResultV0:
    """Classify runtime activation materiality for the current repo tree."""
    authority_negative, authority_material, authority_decisions = _scan_authority_true_hits(
        repo_root
    )
    (
        execution_docstring,
        execution_guarded,
        execution_material,
        execution_decisions,
    ) = _scan_execution_action_hits(repo_root)

    direct_true_flag_assignment = _scan_direct_true_flag_assignment(repo_root)
    runtime_authority_true_material = bool(authority_material)
    execution_action_call_material = bool(execution_material)
    runtime_activation = (
        direct_true_flag_assignment
        or runtime_authority_true_material
        or execution_action_call_material
    )

    return RuntimeActivationMaterialityResultV0(
        direct_true_flag_assignment=direct_true_flag_assignment,
        runtime_authority_true_material=runtime_authority_true_material,
        execution_action_call_material=execution_action_call_material,
        runtime_activation=runtime_activation,
        authority_true_negative_fixture_hits=tuple(authority_negative),
        authority_true_material_hits=tuple(authority_material),
        execution_docstring_example_hits=tuple(execution_docstring),
        execution_guarded_infrastructure_hits=tuple(execution_guarded),
        execution_material_activation_hits=tuple(execution_material),
    )


def _format_hit_lines(hits: Sequence[ClassifierHitV0]) -> str:
    if not hits:
        return ""
    return "\n".join(f"{hit.path}:{hit.line}:{hit.text}" for hit in hits) + "\n"


def write_classifier_evidence_files_v0(
    evidence_dir: Path,
    result: RuntimeActivationMaterialityResultV0,
    *,
    authority_decisions: Sequence[dict[str, object]] | None = None,
    execution_decisions: Sequence[dict[str, object]] | None = None,
) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "authority_true_negative_fixture_hits.txt").write_text(
        _format_hit_lines(result.authority_true_negative_fixture_hits),
        encoding="utf-8",
    )
    (evidence_dir / "authority_true_material_hits.txt").write_text(
        _format_hit_lines(result.authority_true_material_hits),
        encoding="utf-8",
    )
    authority_payload = {
        "negative_fixture_hits": [
            hit.__dict__ for hit in result.authority_true_negative_fixture_hits
        ],
        "material_hits": [hit.__dict__ for hit in result.authority_true_material_hits],
        "decisions": list(authority_decisions or ()),
    }
    (evidence_dir / "authority_true_classifier_decisions.json").write_text(
        json.dumps(authority_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "execution_docstring_example_hits.txt").write_text(
        _format_hit_lines(result.execution_docstring_example_hits),
        encoding="utf-8",
    )
    (evidence_dir / "execution_guarded_infrastructure_hits.txt").write_text(
        _format_hit_lines(result.execution_guarded_infrastructure_hits),
        encoding="utf-8",
    )
    (evidence_dir / "execution_material_activation_hits.txt").write_text(
        _format_hit_lines(result.execution_material_activation_hits),
        encoding="utf-8",
    )
    execution_payload = {
        "docstring_example_hits": [hit.__dict__ for hit in result.execution_docstring_example_hits],
        "guarded_infrastructure_hits": [
            hit.__dict__ for hit in result.execution_guarded_infrastructure_hits
        ],
        "material_activation_hits": [
            hit.__dict__ for hit in result.execution_material_activation_hits
        ],
        "decisions": list(execution_decisions or ()),
    }
    (evidence_dir / "execution_classifier_decisions.json").write_text(
        json.dumps(execution_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def classify_source_snippet_v0(
    *,
    rel_path: str,
    source: str,
) -> RuntimeActivationMaterialityResultV0:
    """Classify a single in-memory source snippet (used by contract tests)."""
    repo_root = Path("/tmp/pr4985_runtime_activation_classifier_snippet")
    path = repo_root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")

    authority_negative: list[ClassifierHitV0] = []
    authority_material: list[ClassifierHitV0] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        if not _AUTHORITY_TRUE_RE.search(line):
            continue
        classification = _classify_authority_line(
            rel_path=rel_path,
            line=line_no,
            text=line,
            source_lines=source.splitlines(),
        )
        hit = ClassifierHitV0(
            path=rel_path,
            line=line_no,
            text=line.strip(),
            classification=classification,
            reason=f"authority_true:{classification}",
        )
        if classification == "negative_fixture":
            authority_negative.append(hit)
        else:
            authority_material.append(hit)

    direct_true_flag_assignment = any(
        _FINAL_FLAG_TRUE_RE.search(line) for line in source.splitlines()
    )

    docstring_hits: list[ClassifierHitV0] = []
    guarded_hits: list[ClassifierHitV0] = []
    material_hits: list[ClassifierHitV0] = []
    if rel_path.endswith(".py") and _should_scan_execution_source(rel_path):
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=rel_path)
        docstring_ranges = _docstring_ranges(tree)
        file_has_material_authority = _file_has_material_authority_assignment(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name not in EXECUTION_ACTION_NAMES:
                continue
            line_no = node.lineno
            line_text = source_lines[line_no - 1] if 0 < line_no <= len(source_lines) else ""
            classification = _classify_execution_call(
                rel_path=rel_path,
                line=line_no,
                text=line_text,
                docstring_ranges=docstring_ranges,
                source_lines=source_lines,
                file_has_material_authority=file_has_material_authority,
            )
            hit = ClassifierHitV0(
                path=rel_path,
                line=line_no,
                text=line_text.strip(),
                classification=classification,
                reason=f"execution_call:{classification}",
            )
            if classification == "docstring_example":
                docstring_hits.append(hit)
            elif classification == "guarded_infrastructure":
                guarded_hits.append(hit)
            else:
                material_hits.append(hit)

    runtime_authority_true_material = bool(authority_material)
    execution_action_call_material = bool(material_hits)
    runtime_activation = (
        direct_true_flag_assignment
        or runtime_authority_true_material
        or execution_action_call_material
    )
    return RuntimeActivationMaterialityResultV0(
        direct_true_flag_assignment=direct_true_flag_assignment,
        runtime_authority_true_material=runtime_authority_true_material,
        execution_action_call_material=execution_action_call_material,
        runtime_activation=runtime_activation,
        authority_true_negative_fixture_hits=tuple(authority_negative),
        authority_true_material_hits=tuple(authority_material),
        execution_docstring_example_hits=tuple(docstring_hits),
        execution_guarded_infrastructure_hits=tuple(guarded_hits),
        execution_material_activation_hits=tuple(material_hits),
    )
