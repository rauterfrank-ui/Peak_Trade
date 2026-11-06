---
docs_token: DOCS_TOKEN_N1_CONSUMER_ACK_READBACK_2026_11_06
status: bounded_offline_verified
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
authority: NONE
runtime_authorization_effect: NONE
---

# N1: Originalconsumer-Abschluss bei verlorenem Übergabe-ACK

Ausgangsstand: 82615aa2cdc01b74a08204b6a156712a6e29344f, nach PR 7182.
Dieser Schritt setzt Paket D/G des beauftragten Außenring-Runbooks fort.
Die historische Link-/Krakenrecherche bleibt zurückgestellt.

## Semantik und belegte Ursache

Der ursprüngliche [N1-Anschluss](../specs/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_V1.md)
schreibt vor dem Consumer CONSUMING und nach seiner tatsächlichen Rückgabe ACKED.
Ein Verlust dieser ACK-Rückgabe vor dem Write ließ den Übergang dauerhaft
ungewiss. Die Sperre verhinderte korrekt einen blinden erneuten Coreaufruf.

Der vorhandene Cursor belegt fortgeschriebenen Zustand; der S5-Ledger hat eigene
Sequenzierungsfelder. Beide enthalten für diesen Übergang keinen vollständigen
dauerhaften Abschluss mit tatsächlichem Core-Inputdigest und exakter
Instrumentgeneration. Aus ihrem bloßen Vorhandensein wird kein ACK abgeleitet.

## Originalowner und Wirkung

Der [Readiness-Composer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1/readiness_join_v1.py)
publiziert auf den explizit gebundenen N1-Aufruf einen
[dauerhaften Consumerabschluss](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1/consumer_completion_v1.py).
Das geschieht nach Original-S7/Coreverbrauch, Instrument-/Rootprüfung und
den bestehenden Readiness-/External-Effect-Checks. Ohne den optionalen
Abschlussauftrag bleibt der bisherige Readinesspfad erhalten.

Der Abschluss enthält Übergangsdigest, Lane und Statewurzel, vollständiges
BoundInstrument, Revision und Cycleprefix sowie tatsächliche Cycle-ID,
Inputdigest und Decisionoutcome. Der originale Bootstrap hat einen anderen
Cyclebezug und kann diese konsumierte Folgeentscheidung nicht bestätigen.
Post-/Permit-/External-Effect-Felder müssen die bisherige gesperrte Grenze
erhalten. Die Quittung ersetzt keinen Cursor, keinen Kapitalzustand und keinen
Ausführungsledger.

Die Veröffentlichung sichert den fertigen Originalausgang zuerst in einer
vorbereiteten Datei und publiziert danach den finalen Abschluss. Datei-fsync,
atomare Create-ohne-Overwrite-Verknüpfungen und Verzeichnis-fsync erhalten diese
Reihenfolge. Scheitert der letzte Schritt, bleibt der vorbereitete Originalbeleg
erhalten. Die Wiederaufnahme liest ihn strikt zurück, veröffentlicht ihn fertig
und trägt danach das ACK nach. Ein anhaltender Speicherfehler wird als
PUBLICATION_RETRY_REQUIRED unterschieden; nach Wegfall des Fehlers kann die
gleiche Übergangsidentität selbsttätig fortsetzen. Andere Inhalte unter derselben
Übergangsidentität und widersprüchliche finale Records werden abgewiesen.
Der gehaltene originale Assignmentwriter begrenzt die Fortsetzungsoperation weiter.

Der [Fortsetzungsowner](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/post_close_continuation_v1.py)
liest bei CONSUMING nur den exakt passenden Originalabschluss. Bei erfolgreichem
Readback trägt er das ACK nach und liefert den historischen Replaybeleg. Core,
Publication und Kapitalrefresh werden dabei nicht neu aufgerufen. Auch ein
normaler ACK bindet jetzt genau diesen Consumerabschluss.

## Prüfungen und bestehende Testinputs

Der neue positive Fall scheiterte vor der Änderung am bisherigen
CORE_OUTCOME_UNCERTAIN. Die [Anschlussfälle](../../../tests/ops/test_productive_n1_post_close_continuation_v1.py)
bestätigen jetzt die Rücklesefortsetzung bei verlorenem ACK vor und nach dem
ACK-Write. Die [zusätzlichen Rücklesefälle](../../../tests/ops/test_n1_consumer_completion_readback_v1.py)
zählen tatsächliche Aufrufe des Original-Coreowners und prüfen deren
unveränderte Anzahl über die Wiederaufnahme. Ein etwaiger Bootstrap bleibt
als eigener ursprünglicher Aufruf sichtbar.

