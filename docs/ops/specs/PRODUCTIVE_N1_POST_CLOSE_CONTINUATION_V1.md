---
docs_token: DOCS_TOKEN_PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_V1
status: implemented_bounded_offline
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
authority: NONE
runtime_authorization_effect: NONE
---

# N1-Fortsetzung nach geprüftem Positionsschluss

## Fachliche Aufgabe

Der vorhandene Post-Close-Composer kann einen Kapitalrefresh und einen Membershipvorschlag liefern. Dieser Anschluss führt den Vorschlag über die ursprünglichen Writer und die Originalbudget-Recovery bis zu einem weiteren tatsächlichen Coreaufruf. Seine Zuständigkeit ist die Reihenfolge und Nachvollziehbarkeit der Übergaben. Entscheidung, Menge, Kapitalwahrheit und Ausführung behalten ihre bisherigen Owner.

Ausgangspunkt ist der [Paket-A-Abgleich](../evidence/OUTER_RING_PACKAGE_A_SEMANTIC_BASELINE_2026_11_06.md), Abschnitt 6. Der [Master-Runbook](../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) und die Originalverträge bleiben übergeordnet. Dieser Vertrag aktiviert weder einen Dienst noch einen Handelslauf.

## Eintritt und Rückgabe

Der vorhandene [FA-Orchestrator](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py) besitzt einen optionalen Parameter post_close_continuation. Ohne diesen Parameter bleibt sein bisheriger Ablauf erhalten.

Der typisierte Kontext ProductiveN1PostCloseContinuationV1 führt:

- den ursprünglichen Lifecycle-/Reconciliationausgang und seine genaue Executionidentität;
- den ursprünglichen Closefeedbackrequest samt gebundener Lane/Instrumentgeneration, Reservationen, frischer kanonischer Kapitalevidence und Rankingreview;
- den expliziten Membershipstore und die frische ursprüngliche Portfolio-/Zielbeobachtung;
- eine Kapitalfrischegrenze, die den bestehenden numerischen Equity-TTL nicht erweitern darf.

Die übergebene Membership ist die ursprüngliche Reviewbasis. Der neue Vorschlag wird vom ursprünglichen Selector berechnet. Ein extern eingeschobener Zielvorschlag oder ein abweichendes Ranking wird abgelehnt. Der Anschluss verlangt genau eine vorherige belegte Lane und genau ein zulässiges Zielmitglied. Eine Auswahl von mehr als einem Mitglied wird nicht auf ein Instrument abgeschnitten.

Beim ersten erfolgreichen Aufruf wird das bisherige Orchestratorresultat um einen Fortsetzungsbeleg ergänzt. Bei identischer Wiederholung eines abgeschlossenen Übergangs ist die Rückgabe ausdrücklich PostCloseContinuationReplayV1 mit dem gespeicherten historischen Beleg; sie enthält keinen neu ausgeführten Corelauf. Ein anderer Cycleprefix für denselben Close gilt als Konflikt.

## Reihenfolge und Originalowner

1. Gehaltener ursprünglicher Assignmentwriter und vorherige dauerhafte N1-Topologie werden geprüft. Die Closingbindung muss mit der vorhandenen Selection und Lane übereinstimmen.
2. Der ursprüngliche Post-Close-Composer prüft bestätigte Closingorder, Flat, Pending/Custody, Identität und Zeitfolge. Der ursprüngliche Budgetowner führt seinen zulässigen N1-Refresh aus.
3. Der ursprüngliche Membershipwriter persistiert den unveränderten Selectorvorschlag und liest ihn zurück. Der Fortsetzungsbeleg speichert Quellenbindung und Zielmembership.
4. Die vorhandene checked Publication schreibt Selection und Topologie unter ihren Originalchecks. Custody-COMMIT bleibt ein eigener erforderlicher Input. Eine abgeschlossene Publication ist nur mit ihrem erhaltenen Originalabschlussbeleg, gleichem Topologiedigest und exakt passenden Selectiondigests wiederverwendbar.
5. Cap24 bindet das tatsächliche Ziel. Der ursprüngliche Budget-Recoverypfad prüft frische Facts und genau diese neue Bindung. Ein aktiver Hold kann dabei nicht still auf eine neue Instrumentgeneration umgebunden werden.
6. Vor dem nächsten tatsächlichen Readiness-/Coreaufruf wird die Phase CONSUMING dauerhaft geschrieben. Danach werden die ursprünglichen S7-/Coreausgabe und die tatsächlich konsumierte Instrumentbindung ausgewertet.
7. Erst bei dieser beobachteten Consumerwirkung wird ACKED gespeichert: Lane, native und kanonische Instrumentidentität, Cycle-ID, tatsächlicher Inputdigest und Decisionoutcome.

