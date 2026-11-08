---
docs_token: DOCS_TOKEN_CURRENT_POST_NATIVE_ORDER_CONSTRAINTS_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle native Orderbedingungen bis zur tatsächlichen HTTP-Grenze

Entwicklungsbasis: 0505217a99d93d1afbb0a096a7b2c69039613f31 nach PR 7196.
Dieser Rejectanschluss ergänzt den bestehenden
[aktuellen Maximalmengenconsumer](CURRENT_POST_NATIVE_VENUE_QUANTITY_V1.md).
Die unveränderte Order braucht passende aktuelle Venuebedingungen. Eine passende
Losgröße oder ein gültiger Preisstep erneuert keine Core-/Risikoentscheidung
und begründet keine eigenständige Sendeauthority.

## Ursprüngliche Konstruktion und belegte Lücke

Der originale [Sizingowner](../../../src/governance/capital_risk_sizing_v1.py)
berechnet native Menge, Losrundung und Mindestmenge vor der Planbildung.
Der [bestehende Kapitalguard-Metadatenadapter](../../../src/ops/full_core_live_path_composition_root_v1/full_core_pre_post_capital_guard_binding_v1.py)
bindet minSz und lotSz in seiner gesonderten Linie. Sein
[Guardconsumer](../../../src/ops/full_core_live_path_composition_root_v1/current_full_core_capital_guard_v1.py)
verwendet zusätzlich eine canarygebundene Planprojektion mit einem eigenen
Tickliteral. Diese gesonderte Projektion wird nicht als aktuelle Preisstepquelle
der heutigen Order übernommen.

Die historische Pflichtzulassung an 5d1c838c15369507c5247834db4dd0df25592169
bindet ihren eigenen Guard und ihre eigenen ratifizierten Caps. Die 14 zuvor
gesicherten Originalkörper sind erneut gegen ihr Quellenmanifest geprüft.
Diese Konstruktion definiert keine gemeinsame neue Ablaufzeit alter Corepläne.

Der spätere tatsächliche POST liest bereits aktuelle Instrumentmetadaten.
Sein bisheriger numerischer Consumer prüft daraus nur die Maximalmenge. Sieben
synthetische Gegenfälle an der unveränderten Entwicklungsbasis werden daher
nicht abgewiesen: Mindestmenge, Losgröße, Preisstep und suspendierter Zustand
am Kontext sowie Mindestmenge, Losgröße und Zustand am oberen Originalwrapper.
Die letzten drei Fälle erreichen den injizierten HTTP-Pfad trotz ungültiger
aktueller Bedingungen.

Die [aktuellen Venue-Felddefinitionen](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments)
trennen native Größen, Preisinkremente, Instrumentstatus und angekündigte
Parameteränderungen. Die vorhandene öffentliche Antwort wird an ihrem bestehenden
Consumer genauer ausgewertet; keine weitere Datenabfrage wird eingeführt.

## Bedeutung, Einheit, Identität und Zeit

Der vorhandene CurrentPostVenueQuantityContextV1 behält genau seine vier Felder:
Originalenvelope, ursprüngliche acquisition_decision_id sowie unveränderliche
öffentliche und private Originalantwortträger. Er bekommt keinen Writer, Grant,
neuen Timestamp oder Ersatzplan. Beide Quellen behalten Endpoint, tatsächliche
Aufnahmezeit, ursprünglichen Bodyhash und abgetrennten Payloadtext.

Der öffentliche Originalrecord muss weiterhin eindeutig zur nativen Kennung
und zum bestehenden SWAP-/FUTURES-Query passen. Zusätzlich gelten:

- `minSz`: positive endliche native Mindestkontraktmenge. Die unveränderte
  Envelopequantity muss mindestens so groß sein; Gleichheit ist zulässig.
- `lotSz`: positive endliche Schrittweite in nativen Kontrakten. Die unveränderte
  Menge muss ein exaktes ganzzahliges Vielfaches sein. Keine Rundung oder Korrektur
  des Orderwertes entsteht. Der Vergleich verwendet exakte Dezimalkoeffizienten,
  damit auch geringe Decimal-Kontextpräzision keinen Rest wegkürzt.
- `tickSz`: positive endliche Schrittweite des nativen Limitpreises in dessen
  Preiseinheit. Ein LIMIT-Preis muss exakt passen. Für MARKET existiert kein
  Limitpreis und dieser Vergleich wird als NOT_APPLICABLE_MARKET ausgewiesen.
- `state`: der ursprüngliche Instrumentstatus. Der vorhandene Consumer unterstützt
  gewöhnliche MARKET-/LIMIT-Entries und verlangt dafür live. Ein post_only- oder
  preopen-Zustand ist kein positives Signal für diese Orderarten.
