# src/strategies/ideas/__init__.py
"""
Peak_Trade Strategy Ideas

Sandbox für neue Strategien: eigene Klassen unter ``ideas/`` ohne die produktiven
Strategien in ``src/strategies/`` zu vermischen.

Typischer Workflow:
- ``python scripts/new_idea_strategy.py --name my_idea`` — Datei aus Vorlage erzeugen
- ``generate_signals`` und Metadaten ausfüllen (TODOs in der Datei)
- ``python scripts/run_idea_strategy.py --module my_idea --symbol BTC/EUR`` — Smoke-Run
- Optional: später in die zentrale Registry übernehmen (separater PR)
"""