Der Beleg besitzt keinen eigenen Ranking-, Sizing-, Reservation- oder Modellzustand. Er ist kein Orderpermit. Alle bisherigen N1-, External-Effect-, Post-, Attempt-, Session- und Safetygrenzen bleiben wirksam.

## Persistenz und Wiederaufnahme

Der Beleg liegt unter dem bestehenden Assignmentcheckpoint in einem eigenen Post-Close-Unterordner. Sein Schlüssel ist die ursprüngliche Close-Envelopeidentität. Quellenbindung, Phase und Consumer-ACK werden per atomarem Dateiersatz mit Datei- und Verzeichnis-fsync geschrieben.

Vor dem Coreeintritt können identische Wiederholungen den ursprünglichen Membershipwriter sowie unterbrochene oder vollständig abgeschlossene Publications wiederverwenden. Der Originalbudgetrefresh bleibt anhand der Closingidentität idempotent. Spätere Reservationen werden bei einem bereits bestätigten Fortsetzungsreplay nicht erneut angerührt.

Nach einem bestätigten ACK wird kein zweiter Coreaufruf ausgeführt. Die Wiederöffnung der ursprünglichen Budget- und Assignmentowner verleiht durch dieses historische ACK keine neue Konto-Admissibility.

Bei CONSUMING ohne ACK wird ausschließlich der dauerhafte Abschlussbeleg des ursprünglichen N1-Consumers zurückgelesen. Der ursprüngliche Readiness-Composer schreibt ihn erst nach dem tatsächlichen S7/Coreverbrauch und seinen bestehenden Boundarychecks. Der Beleg bindet vollständige Instrumentgeneration, Lane/Statewurzel, ursprünglichen Übergangsdigest, Revision, Cycleprefix und tatsächlichen Core-Inputdigest sowie Decisionoutcome. Der Bootstrapzyklus kann den späteren Consumerzyklus nicht bestätigen.

Der Originalconsumer sichert seinen fertigen Ausgang zuerst als dauerhaften vorbereiteten Beleg und veröffentlicht danach den finalen Abschluss. Liegt der finale Abschluss beim Wiederaufruf noch nicht vor, darf die Wiederaufnahme ausschließlich den exakt passenden vorbereiteten Originalbeleg fertig veröffentlichen. Ein vorübergehender Veröffentlichungsfehler erhält diesen Beleg und meldet POST_CLOSE_CONSUMER_PUBLICATION_RETRY_REQUIRED; ein weiterer zulässiger Wiederaufruf kann nach Behebung des Speicherfehlers daran fortsetzen. Ein widersprüchlicher finaler Beleg wird dabei nicht überschrieben.

Liegt der exakte unveränderte Abschluss vor oder wurde seine vorbereitete Veröffentlichung zulässig fertiggestellt, darf die Wiederholung das verlorene ACK nachtragen und einen historischen PostCloseContinuationReplayV1 liefern. Sie führt weder Core, Membershippublication noch Kapitalrefresh erneut aus und stellt keine Konto-Admissibility wieder her. Der normale ACK bindet denselben ursprünglichen Consumerbeleg. Neue und wiederholte Belege verleihen keine Ausführungsauthority.

