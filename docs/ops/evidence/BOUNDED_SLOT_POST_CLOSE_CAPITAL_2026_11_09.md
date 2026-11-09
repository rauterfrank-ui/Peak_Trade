# Slotbezogene Kapitalfortsetzung · erster Arbeitsschritt

Stand: 09.11.2026. Ausführungswirkung: NONE.

Der [Quellbeleg](BOUNDED_SLOT_POST_CLOSE_CAPITAL_2026_11_09.json) umfasst 265
gemeinsam erfolgreiche Fälle, Exit 0 und keine Deselektion. Die 1794 geladenen
Pythonquellen sind vor und nach dem Lauf identisch gebunden. Enthalten sind 50
neue Slotabschlussfälle und die bisherigen N1-Abschluss-, Budget-, Recovery-,
Ausführungs- und Policyverträge.

Die ursprüngliche Lifecycleprüfung verarbeitet vollständigen Fill, Flat,
Zeitfolge, Pendinglage und frisches Kontokapital separat für jeden der fünf
Slots. Vertauschte, fehlende oder veraltete Nachweise geben kein Kapital frei.
Andere Holds und Bindungen bleiben unverändert. Replay kann eine spätere
Neubelegung nicht freigeben. Ein unzureichender frischer Kontowert sperrt den
gemeinsamen Owner unter Erhalt aller Verpflichtungen.

Dies ist die finanzielle Übergabe. Die anschließende ursprüngliche
KEEP/REPLACE-Bindung und der nächste Coreverbrauch sind noch gesondert zu
verbinden. Alle Eingaben dieser Prüfung sind explizit synthetisch.
