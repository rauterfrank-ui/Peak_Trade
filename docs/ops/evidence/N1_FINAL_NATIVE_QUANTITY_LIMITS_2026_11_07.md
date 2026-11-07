---
docs_token: DOCS_TOKEN_N1_FINAL_NATIVE_QUANTITY_LIMITS_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# N1: originale Venuegrenzen am finalen Mengenconsumer

Basis ist d48a75b314d89f6a1e385e964b7356d00bb39ea4 nach PR 7189.
Der [JSON-Beleg](N1_FINAL_NATIVE_QUANTITY_LIMITS_2026_11_07.json) bindet
Quellen, Teststände und offene Grenzen. Dies ist die begrenzte Planungsreparatur
der Quellbindung QB01, keine abgeschlossene Versand- oder Wiederanlaufzulassung.

## Bedeutung und ursprüngliche Konstruktion

Die ursprüngliche Common-Epoch-Aufnahme holt bereits öffentliche
Instrumentmetadaten und private Account-Maximalmengen. Im Stand d48 werden die
Antworten auf erfolgreiche Aufnahme und Instrumentidentität geprüft. Die Zahlen
erreichen den finalen N1-Mengenconsumer jedoch nicht: Positive native Mengen
können dort trotz maxBuy/maxSell beziehungsweise maxMktSz gleich null einen
Plan ergeben. Ein erfolgreicher GET und ein zulässiger Zahlenwert sind
unterschiedliche Aussagen.