Fehlen sowohl finaler als auch vorbereiteter Originalabschluss oder ist der benötigte Beleg unvollständig, korrupt oder widersprüchlich, meldet die Wiederholung weiterhin POST_CLOSE_CORE_OUTCOME_UNCERTAIN_RECONCILIATION_REQUIRED. Ein Cursor, ein einzelner gespeicherter Decisionrecord oder eine abgeschlossene vorgelagerte S5-Phase ersetzt diesen Beleg nicht. Insbesondere bleibt ein Abbruch nach Coreverbrauch, aber vor dem ersten dauerhaften vorbereiteten Consumerbeleg gesperrt. Alte ungewisse Übergänge ohne diesen Originalbeleg werden nicht automatisch migriert. Der [Rücklesebeleg](../evidence/N1_CONSUMER_ACK_READBACK_2026_11_06.md) grenzt die geprüfte Unterbrechung genau ab. Ein physischer Stromausfall wird hier nicht als nachgewiesen bezeichnet.

Franks Ziel der selbsttätigen Wiederherstellung der Betriebsbereitschaft bleibt verbindlich: Übergang aufklären, aktuelle Originalzustände reconciliieren und erst nach erneuter gültiger Admission weiterarbeiten. Der historische ACK allein schaltet kein Konto frei. Der vorhandene originale Budget-Recoveryowner kann nach frischen Kapital-/Portfolio-/Reconciliationinputs wieder zulassen; stale Facts bleiben gesperrt. Diese Ownerwirkung ist gesondert offline geprüft.

## Anschluss am bestehenden Hoststart

Der bestehende [Standing-N1-Supervisor](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/supervisor_v1.py) nimmt optional post_close_startup_recovery entgegen. PostCloseStartupRecoveryRequestV1 bindet den vom aufrufenden Owner erhaltenen ursprünglichen Orchestratoraufruf. Er wird nicht aus einem Dateiscan, Cursor oder einer vermuteten Instrumentidentität zusammengesetzt.

Nach den bestehenden Owner-/Account-/Beobachtungsprüfungen und vor dem WP02-Hook beziehungsweise einem weiteren Corezyklus prüft der [Startanschluss](../../../src/ops/n1_standing_pre_external_runtime_supervisor_v1/startup_binding_v1.py):

- gehaltenen Originalassignmentwriter und exakt dieselbe Topologie-/Lane-Statewurzel;
- ursprüngliche dauerhafte Budgetwurzel und denselben expliziten Account;
- vorhandenen integren Übergangsbeleg in CONSUMING oder ACKED und die vollständige aktuelle BoundInstrument-Generation;
- neue private Kontobeobachtung des bestehenden Budgethosts, offene Orders und ungelöste originale Ausführungsreconciliation.

Nur dann ruft er die ursprüngliche Fortsetzungs-Recovery mit dem wieder geöffneten Originalbudgetowner auf. Der historische Replay darf einen vorbereiteten Originalabschluss veröffentlichen und sein ACK nachtragen. MEMBERSHIP_STORED oder ein fehlender Übergang werden an diesem Startanschluss abgewiesen: Hier darf kein neuer Coreverbrauch als Recovery entstehen. Danach arbeitet der bestehende Supervisor mit seinem ursprünglichen S6/S5/S7-Pfad und eigener gültiger Authorization weiter. Seine lane_state_root ist im aktuellen S8-Consumer die Topologiebasis; ein zusätzlich angehängtes LANE_1 würde eine falsche neue Stateadresse erzeugen.

Der Startanschluss setzt keine Budgetadmission. Diese bleibt bei der bestehenden Entry-Schnittstelle des Budgethosts und benötigt neue kanonische Kapital-/Portfoliofacts. Der Supervisor schließt seinen Owner auch bei nachgelagertem Startfehler. Der [Hoststartbeleg](../evidence/N1_SUPERVISOR_STARTUP_RECOVERY_2026_11_07.md) dokumentiert Ablauf, Gegenfälle und Reichweite.

