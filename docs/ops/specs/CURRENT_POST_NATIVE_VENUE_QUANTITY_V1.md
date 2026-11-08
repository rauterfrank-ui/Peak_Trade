---
docs_token: DOCS_TOKEN_CURRENT_POST_NATIVE_VENUE_QUANTITY_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle native Venuegrenzen am tatsächlichen POST-Consumer

Entwicklungsbasis: 42ba79cefaafd58e89c6a3288fd48d44e2acbb09. Der bestehende
N1-Planungsnachweis ersetzt keinen späteren Versandnachweis. Dieser Anschluss
vergleicht dieselbe unveränderte finale Ordermenge mit den bereits erneut
aufgenommenen öffentlichen und privaten Maximalmengen. Er erteilt keine eigene
Sendebefugnis und ist keine vollständige aktuelle Risiko-/Corezulassung.

## Ursprüngliche Konstruktion und belegte Lücke

Der [N1-Vertrag](../evidence/N1_FINAL_NATIVE_QUANTITY_LIMITS_2026_11_07.md)
prüft nach ursprünglichem Sizing und Planbildung native Maximalmengen. Seine
Account-/BoundInstrument-/Decision-/Cyclebezüge bleiben eigene ursprüngliche
Prädikate. Der spätere direkte Wrapper holt diese beiden Antwortgruppen erneut,
prüfte sie bisher aber nur auf ursprüngliche Aufnahme-/Identitätsbedingungen.
Zwei Gegenfälle am unveränderten Basiscode gelangen trotz aktueller maxBuy=0
oder maxMktSz=0 in den synthetischen HTTP-Aufruf.

Die gesonderte historische NEW_RISK-/Seal-/globale Claimlinie besitzt weitere
Zulassungsowner. Sie ist kein Ersatz für die hier vorhandenen privaten
maxBuy/maxSell-Antworten. Ihr Nichtvorhandensein wird weder durch einen neuen
positiven Default noch eine Rückkopie historischer Grants verdeckt.

Der [ursprüngliche Mengenconsumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_n1_venue_quantity_limit_admission_v1.py)
besitzt jetzt einen gemeinsam verwendeten Aufnahmehelper und genau einen
skalaren Vergleichskern. N1 behält seine eigenen Kontext-/Plan-/Wireprüfungen
und denselben N1_FINAL_PLAN_ONLY-Ausgang. Der spätere Consumer übergibt exakte
Envelopefelder an denselben Kern. Er baut keinen scheinbar ursprünglichen
Venueplan und keine neue Coreentscheidung aus dem Envelope zurück.

## Bedeutung, Einheit, Identität und Zeit

maxBuy/maxSell und maxMktSz/maxLmtSz behalten ihre ursprüngliche Mengenbedeutung:
native Kontraktmengen im abgefragten Instrument-/Account-/tdMode-/Preiskontext,
keine USDC-Margin, kein Notional und kein bestätigter Positionsbestand.
Die tatsächliche Orderseite buy/sell wählt maxBuy/maxSell. Market/Limit wählt
maxMktSz/maxLmtSz. Die unveränderte positive endliche Envelopequantity muss
kleiner oder gleich beiden passenden Maxima sein. Gleichheit ist zulässig.
Null ist ein gültiges Maximum, erlaubt aber keine positive Öffnungsmenge.

Beide privaten Seitenwerte müssen numerisch lesbar sein; der unbenutzte Wert
darf null sein. Fehlende, negative, nicht endliche oder falsch typisierte Werte
und nicht eindeutige Instrumentzeilen sperren. Limit verlangt denselben px-
Querywert wie das Originalenvelope. Market übernimmt keinen preisgebundenen
Limitbeleg. Native Instrumentkennung, öffentliche instType-Zeile, Endpointscope
und tdMode müssen passen. Native Kontrakte werden nicht still in Basiswährung
oder Kapital umgedeutet. Menge und Order bleiben unverändert; kein Clamp,
Resizing, Reranking oder neuer Finanzgrenzwert entsteht.

[CurrentPostVenueQuantityContextV1](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_post_venue_quantity_v1.py)
besitzt vier Felder:

- `envelope`: exakt das ursprüngliche finale Envelope mit unveränderten
  Identitäten, Seite, Menge, Einheit, Ordertyp und gegebenenfalls Limitpreis.
- `acquisition_decision_id`: die tatsächliche neue Aufnahme-ID des vorhandenen
  POST-Collectors. Sie wird weder zur alten N1-Decision-/Cycle-ID noch zur
  Budget-Attempt-ID oder Authoritygeneration umbenannt.
- `public_source` und `private_source`: die bestehenden eingefrorenen
  VenueQuantitySource-Träger der beiden Originalantworten. Sie erhalten Endpoint,
  acquired_at_utc, acquisition_decision_id, ursprünglichen Antwortbodyhash und
  abgetrennten kanonischen Payloadtext. Die Strings sind keine veränderlichen
  Referenzen auf ein später überschriebenes Antwortdict.

Ein Kontext ist ein Quellen-/Orderbezug ohne eigene numerische Einheit, Grant,
Attempt oder Writer. Der Capturepfad verlangt die ursprünglichen typisierten
GET-/DataSafety-Befunde. Hashes belegen lokale Inhaltsbindung, keine unabhängige
Quellensignatur. Der Kontext allein authentifiziert kein Konto. Der obere Pfad
behält dafür seine aktuelle Bindung an den ausdrücklich übergebenen Originalowner;
vollständige unabhängige Authority und aktuelle Zulassung des direkten unteren
Pfads bleiben eigene offene Verträge.

