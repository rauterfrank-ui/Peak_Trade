from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Mapping, Any

import pandas as pd

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class OfflinePaperTradeSessionMeta:
    """Meta-Informationen zu einer Offline-Paper-Trade-Session."""

    session_id: str
    environment: str  # z.B. "offline_paper_trade", "live_dry_run"
    symbol: str
    timeframe: str
    start_ts: pd.Timestamp
    end_ts: pd.Timestamp
    extra: Optional[Mapping[str, Any]] = None


def _ensure_output_dir(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _compute_basic_stats(trades: pd.DataFrame) -> dict:
    """Berechnet einfache Performance-Kennzahlen für einen Trade-DataFrame.

    Erwartete Spalten mindestens:
      - 'price'
      - 'qty'
      - optional: 'fees'
    """
    if trades.empty:
        return {
            "n_trades": 0,
            "gross_pnl": 0.0,
            "fees": 0.0,
            "net_pnl": 0.0,
        }

    # Einfache PnL-Schätzung: Wir gehen davon aus, dass es eine Spalte 'pnl'
    # gibt. Falls nicht, setzen wir alles auf 0 – das ist robust und bricht
    # nicht den Report.
    gross_pnl = float(trades.get("pnl", pd.Series([0.0] * len(trades))).sum())
    fees = float(trades.get("fees", pd.Series([0.0] * len(trades))).sum())
    net_pnl = gross_pnl - fees

    return {
        "n_trades": int(len(trades)),
        "gross_pnl": gross_pnl,
        "fees": fees,
        "net_pnl": net_pnl,
    }


def _plot_equity_curve(trades: pd.DataFrame, output_dir: Path) -> Optional[str]:
    """Erstellt eine einfache Equity-Kurve auf Basis einer 'pnl'-Spalte.

    Gibt den Dateinamen (relativ zu output_dir) zurück oder None.
    """
    if not HAS_MATPLOTLIB:
        return None
    if "pnl" not in trades.columns or trades.empty:
        return None

    eq = trades["pnl"].cumsum()
    plt.figure()
    eq.plot()
    plt.title("Equity-Kurve (kumulierte PnL)")
    plt.xlabel("Trade Index")
    plt.ylabel("Equity")
    img_name = "equity_curve.png"
    img_path = output_dir / img_name
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()
    return img_name


def build_offline_paper_trade_report(
    trades: pd.DataFrame,
    meta: OfflinePaperTradeSessionMeta,
    output_dir: Path,
    *,
    report_filename: str = "offline_paper_trade_report.html",
) -> Path:
    """Erzeugt einen einfachen Offline-Paper-Trade-HTML-Report.

    Diese Funktion ist bewusst robust gehalten:
    - Wenn bestimmte Spalten fehlen, werden entsprechende Teile ausgelassen.
    - Der Report ist dafür gedacht, schnell v0-Insights zu liefern.
    """
    output_dir = _ensure_output_dir(output_dir)
    stats = _compute_basic_stats(trades)
    equity_curve_img = _plot_equity_curve(trades, output_dir)

    report_path = output_dir / report_filename

    # Einfaches inline-HTML, ohne Template-Engine
    html_parts = []
    html_parts.append("<html><head><meta charset='utf-8'><title>Offline Paper Trade Report</title>")
    html_parts.append(
        "<style>"
        "body { font-family: sans-serif; margin: 20px; }"
        "h1, h2, h3 { font-family: sans-serif; }"
        "table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }"
        "th, td { border: 1px solid #ccc; padding: 4px 6px; font-size: 12px; }"
        ".meta-table td { font-size: 13px; }"
        ".note { font-size: 11px; color: #666; }"
        "</style></head><body>"
    )

    # Titel
    html_parts.append("<h1>Offline Paper Trade Report</h1>")

    # Meta
    html_parts.append("<h2>Session Overview</h2>")
    html_parts.append("<table class='meta-table'>")
    html_parts.append(f"<tr><td>Session ID</td><td>{meta.session_id}</td></tr>")
    html_parts.append(f"<tr><td>Environment</td><td>{meta.environment}</td></tr>")
    html_parts.append(f"<tr><td>Symbol</td><td>{meta.symbol}</td></tr>")
    html_parts.append(f"<tr><td>Timeframe</td><td>{meta.timeframe}</td></tr>")
    html_parts.append(f"<tr><td>Start</td><td>{meta.start_ts}</td></tr>")
    html_parts.append(f"<tr><td>End</td><td>{meta.end_ts}</td></tr>")
    if meta.extra:
        for k, v in meta.extra.items():
            html_parts.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
    html_parts.append("</table>")

    html_parts.append(
        "<p class='note'>Hinweis: Dies ist ein Offline/Paper-Trade-Report. "
        "Es wurden keine echten Orders an eine Börse gesendet.</p>"
    )

    # Stats
    html_parts.append("<h2>Performance Summary</h2>")
    html_parts.append("<table>")
    for k, v in stats.items():
        html_parts.append(f"<tr><td>{k}</td><td>{v}</td></tr>")
    html_parts.append("</table>")

    # Equity-Kurve
    if equity_curve_img is not None:
        html_parts.append("<h2>Equity-Kurve</h2>")
        html_parts.append(f"<img src='{equity_curve_img}' alt='Equity Curve' />")

    # Trades-Tabelle (gekappt auf die ersten 200 Zeilen)
    html_parts.append("<h2>Trades</h2>")
    if trades.empty:
        html_parts.append("<p>Keine Trades vorhanden.</p>")
    else:
        max_rows = 200
        truncated = trades.head(max_rows)
        html_parts.append("<table>")
        # Header
        html_parts.append("<tr>")
        for col in truncated.columns:
            html_parts.append(f"<th>{col}</th>")
        html_parts.append("</tr>")
        # Rows
        for _, row in truncated.iterrows():
            html_parts.append("<tr>")
            for col in truncated.columns:
                html_parts.append(f"<td>{row[col]}</td>")
            html_parts.append("</tr>")
        html_parts.append("</table>")
        if len(trades) > max_rows:
            html_parts.append(
                f"<p class='note'>Angezeigt sind nur die ersten {max_rows} Trades. "
                "Für vollständige Analysen bitte die Rohdaten (CSV/Parquet) verwenden.</p>"
            )

    html_parts.append("</body></html>")

    report_path.write_text("".join(html_parts), encoding="utf-8")
    return report_path

