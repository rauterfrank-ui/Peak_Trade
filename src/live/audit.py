# src/live/audit.py
"""
Peak_Trade: Live-Config Audit & Export (Phase 74)
===================================================

Framework für Audit-Snapshots des Live-Sicherheitszustands.

Ziel:
    Erzeugt maschinenlesbare (JSON) und menschenlesbare (Markdown/Text)
    Snapshots für Governance, Audits und "Proof of Safety".

WICHTIG: Phase 74 - Read-Only
    - Keine Config-Dateien ändern
    - Keine State-Änderungen
    - Keine echten Orders
    - Keine Token-Werte exportieren (nur Boolean-Präsenz)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.core.environment import (
    EnvironmentConfig,
    TradingEnvironment,
    LIVE_CONFIRM_TOKEN,
)
from src.live.drills import get_default_live_drill_scenarios
from src.live.risk_limits import LiveRiskLimits
from src.live.safety import SafetyGuard, is_live_execution_allowed

logger = logging.getLogger(__name__)


# =============================================================================
# Datamodel
# =============================================================================


@dataclass
class LiveAuditGatingState:
    """
    Gating-Status für Audit-Snapshot.

    Attributes:
        mode: Environment-Mode (paper/testnet/live)
        effective_mode: Effektiver Modus aus SafetyGuard
        enable_live_trading: Gate 1
        live_mode_armed: Gate 2 (Phase 71)
        live_dry_run_mode: Technisches Gate (Phase 71)
        confirm_token_present: Ob Token gesetzt ist (Boolean, kein Wert!)
        require_confirm_token: Ob Token erforderlich ist
    """

    mode: str
    effective_mode: str
    enable_live_trading: bool
    live_mode_armed: bool
    live_dry_run_mode: bool
    confirm_token_present: bool
    require_confirm_token: bool


@dataclass
class LiveAuditRiskState:
    """
    Risk-Limits-Status für Audit-Snapshot.

    Attributes:
        max_live_notional_per_order: Max. Notional pro Order (Phase 71)
        max_live_notional_total: Max. Gesamt-Notional (Phase 71)
        live_trade_min_size: Min. Order-Größe (Phase 71)
        limits_enabled: Ob Risk-Limits aktiviert sind
        limits_source: Quelle der Limits (z.B. "config.toml")
    """

    max_live_notional_per_order: Optional[float]
    max_live_notional_total: Optional[float]
    live_trade_min_size: Optional[float]
    limits_enabled: bool
    limits_source: str = "config.toml"


@dataclass
class LiveAuditDrillSummary:
    """
    Drill-Meta-Informationen für Audit-Snapshot.

    Attributes:
        available_scenarios: Liste von Drill-Namen (z.B. ["A - Voll gebremst", ...])
        num_scenarios: Anzahl verfügbarer Drills
        drills_executable: Ob Drills ausführbar sind (Meta-Info)
    """

    available_scenarios: List[str]
    num_scenarios: int
    drills_executable: bool = True


@dataclass
class LiveAuditSafetySummary:
    """
    Safety-Zusammenfassung für Audit-Snapshot.

    Attributes:
        is_live_execution_allowed: Ergebnis von is_live_execution_allowed()
        reasons: Liste von Gründen (warum erlaubt/blockiert)
        safety_guarantee_v1_0: Kurzer Text zur Safety-Garantie
    """

    is_live_execution_allowed: bool
    reasons: List[str]
    safety_guarantee_v1_0: str = "Dry-Run only, no real orders possible (v1.0)"


@dataclass
class LiveAuditSnapshot:
    """
    Vollständiger Audit-Snapshot des Live-Sicherheitszustands.

    Attributes:
        timestamp_utc: Zeitstempel des Snapshots (ISO-Format)
        environment_id: Optional Identifier (z.B. Config-Name)
        gating: Gating-Status
        risk: Risk-Limits-Status
        drills: Drill-Meta-Informationen
        safety: Safety-Zusammenfassung
        versions: Optional Versions-Info (z.B. Test-Anzahlen)
    """

    timestamp_utc: str
    environment_id: Optional[str] = None
    gating: LiveAuditGatingState = None  # type: ignore
    risk: LiveAuditRiskState = None  # type: ignore
    drills: LiveAuditDrillSummary = None  # type: ignore
    safety: LiveAuditSafetySummary = None  # type: ignore
    versions: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Funktionen
# =============================================================================


def build_live_audit_snapshot(
    env_config: EnvironmentConfig,
    safety_guard: SafetyGuard,
    live_risk_limits: Optional[LiveRiskLimits] = None,
    environment_id: Optional[str] = None,
) -> LiveAuditSnapshot:
    """
    Erstellt einen Live-Audit-Snapshot.

    Args:
        env_config: EnvironmentConfig-Instanz
        safety_guard: SafetyGuard-Instanz
        live_risk_limits: Optional LiveRiskLimits-Instanz
        environment_id: Optional Identifier (z.B. Config-Name)

    Returns:
        LiveAuditSnapshot mit allen relevanten Informationen

    Note:
        Keine Config-Änderungen, keine State-Änderungen, keine echten Orders.
        Token-Werte werden NICHT exportiert (nur Boolean-Präsenz).
    """
    # Timestamp
    timestamp_utc = datetime.now(timezone.utc).isoformat()

    # Gating-Status
    effective_mode = safety_guard.get_effective_mode()
    confirm_token_present = (
        env_config.confirm_token is not None
        and env_config.confirm_token == LIVE_CONFIRM_TOKEN
    )

    gating = LiveAuditGatingState(
        mode=env_config.environment.value,
        effective_mode=effective_mode,
        enable_live_trading=env_config.enable_live_trading,
        live_mode_armed=env_config.live_mode_armed,
        live_dry_run_mode=env_config.live_dry_run_mode,
        confirm_token_present=confirm_token_present,
        require_confirm_token=env_config.require_confirm_token,
    )

    # Risk-Limits-Status
    if live_risk_limits:
        risk_config = live_risk_limits.config
        risk = LiveAuditRiskState(
            max_live_notional_per_order=risk_config.max_live_notional_per_order,
            max_live_notional_total=risk_config.max_live_notional_total,
            live_trade_min_size=risk_config.live_trade_min_size,
            limits_enabled=risk_config.enabled,
            limits_source="config.toml",
        )
    else:
        risk = LiveAuditRiskState(
            max_live_notional_per_order=None,
            max_live_notional_total=None,
            live_trade_min_size=None,
            limits_enabled=False,
            limits_source="not_loaded",
        )

    # Drill-Meta
    drill_scenarios = get_default_live_drill_scenarios()
    drill_names = [s.name for s in drill_scenarios]

    drills = LiveAuditDrillSummary(
        available_scenarios=drill_names,
        num_scenarios=len(drill_names),
        drills_executable=True,
    )

    # Safety-Summary
    allowed, reason = is_live_execution_allowed(env_config)
    reasons = [reason] if reason else []

    # Zusätzliche Reasons aus Gating-State ableiten
    if not allowed:
        if env_config.environment != TradingEnvironment.LIVE:
            reasons.append(f"Environment ist nicht LIVE (aktuell: {env_config.environment.value})")
        if env_config.environment == TradingEnvironment.LIVE:
            if not env_config.enable_live_trading:
                reasons.append("Gate 1: enable_live_trading=False")
            if not env_config.live_mode_armed:
                reasons.append("Gate 2: live_mode_armed=False (Phase 71)")
            if env_config.live_dry_run_mode:
                reasons.append("Technisches Gate: live_dry_run_mode=True (Phase 71)")
            if env_config.require_confirm_token and not confirm_token_present:
                reasons.append("Confirm-Token fehlt oder ist ungültig")

    safety = LiveAuditSafetySummary(
        is_live_execution_allowed=allowed,
        reasons=reasons,
        safety_guarantee_v1_0="Dry-Run only, no real orders possible (v1.0 - Phase 71-74)",
    )

    # Versions-Info (optional)
    versions = {
        "phase71_tests": "14",
        "phase72_tests": "11",
        "phase73_tests": "18",
        "phase74_tests": "TBD",  # Wird nach Test-Implementierung aktualisiert
    }

    return LiveAuditSnapshot(
        timestamp_utc=timestamp_utc,
        environment_id=environment_id,
        gating=gating,
        risk=risk,
        drills=drills,
        safety=safety,
        versions=versions,
    )


def live_audit_snapshot_to_dict(snapshot: LiveAuditSnapshot) -> Dict[str, Any]:
    """
    Konvertiert LiveAuditSnapshot zu einem JSON-serialisierbaren Dict.

    Args:
        snapshot: LiveAuditSnapshot-Instanz

    Returns:
        Dict mit allen Snapshot-Daten (JSON-serialisierbar)

    Note:
        Token-Werte werden NICHT exportiert (nur Boolean-Präsenz).
    """
    return {
        "timestamp_utc": snapshot.timestamp_utc,
        "environment_id": snapshot.environment_id,
        "gating": {
            "mode": snapshot.gating.mode,
            "effective_mode": snapshot.gating.effective_mode,
            "enable_live_trading": snapshot.gating.enable_live_trading,
            "live_mode_armed": snapshot.gating.live_mode_armed,
            "live_dry_run_mode": snapshot.gating.live_dry_run_mode,
            "confirm_token_present": snapshot.gating.confirm_token_present,
            "require_confirm_token": snapshot.gating.require_confirm_token,
        },
        "risk": {
            "max_live_notional_per_order": snapshot.risk.max_live_notional_per_order,
            "max_live_notional_total": snapshot.risk.max_live_notional_total,
            "live_trade_min_size": snapshot.risk.live_trade_min_size,
            "limits_enabled": snapshot.risk.limits_enabled,
            "limits_source": snapshot.risk.limits_source,
        },
        "drills": {
            "available_scenarios": snapshot.drills.available_scenarios,
            "num_scenarios": snapshot.drills.num_scenarios,
            "drills_executable": snapshot.drills.drills_executable,
        },
        "safety": {
            "is_live_execution_allowed": snapshot.safety.is_live_execution_allowed,
            "reasons": snapshot.safety.reasons,
            "safety_guarantee_v1_0": snapshot.safety.safety_guarantee_v1_0,
        },
        "versions": snapshot.versions,
    }


def live_audit_snapshot_to_markdown(snapshot: LiveAuditSnapshot) -> str:
    """
    Konvertiert LiveAuditSnapshot zu Markdown-Text.

    Args:
        snapshot: LiveAuditSnapshot-Instanz

    Returns:
        Formatierter Markdown-Text

    Note:
        Token-Werte werden NICHT exportiert (nur Boolean-Präsenz).
    """
    lines = []

    # Header
    lines.append("# Peak_Trade - Live Audit Snapshot")
    lines.append("")
    lines.append(f"**Phase 71-74, v1.0**")
    lines.append(f"**Timestamp:** {snapshot.timestamp_utc} (UTC)")
    if snapshot.environment_id:
        lines.append(f"**Environment ID:** {snapshot.environment_id}")
    lines.append("")

    # Gating-Block
    lines.append("## Gating Status")
    lines.append("")
    lines.append(f"- **Mode:** {snapshot.gating.mode}")
    lines.append(f"- **Effective Mode:** {snapshot.gating.effective_mode}")
    lines.append(f"- **enable_live_trading (Gate 1):** {snapshot.gating.enable_live_trading}")
    lines.append(f"- **live_mode_armed (Gate 2 - Phase 71):** {snapshot.gating.live_mode_armed}")
    lines.append(f"- **live_dry_run_mode (Technisches Gate):** {snapshot.gating.live_dry_run_mode}")
    lines.append(f"- **confirm_token_present:** {snapshot.gating.confirm_token_present} (Wert nicht exportiert)")
    lines.append(f"- **require_confirm_token:** {snapshot.gating.require_confirm_token}")
    lines.append("")

    # Risk-Block
    lines.append("## Risk Limits")
    lines.append("")
    lines.append(f"- **Limits Enabled:** {snapshot.risk.limits_enabled}")
    lines.append(f"- **Limits Source:** {snapshot.risk.limits_source}")
    lines.append(f"- **max_live_notional_per_order:** {snapshot.risk.max_live_notional_per_order}")
    lines.append(f"- **max_live_notional_total:** {snapshot.risk.max_live_notional_total}")
    lines.append(f"- **live_trade_min_size:** {snapshot.risk.live_trade_min_size}")
    lines.append("")

    # Drills-Block
    lines.append("## Drills Summary")
    lines.append("")
    lines.append(f"- **Available Scenarios:** {snapshot.drills.num_scenarios}")
    lines.append(f"- **Drills Executable:** {snapshot.drills.drills_executable}")
    lines.append("")
    lines.append("Available Drill Scenarios:")
    for scenario_name in snapshot.drills.available_scenarios:
        lines.append(f"  - {scenario_name}")
    lines.append("")

    # Safety-Summary-Block
    lines.append("## Safety Summary")
    lines.append("")
    lines.append(f"- **is_live_execution_allowed:** {snapshot.safety.is_live_execution_allowed}")
    lines.append(f"- **Safety Guarantee (v1.0):** {snapshot.safety.safety_guarantee_v1_0}")
    lines.append("")
    if snapshot.safety.reasons:
        lines.append("**Reasons:**")
        for reason in snapshot.safety.reasons:
            lines.append(f"  - {reason}")
        lines.append("")
    else:
        lines.append("**Reasons:** (none)")
        lines.append("")

    # Versions-Info
    if snapshot.versions:
        lines.append("## Version Info")
        lines.append("")
        for key, value in snapshot.versions.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("**Note:** This snapshot is read-only. No config changes, no state changes, no real orders.")
    lines.append("**Phase 71-74:** Live-Execution-Path exists as design/Dry-Run only.")
    lines.append("**v1.0:** Research/Testnet system - no real live orders possible.")

    return "\n".join(lines)







