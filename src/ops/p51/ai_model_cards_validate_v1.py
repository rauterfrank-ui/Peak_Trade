from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "ERROR: missing dependency 'pyyaml'. Add to deps or vendor a minimal YAML parser."
    ) from e


REQUIRED_TOP_LEVEL = {
    "id",
    "provider",
    "model",
    "purpose",
    "data_handling",
    "guardrails",
    "risk",
    "ops",
}

FORBIDDEN_PURPOSE_SUBSTRINGS = [
    "execute trades",
    "place orders",
    "autonomous trading",
    "bypass",
    "disable gate",
]

REQUIRED_GUARDRAILS_KEYS = {"allowed_tasks", "forbidden_tasks", "must_include"}
REQUIRED_DATA_HANDLING_KEYS = {"pii", "secrets", "storage"}
REQUIRED_RISK_KEYS = {"level", "rationale"}
REQUIRED_OPS_KEYS = {"owner", "last_reviewed_utc"}


@dataclass(frozen=True)
class Violation:
    path: str
    msg: str


def _load_yaml(p: Path) -> Any:
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _as_dict(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise TypeError(f"expected dict, got {type(obj).__name__}")
    return obj  # type: ignore[return-value]


def validate_one(p: Path) -> list[Violation]:
    v: list[Violation] = []
    try:
        obj = _as_dict(_load_yaml(p))
    except Exception as e:
        return [Violation(str(p), f"invalid YAML: {e}")]

    missing = sorted(REQUIRED_TOP_LEVEL - set(obj.keys()))
    if missing:
        v.append(Violation(str(p), f"missing top-level keys: {missing}"))

    purpose = str(obj.get("purpose", "")).lower()
    for s in FORBIDDEN_PURPOSE_SUBSTRINGS:
        if s in purpose:
            v.append(Violation(str(p), f"forbidden substring in purpose: {s!r}"))

    # nested sections
    for sect, req in [
        ("guardrails", REQUIRED_GUARDRAILS_KEYS),
        ("data_handling", REQUIRED_DATA_HANDLING_KEYS),
        ("risk", REQUIRED_RISK_KEYS),
        ("ops", REQUIRED_OPS_KEYS),
    ]:
        sec_obj = obj.get(sect)
        if not isinstance(sec_obj, dict):
            v.append(Violation(str(p), f"{sect} must be a mapping"))
            continue
        miss2 = sorted(req - set(sec_obj.keys()))
        if miss2:
            v.append(Violation(str(p), f"missing {sect} keys: {miss2}"))

    # explicit forbiddens include "place_orders"/"withdraw_funds"/"bypass_gates"
    guard = obj.get("guardrails", {})
    if isinstance(guard, dict):
        forb = guard.get("forbidden_tasks", [])
        if isinstance(forb, list):
            must_forbid = {"place_orders", "withdraw_funds", "bypass_gates"}
            have = {str(x) for x in forb}
            miss_forb = sorted(must_forbid - have)
            if miss_forb:
                v.append(Violation(str(p), f"guardrails.forbidden_tasks missing: {miss_forb}"))

        must_inc = guard.get("must_include", [])
        if isinstance(must_inc, list):
            needle = "deny-by-default"
            if not any(needle in str(x).lower() for x in must_inc):
                v.append(Violation(str(p), f"guardrails.must_include must mention '{needle}'"))

    return v


def validate_paths(paths: list[Path]) -> list[Violation]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted([*p.glob("*.yml"), *p.glob("*.yaml")]))
        else:
            files.append(p)
    files = [f for f in files if f.exists()]
    if not files:
        return [Violation("<paths>", "no model card YAML files found")]

    out: list[Violation] = []
    for f in files:
        out.extend(validate_one(f))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="+", required=True)
    args = ap.parse_args(argv)

    paths = [Path(x) for x in args.paths]
    viols = validate_paths(paths)
    if viols:
        for vi in viols:
            print(f"{vi.path}: {vi.msg}")
        return 2
    print("OK: ai model cards validate v1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