acquired_at_utc ist tatsächliche lokale Aufnahmezeit, nicht alter Plan-/Venueepoch
und nicht Signierzeit. Jeder spätere Consumer wertet dieselben Originalzeiten
mit der bestehenden acquisition_age_seconds-Policy erneut aus. Kein Consumer
erneuert sie oder erklärt einen alten N1-Befund zu einer neuen Aufnahme. Eine
frische Mengenbeobachtung erneuert die ursprüngliche Core-/Riskentscheidung nicht.
Es entsteht keine pauschale Planablauffrist.

## Durchgehende tatsächliche Verwendung

1. Der vorhandene Collector führt seine neun gemeinsamen GET-Gruppen aus; der
   vorhandene scoped Positionsread bleibt der zehnte Request. Keine zusätzlichen
   GETs, Wiederholungen oder Zählerrücksetzungen entstehen.
2. Die [ursprüngliche Pre-mutation-Prüfung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py)
   bindet dieselben aufgenommenen Mengenquellen und prüft die aktuelle
   Originalmenge vor POST-GO. Der Ergebnisstatus der GET-Aufnahme bleibt vom
   tatsächlichen numerischen Mengenurteil getrennt. Das bisherige kombinierte
   Übergabeprädikat verlangt zusätzlich venue_quantity_limits_admissible.
3. Der obere Wrapper übergibt exakt denselben Kontext an den unteren
   Einmalwrapper. Der untere tatsächliche Pfad verlangt ihn vor dem tatsächlichen
   Permitmint; fehlender Kontext ist kein positiver Default. Seine historischen
   Offline-Testaufrufe binden ausdrücklich frische synthetische Originalquellen.
4. Die [Sendenaht](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
   prüft den übergebenen Kontext vor der Originalbudgetmutation. Die generische
   Nichtnetzwerknaht bleibt ohne diesen optionalen Kontext nutzbar. Der tatsächliche
   HTTP-Pfad kann dadurch nicht ohne Quellen senden.
5. Vor K1, bei der ursprünglichen HTTP-/Claimbindung und nach Openerkonstruktion
   unmittelbar vor der Socketgrenze werden Originalmenge, Quellenscope und
   Aufnahmealter erneut geprüft. Auch der interne HTTP-Performpfad verlangt
   denselben typisierten Kontext und das exakte Safety-Envelope.
6. Ein tatsächlicher Mengen-/Altersfehler vor der gespeicherten Socketgrenze
   kann den offenen Originalclaim über den
   [vorhandenen negativen Transportabschluss](ORIGINAL_PERMIT_TRANSPORT_ABORT_AND_BUDGET_V1.md)
   schließen. Der zulässige Diagnosepräfix POST_QUANTITY ergänzt POST_SAFETY;
   die Writerphase bleibt der maßgebliche Beleg. Nach MAY_HAVE_SENT kann auch ein
   typisierter Mengenfehler keinen negativen Abschluss erzeugen. Holds werden
   weiterhin nur vom ursprünglichen Budgetreconciler mit seinen eigenen frischen
   Exchange-/Positions-/Pendingprüfungen freigegeben.
7. Die vorhandene POST-Quellintegritätsprüfung schützt zusätzlich den neuen
   Contextconsumer und den tatsächlich gemeinsam verwendeten ursprünglichen
   Mengenvergleich. Der gespeicherte Baselinepin bleibt unverändert.

Die erweiterten Scopebezeichnungen der Pre-mutation-Probe nennen jetzt ausdrücklich
Account/Position/Mengenanteil beziehungsweise Position/Mengenanteil. Sie bleiben
Teilmengen der vollständigen Zulassung; ein Feldname mit all_required ist keine
unabhängige Gesamtabnahme. Die Mengenassessment-Ausgabe erhält gewählte Felder,
Maxima, unveränderte Originalmenge und exakte Quellen-/Envelopebezüge.

## Verifikation und offene Grenzen

[Neue Originalconsumerfälle](../../../tests/ops/test_current_post_venue_quantity_v1.py)
prüfen echte obere Nullgrenzen vor GO, BUY/SELL und Market/Limit, Gleichheit und
Überschreitung, fehlerhafte/fehlende/fremde Quellen, fehlenden unteren Kontext,
öffentlichen und internen HTTP-Pfad und Alterswechsel nach GET/GO/Mint/Budget/
Permit/K1/Opener sowie typisierten Fehler nach möglichem Socket. Die unveränderten
N1-Fachfälle prüfen den gemeinsam verwendeten ursprünglichen Kern ebenfalls.

Die tatsächlichen GETs bleiben vor dem Versand liegende Beobachtungen. Ein
späterer Venuewechsel zwischen letzter Prüfung und Außenwirkung ist damit nicht
ausgeschlossen. Kaltes Öffnen erzeugt keinen neuen aktuellen Kontext aus einem
alten gespeicherten Ergebnis. Natürlicher erneuter Quellenbezug und Session-/GET-
Ressourcenowner bleiben gesondert zu integrieren.

Vollständige heutige Core-/Risk-/Altplan-/Kapital-/Pendingzulassung, zusätzliche
Lot-/Minimum-/Preisbandverträge und Reduktionsausnahmen werden durch passende
Maximalmengen nicht bewiesen. Unabhängige Sendemandate, signierte Recovery,
globale Root-/Anti-Clone-Herkunft, autonomer Host-POST, fünf natürliche Slots,
vollständige Lern-/Double-Play-Rückwirkung und physische Recovery bleiben offen.
