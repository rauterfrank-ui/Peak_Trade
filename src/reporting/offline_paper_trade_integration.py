from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Any, Optional, Sequence, Dict

import pandas as pd

from .offline_paper_trade_report import (
    OfflinePaperTradeSessionMeta,
    build_offline_paper_trade_report,
)
from .trigger_training_report import (
    TriggerTrainingEvent,
    build_trigger_training_report,
)


@dataclass
class OfflinePaperTradeReportConfig:
    """Konfiguration für Offline-Paper-Trade-Reports.

    Diese Struktur dient als v0-Container für Meta-Informationen, die typischerweise
    aus einer Session-Struktur stammen (SessionResult, Config, etc.).
    """

    session_id: str
    environment: str  # z.B. "offline_paper_trade", "live_dry_run"
    symbol: str
    timeframe: str
    start_ts: pd.Timestamp
    end_ts: pd.Timestamp
    extra_meta: Optional[Mapping[str, Any]] = None
    base_reports_dir: Path = Path("reports/offline_paper_trade")


def _ensure_output_dir(base_dir: Path, session_id: str) -> Path:
    output_dir = base_dir / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_reports_for_offline_paper_trade(
    trades: pd.DataFrame,
    report_config: OfflinePaperTradeReportConfig,
    *,
    trigger_events: Optional[Sequence[TriggerTrainingEvent]] = None,
    session_meta_for_trigger: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Path]:
    """Erzeugt spezialisierte Reports für eine Offline-Paper-Trade-Session.

    - Erstellt immer den Offline-Paper-Trade-Report.
    - Erstellt zusätzlich einen Trigger-Training-Report, wenn trigger_events angegeben sind.

    Parameters
    ----------
    trades:
        DataFrame mit Trade-Informationen (wie in offline_paper_trade_report.py beschrieben).
    report_config:
        Meta-Informationen und Basis-Verzeichnis.
    trigger_events:
        Optionale Liste von TriggerTrainingEvent-Objekten. Wenn None oder leer, wird kein
        Trigger-Training-Report erzeugt.
    session_meta_for_trigger:
        Optionales Mapping mit Meta-Infos für den Trigger-Report (z.B. Session-ID, Mode, Date).

    Returns
    -------
    Dict[str, Path]
        Dictionary mit Schlüsseln:
          - "paper_report": Pfad zum Offline-Paper-Trade-Report
          - "trigger_report": Pfad zum Trigger-Training-Report (nur falls erzeugt)
    """
    output_dir = _ensure_output_dir(report_config.base_reports_dir, report_config.session_id)

    meta = OfflinePaperTradeSessionMeta(
        session_id=report_config.session_id,
        environment=report_config.environment,
        symbol=report_config.symbol,
        timeframe=report_config.timeframe,
        start_ts=report_config.start_ts,
        end_ts=report_config.end_ts,
        extra=report_config.extra_meta,
    )

    paper_report_path = build_offline_paper_trade_report(
        trades=trades,
        meta=meta,
        output_dir=output_dir,
    )

    result: Dict[str, Path] = {"paper_report": paper_report_path}

    if trigger_events:
        # Default-Meta, falls nichts übergeben wurde
        if session_meta_for_trigger is None:
            session_meta_for_trigger = {
                "session_id": report_config.session_id,
                "mode": report_config.environment,
                "symbol": report_config.symbol,
                "timeframe": report_config.timeframe,
            }

        # NEU: Extrahiere Speed-Metriken aus session_meta (falls vorhanden)
        reaction_summary = None
        latency_summary = None
        if isinstance(session_meta_for_trigger, dict):
            reaction_summary = session_meta_for_trigger.get("reaction_summary")
            latency_summary = session_meta_for_trigger.get("latency_summary")

        trigger_report_path = build_trigger_training_report(
            events=list(trigger_events),
            output_dir=output_dir,
            session_meta=session_meta_for_trigger,
            reaction_summary=reaction_summary,
            latency_summary=latency_summary,
        )
        result["trigger_report"] = trigger_report_path

    return result
