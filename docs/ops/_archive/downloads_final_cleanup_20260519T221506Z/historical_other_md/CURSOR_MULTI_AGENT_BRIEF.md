Ziel
Erstelle eine rein informative, read-only Bestandsaufnahme zum aktuellen Stand des OPS Cockpit im Peak_Trade-Repo. Keine Codeänderungen, keine Commits, keine Branches, keine Dateien im Repo verändern. Nur lesen, auswerten, zusammenfassen.

Git-Kontext
- Arbeite explizit auf Branch: main
- Modus: read-only / inventory-only
- Keine Mutationen im Repository
- Keine Testdaten, Paper/Shadow/Evidence-Läufe anfassen
- Keine Live-/Execution-/Secrets-bezogenen Änderungen

Arbeitsauftrag
Bitte liefere eine kompakte, aber belastbare Statusübersicht zum Thema OPS Cockpit. Ich will wissen, wo wir aktuell stehen geblieben sind.

Untersuche mindestens:
1. Source-of-Truth-Dateien zum OPS Cockpit
   - src/webui/ops_cockpit.py
   - src/webui/app.py
   - tests/webui/test_ops_cockpit.py
   - alle docs/* mit Bezug zu OPS_COCKPIT / ops cockpit / truth_first_ops_cockpit / required views / operator summary surface
2. Relevante offene oder halb-fertige Bereiche
   - geplante vs. implementierte Views/Karten
   - Payload-/Read-Model-/HTML-Abdeckung
   - Contract-/Smoke-/HTML-Tests
   - Docs-Abdeckung
3. Jüngste Historie
   - letzte relevante Commits/PR-Hinweise zum OPS Cockpit auf main
4. Aktueller Funktionsstand
   - welche Bereiche im Cockpit sichtbar/implementiert sind
   - welche IDs / Karten / Sections explizit im HTML vorhanden sind
   - welche Observation-/Truth-/Runtime-Unknown-/Mismatch-/Gate-/Registry-/Evidence-Bereiche existieren
5. Offene Lücken / nächste sinnvolle größere Scheibe
   - nur analytisch benennen, nichts umsetzen

Konkrete Such-/Prüfpfade
- Nutze rg, git log, sed, python oder ähnliche read-only Mittel
- Beziehe auch Querverweise aus Docs ein
- Prüfe insbesondere, ob es Design-/Phase-/Checklist-Dokumente gibt, die den Soll-Stand beschreiben
- Stelle implementiert vs. dokumentiert gegenüber
- Benenne Widersprüche oder Unsicherheiten explizit

Gewünschtes Ergebnisformat
Schreibe eine Markdown-Datei:
  /tmp/peak_trade_ops_cockpit_status_readonly/OPS_COCKPIT_STATUS_SUMMARY.md

Struktur:
1. Executive Summary
2. Current State Snapshot
3. Source of Truth Map
4. Implemented Surfaces / Cards / Views
5. Test Coverage Snapshot
6. Docs Coverage Snapshot
7. Recent Change History
8. Gaps / Unclear Areas
9. Recommended Next Larger Slice (nur Empfehlung, keine Umsetzung)

Zusatzanforderungen
- Trenne sauber zwischen gesicherter Repo-Evidenz und Interpretation
- Zitiere konkrete Dateien/Funktionen/Testnamen/IDs
- Wenn etwas unklar ist, schreibe "unklar auf Basis der aktuellen Repo-Evidenz"
- Keine spekulativen Annahmen ohne Kennzeichnung
