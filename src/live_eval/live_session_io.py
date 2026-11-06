"""IO utilities for reading live session data."""

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from .live_session_eval import Fill


def read_fills_csv(path: Path, strict: bool = False) -> List[Fill]:
    """
    Read fills from a CSV file.

    Expected CSV format:
        ts,symbol,side,qty,fill_price

    Args:
        path: Path to the fills CSV file
        strict: If True, raise errors on parse failures. If False, skip invalid rows.

    Returns:
        List of Fill objects

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If CSV format is invalid or required columns are missing
    """
    if not path.exists():
        raise FileNotFoundError(f"Fills CSV not found: {path}")

    fills: List[Fill] = []
    errors: List[str] = []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        required_cols = {"ts", "symbol", "side", "qty", "fill_price"}
        if reader.fieldnames is None or not required_cols.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV must contain columns: {required_cols}. Found: {reader.fieldnames}"
            )

        for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
            try:
                # Parse timestamp (support ISO8601 with or without 'Z')
                ts_str = row["ts"].strip()
                if ts_str.endswith("Z"):
                    ts = datetime.fromisoformat(ts_str[:-1] + "+00:00")
                else:
                    ts = datetime.fromisoformat(ts_str)

                # Ensure timezone-aware (UTC)
                if ts.tzinfo is None:
                    raise ValueError(f"Timestamp must be timezone-aware: {ts_str}")

                symbol = row["symbol"].strip()
                side = row["side"].strip().lower()
                qty = float(row["qty"])
                fill_price = float(row["fill_price"])

                fill = Fill(ts=ts, symbol=symbol, side=side, qty=qty, fill_price=fill_price)
                fills.append(fill)

            except (ValueError, KeyError) as e:
                error_msg = f"Line {line_num}: {e}"
                errors.append(error_msg)
                if strict:
                    raise ValueError(f"Parse error: {error_msg}") from e

    if errors and not strict:
        # Log warnings (in a real system, use logging)
        for err in errors:
            print(f"WARNING: Skipped invalid row - {err}")

    return fills
