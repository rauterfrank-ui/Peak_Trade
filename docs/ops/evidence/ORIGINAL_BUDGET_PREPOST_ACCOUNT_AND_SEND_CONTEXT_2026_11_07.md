---
docs_token: DOCS_TOKEN_ORIGINAL_BUDGET_PREPOST_ACCOUNT_AND_SEND_CONTEXT_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Originalbudget, aktuelle Kontobindung und direkte Versandübergabe

Basis: 220b474b5ed4f408fc942ddf65dd74940ce014ef nach PR 7191.
Der [JSON-Nachweis](ORIGINAL_BUDGET_PREPOST_ACCOUNT_AND_SEND_CONTEXT_2026_11_07.json)
bindet den genauen Prüfstand, die ursprünglichen Quellen und verbliebene Grenzen.
QB02 erhält eine Kontobindung aus dem übergebenen Originalbudgetkontext;
QB03 erhält die Weitergabe desselben Kontexts durch die direkten Wrapper.
Die natürliche Hostzulieferung und vollständige Versandzulassung bleiben offen.

## Ursprüngliche Konstruktion und zeitliche Varianten

Der direkte Einmaljoin wurde mit 95f597823215533afc65197135fe17d4405e652a
zu PR 6747 am 22. September 2026 eingeführt. Er verbindet ein exaktes Envelope,
einen gesonderten POST-Owner-GO, einen einmaligen Permit, dessen dauerhaften
Verbrauch und den bestehenden K1-/HTTP-Transport. Er führt keinen Portfoliobudgetowner.

Die spätere originale Budget-/Executionbindung ist im lokal erreichbaren
Checkpoint 0808d2eed72edc9c4677f01da48cb5a8b11110dc vom 3. November 2026
erstmals nachweisbar. Der nächste belegte Stand 28f0115fbc69a3bd1e8f5ad87f5f45492cf8dc44
ergänzt die heutige Riskbindung. Ein Checkpoint belegt den enthaltenen Code;
er beweist weder den exakten früheren Entstehungszeitpunkt jeder Idee noch Betrieb.

Der heutige originale N1-Producer bindet das fertige Envelope bereits mit der
Reservations-ID beim dauerhaften Budgetowner. Die September-Wrapper reichen
diesen später eingeführten Kontext dagegen nicht weiter. Die vorhandene
Submitbarriere meldet deshalb HOST_PORTFOLIO_EXECUTION_CONTEXT_REQUIRED.
Das ist ein belegter Integrationsbruch; die Sperre wird nicht entfernt.
Die separat rekonstruierte historische Pflichtzulassungs-/Kill-/Recoverylinie
wird hier nicht kopiert oder aktiviert.

## Bedeutung und Zustandsowner

COMMITTED bezeichnet den weiterhin gehaltenen internen Kapitalhold.
PLAN_BOUND verbindet dessen ursprüngliche Sizing-/Risk-/Instrument-/Decision-
und Kontobindung mit genau diesem Envelope. Keiner dieser Zustände bestätigt
einen Submit, einen Fill oder eine Positionsänderung bei OKX.

Die typisierte Executionidentität trägt unter anderem kanonische Decision-ID,
kanonisches und natives Instrument, Konto, Richtung, native Kontraktmenge,
Ordertyp/-preis, Envelope und Clientorder-ID. Der Originalbudgetowner prüft
seine bereits vorhandenen Bindungsprädikate. Nicht jedes weitere nichtleere
Feld dieser Identität ist dadurch unabhängig autorisiert: Insbesondere werden
Opaque-Owner-GO-, Plan-, Attempt- und Consumption-Referenzen hier nicht zu
einem neuen authentifizierten Versandmandat erklärt.

Ein frischer Konto-GET und ein ursprünglicher Kapitalhold tragen verschiedene
Aussagen. Das erwartete Konto kommt aus dem vorhandenen, tatsächlich
übergebenen Budgetowner. Es wird weder aus einer alten Canary-UID noch aus
der gerade beobachteten UID als eigener Erwartungswert erfunden.

