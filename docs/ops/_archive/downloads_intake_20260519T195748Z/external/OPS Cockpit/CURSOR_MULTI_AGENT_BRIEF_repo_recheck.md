Ziel
Führe eine repo-weite, rein informative Gegenprüfung des OPS Cockpit durch. Prüfe, ob der aktuelle OPS-Cockpit-Stand auf main inhaltlich noch zum gesamten Repo passt, ob am bestehenden Cockpit jetzt etwas angepasst werden sollte, und ob es sinnvolle additive Erweiterungen gibt. Keine Umsetzung, kein Code, keine Commits, keine Branches, keine Repo-Dateien verändern.

Git-Kontext
- Arbeite explizit auf Branch: main
- Modus: read-only / audit-only / inventory-only
- Keine Mutationen im Repository
- Keine Paper/Shadow/Evidence-/Live-Artefakte anfassen
- Keine Secrets, keine Live-Unlocks, keine Infrastrukturänderungen

Ausgangslage
Es gibt bereits eine read-only Statuszusammenfassung des OPS Cockpit. Nutze sie nur als Startpunkt, aber prüfe das Thema jetzt eigenständig gegen das gesamte Repo.

Pfad der vorhandenen Zusammenfassung:
- /mnt/data/OPS_COCKPIT_STATUS_SUMMARY.md

Arbeitsauftrag
Bitte beantworte auf Basis des gesamten Repos belastbar:

1. Ist das OPS Cockpit aktuell noch auf dem Stand des Repos?
   - Gibt es neue Features, Read-Models, States, Surfaces, APIs, Views, Governance-/Operator-Konzepte, die im Repo inzwischen existieren, aber im OPS Cockpit nicht oder nicht ausreichend sichtbar sind?
   - Gibt es Docs/Phase-/Checklist-/Runbook-Sollstände, die vom aktuellen Cockpit abweichen?

2. Muss am bestehenden Cockpit aktuell etwas geändert werden?
   - echte Inkonsistenzen
   - veraltete oder drifte Specs/Runbooks
   - fehlende HTML-Anker / fehlende Discoverability
   - Payload-/API-/HTML-/Test-Diskrepanzen
   - ungenutzte oder redundant gewordene Cockpit-Flächen

3. Lässt sich das Cockpit sinnvoll erweitern?
   - nur additive, plausible Erweiterungen
   - priorisiert nach Nutzen für Operator/Truth-first/Read-only-Observability
   - keine spekulativen Großbauten
   - klar trennen zwischen "sollte jetzt korrigiert werden" und "könnte sinnvoll als nächster Slice kommen"

Repo-weite Prüfrichtung
Suche breit, nicht nur in ops_cockpit.py:
- src/webui/**
- src/ops/**
- src/live/**
- src/execution/**
- src/observability/**
- src/experiments/**
- tests/**
- docs/**
- .github/workflows/** sofern UI-/Operator-/Evidence-relevant

Besonders prüfen
- neue State-/Observation-/Snapshot-/Read-Model-Konzepte
- neue API-Endpunkte / neue HTML-Seiten / neue Dashboard-Surfaces
- Truth / Runtime Unknown / Incident / Session End Mismatch / Transfer Ambiguity / Exposure / Dependencies / Evidence / Safety / Policy / Guard / Workflow Officer / Update Officer / Phase 57 / Phase 83
- Docs-Wahrheit in:
  - docs/ops/specs/OPS_COCKPIT_PAYLOAD_READ_MODEL_CONTRACT.md
  - docs/ops/specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md
  - docs/ops/specs/OPS_COCKPIT_VNEXT_REQUIRED_VIEWS_COVERAGE.md
  - docs/DASHBOARD_COMPLETION_MASTER_CHECKLIST.md
- Runbooks / reviews / phase docs / dashboard docs auf Drift gegen Code
- Tests:
  - tests/webui/test_ops_cockpit.py
  - tests/ops/test_ops_cockpit_payload_top_level_contract.py
  - weitere ops-cockpit/api-json-contract/webui Tests

Konkrete Erwartungen
- Stelle "Repo kann heute X, Cockpit zeigt X / zeigt X nicht / zeigt X nur indirekt" gegenüber
- Benenne nur belastbare Findings
- Markiere Unsicherheit explizit
- Keine Änderungen durchführen

Gewünschtes Ergebnisformat
Schreibe nach:
  /tmp/peak_trade_ops_cockpit_repo_recheck/OPS_COCKPIT_REPO_WIDE_RECHECK.md

Struktur:
1. Executive Summary
2. Current Cockpit vs Repo Alignment
3. Confirmed Coverage
4. Confirmed Gaps Requiring Change Now
5. Candidate Additive Extensions
6. Docs/Tests/Contract Drift Check
7. Recent Repo Signals Relevant To Cockpit
8. Recommended Next Larger Slice
9. Appendix: evidence table with concrete file paths / symbols / test names

Zusatzanforderungen
- Trenne strikt zwischen gesicherter Repo-Evidenz und Interpretation
- Zitiere konkrete Dateien, Funktionen, Testnamen, HTML ids, Doc-Pfade
- Wenn etwas nicht belastbar beweisbar ist: "unklar auf Basis der aktuellen Repo-Evidenz"
- Keine spekulativen Implementierungsvorschläge ohne Repo-Anker
