# src/strategies/bouchaud/__init__.py
"""
Bouchaud-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf Jean-Philippe Bouchauds Arbeiten zur
Markt-Mikrostruktur und statistischen Physik der Finanzmärkte.

Kernkonzepte:
- Orderbuch-Imbalance als Preisdruckindikator
- Trade-Sign-Korrelationen (Metaorders)
- Propagator-Modelle für Preisimpact
- Statistische Regularitäten in Hochfrequenzdaten

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN

Hinweis: Diese Strategien benötigen Tick- oder Orderbuch-Daten,
die in Peak_Trade aktuell nicht standardmäßig verfügbar sind.

Referenzen:
- "Trades, Quotes and Prices" (Bouchaud, Bonart, Donier, Gould)
- "Theory of Financial Risk and Derivative Pricing" (Bouchaud, Potters)
"""
from .bouchaud_microstructure_strategy import BouchaudMicrostructureStrategy

__all__ = ["BouchaudMicrostructureStrategy"]
