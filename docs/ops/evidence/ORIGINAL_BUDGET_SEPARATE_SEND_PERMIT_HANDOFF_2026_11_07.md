---
docs_token: DOCS_TOKEN_ORIGINAL_BUDGET_SEPARATE_SEND_PERMIT_HANDOFF_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Gesondertes Sendemandat am ursprünglichen Budgetübergang

Basis: 3ca65eee148a5aa215de0b1e8903731553a72f9f nach PR 7193.
Der [JSON-Nachweis](ORIGINAL_BUDGET_SEPARATE_SEND_PERMIT_HANDOFF_2026_11_07.json)
bindet die untersuchten Quellen und die vollständig beendeten Prüfungen.
Die natürliche Executionidentity-Zulieferung bleibt offen.

## Ursprüngliche Konstruktion und heutige Producer

Die gezielt gelesene historische Kapitalguardlinie aus PR 7092
(3a3f43a46bc6a2a95d4d106adcd212baac8cf2c4, 12. Oktober 2026) und der
Reconciliationbuilder aus PR 7093
(cccd5bbd3f7eb7e89722b8b8133740325ec03674, 13. Oktober) bilden einen eigenen
Vertrag. Diese Commits belegen enthaltene Fassungen, keinen natürlichen Betrieb.
Der ursprüngliche [Identity-Builder](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_integration_v1.py)
kopiert Kapitalguard-Owner-GO und dessen Consumption-Key aus der ausdrücklich
übergebenen FullCoreAuthorizationBindingV1. Planidentität, Attempt-ID,
Decisionoutcome und lokale Stateversion kommen zusätzlich vom Caller.

Der [alte Join](../../../src/ops/full_core_live_path_composition_root_v1/full_core_pre_post_capital_guard_join_v1.py)
deaktiviert LIVE_POST und lehnt LIVE ab. Sein Instrumentfeld stammt aus dem
nativen Envelope; der heutige Budgetconsumer erwartet dort dagegen die kanonische
BoundInstrument-Kennung. Weder die Instrumentfelder noch die Authorityrollen
dürfen durch Umbenennen passend gemacht werden.

Der gesonderte envelopegebundene Permitvertrag ist bereits in PR 6508
(114a68670bdd552fc1fcc90352a01b4dd7dc4dc5, 15. September) enthalten. Heute ruft der
[direkte Einmalwrapper](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py)
den ursprünglichen Permitproducer mit dem gesonderten POST-Owner-GO auf.
Das konkrete ExternalEffectPermitV1 bindet seine eigene ID und Authorityreferenz
an genau dieses Envelope. Es ersetzt die Kapitalguardautorisierung nicht.
Die andere [Versandzulassung](../../../src/governance/current_productive_real_venue_post_admission_v1.py)
und der dauerhafte POST-Owner-GO-Verbrauch bleiben zuständig.

## Quellen und Bedeutung der Identityfelder

- Decision-ID: ursprüngliche Replayevidence und dieselbe Budgetreservation.
  Der PendingDecisionContext wird erst nach S5 aus der tatsächlichen N1-Invocation
  übernommen. Er ist Beobachtungskontext, kein Versuch oder Sendemandat.
- Kanonisches Instrument: ursprüngliche BoundInstrument-Bindung. Native Kennung,
  Orderseite, native Kontraktmenge, Ordertyp, Preis und clOrdId: der ursprüngliche
  Venueplan und sein finales Envelope; Einheit CONTRACTS bleibt erhalten.
- Planreferenz: der Venueübersetzer erzeugt die clOrdId aus seinen ursprünglichen
  Aufrufinputs. Der alte Envelopedigest-Helper hat ein eigenes benanntes
  Digestschema. Beliebige Callerstrings sind kein Herkunftsnachweis.
- Account: der ursprüngliche Budgetowner und seine geprüfte Accountbindung.
  Ein Enveloperecord allein enthält keinen vollständigen Account-/Environmentvertrag.
- Owner-GO und Consumption-Key der alten Identity: Kapitalguardbinding und dessen
  eigener Stateowner. Sendemandat: tatsächliches gesondertes ExternalEffectPermitV1.
  Eine Gleichheitsprüfung beider Authorityfelder wäre keine fachliche Lösung.