Die bestehende Unified-Recovery meldet Beobachtungs-Recovery und Beispiel-/Vertragsprüfungen getrennt. Ein simulierter Order-Lifecycle oder ein geprüftes Reservation-Enum ist keine Rekonstruktion der tatsächlichen Orders, Holds oder Treasury. recovery_completed und unified_restart_safe bleiben deshalb für eine unbelegte vollständige Owner-Recovery false; observation_recovery_completed bezeichnet den engeren Beobachtungserfolg. Ein erfolgreicher begrenzter PRE_EXTERNAL-Supervisorlauf hebt diese Grenze nicht auf.

Offen bleiben die dauerhafte Bereitstellung des vollständigen Startkontexts durch einen Prozesshost nach echtem Prozessverlust, die durchgängige Verknüpfung aller Betriebsbereitschafts-/Safetygates und die Aufklärung eines Ausgangs ohne jeden Originalabschluss. Es wird kein vollständiger autonomer Hostneustart behauptet.

## Bestehende Auswahl- und Zustandsregeln

Mindesthaltung, Hysterese und Gültigkeit werden beim zuständigen Selection-/Bindingowner ausgewertet. Die Injektionsfälle der Abnahme liefern ausdrücklich einen qualifizierten Rangnachrücker und ein erfülltes Haltefenster. Daraus folgt keine neue allgemeine Rotationsparameterwahl.

Der ursprüngliche Keep-Befund ist durch die [Auswahlfrischekorrektur](../evidence/N1_SELECTION_FRESHNESS_2026_11_06.md) im begrenzten Offlinepfad behoben: Cap23 erhält den ursprünglichen Instrumenteintritt für die Mindesthaltung und bindet die aktuelle Gültigkeitsgrenze an das neu geprüfte Rankingereignis. Wiederholtes Beobachten desselben Rankings verlängert diese Frist nicht. Zukünftige, alte oder korrupte Rankinginputs können die Auswahl nicht erneuern.

Die Abnahme zeigt zuerst die Ablehnung der unveränderten abgelaufenen Auswahl am originalen Cap24-Gate und danach die tatsächliche Fortsetzung mit frisch geprüfter, vom Originalwriter persistierter Keep-Auswahl. Alte gespeicherte Receipts werden nicht nachträglich umgeschrieben; eine automatische Migration bereits unter der alten Semantik fehlgeschlagener Checkpoints wird nicht behauptet.

Der ursprüngliche Lane-Generation-Vertrag entscheidet weiter über Carry, Rekey oder Reset. Bei geänderter Bindungsidentität verwendet er die vorhandene Retention vor der Freigabe generationgebundener Dateien. Der Anschluss behauptet keine neue Garantie, aktive Scope-/SideStatefelder über beliebige geänderte Selectiongenerationen weiterzutragen. Die Mechanikgeschichte bleibt von der aktuellen Instrumentgeneration getrennt.

## Reichweite der Abnahme

Die [neuen Anschlussfälle](../../../tests/ops/test_productive_n1_post_close_continuation_v1.py) verwenden explizit injizierte Markt-/Ranking-/Account-/Closingbeobachtungen. Die originalen Produktionswriter, Budget-Recovery und der tatsächliche nächste S7/Coreconsumer werden auf temporären Testwurzeln aufgerufen. Der Test ersetzt keine dieser drei Kernwirkungen durch einen Dummy.

Geprüft werden außerdem Teilclose, fehlendes Kapital, fremder Account, falsche Zeitfolge, widersprüchliche Zielbeobachtung, unzulässige Frischeerweiterung, N>1, identische Replays, spätere Reservation, Ownerwiederöffnung, unterbrochener Membershipwrite, abgeschlossene Publication vor Core und verlorene ACK-Rückgabe. Ein ungewisser Consumerausgang bleibt gesperrt. Die Abnahme und weiterhin offenen Integrationsgrenzen stehen im [Umsetzungsbeleg](../evidence/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_2026_11_06.md).

Natürliche Datenqualität, neue echte Entries/Fills, N5-Dauerbetrieb, wirtschaftlicher Vorteil und selbsttätige produktive Übernahme sind keine Teilbehauptungen dieses Anschlusses.
