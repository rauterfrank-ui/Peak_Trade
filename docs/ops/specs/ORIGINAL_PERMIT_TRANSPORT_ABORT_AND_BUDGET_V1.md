---
docs_token: DOCS_TOKEN_ORIGINAL_PERMIT_TRANSPORT_ABORT_AND_BUDGET_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Originaler Transportabschluss und ursprünglicher Budgetconsumer

Entwicklungsbasis: b78406ae3bd40a27dd79cfabbf188a6375899c9c. Dieser Vertrag ergänzt
das [aktuelle Originalveto](CURRENT_POST_ORIGINAL_SAFETY_VETO_V1.md). Ein negativer
Transportabschluss erzeugt weder Senderecht noch einen Retry. Den Kapitalübergang
entscheidet weiterhin ausschließlich der ursprüngliche Budgetowner.

## Ursprung und belegte Lücke

Die vorhandene Exchange-Reconciliation unterscheidet NOT_SUBMITTED von
TRANSPORT_UNKNOWN. Ein leeres Order-/Fill-Ergebnis allein beweist kein Nichtabsenden.
Der ursprüngliche Budgetconsumer verwendete bislang immer TRANSPORT_UNKNOWN.
Der direkte Wrapper meldete einen tatsächlichen Vetostopp vor dem Socket zwar
lokal, hinterließ aber nur SENT_INITIATED im Originalpermitstore.

Die gesonderte historische Linie 5d1c838c15369507c5247834db4dd0df25592169 besaß
bereits ABORTED_BEFORE_TRANSPORT. Ihr Wrapper leitete den Übergang aus Fehlerpräfix
und lokalem HTTP-Zähler ab und band zusätzlich einen globalen Claimledger ein.
Diese historischen Originalkörper sind erneut gegen ihr gesichertes Manifest
geprüft. Sie werden weder unverändert zurückkopiert noch als heutige Installation
oder unabhängige Autorisierung ausgegeben.

Die jetzige Weiterentwicklung verwendet denselben vorhandenen Permitwriter. Vor
dem Transport entstehen ein exklusiver Versuch und eine vor dem möglichen Socket
dauerhaft zu schreibende Unsicherheitsgrenze. Nur der noch davor offene Versuch
kann negativ geschlossen werden. Ein Zählerstand null oder eine passende
Fehlerzeichenfolge ersetzt diesen Zustandsbeweis nicht.

## Bedeutung, Identität und Zeit

Der [Originalpermitstore](../../../src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py)
behält Permit-ID, Authorityreferenz, Originalenvelope und gegebenenfalls die exakte
ursprüngliche Portfolio-Executionidentität V2. Keine dieser Kennungen wird umbenannt.

- `transport_attempt.claim_id`: neue zufällige, innerhalb dieses Originalstores
  einmalig erworbene Transportreferenz. Sie ist weder die budgeteigene
  `submit_attempt_id` noch ein Permit oder eine globale Authority-ID. Sie hat keine
  numerische Einheit und erlaubt ausschließlich die Übergänge ihres eigenen
  bereits verbrauchten Originalpermitrecords.
- `PRE_SOCKET`: ein Transportaufruf hat den Originalrecord exklusiv übernommen;
  die persistente Grenze vor einem möglichen HTTP-Aufruf ist noch nicht geschrieben.
  Ein solcher Record nach einem Prozessabbruch bleibt ungewiss. Aus der fehlenden
  späteren Markierung wird kein negativer Abschluss abgeleitet.
- `MAY_HAVE_SENT`: unmittelbar vor Zähler und opener.open erfolgreich synchronisierte
  Unsicherheitsgrenze. Selbst ein anschließender Absturz vor dem wirklichen
  Socketaufruf bleibt ungewiss. Der Zustand ist kein bestätigter Submit oder Fill.
- `ABORTED`: derselbe noch offene PRE_SOCKET-Versuch ist endgültig geschlossen.
  Der umgebende Originalrecord trägt ABORTED_BEFORE_TRANSPORT und bleibt consumed;
  retry_allowed, resubmit_allowed und second_submit_allowed bleiben false.
