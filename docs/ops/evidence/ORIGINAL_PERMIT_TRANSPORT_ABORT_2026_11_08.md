---
docs_token: DOCS_TOKEN_ORIGINAL_PERMIT_TRANSPORT_ABORT_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originaler Transportabort erreicht den ursprünglichen Budgetconsumer

Arbeitsbasis: b78406ae3bd40a27dd79cfabbf188a6375899c9c auf dem bestehenden Branch
fix/current-post-safety-veto-handoff. Arbeitscommit ohne neuen PR; keine
Gesamtabnahme des Außenrings oder Betriebsaktivierung.

Der [Semantikvertrag](../specs/ORIGINAL_PERMIT_TRANSPORT_ABORT_AND_BUDGET_V1.md)
erklärt Originale, historische Variante, Identitäten, Einheiten, Zeitbezüge,
Zustandsübergänge und tatsächliche Wirkung beim Consumer. Der
[JSON-Nachweis](ORIGINAL_PERMIT_TRANSPORT_ABORT_2026_11_08.json) bindet die zuerst
fehlschlagenden Originalconsumerfälle und den beendeten gemeinsamen Ownerlauf.

## Ursache und Änderung

Zwei Gegenproben am unveränderten Arbeitscommit stoppen tatsächlich vor HTTP,
hinterlassen aber nur SENT_INITIATED. Der Budgetconsumer kann daraus kein
Nichtabsenden belegen. Die historische separate Sicherheitslinie kennt einen
negativen Endzustand; ihr damaliger lokaler Nullzähler ist für die jetzige
Budgetverwendung kein ausreichender Ersatz für eine gebundene Transportgrenze.

Die neue Verbindung bleibt bei den ursprünglichen Writern: Der Permitrecord
erhält einen exklusiven Transportclaim und eine irreversible, vor dem Socket
dauerhaft geschriebene MAY_HAVE_SENT-Grenze. Nur der noch davor offene konkrete
Claim kann auf ABORTED_BEFORE_TRANSPORT wechseln. Permit und GO bleiben verbraucht.
Der Original-V2-Budgetlink pinnt beim Submit den tatsächlichen Sendestore. Der
Budgetconsumer liest dort den exakten ursprünglichen negativen Record und gibt
ihn an seine vorhandene Reconciliation weiter. Seine aktuellen Venue-/Positions-/
Pendingprüfungen bestimmen weiterhin die tatsächliche Kapitalfreigabe.

Eine passende Fehlerzeichenfolge oder ein lokaler Zählerstand null genügt nicht.
Nach MAY_HAVE_SENT, bei fehlendem Abschluss, fremden Originalen oder Konflikt
mit einer Venuebeobachtung bleibt die Kapitalbindung erhalten. Ein bloß negativ
geschlossener Transport erteilt keine neue Kapitaladmission.

## Prüfung und berichtigte Testannahmen

26 neue Fälle prüfen die konkreten Originalconsumer einschließlich Kaltlesen,
Sync-/Readbackfehlern und zwei konkurrierenden Claims. Die ersten beiden Fälle
scheitern am unveränderten Basiscode. Die gemeinsame Prüfung umfasst auch die
vorherige Safety-, Budget-, Plan-/V1-/V2-, Wrapper-, HTTP- und Exchangekette.
Der vollständig beendete standgebundene Lauf steht im JSON. Ein bestandenes
identisches Prüfergebnis wird für Dokumentation oder Commit nicht wiederholt.
Ergebnis: **545 PASS, Exit 0**, darunter 26 neue Fälle; zwei bekannte historische
Dokumenttests bleiben deselected und zählen nicht als PASS.

Ein neuer Wiederanlauftest nahm zunächst einen bereits geöffneten Hostowner und
anschließend einen schreibfreien zweiten Observe-Aufruf an. Tatsächlich öffnet
der Originalhost den Owner erst bei Observe und schreibt bei jedem erneuten
Aufruf seinen vorhandenen Recovery-Zaun. Der Test kontrolliert nun zuerst den
kalt geöffneten Originalowner und verlangt später nur diesen einen Fence-Write,
keinen zweiten Release-/Reconciliationlauf. Die Hostlogik wurde nicht dafür geändert.
Ruff beanstandete außerdem eine Lambda-Zuweisung im neuen Testhelper; sie ist
als reguläre Funktion geschrieben. Die frühere Diagnoseausgabe bleibt erhalten.

Zwei frühere Dokumenttests bleiben ausdrücklich ausgeklammert und offen. Ihre
alten Atlas-/Runbookverträge werden durch diesen Finanz-/Transportnachweis nicht
geschlossen. Sieben ältere Collector-/Account-Closeout-Fehler, frühere breite
Abnahmebefunde und der datierte Obsidian-Projektionscheck bleiben ebenfalls offen.

## Nachweisgrenzen

Temporäre Originalwriter und injizierte GET-/K1-/HTTP-Ports, gesperrte Sockets;
kein realer Safetyzustand, Schlüssel, Venuekontakt, Dienststart oder Kapitalfluss.
Lokale Dateisynchronisation und Wiederöffnung ersetzen keinen physischen
Stromausfallnachweis. Globale Root-/Anti-Clone-Herkunft, unabhängige Authority,
signierte Recovery, vollständige aktuelle Zulassung und fortgesetzter autonomer
Hostanschluss sind weiterhin offen. Der Außenring A–H ist nicht insgesamt abgenommen.
