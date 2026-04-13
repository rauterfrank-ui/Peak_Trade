# Bayesian Evidence Layer v0 — Decision / Parking Rule

## Status
machbar unter Guardrails

## Rolle
Ein zukünftiger Bayesian Evidence Layer v0 ist für Peak_Trade nur als kleiner, additiver, offline/read-only, versionierter Evidenz-Baustein vorgesehen.

Er darf vorerst:
- Unsicherheit sichtbar machen
- Evidenz verdichten
- Review priorisieren
- Drift-/Novelty-/Reliability-Hinweise liefern

Er darf vorerst nicht:
- Alpha-/Trading-Modell sein
- Execution, Sizing oder Go-Live steuern
- Auto-Retraining auslösen
- still Samples droppen/gewichten
- geschlossene Selbstlern-Loops erzeugen

## Guardrails
1. Offline only
2. Observation-first / read-only
3. Versionierte Provenance
4. Keine stille AI-/Execution-Kopplung
5. Keine Scheinsicherheit

## Re-Entry-Regel
Das Thema darf nur dann wieder aktiv vorgeschlagen werden, wenn ein kleiner, klar abgegrenzter Slice natürlich verfügbar ist, der:
- ausschließlich offline/read-only Evidence oder Read-Model betrifft
- keine Änderungen an Training, Execution, Risk-/Go-No-Go-Kernpfaden benötigt
- keine Live-/Auto-Retraining-Logik berührt
- Paper-/Shadow-/Test-Stabilität nicht gefährdet

## Gewünschter Hinweistext
Wenn diese Bedingungen erfüllt sind, soll explizit dieser Hinweis gegeben werden:

Hinweis: Jetzt wäre ein guter Zeitpunkt, den Bayesian Evidence Layer v0 als kleinen, additiven offline/read-only Evidence-Slice zu planen, weil der aktuelle Systemkontext dafür eine risikoarme Integrationsgrenze bietet.