- `claimed_at_utc`, `socket_boundary_at_utc`, `aborted_at_utc`: lokale UTC-Zeiten
  der jeweiligen Writerübergänge. Sie haben Zeiteinheit und Reihenfolge, sind aber
  keine Markt-/Entscheidungszeit, TTL, frische Fachzulassung oder neue Authoritygeneration.
  Zeitfelder müssen timezonegebunden und innerhalb eines Records geordnet sein.
- `reason_code`: Diagnose des tatsächlichen Originalvetos. Im natürlichen Pfad
  erzeugt der typisierte Safetyfehler den Abschluss; passender fremder Fehlertext
  allein erzeugt ihn nicht. Auch ein typisierter Fehler nach MAY_HAVE_SENT kann
  diese Grenze nicht zurücksetzen.
- `post_count=1` des bisherigen Permitrecords bleibt der belegte Verbrauch seines
  einen POST-Slots. Es ist nach einem Abbruch keine Behauptung eines tatsächlich
  geöffneten Sockets. `http.post_count` bleibt der gesonderte lokale Aufrufzähler.

Der ursprüngliche Budgetlink erhält optional `transport_store_root`. Dies ist der
aufgelöste absolute Pfad des tatsächlich übergebenen Sendestores, gespeichert in
derselben ursprünglichen V2-Submittransaktion. Die bestehende Rückprüfung der
Originalrevision verlangt denselben Wert. Ein später vom Caller ausgewählter
anderer Store oder ein geänderter aktueller Link ersetzt den Originalpfad nicht.
Ein Pfad ist weder globale Owneridentität noch kryptographisch authentifizierte
Herkunft. Das bestehende lokale Single-writer-/Verzeichnisvertrauen bleibt eine
ausdrückliche Grenze; Anti-Clone und unabhängige Authority sind nicht bewiesen.

## Tatsächliche Producer und Consumer