Laut [OKX-Vertrag](https://www.okx.com/docs-v5/en/) sind maxBuy und maxSell
für FUTURES/SWAP native Kontraktmengen der jeweiligen Orderseite im abgefragten
Kontokontext. Sie sind weder USDC-Margin noch Nominalwert noch ein bestätigter
Positionsbestand. maxMktSz und maxLmtSz begrenzen die einzelne Order des
jeweiligen Typs in derselben nativen Einheit. LONG-Entry kauft, SHORT-Entry
verkauft; diese Prüfung verwendet den tatsächlichen Plan side=buy/sell.
Limitpreis und tdMode gehören zum abgefragten Kontext. Eine erfolgreiche
Mengenprüfung ersetzt keine Risiko-, Kapital-, Slot- oder Sendeberechtigung.

Die ursprüngliche Budgetseam berechnet und reserviert zuerst die kanonische
Menge beziehungsweise deren resulting_notional. Danach bindet der ursprüngliche
Venueplan die native Menge. Die neue Prüfung folgt diesem Plan, vor dem internen
Commit und dem finalen Envelope. Sie führt weder eine zweite Sizingformel noch
einen stillen Clamp oder ein erneutes Entscheidungsverfahren ein.

## Kausale Kette und tatsächliche Consumerwirkung

1. Der originale Collector fordert seine bisherigen neun Fetchgruppen für
   denselben ursprünglichen S5-Cycle und Decision-Epoch an. Kein zusätzlicher
   Request, Cachezugriff oder nachträgliches Auffrischen erfolgt hier.
2. Der Common-Epoch-Handoff trennt Kopien der beiden originalen Antworten ab.
   Er trägt die vorhandene Accountidentität, den vollständigen BoundInstrument,
   Cycle, Epoch, Aufnahme-ID und ursprüngliche Aufnahmezeiten weiter.
3. Originaler 29P-/Budgetowner und Venueplan bestimmen die Menge unverändert.
4. Der neue Consumer verlangt exakte Owner-/Generations-/Cycle-Bindung und
   prüft die ursprüngliche Aufnahmealter-Policy erneut. Öffentlicher instType,
   native ID und privater tdMode müssen passen. Limit verlangt dieselbe px;
   Market darf keinen preisgebundenen Limitbeleg übernehmen. Genau eine passende
   Antwortzeile ist erforderlich. Beide privaten Seitenwerte müssen lesbar sein;
   nur die tatsächliche Seite wird mit der Menge verglichen. Die unbenutzte
   Seite darf null sein. Öffentlich wird nur das passende Ordertyp-Limit gewählt.
5. Die unveränderte positive native Menge muss kleiner oder gleich beiden
   passenden Maxima sein. Fehlend, negativ, nicht endlich, fremd, widersprüchlich
   oder abgelaufen bedeutet Ablehnung. Null ist eine gültige Höchstmenge,
   erlaubt aber keine positive Öffnungsmenge.
6. Bei Ablehnung erzeugt dieser Pfad kein finales Envelope. Der ursprüngliche
   Budgetowner gibt seinen noch nicht gesendeten Hold mit
   SIZING_OR_ADMISSION_DENY frei. Fehlgeschlagene eigentliche Planbildung behält
   ihren bisherigen PLAN_FAILURE-Pfad. Die allgemeine Releaseimplementierung
   sowie Kapitalalgebra werden nicht geändert.
   S5 meldet diesen Fall als VENUE_QUANTITY_ADMISSION_DENIED mit der
   ursprünglichen Reservation-ID, nicht als fehlenden Marktzustand. Die Core-
   Entscheidung bleibt erhalten. Eine neue reguläre Aufnahme/Entscheidung muss
   ihre eigenen Quellen, Sizing- und Reservationsbindungen erzeugen.
7. Bei Erfolg folgt der ursprüngliche interne Commit-/Envelopepfad. Der
   bestehende S5-Ledgerwriter und die vorhandenen Extras halten das Prüfergebnis
   inklusive Quellen-/Planbindung fest. Der Beleg heißt ausdrücklich
   N1_FINAL_PLAN_ONLY und besitzt RUNTIME_AUTHORIZATION_EFFECT=NONE.

Die Hashes zeigen lokale Inhalts-/Kontextbindung, keine externe Signatur oder
unabhängige Kontoauthentifizierung. Der originale produktive Handoff bleibt
Owner seiner Transport-/Accountvalidierung. Testlabels ersetzen keinen echten
Venuekontakt. Der bestehende S5-Writer wird durch dieses Zusatzfeld nicht zu
einem neuen atomaren oder stromausfallsicheren Autorisierungsjournal.

## Historische Sicherheitsvariante: getrennte Verträge

Gezielte lesende Git-Rekonstruktion auf M2DATA findet eine weitere Linie:
PR 7103 führte eine verpflichtende NEW_RISK-Zulassung und ein ordergebundenes
Seal vor dem Permit ein. PR 7118 ergänzte Lifecycle-Root-Bindungen; PR 7138
einen globalen Einmalanspruch, ein spätes Kill-Gate und technischen
Risk-Reduction-Nachweis; PR 7139 eine signierte Recovery-Attestation.
Die genaue untersuchte spätere Revision ist
5d1c838c15369507c5247834db4dd0df25592169. Die einzelnen Einführungsrevisionen
und Quellhashes sind im JSON-Beleg festgehalten.

Diese Pflichtbausteine fehlen bereits im aktiven Vor-Freeze-Stand
78014602eb55c47e39e003f22094691b62c77039 und im früher sichtbaren
a8e1c0088e25651ad4bb29ebe02e10142a0a92b2. Der gemeinsame Vorfahr mit der
7103-Linie ist 3a3f43a46bc6a2a95d4d106adcd212baac8cf2c4. Damit ist eine
abweichende Entwicklungslinie belegt, keine durch diese Untersuchung bewiesene
versehentliche Löschung bei der späteren Bereinigung. Ein jetziger grüner
Quellintegritätsvergleich belegt nicht das Vorhandensein dieser alten Verträge.

Ihre Semantik ist entscheidend: Der historische globale Anspruch erlaubt nur
einen Effekt je Owner-GO/Baseline-Pin/Konto/Umgebung. Das ist kein fortlaufendes
Double-Play-Mandat. Ein Hold, ordergebundenes Seal, Permit, Transportbeginn,
HTTP-Antwort, Fill und bestätigte Position bleiben verschiedene Zustände.
Der alte nachgelagerte DW-Status PASS kann einen noch ungeklärten
Reconciliation-Ausgang enthalten. Ein Label reduce_only beweist keine tatsächliche
Risikoreduktion; der alte Nachweis prüft frische Position/Pending/Accountfacts.

Die ursprüngliche Nichtgesendet-Prädikatsprobe erlaubt nur den eigenen
CLAIMED-Erstzustand, denselben Host und bekannten Boot sowie nachgewiesen toten
Originalprozess ohne lebendes Versuchstoken. Nach Bootwechsel oder unbekanntem
Ausgang bleibt die Authority gesperrt. Ein lokales ABORTED_BEFORE_TRANSPORT
kann weiterhin einen verbrauchten Permit bedeuten. Frische Daten allein heben
keinen absichtlichen Kill auf. Unabhängiger Recovery-Journal-Rollbackschutz
ist durch die untersuchte historische Konstruktion nicht belegt.

Keine dieser historischen Implementierungen wurde importiert oder aktiviert.
Die alte Pilot-GET-Kette fragt die privaten maxBuy/maxSell nicht ab und löst
diese Mengenlücke deshalb nicht. Alte Einheiten, Caps und TTLs werden nicht
auf die heutige Architektur übertragen.

## Prüfung und verbleibende Grenzen

Vor der Änderung schlagen fünf der neun neuen tatsächlichen N1-Integrationsfälle
fehl, weil die Originalkette trotz ungültiger Grenzen einen Plan erzeugt.
Die Gegenprobe nutzt synthetische Originalports; alle Socketverbindungen sind
gesperrt. Die reparierte Kette überprüft LONG BUY=1 und SHORT SELL=3 unverändert,
Ablehnung sowie ursprünglichen Releasezustand und vorhandenen Ledgerreadback.

201 final gebundene Owner-/Integrationsfälle bestehen: neun tatsächliche
Supervisor→Core→29P→Plan→Reservation-Integrationen, 60 Vertragsfälle und 13
betroffene Pre-External-Fixturefälle sowie die vorhandenen N1-, Close-/Fortsetzungs-,
S5- und 37 WP03-/Liveness-/WP04-Fälle. Drei zunächst fehlgeschlagene Positivfälle hatten keine expliziten
Maximalmengen in ihren synthetischen Eingaben; eine begrenzte Gegenprobe mit
den vier exakten Originalproduktmodulen besteht mit 30 Fällen. Die positive
Fixture enthält nun ausreichende native Maxima. Keine Negativassertion wird
gelockert. Frühere 80er-, 82er- und 37er-Prüfstände sind getrennt dokumentiert.
Nach der anschließenden semantischen S5-Statuskorrektur bindet der einmalige
201er-Lauf den finalen Stand einschließlich dieser abhängigen Consumer.

Weiter offen bleiben frische Zulassung unmittelbar vor einem späteren POST,
persistenter Wiederanlauf und vollständige Authority-/Kill-/Recovery-Verkettung.
Reduce-only/Close besitzt seinen eigenen Positions- und Releaseowner; dieser
Öffnungsmengenconsumer ist dafür kein Ersatz. Eine gespeicherte PASS-Beurteilung
darf später nicht als erneuerte Maximalmenge oder Versandrecht verwendet werden.
Die früher dokumentierten breiteren Alt-/Setupfehler und die anderen offenen
Quellbindungen sind hier nicht pauschal geschlossen. Es gibt keinen Beleg für
vollständige Betriebsbereitschaft, echten Venuekontakt oder bestätigte Fills.
