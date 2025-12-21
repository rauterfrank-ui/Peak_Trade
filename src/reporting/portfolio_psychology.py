#!/usr/bin/env python3
"""
Peak_Trade Portfolio Psychology Layer (v0)
==========================================

Mini-Psychologie-Layer für Portfolio-Health-Tests.
Setzt auf Basis der Health-Metriken einfache Psychologie-Flags:

- psychology_level: "CALM" | "MEDIUM" | "SPICY"
- psychology_notes: Liste von kurzen Text-Hinweisen

Diese Flags sind rein beschreibend (keine Optimierungskriterien).
Sie helfen Operatoren, das Portfolio psychologisch einzuordnen.

Autor: Peak_Trade QA Team
Stand: Dezember 2024
Version: v0
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Literal


# ============================================================================
# Type Definitions
# ============================================================================

PsychologyLevel = Literal["CALM", "MEDIUM", "SPICY"]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PsychologyAnnotation:
    """
    Psychologie-Annotation für Portfolio-Health-Ergebnisse.

    Attributes:
        level: Psychologisches Risikoprofil ("CALM", "MEDIUM", "SPICY")
        notes: Liste von kurzen Hinweisen/Warnungen
        max_drawdown_pct: Verwendeter Max-Drawdown (für Transparenz)
        total_return_pct: Verwendeter Return (für Transparenz)
        trades_count: Verwendete Trade-Anzahl (für Transparenz)
    """

    level: PsychologyLevel
    notes: List[str]
    max_drawdown_pct: Optional[float] = None
    total_return_pct: Optional[float] = None
    trades_count: Optional[int] = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für JSON-Serialisierung."""
        return asdict(self)

    @property
    def level_emoji(self) -> str:
        """Gibt Emoji für das Level zurück."""
        return {"CALM": "🧘", "MEDIUM": "⚠️", "SPICY": "🔥"}.get(self.level, "❓")

    @property
    def level_color(self) -> str:
        """Gibt CSS-Farbe für das Level zurück."""
        return {
            "CALM": "#28a745",  # Grün
            "MEDIUM": "#ffc107",  # Gelb/Orange
            "SPICY": "#dc3545",  # Rot
        }.get(self.level, "#6c757d")


# ============================================================================
# Core Function: Psychologie aus Metriken ableiten
# ============================================================================


def derive_portfolio_psychology(
    total_return_pct: float,
    max_drawdown_pct: float,
    trades_count: int,
    volatility_pct: Optional[float] = None,
) -> PsychologyAnnotation:
    """
    Leitet Psychologie-Annotation aus Portfolio-Health-Metriken ab.

    Die Logik ist bewusst simpel gehalten (v0):
    - Basis-Level wird primär vom Max-Drawdown bestimmt
    - Notes werden bei Extremwerten hinzugefügt
    - Kein Machine Learning, keine komplexen Heuristiken

    Parameters
    ----------
    total_return_pct : float
        Portfolio-Gesamtreturn in Prozent (z.B. 45.0 für 45%)
    max_drawdown_pct : float
        Maximaler Drawdown in Prozent (als positive Zahl, z.B. 32.0 für 32%)
    trades_count : int
        Anzahl der Trades im Backtest-Zeitraum
    volatility_pct : Optional[float]
        Optionale Volatilität in Prozent (für zukünftige Erweiterung)

    Returns
    -------
    PsychologyAnnotation
        Annotation mit level und notes

    Examples
    --------
    >>> psych = derive_portfolio_psychology(45.0, 25.0, 18)
    >>> psych.level
    'CALM'
    >>> psych.notes
    ['Ruhiges Profil – psychologisch gut beherrschbar.']

    >>> psych = derive_portfolio_psychology(-50.0, 70.0, 5)
    >>> psych.level
    'SPICY'
    >>> 'Hoher Max-Drawdown' in psych.notes[0]
    True
    """
    notes: List[str] = []

    # =========================================================================
    # 1. Basis-Level anhand Max-Drawdown
    # =========================================================================
    # Drawdown ist der primäre psychologische Stressfaktor

    if max_drawdown_pct <= 30:
        level: PsychologyLevel = "CALM"
    elif max_drawdown_pct <= 60:
        level = "MEDIUM"
    else:
        level = "SPICY"
        notes.append(
            f"Hoher Max-Drawdown ({max_drawdown_pct:.1f}%) – "
            "psychologisch anspruchsvoll, nur für erfahrene Operatoren."
        )

    # =========================================================================
    # 2. Performance-Extremwerte flaggen
    # =========================================================================

    # Extrem gute Performance → Overconfidence-Risiko
    if total_return_pct >= 150:
        notes.append(
            f"Sehr hohe Performance ({total_return_pct:.1f}%) – "
            "Gefahr von Overconfidence und überhöhtem Risiko in Folge."
        )
    elif total_return_pct >= 100:
        notes.append(
            f"Starke Performance ({total_return_pct:.1f}%) – "
            "Erwartungsmanagement beachten (nicht als Normalfall interpretieren)."
        )

    # Extrem schlechte Performance → Panic-Risiko
    if total_return_pct <= -40:
        notes.append(
            f"Starke Verluste ({total_return_pct:.1f}%) – "
            "Gefahr von Panic-Reaktionen oder vorzeitigem Abschalten."
        )
        # Bei starken Verlusten mindestens MEDIUM
        if level == "CALM":
            level = "MEDIUM"

    # =========================================================================
    # 3. Trade-Anzahl analysieren
    # =========================================================================

    if trades_count < 3:
        notes.append(
            f"Sehr wenige Trades ({trades_count}) – "
            "psychologische Aussagekraft begrenzt, Sample-Size zu klein."
        )
    elif trades_count < 10:
        notes.append(f"Wenige Trades ({trades_count}) – Ergebnisse könnten zufallsbedingt sein.")
    elif trades_count > 100:
        notes.append(
            f"Viele Trades ({trades_count}) – "
            "Gefahr von Overtrading & Decision-Fatigue bei manuellem Monitoring."
        )
    elif trades_count > 50:
        notes.append(
            f"Erhöhte Trade-Frequenz ({trades_count}) – automatisches Monitoring empfohlen."
        )

    # =========================================================================
    # 4. Volatilität (falls verfügbar)
    # =========================================================================

    if volatility_pct is not None:
        if volatility_pct > 50:
            notes.append(
                f"Sehr hohe Volatilität ({volatility_pct:.1f}%) – "
                "erwarte starke Schwankungen im Equity-Verlauf."
            )
            if level == "CALM":
                level = "MEDIUM"

    # =========================================================================
    # 5. Default-Notes falls keine spezifischen Notes
    # =========================================================================

    if not notes:
        if level == "CALM":
            notes.append("Ruhiges Profil – psychologisch gut beherrschbar.")
        elif level == "MEDIUM":
            notes.append("Mittlere Schwankungen – bewusstes Risikomanagement erforderlich.")
        else:
            notes.append("Spicy Profil – nur für erfahrene Operatoren geeignet.")

    return PsychologyAnnotation(
        level=level,
        notes=notes,
        max_drawdown_pct=max_drawdown_pct,
        total_return_pct=total_return_pct,
        trades_count=trades_count,
    )


