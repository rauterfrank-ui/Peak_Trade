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

Bei CONSUMING ohne ACK bleibt der Ausgang ungewiss. Eine Wiederholung meldet POST_CLOSE_CORE_OUTCOME_UNCERTAIN_RECONCILIATION_REQUIRED. Ein fehlendes ACK wird nicht in einen neuen Versuch oder einen angeblich erfolgreichen Lauf umgedeutet. Die automatische Rekonstruktion dieses ungewissen Consumerausgangs ist in diesem Slice nicht implementiert; dafür ist ein gesonderter originaler Consumer-/Ledgerreadback erforderlich. Ein physischer Stromausfall wird hier nicht als nachgewiesen bezeichnet.

## Bestehende Auswahl- und Zustandsregeln

Mindesthaltung, Hysterese und Gültigkeit werden beim zuständigen Selection-/Bindingowner ausgewertet. Die Injektionsfälle der Abnahme liefern ausdrücklich einen qualifizierten Rangnachrücker und ein erfülltes Haltefenster. Daraus folgt keine neue allgemeine Rotationsparameterwahl.

Ein zusätzlicher Gegenfall zeigt: Eine lange gehaltene Auswahl kann im vorhandenen Keep-Pfad trotz neuem Ranking an einer alten Gültigkeitsgrenze scheitern. Der neue Anschluss meldet dann keine erfolgreiche Corefortsetzung. Die genaue Erneuerungssemantik des ursprünglichen Cap23-/Cap24-Vertrags bleibt ein gesonderter offener Befund.

Der ursprüngliche Lane-Generation-Vertrag entscheidet weiter über Carry, Rekey oder Reset. Bei geänderter Bindungsidentität verwendet er die vorhandene Retention vor der Freigabe generationgebundener Dateien. Der Anschluss behauptet keine neue Garantie, aktive Scope-/SideStatefelder über beliebige geänderte Selectiongenerationen weiterzutragen. Die Mechanikgeschichte bleibt von der aktuellen Instrumentgeneration getrennt.

## Reichweite der Abnahme

Die [neuen Anschlussfälle](../../../tests/ops/test_productive_n1_post_close_continuation_v1.py) verwenden explizit injizierte Markt-/Ranking-/Account-/Closingbeobachtungen. Die originalen Produktionswriter, Budget-Recovery und der tatsächliche nächste S7/Coreconsumer werden auf temporären Testwurzeln aufgerufen. Der Test ersetzt keine dieser drei Kernwirkungen durch einen Dummy.

Geprüft werden außerdem Teilclose, fehlendes Kapital, fremder Account, falsche Zeitfolge, widersprüchliche Zielbeobachtung, unzulässige Frischeerweiterung, N>1, identische Replays, spätere Reservation, Ownerwiederöffnung, unterbrochener Membershipwrite, abgeschlossene Publication vor Core und verlorene ACK-Rückgabe. Ein ungewisser Consumerausgang bleibt gesperrt. Die Abnahme und weiterhin offenen Integrationsgrenzen stehen im [Umsetzungsbeleg](../evidence/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_2026_11_06.md).

Natürliche Datenqualität, neue echte Entries/Fills, N5-Dauerbetrieb, wirtschaftlicher Vorteil und selbsttätige produktive Übernahme sind keine Teilbehauptungen dieses Anschlusses.
