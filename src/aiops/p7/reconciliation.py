from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReconciliationIssue:
    code: str
    path: str
    detail: str


@dataclass(frozen=True)
class ReconciliationResult:
    ok: bool
    issues: List[ReconciliationIssue]
    metrics: Dict[str, Any]


def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def reconcile_p7_outdir(p7_dir: Path) -> ReconciliationResult:
    """
    Best-effort reconciliation for a P7 run directory.

    Inputs (expected):
      - p7_fills.json
      - p7_account.json
      - p7_evidence_manifest.json (optional but usually present)

    Current checks (minimal invariants):
      - required files exist
      - fills is a list (or dict with list) and has deterministic schema
      - account has required numeric fields (best-effort)
      - evidence manifest references the produced artifacts (best-effort)
    """
    issues: List[ReconciliationIssue] = []
    metrics: Dict[str, Any] = {}

    fills_p = p7_dir / "p7_fills.json"
    acct_p = p7_dir / "p7_account.json"
    ev_p = p7_dir / "p7_evidence_manifest.json"

    for req in [fills_p, acct_p]:
        if not req.exists():
            issues.append(
                ReconciliationIssue(
                    code="MISSING_FILE", path=str(req), detail="required file missing"
                )
            )

    if issues:
        return ReconciliationResult(ok=False, issues=issues, metrics=metrics)

    fills = _read_json(fills_p)
    acct = _read_json(acct_p)
    ev = _read_json(ev_p) if ev_p.exists() else None

    # fills: accept list OR {"fills":[...]}
    fills_list: Optional[List[Any]] = None
    if isinstance(fills, list):
        fills_list = fills
    elif isinstance(fills, dict) and isinstance(fills.get("fills"), list):
        fills_list = fills["fills"]

    if fills_list is None:
        issues.append(
            ReconciliationIssue(
                code="BAD_SHAPE",
                path=str(fills_p),
                detail="fills must be list or dict{fills:list}",
            )
        )
    else:
        metrics["fills_count"] = len(fills_list)

    # account: best-effort numeric checks
    if not isinstance(acct, dict):
        issues.append(
            ReconciliationIssue(
                code="BAD_SHAPE",
                path=str(acct_p),
                detail="account must be an object/dict",
            )
        )
    else:
        # tolerate different schema keys; check any numeric balance-like fields
        numeric_keys = [k for k, v in acct.items() if isinstance(v, (int, float))]
        metrics["account_numeric_keys"] = numeric_keys
        if not numeric_keys:
            issues.append(
                ReconciliationIssue(
                    code="NO_NUMERIC_FIELDS",
                    path=str(acct_p),
                    detail="no numeric fields found in account json",
                )
            )

    # evidence manifest: best-effort must reference fills and account (p7_* or non-prefixed)
    if ev is not None:
        ev_txt = json.dumps(ev, sort_keys=True)
        for p7_name, alt_name in [
            ("p7_fills.json", "fills.json"),
            ("p7_account.json", "account.json"),
        ]:
            if p7_name not in ev_txt and alt_name not in ev_txt:
                issues.append(
                    ReconciliationIssue(
                        code="EVIDENCE_MISSING_REF",
                        path=str(ev_p),
                        detail=f"manifest does not reference {p7_name} or {alt_name}",
                    )
                )

    ok = len(issues) == 0
    return ReconciliationResult(ok=ok, issues=issues, metrics=metrics)