Weitere Fälle prüfen fehlende, partielle, korrupte und selbstkonsistent neu
gehashte, aber falsch gebundene Belege, fremde Generation/Revision/Lane/Root,
Bootstrapverwechslung, External-Effect-Leaks, unveränderliche Veröffentlichung,
spätere Reservation, Ownerwiederöffnung sowie Readback in einem frischen
Pythonprozess. Ein echter Fehler vor dem ersten dauerhaften vorbereiteten
Consumerbeleg lässt CONSUMING und die Sperre bestehen. Eine Unterbrechung der
anschließenden finalen Publication wird dagegen automatisch aus dem vorbereiteten
Originalbeleg aufgearbeitet, auch nach Ownerwiederöffnung. Ein wiederholter
Speicherfehler erhält die Originale bis zu einem späteren erfolgreichen Versuch.
Eine anfänglich zu breit injizierte
Dateiverknüpfungsstörung wurde auf diese genaue Publication begrenzt.

Sieben bestehende Readinessfälle scheiterten auch mit der unveränderten
Ausgangsfunktion an nicht mehr zulässigen nativen Instrumentplatzhaltern.
Die betroffenen lokalen Fixtures verwenden jetzt gültige unterschiedliche
Futuresidentitäten sowie je Lane gebundene Preis-/Candleinputs. Ihre ursprünglichen
Isolations-, Restart-, Lock- und Boundaryasserts bleiben erhalten; ein zusätzlicher
Negativfall erhält die Ablehnung der alten unbekannten Contractidentität.
Die Produktprüfung wird nicht abgeschwächt.

Prüfzahlen, Quellhashes und genaue Reichweite stehen im
[maschinenlesbaren Beleg](N1_CONSUMER_ACK_READBACK_2026_11_06.json).

## Betriebsbereitschaft nach Recovery

Franks zusätzliche Vorgabe verlangt die selbsttätige Wiederherstellung der
Betriebsbereitschaft. Die Übergangsreparatur ist der erste Schritt. Nach
Ownerwiederöffnung ist der Budgetowner trotz repariertem ACK weiter gesperrt.
Ein gesonderter Anschlussfall ruft den originalen Budget-Recoveryowner mit
aktuellen Instrumentbindungen und expliziten Originalbeobachtungen auf:
Frische Facts erzeugen ADMITTED, dieselben überalterten Facts keine Zulassung.
Auch dieser Ablauf führt keinen weiteren Corezyklus und keine Order aus.

Damit ist ein konkreter Rückweg vom vorbereiteten Originalausgang bis zum
bestätigten ACK und zur erneut belegten Budget-Admissibility geprüft. Die
automatische Hostauslösung und der gemeinsame Nachweis aller weiteren
Readiness-/Safetygates gehören zur weiteren Außenringintegration. Ein ACK wird
nicht als fertige Wiederaufnahme des Gesamtsystems etikettiert.

## Verbleibende Grenzen

Ein Abbruch vor dem ersten dauerhaften vorbereiteten Originalbeleg bleibt
ungewiss und benötigt weitere originale Zustands-/Consumerreconciliation. Alte
CONSUMING-Belege ohne Originalabschluss werden nicht nachträglich erraten.
Die Rückgabe eines historischen ACK erneuert keine Account-, Trading- oder
Orderfreigabe; aktuelle Originaladmission bleibt erforderlich. Die vollständige
Handels-/Finanztransaktion ist dadurch nicht
atomar geworden. Natürlicher Dauerbetrieb, N5, aktiver Scope-/SideState-Carry
über neue Bindungsgenerationen, der vollständige Kill-Switch-Notfallablauf
und physischer Stromausfall bleiben gesonderte Aufgaben.

Die Prüfungen verwenden temporäre Stores und injizierte Inputs. Freeze-Tags,
Kernquellen, finanzielle Defaults, bestehende Sperren und operative Zustände
werden nicht verändert; kein Dienst oder Handelslauf wird gestartet.