1. Die [ursprüngliche Sendenaht](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
   bindet den konkreten Sendepfad beim bestehenden V2-Budgetübergang. Danach
   folgen unverändert die beiden Originalbarrieren: Budget SUBMIT_MAY_HAVE_OCCURRED
   und Permit SENT_INITIATED.
2. Der [direkte Einmaltransport](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py)
   erwirbt unter dem ursprünglichen nicht blockierenden Writerlock genau einen
   Transportclaim. Ein zweiter Aufruf erhält weder denselben noch einen neuen
   offenen Claim; ein kalter Neustart übernimmt keinen verwaisten PRE_SOCKET-Claim.
3. Das tatsächliche Veto vor K1 schließt diesen Claim negativ. Für ein Veto im
   HTTP-Pfad erfolgt der Abschluss erst nach Verlassen des ursprünglichen K1-
   Kontextes. Unbekannte Ausnahmen und K1-Fehler werden nicht pauschal in einen
   Nie-gesendet-Beleg umgedeutet.
4. Der [HTTP-Consumer](../../../src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py)
   verlangt zusätzlich zum aktuellen Safetykontext den typisierten Originalclaim
   und dieselbe Permit-/Envelopeidentität. Auch der interne Performpfad prüft ihn.
   Nach dem letzten aktuellen Veto und vor dem HTTP-Zähler schreibt der originale
   Writer MAY_HAVE_SENT. Ohne erfolgreichen Write/Sync/Readback wird kein Socket
   geöffnet. Zwei konkurrierende Consumer können diese Grenze nicht beide gewinnen.
5. Der [ursprüngliche Budgetconsumer](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py)
   validiert weiterhin seinen gesamten Original-V2-Link einschließlich der
   tatsächlichen historischen Submitrevision. Nur am dort gebundenen Pfad liest
   er einen exakten ABORTED-Originalrecord samt derselben V2-Identität, separatem
   Permit und Envelope. Fehlende, unlesbare, alte oder widersprüchliche Records
   bleiben TRANSPORT_UNKNOWN. Der Legacy-V1-Pfad und V2-Links ohne Originalpfad
   erhalten keinen erfundenen positiven Fallback.
6. Ein gültiger negativer Originalrecord erreicht denselben bestehenden
   Exchange-Adjudicator als NOT_SUBMITTED plus belegtes Nichtabsenden. Seine
   bisherigen Identitäts-, Freshness-, Pagination-, History- und Fehlerprüfungen
   bleiben bestehen. Gegenläufige Order-/Fillevidence führt ausdrücklich zu
   LOCAL_NEVER_SUBMITTED_VENUE_CONTRADICTION und behält die Kapitalbindung.
7. Freigabe braucht weiterhin den ursprünglichen frischen Positionsread, passende
   Flat-Menge sowie frische, exakte und leere Pending-Custody. Erst der originale
   Budgetwriter persistiert dann RELEASED. Die bestehende interne Terminalreason
   RECONCILED_ENTRY_NO_FILL umfasst hier auch das bewiesene Nichtabsenden; der
   gespeicherte Entscheidungszustand unterscheidet ausdrücklich `never_submitted`.
   Budgetadmission bleibt ein eigener nachfolgender frischer Recoveryvertrag.

Die Reconciliation persistiert `local_submit_outcome` und `local_submit_evidence`
mit Originalrecord, dessen Digest und dem gebundenen Pfad innerhalb ihres bereits
vorhandenen Budgetrecords. Diese Felder sind Nachweis des konkreten Consumerlaufs,
keine neue Positivauthority oder dauerhafte Erlaubnis zur Wiederverwendung alter
Venuebeobachtungen. Der bestehende Host lädt weiterhin seine eigenen aktuellen
Beobachtungen; GET-Zähler und Ressourcenlimits werden nicht zurückgesetzt.

## Persistenz, Lücken und Prüfbereich

Alle neuen Übergänge verwenden den ursprünglichen Writerlock und denselben
Originalrecord. Die Datei wird temporär geschrieben, geflusht, synchronisiert,
ersetzt, ihr Verzeichnis synchronisiert und der Inhalt zurückgelesen. Auch die
bestehenden Initial-/Completed-Schreibwege verwenden diesen Writer. Ein Fehler
öffnet keinen Transport und gibt kein Permit zurück. Ein Record nach fehlendem
oder unbestätigtem negativen Write ist kein Nie-gesendet-Beleg.

Der natürliche Pfad bleibt nach erfolgreichem Abort dauerhaft für dasselbe Permit
gesperrt. Ein erneut ACTIVE gemeldeter Killzustand setzt den Claim nicht zurück.
Ein Crash vor dem Abortwrite, nach einer möglichen Socketgrenze oder in der Lücke
zwischen Budget und Permit erhält weiterhin den Hold. Die Tests belegen lokale
synthetische Fehler-/Wiederanlaufpfade und Readback; sie sind kein physischer
Stromausfall- oder Hostcrashnachweis, keine globale Quellenechtheit und kein
produktiver Dauerbetrieb.

[Originalconsumerfälle](../../../tests/ops/test_original_permit_transport_abort_v1.py)
prüfen negative Abschlüsse bei K1/Openerfactory, tatsächlichen Budgetanschluss,
kaltes Öffnen, wiederholte Hostbeobachtung mit ursprünglichem Recovery-Zaun,
fremde/fehlende Quellen, ungeklärte Crashlücken, konkurrierende Claims,
Sync-/Readbackfehler, widersprüchliche Venuebeobachtungen und mögliche HTTP-Wirkung
trotz späterem typisiertem Vetofehler. Alle Ports und Zustandswriter sind synthetisch.

Unabhängige Sendemandate, globale Root-/Owner-Eindeutigkeit, signierte Kill-Recovery,
vollständige aktuelle Fachzulassung, autonomer Host-POST, fünf natürliche Slots
und physische Wiederanlaufnachweise bleiben offen.