## Konkreter Producer-Consumer-Weg

1. Der [originale N1-Producer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
   reserviert und committet beim vorhandenen Owner und bindet sein originales
   finales Envelope einschließlich Reservationsreferenz. Dieser Producer und
   seine finanzielle Rechnung werden hier nicht geändert.
2. Der [Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
   bietet eine reine Kontextprüfung unter seinem bisherigen Lock an. Sie
   verwendet dieselben [ursprünglichen Submitprädikate](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py):
   dauerhafter verfügbarer Owner, COMMITTED, unverbrauchter PLAN_BOUND-Link,
   passende typisierte Executionidentität und exaktes gespeichertes Envelope.
   Die Prüfung schreibt keinen Zustand und erzeugt keinen zweiten Owner.
3. Der [obere direkte Wrapper](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py)
   nimmt Owner, Reservation und Executionidentität gemeinsam entgegen und
   prüft sie vor Storeanlage, Pre-Live-Permit und dauerhaftem GO-Verbrauch.
   Fehlender oder unpassender N1-Kontext bleibt eine konkrete Ablehnung.
4. Der [bestehende Vor-POST-Consumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py)
   verwendet seine unveränderten neun gemeinsamen GET-Gruppen und den zehnten
   scoped Positionsread. Er prüft den Originalowner nach diesen Aufnahmen
   nochmals. Die Erwartung aus dessen Konto, Envelope-Instrument und tdMode
   erreicht den vorhandenen LIVE_ACCOUNT_BOUND-Consumer. Die echte einzelne
   Config-UID muss zusätzlich ein nichtleerer exakter Text sein; fehlende,
   mehrfach vorhandene oder typfalsche Identitäten werden nicht normalisiert.
   Widersprüchliche Konten aus anderen gemeinsamen Antworten bleiben gesperrt.
5. Der positive Teilbeleg bindet die tatsächliche Configaufnahme, einen Digest
   des Originalowner-Scopes, Reservation, Envelopedigest und Executiondigest.
   Accountaufnahmefrische und Kontobindung bleiben getrennte Felder. Der
   Teilbeleg ist kein persistentes Sendeseal und keine neue Autorisierung.
6. Beide Wrapper reichen dieselbe Ownerinstanz, Reservations-ID und typisierte
   Executionidentität bis zur [vorhandenen Submitbarriere](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
   weiter. Der untere Join prüft vor seinem eigenen Permit erneut. Die
   ausdrücklich produktiven Wrapper und ihr Vor-POST-Consumer verlangen LIVE;
   ein Shadow-, Paper- oder Testnetkontext darf keinen produktiven POST tragen.
   Die generische Budget-/Sendeseam behält ihre getrennten Umgebungszweige.
7. Unmittelbar vor möglichem Transport validiert der Originalbudgetowner wieder
   unter Lock und persistiert SUBMIT_MAY_HAVE_OCCURRED. Danach folgt der
   ursprüngliche dauerhafte Permitverbrauch SENT_INITIATED. Beide Barrieren
   bleiben vor K1 und HTTP. Ein Crash zwischen ihnen bleibt ungewiss und
   erteilt keine Wiederholungsfreigabe.
8. Auch die vorhandene reine Wiederholungsprobe erhält den Reservationskontext,
   damit sie nach einem Attempt den tatsächlich verbrauchten Permit nachliest.
   Ein Timeout hält den Originalhold und die Executionidentität; ein zweiter
   Versuch bleibt gesperrt. Der spätere lose Positionsread des oberen Wrappers
   ist weiterhin keine vollständige Budget-/Order-/Fillreconciliation.

## Belegter Umfang und echte Grenzen

137 gezielte Fälle bestehen am final gebundenen Codestand. Darin liegen 48 neue
Fälle sowie bisherige Positions-, Wrapper-, einmalige Permit-/HTTP- und
Budget-/Execution-/Recoveryverträge. Die zwei N1-Proben führen die echten
Long-/Short-Producer und den vorhandenen Budgetwriter bis zum neuen
Accountconsumer aus. Ihre Executionidentität wird ausdrücklich vom Testcaller
synthetisch zugeliefert. Die natürliche Host-/Authorizationzulieferung dieses
Inputs wird dadurch nicht implementiert oder nachgewiesen.

Eine weitere Probe führt beide wirklichen Wrapper bis zu beiden Original-
Submitbarrieren und einem expliziten Fake-HTTP-Timeout. Der Callback sieht
vorher den persistierten Budgetlink und Permitverbrauch. Ein Wiederholungs-
versuch erreicht keinen zweiten HTTP-Callback; das Kapital bleibt gebunden.
Alle Stores sind temporär, K1/HTTP ausdrücklich Fakes, Socketverbindungen gesperrt.
Bestehende physische Prozessabbruchproben bleiben getrennt von Stromausfallsicherheit.

Drei Gegenproben mit den exakten drei Wrapper-/Frischemodulen des
Basiscommits zeigen: Der alte Vorconsumer kann ein fremdes Konto mangels
Originalkontextinput nicht binden und liefert trotzdem seinen begrenzten PASS;
der obere Wrapper erreicht ohne Originalbudgetkontext den verbotenen GO-Callback;
der untere mintet bereits einen In-Memory-Permit, bevor seine spätere Admission
ablehnt. Keine dieser Proben sendet oder schreibt einen echten GO-Verbrauch.
Das ist ein begrenzter Modulvergleich mit aktuellen Abhängigkeiten, kein Lauf
des gesamten historischen Baums.

Im ersten neuen Testlauf wurde ein bereits beschädigtes Envelope vor der
erwarteten Fehlerklasse korrekt gesperrt. Die Testprobe wurde auf ein gültig
neu gebundenes, aber fremdes Envelope korrigiert. Ein weiterer gemeinsamer
Lauf zeigte zwölf durch geteilten Prozesszustand verursachte Fixturefehler:
Die neue N1-Probe hinterließ eine neuere synthetische Kapitalaufnahme vor den
alten Recoveryfixtures. Die neuen Tests verwenden jetzt die vorhandene
temporäre PRE_EXTERNAL-Testisolation, ohne Workspace-Reseeding oder Änderung
des ursprünglichen Replayguards. Danach bestehen dieselben Recoveryfälle.

Die sieben bereits dokumentierten Collector-/Account-Closeout-Altverträge aus
dem vorigen Nachweis werden hier nicht als behoben erklärt. Ebenso bleiben
die frühere breite Abnahme und nicht geprüfte historische Dokumentprüfungen
an ihren damaligen Ständen offen.

Der Anschluss gilt, wenn der Caller den vorhandenen ursprünglichen Kontext
liefert. Die natürliche Host-Instanz-/Root-/Executionidentity-Zulieferung,
Pending-Order-Custody, erneute finale Mengen-/Risiko-/Safetyzulassung,
fortdauernde Gültigkeit des Altplans und das fortgesetzte Hostmandat bleiben
eigene offene Übergaben. Globale Eindeutigkeit kopierter Ownerstores wird
dadurch ebenfalls nicht bewiesen. Ein Legacy-Envelope ohne Reservationsmarker
und ohne Kontext behält NOT_ASSESSED; dieser ältere Zweig ist nicht plötzlich
vollständig kontogebunden.

Es gibt keinen neuen GET, keine Kapitalformel, keine Höchstmengenänderung und
keinen automatischen Release. Zusätzliche lokale Prüfungen verbrauchen
Rechenzeit; ihre reale Laufzeitwirkung und Latenz werden hier nicht gemessen.
Die unabhängige Marktpreisanzeige bei Nullposition aus PR 7191 bleibt unverändert.
