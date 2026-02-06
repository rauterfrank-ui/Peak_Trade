#!/usr/bin/env python3
"""
AI Matrix vs Model Registry validator (P0+P1)

P0:
- Parse authoritative AI autonomy matrix (MD table) and cross-check layer mapping in config/model_registry.toml.
- Enforce Separation-of-Duties (SoD): critic != primary where critic is defined.
- Ensure model_registry Reference points to authoritative matrix path.
- CI-friendly output + exit codes.

P1:
- Matrix schema guardrails:
  - Required columns exist in table header
  - No duplicate layer rows
- Models referenced in matrix exist in model_registry.toml (keys and optional model_id fields)
- Capability scopes cross-check (best-effort):
  - If scope file exists for L0..L4 in config/capability_scopes/, it must contain matching layer_id
  - (No hard requirement that every layer must have a scope file yet)

Exit codes:
  - 0: PASS
  - 2: FAIL (violations)
  - 1: unexpected error
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass(frozen=True)
class Violation:
    code: str
    msg: str


EXPECTED_LAYER_IDS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
AUTHORITATIVE_MATRIX_PATH = "docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"


# Best-effort expected scope file locations (you can expand later)
DEFAULT_SCOPE_FILES = {
    "L0": "config/capability_scopes/L0_ops_docs.toml",
    "L1": "config/capability_scopes/L1_deep_research.toml",
    "L2": "config/capability_scopes/L2_market_outlook.toml",
    "L3": "config/capability_scopes/L3_trade_plan_advisory.toml",
    "L4": "config/capability_scopes/L4_governance_critic.toml",
    # L5/L6 are deterministic/forbidden; typically no scope file
}


def _fail(violations: list[Violation]) -> int:
    for v in violations:
        print(f"[FAIL] {v.code}: {v.msg}")
    print(f"[SUMMARY] violations={len(violations)}")
    return 2


def _pass() -> int:
    print("[PASS] AI matrix vs registry validation OK")
    return 0


def _strip_md(x: str) -> str:
    x = x.strip()
    x = x.replace("**", "").replace("`", "").replace("*", "")
    return x.strip()


def _norm_model(x: Any) -> str:
    if x is None:
        return "none"
    s = _strip_md(str(x))
    if s in ("", "-", "—", "none", "null", "None", "(kein LLM)"):
        return "none"
    return s


def _split_fallback(cell: str) -> list[str]:
    c = _strip_md(cell)
    if c in ("", "-", "—", "none", "null", "None"):
        return []
    parts = [p.strip() for p in re.split(r"[,\n]+", c) if p.strip()]
    return parts


def _extract_matrix_table_block(md_text: str) -> tuple[Optional[str], list[str]]:
    """
    Returns (header_line, row_lines) for the first markdown table that contains a '| **L0** |' row.
    """
    lines = md_text.splitlines()
    header = None
    rows: list[str] = []
    in_table = False

    for i, line in enumerate(lines):
        if "|" not in line:
            if in_table and rows:
                break
            continue

        # detect potential header: line starting with '|' and contains 'Layer' token
        if (
            not in_table
            and line.lstrip().startswith("|")
            and re.search(r"\bLayer\b", line, re.IGNORECASE)
        ):
            # next line should be separator '---'
            if i + 1 < len(lines) and re.match(r"^\s*\|?\s*[-: ]+\|", lines[i + 1]):
                header = line.rstrip()
                in_table = True
                continue

        if in_table:
            # skip separator row (|---|---|)
            if re.match(r"^\s*\|?\s*[-: ]+\|", line):
                continue
            if line.strip() == "":
                if rows:
                    break
                continue
            rows.append(line.rstrip())

    # ensure it's the table we want (contains a layer row)
    if header and any("| **L0**" in r for r in rows):
        return header, rows
    return None, []


def parse_matrix_md(md_text: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """
    Parses rows like: | **L2** | ... |
    Returns:
      - layers: dict[layer_id] -> {autonomy, primary, fallback(list), critic}
      - meta: {duplicates: set[str], header_cols: list[str]}
    """
    header, row_lines = _extract_matrix_table_block(md_text)
    meta: dict[str, Any] = {"duplicates": set(), "header_cols": []}
    layers: dict[str, dict[str, Any]] = {}

    if header:
        meta["header_cols"] = [c.strip() for c in header.strip().strip("|").split("|")]

    for line in row_lines:
        if not line.lstrip().startswith("|"):
            continue
        if "| **L" not in line:
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 7:
            continue

        layer = _strip_md(cols[0])
        if layer not in EXPECTED_LAYER_IDS:
            continue

        autonomy = _strip_md(cols[3])
        primary = _norm_model(cols[4])
        fallback = _split_fallback(cols[5])
        critic = _norm_model(cols[6])

        if layer in layers:
            meta["duplicates"].add(layer)

        layers[layer] = {
            "autonomy": autonomy,
            "primary": primary,
            "fallback": fallback,
            "critic": critic,
        }

    return layers, meta


def read_registry(toml_text: str) -> dict[str, Any]:
    return tomllib.loads(toml_text)


def _get_ref_line(reg_toml: str) -> Optional[str]:
    for line in reg_toml.splitlines():
        # allow "Reference:" and "# Reference:" in same manner
        if re.match(r"^\s*#?\s*Reference:\s*", line):
            return line.strip()
    return None


def _load_layer_mapping(reg: dict[str, Any]) -> dict[str, Any]:
    lm = reg.get("layer_mapping")
    return lm if isinstance(lm, dict) else {}


def _models_defined(reg: dict[str, Any]) -> set[str]:
    """
    Collects model identifiers that can be referenced from the matrix:
    - keys under [models]
    - optional model_id fields inside each model entry
    """
    models = reg.get("models")
    if not isinstance(models, dict):
        return set()

    out: set[str] = set()
    for k, v in models.items():
        out.add(str(k))
        if isinstance(v, dict):
            mid = v.get("model_id")
            if mid:
                out.add(str(mid))
    return out


def _check_capability_scopes(violations: list[Violation], repo_root: Path) -> None:
    """
    Best-effort cross-check: if a scope file exists, ensure it declares the matching layer_id.
    (Does not require that every layer has a scope file.)
    """
    for lid, rel in DEFAULT_SCOPE_FILES.items():
        p = repo_root / rel
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        # simple invariant: must contain layer_id = "Lx"
        if f'layer_id = "{lid}"' not in txt:
            violations.append(
                Violation(
                    "SCOPE_LAYER_MISMATCH",
                    f'{rel} does not declare layer_id = "{lid}"',
                )
            )


def main(matrix_path: str, registry_path: str) -> int:
    violations: list[Violation] = []
    try:
        mp = Path(matrix_path)
        rp = Path(registry_path)
        repo_root = Path.cwd()

        if not mp.exists():
            return _fail([Violation("MATRIX_NOT_FOUND", f"{matrix_path} missing")])
        if not rp.exists():
            return _fail([Violation("REGISTRY_NOT_FOUND", f"{registry_path} missing")])

        md = mp.read_text(encoding="utf-8")
        reg_text = rp.read_text(encoding="utf-8")
        reg = read_registry(reg_text)

        # Reference must point to authoritative matrix path
        ref_line = _get_ref_line(reg_text)
        if ref_line is None:
            violations.append(
                Violation(
                    "REGISTRY_REFERENCE_MISSING",
                    "model_registry.toml missing 'Reference:' line",
                )
            )
        else:
            if AUTHORITATIVE_MATRIX_PATH not in ref_line:
                violations.append(
                    Violation(
                        "REGISTRY_REFERENCE_DRIFT",
                        f"Reference must point to {AUTHORITATIVE_MATRIX_PATH} (got: {ref_line})",
                    )
                )

        md_layers, meta = parse_matrix_md(md)
        if not md_layers:
            violations.append(
                Violation(
                    "MATRIX_PARSE_EMPTY",
                    "Failed to parse any layer rows from matrix table",
                )
            )

        # P1 schema: header columns + duplicates
        header_cols = meta.get("header_cols", [])
        if not header_cols:
            violations.append(
                Violation("MATRIX_HEADER_MISSING", "Could not locate matrix table header")
            )
        else:
            required = {"Layer", "Autonomy", "Primary", "Fallback", "Critic"}
            present = {re.sub(r"\s+", " ", c).strip() for c in header_cols}
            for tok in required:
                if not any(re.search(rf"\b{re.escape(tok)}\b", c, re.IGNORECASE) for c in present):
                    violations.append(
                        Violation(
                            "MATRIX_HEADER_COL_MISSING",
                            f"Matrix table missing required column token: {tok}",
                        )
                    )

        dups = meta.get("duplicates", set())
        if dups:
            violations.append(
                Violation(
                    "MATRIX_DUPLICATE_LAYER_ROWS",
                    f"Duplicate layer rows: {sorted(dups)}",
                )
            )

        # Enforce expected layers exist in matrix
        for lid in EXPECTED_LAYER_IDS:
            if lid not in md_layers:
                violations.append(
                    Violation("MATRIX_LAYER_MISSING", f"Matrix missing row for {lid}")
                )

        lm = _load_layer_mapping(reg)
        if not lm:
            violations.append(
                Violation(
                    "REGISTRY_LAYER_MAPPING_MISSING",
                    "registry missing [layer_mapping] table",
                )
            )

        # Cross-check matrix vs registry mapping
        for lid in EXPECTED_LAYER_IDS:
            m = md_layers.get(lid)
            r = lm.get(lid) if isinstance(lm, dict) else None
            if m is None or r is None:
                if m is None:
                    continue
                violations.append(
                    Violation(
                        "REGISTRY_LAYER_MISSING",
                        f"registry.layer_mapping missing {lid}",
                    )
                )
                continue

            r_autonomy = _strip_md(str(r.get("autonomy", "")))
            if r_autonomy != m["autonomy"]:
                violations.append(
                    Violation(
                        "DRIFT_AUTONOMY",
                        f"{lid}.autonomy md={m['autonomy']} reg={r_autonomy}",
                    )
                )

            r_primary = _norm_model(r.get("primary"))
            if r_primary != m["primary"]:
                violations.append(
                    Violation(
                        "DRIFT_PRIMARY",
                        f"{lid}.primary md={m['primary']} reg={r_primary}",
                    )
                )

            rf = r.get("fallback")
            if isinstance(rf, str):
                r_fallback = [_norm_model(rf)] if _norm_model(rf) != "none" else []
            elif isinstance(rf, list):
                r_fallback = [_norm_model(x) for x in rf if _norm_model(x) != "none"]
            elif rf is None:
                r_fallback = []
            else:
                r_fallback = [_norm_model(str(rf))] if _norm_model(str(rf)) != "none" else []

            if r_fallback != m["fallback"]:
                violations.append(
                    Violation(
                        "DRIFT_FALLBACK",
                        f"{lid}.fallback md={m['fallback']} reg={r_fallback}",
                    )
                )

            r_critic = _norm_model(r.get("critic"))
            if r_critic != m["critic"]:
                violations.append(
                    Violation(
                        "DRIFT_CRITIC",
                        f"{lid}.critic md={m['critic']} reg={r_critic}",
                    )
                )

            # SoD: critic != primary when critic is defined
            if m["critic"] != "none" and m["primary"] != "none" and m["critic"] == m["primary"]:
                violations.append(
                    Violation(
                        "SOD_VIOLATION",
                        f"{lid}: critic_model must differ from primary_model",
                    )
                )

        # P1 models existence
        defined_models = _models_defined(reg)
        if defined_models:
            for lid in EXPECTED_LAYER_IDS:
                m = md_layers.get(lid)
                if not m:
                    continue
                for k in ("primary", "critic"):
                    mid = m[k]
                    if mid != "none" and mid not in defined_models:
                        violations.append(
                            Violation(
                                "MODEL_UNDEFINED",
                                f"{lid}.{k}={mid} not defined in registry.models",
                            )
                        )
                for mid in m["fallback"]:
                    if mid != "none" and mid not in defined_models:
                        violations.append(
                            Violation(
                                "MODEL_UNDEFINED",
                                f"{lid}.fallback={mid} not defined in registry.models",
                            )
                        )

        # P1 capability scopes (best-effort)
        _check_capability_scopes(violations, repo_root)

        if violations:
            return _fail(violations)
        return _pass()

    except SystemExit:
        raise
    except Exception as e:
        print(f"[FAIL] UNEXPECTED_ERROR: {e}")
        print("[SUMMARY] violations=1")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: validate_ai_matrix_vs_registry.py <matrix.md> <model_registry.toml>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
