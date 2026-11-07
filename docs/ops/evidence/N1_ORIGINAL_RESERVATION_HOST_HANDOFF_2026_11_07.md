---
docs_token: DOCS_TOKEN_N1_ORIGINAL_RESERVATION_HOST_HANDOFF_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Originale Reservation bis zur natürlichen Host-Rückgabe

Basis: 8dc28cb984b18fa72dd0fab5b82b987dcdaeab53 nach PR 7192.
Der [JSON-Nachweis](N1_ORIGINAL_RESERVATION_HOST_HANDOFF_2026_11_07.json)
bindet Quellen, historische Varianten, Gegenprobe und abgeschlossene Ownerprüfung.
Der Anschluss erhält eine ursprüngliche Referenz; er erzeugt keine Ausführungsidentität.

## Ursprüngliche Konstruktion und historische Varianten

Der [originale N1-Consumer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
committet den Kapitalhold und bindet das finale Envelope beim Originalbudgetowner.
Er gibt dieselbe Reservations-ID ausdrücklich zusammen mit diesem Envelope zurück.
S5 übernimmt sie in sein Ergebnisfeld PORTFOLIO_RESERVATION_ID.
S6 übernimmt bisher das Envelope, aber nicht dieses zusätzliche S5-Feld.

Die gezielte Gegenprobe am Basiscommit führt den wirklichen Standing-Supervisor
mit ursprünglichem N1, Sizing, Budgetwriter, S5 und S6 für Long und Short aus.
Beide Ergebnisse stoppen an PRE_EXTERNAL_EFFECT. Das zurückgegebene Envelope
trägt den Reservationsbezug, während der S6-Cycle-Record kein entsprechendes Feld hat.
Sämtliche Markt-/Kontofacts sind synthetisch, Stores temporär und Sockets gesperrt.

Der historische S6-Stand 0808d2eed72edc9c4677f01da48cb5a8b11110dc vom 3. November
trägt noch weniger Rückgabekontext. Er belegt die damals enthaltene Fassung,
keinen exakten ursprünglichen Entstehungszeitpunkt und keinen Betrieb.
Die Oktoberlinie aus PR 7092/7093 besitzt eine gesonderte Full-Core-
Kapitalguardautorisierung und einen daraus ableitenden Reconciliationidentity-Builder.
Dieser ältere Join ist offline begrenzt; LIVE_POST wird deaktiviert und LIVE
explizit abgelehnt. Er ist kein bereits vorhandener produktiver Hostauftrag.

## Konkreter Producer-Consumer-Weg und Änderung

1. N1 erzeugt die Reservation beim vorhandenen dauerhaften Owner und bindet dessen
   fertiges Envelope als PLAN_BOUND. Der Hold bleibt COMMITTED.
2. Der [originale S5-Consumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py)
   übernimmt diese Reservations-ID in sein bestehendes Extra-Feld.
3. Der [S6-Consumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py)
   kopiert jetzt genau dieses Feld in den jeweiligen ContinuousCycleRecordV1.
   Die neue optionale Eigenschaft heißt portfolio_reservation_id und liegt am Ende
   der bisherigen Dataclassfelder. Ihr Default bleibt leer. Das Envelope wird
   nicht nach einer vermeintlichen Ersatz-ID durchsucht.
4. Der vorhandene Policy-/Natural-ENTER-Pfad reicht dasselbe S6-Ergebnis bis zur
   tatsächlichen [Supervisor-Rückgabe](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/supervisor_v1.py)
   weiter. Dort erreicht die originale ID jetzt gemeinsam mit dem ursprünglichen
   Envelope, CanonicalIntent und dem später vom N1-Runner ergänzten Decisioncontext
   den aufrufenden Hostconsumer.

Die ID bezeichnet einen früher vom Originalowner angelegten Hold. Sie ist weder
eine aktuelle Ownerzulassung noch Permit, Submitversuch, bestätigter Fill oder
OKX-Positionswechsel. Auch ein HOLD-/Deny-Record kann eine inzwischen freigegebene
Reservation referenzieren. Jeder Cycle behält deshalb seinen eigenen Bezug;
eine spätere leere Referenz übernimmt nicht den Wert des vorherigen Records.

Die Änderung betrifft nur das native Rückgabeobjekt. Sie ergänzt keinen neuen
dauerhaften Ledger oder Recoverywriter und behauptet keine neue CLI- oder
dauerhafte JSON-Ausführungsschnittstelle. Der bestehende Originalbudgetstore
bewahrt Reservation und Envelope bereits selbst.

## Owner-Lebensdauer und Wiederaufnahme

Der Supervisor schließt seinen Budgetowner weiterhin im bestehenden finally-Pfad.
Ein dabei historisch noch positives Admission-Anzeigefeld ist keine operative
Nutzungsfreigabe: Der tatsächliche originale Submitkontextpredicate sperrt den
geschlossenen Owner. Die Cold-Read-Probe öffnet nur denselben temporären Store
über den ursprünglichen Ownervertrag. Holdbetrag, ID und PLAN_BOUND-Envelope
bleiben erhalten; der wieder geöffnete Owner verlangt seine originale frische
Recovery und sperrt weiterhin. Die neue Referenz liest weder ein Konto frisch
noch erneuert sie eine frühere Entscheidung.

## Executionidentität und weitere offene Anschlüsse

Der [vorhandene Identity-Builder](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_integration_v1.py)
übernimmt Account, Richtung, Mengen-/Plan-/Envelopebezug und Owner-GO aus einem
ausdrücklich zugelieferten FullCoreAuthorizationBindingV1. Plan-ID, Attempt-ID und
lokale Stateversion kommen zusätzlich vom Caller. Die natürliche produktive
Zulieferung dieser Authority-/Attemptfelder ist damit nicht schon hergestellt.

Die alte [Kapitalguardbindung](../../../src/ops/full_core_live_path_composition_root_v1/full_core_pre_post_capital_guard_binding_v1.py)
setzt instrument_id aus dem nativen Envelopeinstrument. Der heutige Budgetowner
verlangt dort dagegen das kanonische BoundInstrument. Die Gegenprobe hält beide
tatsächlich verschiedenen Instrumentkennungen getrennt fest. Diese historischen
Builder dürfen deshalb nicht ohne Prüfung ihrer eigenen Semantik eingesetzt werden.

Auch die alte atomare Consumption-Key-Konstruktion und der heutige
envelopegebundene Permitverbrauch gehören zu verschiedenen Zustandsownern.
Die neue Reservationsübergabe füllt keines dieser Felder mit einem Platzhalter,
aliasiert keinen Owner-GO und schließt keine dieser Authoritygrenzen.
Globale Root-/Owner-Eindeutigkeit, Pending-Custody, aktuelle Mengen-/Risiko-/Safety-
und Altplanzulassung, Never-submitted-Recovery und fortgesetztes Hostmandat bleiben offen.
Die sieben älteren Collector-/Account-Closeout-Verträge bleiben ebenfalls offen.

## Prüfung und Auswirkungen

Die [neuen Consumerprüfungen](../../../tests/ops/test_n1_original_reservation_host_handoff_v1.py)
verfolgen Long/Short am tatsächlichen Supervisor, ursprünglichen Hold und Decisionbezug,
geschlossene und kalt restaurierte Owner sowie getrennte HOLD-/ENTER-Referenzen.
Fehlende Producerwerte bleiben leer; ein nur im Envelope eingebetteter Bezug
ersetzt sie nicht. Der bestehende Sendeseam blockiert einen solchen fehlenden
Originalkontext weiterhin vor Transport.

Der JSON-Nachweis enthält die abgeschlossene gemeinsame Prüfung mit ursprünglichen
S5-/S6-/Host-/Budget-/Recovery- und direkten Wrapperverträgen. Zwei frühere neue
Testannahmen waren falsch: Das native Record mit Decimal-Intent ist nicht insgesamt
ein fertiges JSON-Wireformat; der PendingDecisionContext entsteht erst im N1-Runner
nach S5. Die Proben wurden an diesen vorhandenen Konstruktionen berichtigt,
ohne sie im Produkt zu verändern. Die frühere Gegenprobe erwartete außerdem
fälschlich eine geänderte Recovery-Anzeige beim Schließen; maßgeblich ist der
tatsächliche operative Ownerpredicate.

Handelsentscheidung, finanzielle Rechnung, Holds/Release, ursprüngliche Quellenzeiten,
GET-Budget, Permit-/Submitbarrieren und die Marktpreisanzeige bei Nullposition
bleiben unverändert. PRE_EXTERNAL_EFFECT beendet weiterhin den Lauf vor dem
gesonderten Versand; es gibt keinen neuen GET, Transportaufruf oder Aktivierungsweg.