# ============================================================================
# Utility Functions
# ============================================================================


def psychology_to_markdown(psych: PsychologyAnnotation) -> str:
    """
    Formatiert PsychologyAnnotation als Markdown-Snippet.

    Parameters
    ----------
    psych : PsychologyAnnotation
        Die zu formatierende Annotation

    Returns
    -------
    str
        Markdown-formatierter String
    """
    lines = [
        f"### {psych.level_emoji} Psychologie: **{psych.level}**",
        "",
    ]

    if psych.notes:
        for note in psych.notes:
            lines.append(f"- {note}")
        lines.append("")

    # Metriken-Kontext (optional)
    if any([psych.max_drawdown_pct, psych.total_return_pct, psych.trades_count]):
        lines.append("*Basierend auf:*")
        if psych.max_drawdown_pct is not None:
            lines.append(f"- Max-DD: {psych.max_drawdown_pct:.1f}%")
        if psych.total_return_pct is not None:
            lines.append(f"- Return: {psych.total_return_pct:+.1f}%")
        if psych.trades_count is not None:
            lines.append(f"- Trades: {psych.trades_count}")
        lines.append("")

    return "\n".join(lines)


def psychology_to_html(psych: PsychologyAnnotation) -> str:
    """
    Formatiert PsychologyAnnotation als HTML-Snippet.

    Parameters
    ----------
    psych : PsychologyAnnotation
        Die zu formatierende Annotation

    Returns
    -------
    str
        HTML-formatierter String
    """
    badge_class = {"CALM": "badge-success", "MEDIUM": "badge-warning", "SPICY": "badge-danger"}.get(
        psych.level, "badge-secondary"
    )

    notes_html = ""
    if psych.notes:
        notes_items = "\n".join(f"<li>{note}</li>" for note in psych.notes)
        notes_html = f"<ul class='psychology-notes'>{notes_items}</ul>"

    return f"""
<div class="psychology-section">
    <h4>{psych.level_emoji} Psychologie</h4>
    <span class="badge {badge_class}" style="background-color: {psych.level_color}; color: white; padding: 4px 8px; border-radius: 4px;">
        {psych.level}
    </span>
    {notes_html}
</div>
"""


# ============================================================================
# CLI-Test (falls direkt ausgeführt)
# ============================================================================


if __name__ == "__main__":
    # Beispiel-Tests
    print("=" * 60)
    print("Portfolio Psychology Layer - Test")
    print("=" * 60)

    test_cases = [
        {"total_return_pct": 45.0, "max_drawdown_pct": 20.0, "trades_count": 25},
        {"total_return_pct": 110.0, "max_drawdown_pct": 35.0, "trades_count": 50},
        {"total_return_pct": -30.0, "max_drawdown_pct": 55.0, "trades_count": 8},
        {"total_return_pct": 200.0, "max_drawdown_pct": 75.0, "trades_count": 150},
        {"total_return_pct": 15.0, "max_drawdown_pct": 10.0, "trades_count": 2},
    ]

    for i, tc in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(
            f"Input: return={tc['total_return_pct']}%, dd={tc['max_drawdown_pct']}%, trades={tc['trades_count']}"
        )

        psych = derive_portfolio_psychology(**tc)

        print(f"Level: {psych.level_emoji} {psych.level}")
        print("Notes:")
        for note in psych.notes:
            print(f"  - {note}")

    print("\n" + "=" * 60)
    print("✅ Tests abgeschlossen")
