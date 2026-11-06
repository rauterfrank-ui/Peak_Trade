#!/usr/bin/env python3
"""P7 — Reconciliation checks for paper trading outputs (p7_fills.json, p7_account.json)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def load_json(p: Path) -> dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        o = json.load(f)
    if not isinstance(o, dict):
        raise TypeError(f"expected dict json: {p}")
    return o


def verify_cash_finite(cash: float) -> None:
    """Reject NaN/Inf cash."""
    if cash != cash:
        raise RuntimeError("P7_RECON:CASH_NAN")
    if not (-1e18 < cash < 1e18):
        raise RuntimeError(f"P7_RECON:CASH_SUSPICIOUS cash={cash}")


def verify_positions_non_negative(positions: Dict[str, float]) -> None:
    """Reject negative positions."""
    for sym, qty in positions.items():
        if qty < -1e-12:
            raise RuntimeError(f"P7_RECON:NEGATIVE_POSITION {sym}={qty}")


def reconcile_from_fills(
    fills: List[Dict[str, Any]], initial_cash: float
) -> tuple[float, Dict[str, float]]:
    """Compute expected cash and positions from fills (BUY/SELL)."""
    cash = float(initial_cash)
    positions: Dict[str, float] = {}
    for f in fills:
        sym = str(f["symbol"])
        side = str(f["side"]).upper()
        qty = float(f["qty"])
        price = float(f["price"])
        fee = float(f.get("fee", 0.0))
        notional = price * qty
        if side == "BUY":
            cost = notional + fee
            if cash < cost:
                raise RuntimeError(f"P7_RECON:INSUFFICIENT_CASH fill={f}")
            cash -= cost
            positions[sym] = positions.get(sym, 0.0) + qty
        else:
            pos = positions.get(sym, 0.0)
            if pos < qty:
                raise RuntimeError(f"P7_RECON:INSUFFICIENT_POSITION fill={f}")
            proceeds = notional - fee
            cash += proceeds
            positions[sym] = pos - qty
    return cash, positions


def run_reconcile(
    outdir: Path,
    fills_path: Path | None = None,
    account_path: Path | None = None,
    spec_path: Path | None = None,
    tol: float = 1e-6,
) -> int:
    """Run reconciliation checks. Returns 0 on success, 1 on failure."""
    fills_p = fills_path or outdir / "p7_fills.json"
    acct_p = account_path or outdir / "p7_account.json"

    if not acct_p.is_file():
        print(f"SKIP: no account file {acct_p}", file=sys.stderr)
        return 0

    # Structural + expected-vs-actual (reconcile_p7_outdir) when spec provided
    if spec_path and spec_path.is_file():
        from src.aiops.p7.reconciliation import reconcile_p7_outdir

        res = reconcile_p7_outdir(outdir, expected_spec_path=spec_path)
        if not res.ok:
            for i in res.issues:
                print(f"P7_RECON:ISSUE {i.code} {i.path} {i.detail}", file=sys.stderr)
            return 1

    acct = load_json(acct_p)
    cash = float(acct.get("cash", 0.0))
    positions = {k: float(v) for k, v in (acct.get("positions") or {}).items()}

    verify_cash_finite(cash)
    verify_positions_non_negative(positions)

    if fills_p.is_file():
        data = load_json(fills_p)
        fills = data.get("fills") or []
        if spec_path and spec_path.is_file():
            spec = load_json(spec_path)
            initial_cash = float(spec.get("initial_cash", 0.0))
            exp_cash, exp_pos = reconcile_from_fills(fills, initial_cash)
            if abs(cash - exp_cash) > tol:
                raise RuntimeError(f"P7_RECON:CASH_MISMATCH actual={cash} expected={exp_cash}")
            for sym, exp_q in exp_pos.items():
                act_q = positions.get(sym, 0.0)
                if abs(act_q - exp_q) > tol:
                    raise RuntimeError(
                        f"P7_RECON:POSITION_MISMATCH {sym} actual={act_q} expected={exp_q}"
                    )
            for sym in positions:
                if sym not in exp_pos and abs(positions[sym]) > tol:
                    raise RuntimeError(f"P7_RECON:EXTRA_POSITION {sym}={positions[sym]}")

    print("P7_RECON:OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="run_p7_reconcile",
        description="P7 reconciliation checks for paper trading outputs.",
    )
    ap.add_argument(
        "outdir",
        type=str,
        help="Shadow session output dir (contains p7_fills.json, p7_account.json)",
    )
    ap.add_argument(
        "--fills",
        type=str,
        default="",
        help="Override fills path (default: outdir/p7_fills.json)",
    )
    ap.add_argument(
        "--account",
        type=str,
        default="",
        help="Override account path (default: outdir/p7_account.json)",
    )
    ap.add_argument(
        "--spec",
        type=str,
        default="",
        help="P7 spec JSON for expected vs actual (optional)",
    )
    ap.add_argument(
        "--tol",
        type=float,
        default=1e-6,
        help="Tolerance for cash/position comparison (default 1e-6)",
    )
    args = ap.parse_args()

    repo = _repo_root
    outdir = (
        Path(args.outdir).expanduser().resolve()
        if Path(args.outdir).is_absolute()
        else (repo / args.outdir).resolve()
    )
    fills_path = Path(args.fills).resolve() if args.fills else None
    account_path = Path(args.account).resolve() if args.account else None
    spec_path = (
        (repo / args.spec).resolve()
        if args.spec and not Path(args.spec).is_absolute()
        else (Path(args.spec).resolve() if args.spec else None)
    )

    try:
        return run_reconcile(
            outdir,
            fills_path=fills_path,
            account_path=account_path,
            spec_path=spec_path,
            tol=args.tol,
        )
    except Exception as e:
        print(f"P7_RECON:FAIL {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