- Attempt-ID und lokale Stateversion: explizite Inputs der bestehenden
  Lifecycle-Orchestrierungsrequest. Im untersuchten natürlichen N1-/S6-Rückweg ist
  dafür kein autorisierter produktiver Producer belegt. Permit-ID, Reservation,
  Cycle-ID oder Budgetsequenz werden deshalb nicht als Ersatz eingetragen.

## Konkrete Änderung und Consumerwirkung

1. Der unveränderte Permitproducer erzeugt sein konkretes envelopegebundenes
   Permit. Der [Sendeseam](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
   prüft dieses Permit wie bisher.
2. Bei vorhandenem Originalbudgetkontext übergibt er jetzt zusätzlich genau
   dieses Objekt an die bestehende Budget-Submitbarriere.
3. Der [ursprüngliche Budgetwriter](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py)
   prüft den typisierten Permitvertrag gegen das bereits gebundene Envelope und
   speichert dessen vollständige kanonische Felder samt permit_id als eigenes
   optionales Feld external_effect_permit im bestehenden Executionlink.
   Die Executionidentität bleibt unverändert. Ein zweiter Ledger entsteht nicht.
4. Der bestehende Originalstore persistiert dieses Feld gemeinsam mit
   SUBMIT_MAY_HAVE_OCCURRED. Erst danach folgt der bisherige dauerhafte
   Permitverbrauch SENT_INITIATED; erst danach sind K1 und Transport erreichbar.
5. Kaltlesen validiert ein vorhandenes Permit ohne Felddefaults gegen sein
   gespeichertes Envelope. Der Originalhost reconciliert weiterhin mit der
   ursprünglichen Identity und erhält das zusätzliche Permit bei seinem Writeback.

Die gespeicherte Permitkopie beweist weder den späteren dauerhaften Verbrauch
noch einen bestätigten Submit oder Fill. Ein Abbruch zwischen beiden Barrieren
behält den Hold und verlangt Reconciliation; er erlaubt keinen erneuten Versuch.
Lesen des Feldes erzeugt keine Versandfreigabe und keine aktuelle Risk-/Safetyzulassung.

Ältere Links ohne dieses Feld bleiben lesbar und erhalten keinen erfundenen Wert.
Die bisherige direkte Budget-API ohne Permit bleibt erhalten; nur der konkrete
Sendeseam liefert das tatsächliche Permit. Ältere Reader können erweiterte Links
wegen ihrer strikten Formprüfung ablehnen. Ein Rückwechsel darf deshalb keine
gespeicherten Felder entfernen oder Holds zurücksetzen.

## Prüfung und offene Grenzen

Die [15 neuen Fälle](../../../tests/ops/test_original_budget_send_permit_handoff_v1.py)
bestehen vollständig mit Exit 0 am gebundenen Stand. Sie verfolgen den tatsächlichen
direkten Wrapper und Sendeseam, beide Barrieren, Kaltlesen, beschädigte Daten,
Legacy ohne Ergänzung, Replay sowie den ursprünglichen Host-Reconciliationconsumer
für bestätigtes Cancel ohne Fill und für bestätigten Fill. Sämtliche Quellen sind
synthetisch, Stores temporär, HTTP/K1 injiziert und Sockets gesperrt.

Die zusätzliche gemeinsame Prüfung endet mit **177 PASS, einem FAIL, Exit 1**.
Der unveränderte ältere Test test_ssot_docs_once_present erwartet den schon an
der Basis fehlenden Atlas-Katalog und alte Runbookabschnitte. Sein erster Fehler
ist FileNotFoundError für den Atlas-Katalog. Er wird weder entfernt noch durch
den neuen Owner-PASS für erledigt erklärt. Die frühere Gleichheitshypothese für
die Authorityfelder wurde vor Produktänderung verworfen; ihre Diagnose ist kein
Nachweis einer unzulässigen tatsächlichen Order.

Offen bleiben natürliche Host-/Executionidentity-/Attemptzulieferung, eigenständige
Authorityherkunft, globale Root-/Owner-Eindeutigkeit, aktuelle vollständige
Risiko-/Mengen-/Safety-/Altplanzulassung, Pending-Custody, Never-submitted-Recovery,
Ressourcenvertrag und fortgesetzter Hostauftrag. Auch die sieben älteren
Collector-/Account-Closeout-Verträge und die frühere Gesamtabnahme bleiben offen.
S6 endet weiter an PRE_EXTERNAL_EFFECT; dieser Schritt aktiviert keinen Betrieb.
