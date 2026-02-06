#!/usr/bin/env python3
"""
AI Matrix vs Model Registry validator (P0)
- Parses the authoritative AI autonomy matrix (MD table) and cross-checks layer mapping in config/model_registry.toml.
- Enforces Separation-of-Duties (SoD): critic != primary where critic is defined.
- Ensures model_registry Reference points to the authoritative matrix path.
- CI-friendly output:
  - [FAIL] CODE: message (one per violation)
  - [SUMMARY] violations=N
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
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[assignment]


@dataclass(frozen=True)
class Violation:
    code: str
    msg: str


EXPECTED_LAYER_IDS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
AUTHORITATIVE_MATRIX_PATH = "docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"


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
    # remove bold/italics/code markers
    x = x.replace("**", "").replace("`", "").replace("*", "")
    return x.strip()


def _split_fallback(cell: str) -> list[str]:
    c = _strip_md(cell)
    if c in ("", "-", "—", "none", "null", "None"):
        return []
    # normalize separators: comma or newline
    parts = [p.strip() for p in re.split(r"[,\n]+", c) if p.strip()]
    return parts


def _norm_model(x: str | None) -> str:
    if x is None:
        return "none"
    x = _strip_md(str(x))
    if x in ("", "-", "—", "none", "null", "None", "(kein LLM)"):
        return "none"
    return x


def parse_matrix_md(md_text: str) -> dict[str, dict[str, Any]]:
    """
    Parses rows starting with '| **Lx** |' and extracts:
      layer_id, autonomy, primary, fallback(list), critic
    Assumes the matrix table matches the project's current format.
    """
    rows: dict[str, dict[str, Any]] = {}
    for line in md_text.splitlines():
        line = line.rstrip()
        if not line.lstrip().startswith("|"):
            continue
        # We only care about layer rows like: | **L2** | ... |
        if "| **L" not in line:
            continue

        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        # Defensive: need at least 7 columns to reach critic.
        if len(cols) < 7:
            continue

        layer = _strip_md(cols[0])
        if layer not in EXPECTED_LAYER_IDS:
            continue

        # Expected layout (current repo):
        # 0 layer | 1 layer_name | 2 role/notes | 3 autonomy | 4 primary | 5 fallback | 6 critic | ...
        autonomy = _strip_md(cols[3])
        primary = _norm_model(cols[4])
        fallback = _split_fallback(cols[5])
        critic = _norm_model(cols[6])

        rows[layer] = {
            "autonomy": autonomy,
            "primary": primary,
            "fallback": fallback,
            "critic": critic,
        }

    return rows


def read_registry(toml_text: str) -> dict[str, Any]:
    reg = tomllib.loads(toml_text)
    return reg


def _get_ref_line(reg_toml: str) -> str | None:
    for line in reg_toml.splitlines():
        if "Reference:" in line:
            return line.strip()
    return None


def _load_layer_mapping(reg: dict[str, Any]) -> dict[str, Any]:
    lm = reg.get("layer_mapping")
    if not isinstance(lm, dict):
        return {}
    return lm


def _models_defined(reg: dict[str, Any]) -> set[str]:
    models = reg.get("models")
    if not isinstance(models, dict):
        return set()
    out: set[str] = set()
    for k, v in models.items():
        out.add(str(k))
        if isinstance(v, dict) and "model_id" in v:
            out.add(str(v["model_id"]))
    return out


def main(matrix_path: str, registry_path: str) -> int:
    violations: list[Violation] = []
    try:
        mp = Path(matrix_path)
        rp = Path(registry_path)

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
                    "REGISTRY_REFERENCE_MISSING", "model_registry.toml missing 'Reference:' line"
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

        md_layers = parse_matrix_md(md)
        if not md_layers:
            violations.append(
                Violation("MATRIX_PARSE_EMPTY", "Failed to parse any layer rows from matrix table")
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
                    "REGISTRY_LAYER_MAPPING_MISSING", "registry missing [layer_mapping] table"
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
                    Violation("REGISTRY_LAYER_MISSING", f"registry.layer_mapping missing {lid}")
                )
                continue

            r_autonomy = _strip_md(str(r.get("autonomy", "")))
            if r_autonomy != m["autonomy"]:
                violations.append(
                    Violation(
                        "DRIFT_AUTONOMY", f"{lid}.autonomy md={m['autonomy']} reg={r_autonomy}"
                    )
                )

            r_primary = _norm_model(r.get("primary"))
            if r_primary != m["primary"]:
                violations.append(
                    Violation("DRIFT_PRIMARY", f"{lid}.primary md={m['primary']} reg={r_primary}")
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
                    Violation("DRIFT_CRITIC", f"{lid}.critic md={m['critic']} reg={r_critic}")
                )

            # SoD: critic != primary when critic is defined
            if m["critic"] != "none" and m["primary"] != "none" and m["critic"] == m["primary"]:
                violations.append(
                    Violation(
                        "SOD_VIOLATION",
                        f"{lid}: critic_model must differ from primary_model",
                    )
                )

        # Model existence checks (P1-ish but cheap + useful)
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
