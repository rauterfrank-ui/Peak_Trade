# Autorität und Nutzung des aktuellen Atlas

```text
ATLAS_AUTHORITY=NONE
ATLAS_MUST_NOT_CREATE_AUTHORITY=true
CURRENT_ONLY=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
SOURCE_TAG=freeze/visible-system-2026-11-06-v2
SOURCE_COMMIT=a8e1c0088e25651ad4bb29ebe02e10142a0a92b2
```

Der [Atlas](generated/SYSTEM_ATLAS.md) stellt den fixierten Code und seine Schnittstellen dar. Der [Master Runbook](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) enthält die Betriebs-/Entwicklungsorientierung; ausführbare Verträge liegen in den dort zitierten Codeownern. Die [Map of Truth](../governance/PEAK_TRADE_MAP_OF_TRUTH.md) vermittelt die Navigation.

Fachgruppen und Katalogeinträge sind beschreibende Zuordnungen. Dateiexistenz, Syntaximport, tatsächlicher Zahlenverbrauch, Zustandsänderung und beobachtete Ausführung werden getrennt beurteilt. Das Atlasmodell erteilt keine Auswahl-, Kapital-, Credential-, Trading- oder Applyberechtigung.

Die Quelldaten unter [source](source/) und der Renderer `current_atlas.py` erzeugen die Ansichten unter [generated](generated/). Geänderte Produktquellen erfordern einen passend gebundenen Quellenstand. Ein unverändert fixierter Commit ist die Referenz für diese Darstellung.
