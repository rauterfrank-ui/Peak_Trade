from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportResult:
    ok: bool
    rows: int
    json_path: str
    csv_path: str


def export_candidates(
    con: sqlite3.Connection,
    out_dir: Path,
    *,
    run_id: str,
    limit: int | None = None,
) -> ExportResult:
    out_dir.mkdir(parents=True, exist_ok=True)

    q = """
    SELECT
      a.asset_id,
      a.symbol,
      COALESCE(r.severity, 'UNKNOWN') AS risk_severity,
      COALESCE(s.score, -1) AS score,
      a.first_seen_at
    FROM assets a
    LEFT JOIN v_latest_risk r ON r.asset_id = a.asset_id
    LEFT JOIN v_latest_score s ON s.asset_id = a.asset_id
    WHERE a.asset_id IN (SELECT asset_id FROM v_assets_candidates)
    ORDER BY score DESC, a.asset_id ASC
    """
    if limit is not None:
        q += "\nLIMIT ?"
        cursor = con.execute(q, (int(limit),))
    else:
        cursor = con.execute(q)

    rows = [
        {
            "asset_id": r[0],
            "symbol": r[1],
            "risk_severity": r[2],
            "score": r[3],
            "first_seen_at": r[4],
        }
        for r in cursor.fetchall()
    ]

    jpath = out_dir / f"candidates_{run_id}.json"
    cpath = out_dir / f"candidates_{run_id}.csv"

    jpath.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with cpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "asset_id",
                "symbol",
                "risk_severity",
                "score",
                "first_seen_at",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    return ExportResult(ok=True, rows=len(rows), json_path=str(jpath), csv_path=str(cpath))