- `upcChg`: die ausdrückliche Liste angekündigter Änderungen, leer wenn keine
  gemeldet ist. Jeder Record braucht param, newValue und effTime. Die derzeit
  benannten Parameter tickSz, minSz und maxMktSz werden identifiziert; unbekannte
  oder fehlerhafte Einträge sperren. effTime ist der originale Venue-Wirksamkeits-
  zeitpunkt in Unixmillisekunden, keine Capturezeit, Decision-ID oder neue TTL.
  Sobald der unveränderte Beleg eine bereits wirksam gewordene Änderung enthält,
  ist ein neuer Originalquellenbezug erforderlich. Der Consumer stoppt; er holt
  keine Daten selbst und wendet newValue nicht als Ersatzmetadata an.

Die vorhandenen maxBuy/maxSell- und maxMktSz/maxLmtSz-Vergleiche bleiben erhalten.
Mindest-/Maximalmenge, Kapitalnotional und Margin sind verschiedene Größen.
Ein Preisstep ist kein Preisband und kein unabhängiger Marktpreis.

## Producer, Übergabe und tatsächliche Consumerwirkung

Der vorhandene Pre-mutation-Collector liefert dieselben zehn GETs. Capture und
DataSafetyprüfung bleiben unverändert. Der aktuelle Mengen-/Orderkontext prüft
seine bestehenden Originalantworten zunächst vor POST-GO. Derselbe Kontext
erreicht den unteren Einmalwrapper vor Permitmint, die Sendenaht vor ursprünglicher
Budgetmutation und den Adapter vor K1. Öffentlicher sowie interner HTTP-Performpfad
prüfen erneut; die letzte Prüfung liegt nach Openerkonstruktion und vor der
ursprünglichen Socketgrenze.

An jeder Prüfstelle gilt dieselbe aktuelle Auswertungszeit für Aufnahmealter
und angekündigte Regelwirkung. Die Aufnahmezeit der Quelle und sämtliche
ursprünglichen Orderfelder bleiben erhalten. Aktuelle Metadata können daher
auch innerhalb des bisherigen zulässigen Aufnahmealters ungültig werden, wenn
eine bereits angekündigte Änderung wirksam wird. Es entsteht keine pauschale
neue Lebensdauer für einen alten Plan.

Der zusätzliche Readback unter order_constraints benennt Instrumentstatus,
native Mindestmenge, nativen Mengenstep, gegebenenfalls Limitpreisstep,
Originaländerungsliste und tatsächliche Auswertungszeit. Der Scope lautet
CURRENT_NATIVE_VENUE_ORDER_CONSTRAINTS_ONLY. Er ist keine Gesamtabnahme.

Ein frühes Veto verändert weder Budgetversuch noch Permit oder POST-GO.
Ein spätes typisiertes POST_QUANTITY-Veto darf denselben noch offenen PRE_SOCKET-
Claim nach dem bestehenden [Originaltransportvertrag](ORIGINAL_PERMIT_TRANSPORT_ABORT_AND_BUDGET_V1.md)
negativ schließen. Nach MAY_HAVE_SENT bleibt eine mögliche Außenwirkung ungewiss.
Die Kapitalfreigabe bleibt beim ursprünglichen Budgetreconciler mit dessen eigenen
frischen Exchange-, Positions- und Pendingprüfungen. Keine neue Transition oder
Rücksetzung eines verbrauchten Permits entsteht.

## Verifikation und verbleibende Grenzen

[Originalconsumerfälle](../../../tests/ops/test_current_post_native_order_constraints_v1.py)
prüfen gültige Grenzen für beide Seiten und Orderarten, unveränderte Wirewerte,
fehlende oder fehlerhafte Metadata, exakte hohe Dezimalpräzision, angekündigte
Regelwirkung und die ursprünglichen GO-/Mint-/Budget-/Permit-/K1-/HTTP-Grenzen.
Alle Writer sind temporär, die Ports injiziert und Sockets gesperrt.

N1s ursprüngliche Sizing- und Maximalmengenprüfungen bleiben eigenständig. Die
numerischen [entscheidungsgebundenen Risikomodelle](../../../src/risk/decision_bound_model_adapters_v1.py)
verlangen ausdrücklich EXPLICIT_OFFLINE_TEST_POLICY. Ihre vorhandene Offline-
RiskAdmissionBinding wird durch passende aktuelle Venuebedingungen nicht zu
produktiver Zulassung. Vollständige Core-/Risk-/Altplan-/Kapitalzulassung,
Preisbandverbrauch, unabhängige Sendemandate, globale Anti-Clone-Herkunft,
signierte Recovery und autonome Hostkomposition bleiben offen. Die letzte Race-
grenze zwischen Prüfung und Venuewirkung bleibt ebenfalls bestehen.

S6 endet weiterhin PRE_EXTERNAL_EFFECT. Fünf natürliche Slots, vollständige
Double-Play-/Lernrückwirkung und physische Wiederanlaufnachweise werden durch
diesen Anschluss nicht behauptet. Kein operativer Safetyzustand, Credential,
Venuezugriff oder Dienststart gehört zu dieser Verifikation.
