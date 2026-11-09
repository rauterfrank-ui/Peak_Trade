---
docs_token: DOCS_TOKEN_CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Entryzulassung während eines dauerhaften Coreversuchs

Ausgangspunkt ist der aktuelle Merge
`72c1de29b223abd6597fc1c88b38feeb1f1a7860`. Ein neuer nativer Corelauf konnte
vor einer verwendbaren Vorschau abbrechen, ohne den zuletzt gespeicherten
positiven Assessmentframe zu ersetzen. Ein zuvor gebundener Entryplan konnte
deshalb weiterhin an genau diesem alten Originalcursor geprüft werden.

## Veröffentlichung und Bedeutung

Der tatsächliche N1-T2-Pfad ruft den
[S7-Durable-Join](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py)
auf. Nach dessen Lane-/Storebindung und vor Restore plus Coreauswertung schreibt
der [Versuchsadapter](../../../src/ops/full_core_live_path_composition_root_v1/current_core_entry_attempt_v1.py)
eine negative Zulassungsmarkierung in das vorhandene `entry_assessment_frame`
des Originalcursors. Schema: `current_core_entry_attempt_uncommitted.v1`;
Status: `EVALUATION_NOT_COMMITTED`. Instrument, Native-ID, Cycle-ID, eine eindeutige
Attempt-ID und der Digest des vorherigen Cursors binden den Versuch. Die Markierung
hat keine Preise, Einheiten, wirtschaftlichen Schwellen oder Gültigkeitsdauer.

Dies bedeutet ausschließlich: Der neue dauerhafte Versuch ist noch nicht mit
einem tatsächlichen Coreausgang veröffentlicht. Es ist kein erfundenes
Survival-BLOCKED, C3-Ergebnis, Scopewechsel oder bestätigter Fill. Sämtliche
nativen Cursorfelder einschließlich SideState, Scope, C3/C1 und Epochen bleiben
bei der Markierung gleich. Es entsteht weder eine zweite Entscheidungsformel
noch ein zusätzlicher Store oder positiver Authority-Owner.

Nur der ursprüngliche Cursorwriter veröffentlicht diese Markierung. Sein
bestehender Lock, temporäre Datei, Datei-fsync, atomarer Dateiaustausch und
Readback bleiben die Schreibgrenze. Die erste Veröffentlichung verlangt den
exakten Digest des gelesenen Vorgängers. Der tatsächliche native Folgelauf
ersetzt die Markierung erst nach der bisherigen Outgoing-Prüfung und erfolgreichem
Layered-Episode-Bootstrap, wiederum mit genau dieser Markierung als CAS-Vorgänger.
Eine jüngere Markierung kann dadurch nicht von einem älteren S7-Versuch
überschrieben werden. Ein unbedingter Legacy-Write über eine offene Markierung
wird vom Originalwriter ausdrücklich abgewiesen.

Fehlen Originalcursor oder gültiger restaurierbarer Originalzustand, erzeugt
der Adapter keinen erfundenen Corezustand. Die bisherigen Restore-/Consumer-
Verweigerungen bleiben zuständig. Ein veralteter expliziter EG-Override darf
keinen neueren Originalcursor ersetzen. In-Memory-S5 und direktes S6-Restore
erhalten durch diesen Anschluss keinen neuen Persistenzauftrag.

## Consumer und Versandgrenze

Der [vorhandene Originalcursor-Consumer](../../../src/ops/portfolio_capital_reservation_budget_v1/core_cursor_source_v1.py)
weist die Markierung mit `CURRENT_CORE_ASSESSMENT_ATTEMPT_NOT_COMMITTED` ab.
Der bisherige KILL_ALL-Vorrang bleibt erhalten. Das explizite negative Faktum
wirkt auch bei älteren Sourceversionen; deren positive Assessmentscope wird
dadurch nicht aufgewertet. Der
[Framereader](../../../src/ops/full_core_live_path_composition_root_v1/current_core_entry_assessment_frame_v1.py)
verweigert dieselbe Markierung.

Damit verwenden frühe und späte tatsächliche POST-Prüfung weiter dieselben
Originalreader. Vor möglichem Socketzugriff gelten die bestehenden negativen
PRE_SOCKET-Abschlussregeln. Ein bereits konsumierter abgebrochener Versuch wird
auch nach einer später passenden Cursorveröffentlichung nicht wieder geöffnet.
Nach möglicherweise erfolgtem Senden bleiben Unknown, SENT_INITIATED,
MAY_HAVE_SENT und die Kapitalbindung erhalten. Weder Fehler noch Scopewechsel
begründen eine Freigabe reservierten Kapitals.

Die tatsächliche POST-Sourceintegrität umfasst jetzt auch den Versuchsadapter
und den tatsächlichen S7-Join. Drift in einem dieser Körper wird vor einer
Sendeberechtigung abgewiesen. Die bloße Existenz der Markierung ersetzt diese
Quellenprüfung nicht.

## Nachweis und verbleibende Grenzen

Die [Tests](../../../tests/ops/test_current_core_entry_attempt_v1.py) verbinden
echten S7-Aufruf, Originalwriter und gehaltenen Plan. Eine kausale Gegenprobe
entfernt ausschließlich die neue Veröffentlichung: Derselbe ungültige native
Lauf beziehungsweise dieselbe Producerexception lässt dann die alte Zulassung
stehen. Mit Veröffentlichung verweigert derselbe Consumer den Plan. Weitere
Fälle prüfen native LONG-/SHORT-Supervisorfortsetzung, Legacy-Quellen, konkurrierende
Versuche, gescheiterten Bootstrap, frühe/späte POST-Barrieren, irreversiblen
Verbrauch, möglichen Versand, unveränderte Holds und Prozessende nach
abgeschlossener Markierung. Zwei tatsächliche Source-Driftfälle schützen die
neuen Pfade. Der [Abschlussbeleg](../evidence/CURRENT_CORE_ENTRY_ATTEMPT_ADMISSION_2026_11_09.md)
bindet Lauf, Quellen und verbleibende Grenzen.

Scheitert der Speicherzugriff bereits vor Veröffentlichung der Markierung,
wird Core nicht aufgerufen; der bisherige Cursor kann unverändert vorhanden
sein. Ein unabhängiger Sender bei solchem Speicherausfall ist hierdurch nicht
als koordiniert nachgewiesen. Prozessende nach Datei-fsync und Readback ist
kein Beweis für physischen Stromausfall, Verzeichnis-fsync oder atomaren
Checkpoint über Cursor, Layered Episode, DDO und weitere Stores. Ein späterer
CAS-Konflikt setzt deren gegebenenfalls schon erfolgte Fortschreibung nicht
automatisch zurück. Direkte Coreaufrufer außerhalb des tatsächlichen N1/S7-Pfads
werden nicht pauschal in diesen Vertrag einbezogen.

Die aktuellen festen Replay-Kosten-/Metrikwerte liefern weiterhin keinen
belegten wirtschaftlichen Producer mit Einheit, Horizont und Kenntniszeit.
Produktives numerisches Risiko und die Gesamtabnahme bleiben offen. Native
Handelsformeln, Kernsiegel, Format-Freeze, Policys und Freeze-Tags bleiben
erhalten; historische Implementierungen oder Parameter werden nicht übernommen.
