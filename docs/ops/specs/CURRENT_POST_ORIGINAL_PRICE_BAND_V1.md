---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_PRICE_BAND_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Originales aktuelles Preisband am tatsächlichen LIMIT-POST

Entwicklungsbasis: f2fd836a9a1d4ea01ff66fe275dcd650bf050194. Fortsetzung der
[nativen Orderbedingungen](CURRENT_POST_NATIVE_ORDER_CONSTRAINTS_V1.md) auf
demselben Arbeitsbranch. Dieser zusätzliche ablehnende Consumer ist keine
vollständige aktuelle Core-/Risiko-/Altplan-/Kapitalzulassung.

## Ursprung und tatsächliche Lücke

Der [ursprüngliche Canaryconsumer](../../../src/ops/section_11_13_5_live_canary_minimum_exposure_v1/price_band_consumer_v1.py)
vergleicht geplanten LIMIT-Preis und seitenspezifische Venuegrenze. Sein
[Quellenowner](../../../src/ops/section_11_13_5_live_canary_minimum_exposure_v1/price_band_observation_v1.py)
verlangt eine eigene entscheidungsgebundene, unsigned öffentliche Quelle und
seine eigene Canary-Instrumentbindung. Beide Körper liegen bereits in der
lokalen eingefrorenen Historie an 9397d04a37d527a8316b3e44ef4f80b4ef44db7a.
Das [datierte Originaldokument](PEAK_TRADE_PRICE_BAND_FORENSIC_BINDING_IMPLEMENTATION_AND_CLOSURE_V1.md)
beschreibt die Konstruktion vom August 2026; seine damaligen PROVEN-Aussagen
ersetzen keinen aktuellen Full-Core-Lauf. Die früheste historische Entstehung
ist durch diesen lokalen Pfadverlauf nicht belegt.

Die ursprüngliche skalare Regel bleibt erhalten und hat jetzt genau einen
gemeinsamen Helper: BUY verlangt Preis kleiner oder gleich buyLmt; SELL verlangt
Preis größer oder gleich sellLmt. Der bestehende Canaryconsumer ruft diesen
Helper nach seinen unveränderten eigenen Quellen- und Domainprüfungen auf.
Der aktuelle POST übernimmt nur den numerischen Vergleich. Er erzeugt keine
Canary-Beobachtung mit fremder Instrumentkennung oder erfundenen Originalfeldern.

Der vorhandene [Full-Core-Collector](../../../src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py)
liest PRICE_BAND bereits als öffentliche price_limit-Gruppe. Der spätere POST
wertete die Preisfelder bislang nicht aus. Vier Gegenfälle an unverändertem
Basiscode reproduzieren fehlende Ablehnungen für BUY-/SELL-Verletzung,
deaktiviertes Band und fehlenden Venuezeitstempel.

Die [First-Party-Felddefinition](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-limit-price)
benennt buyLmt als Kaufhöchstpreis, sellLmt als Verkaufsmindestpreis, enabled
als Wirksamkeit und ts als Venuezeitfeld in Unixmillisekunden. Prozentfelder
der Instrumentantwort sind keine berechneten aktuellen Preisgrenzen.

## Quellen-, Identitäts- und Zeitvertrag

CurrentPostVenueQuantityContextV1 behält seine vier bisherigen Felder und trägt
zusätzlich optional price_band_source. Dieser ursprüngliche VenueQuantitySourceV1
ist derselbe unveränderliche Antwortträgertyp: Endpoint, acquisition_decision_id,
acquired_at_utc, Originalantwortbodyhash und abgetrennter kanonischer Payloadtext.
Seine historische Typbezeichnung ändert die Preise nicht in Kontraktmengen um.
Für LIMIT ist der fünfte Träger zwingend; ein alter vierfeldriger LIMIT-Kontext
ohne Quelle sperrt. MARKET erhält keinen erfundenen Limitpreis und meldet
NOT_APPLICABLE_MARKET für diesen numerischen Preisvergleich.

Capture verwendet die bestehende PRICE_BAND-Itemdefinition und deren ursprüngliche
GET-/Status-/DataSafety-Prüfung. Ein LIMIT-Capture verlangt ausdrücklich
auth_header_sent=false für die öffentliche Quelle. Der spätere Consumer prüft:

- Exakten ursprünglichen Trägertyp und dieselbe neue Aufnahme-ID wie der
  aktuelle POST-Collector. Diese ID ersetzt keine alte Coredecision oder
  Budget-Attempt-/Authorityidentität.
- Ursprüngliches Aufnahmealter mit der bereits vorhandenen
  [acquisition_age_seconds-Policy](../../../src/ops/full_core_live_path_composition_root_v1/pretrade_acquisition_v1.py).
  Keine neue TTL, keine erneuerte Uhr und kein erfundener gemeinsamer
  Aufnahmezeitpunkt für nacheinander gelesene Antworten.
- Exakten öffentlichen price-limit-Pfad mit ausschließlich instId der
  Originalorder. Kein px-, tdMode-, Prozent- oder fremder Instrumentquery.
- Erfolgreichen ursprünglichen Antwortcode und genau eine passende Zeile;
  deren instType muss zur bereits gebundenen SWAP-/FUTURES-Instrumentquelle passen.
- Wirksames enabled nach ursprünglichem Normalizer. False oder unbekannt
  bedeutet keinen unbegrenzten positiven Ersatzwert.
- Ein positives originales ASCII-Unixmillisekundenfeld ts. Es wird roh erhalten.
  Daraus wird keine zusätzliche Alters- oder Zukunftsschwelle abgeleitet.
  Der historische PRICE_BAND_TS_AGE_BOUND bleibt UNBOUND; Aufnahmealter und
  Venuezeit sind verschiedene Aussagen.
- Beide originalen Preisstrings, ohne Float-/Booleanumdeutung oder Whitespace-
  Korrektur, danach den ursprünglichen endlichen nichtnegativen Preisparser.
  Seine bestehende Domainbegrenzung bleibt erhalten. Null wird nicht ersetzt:
  BUY mit positiver Order überschreitet buyLmt=0; sellLmt=0 bleibt eine echte
  untere Preisgrenze.

Die Auswahl des Seitengrenzwertes erzeugt kein beidseitiges Intervall.
Ein BUY unter sellLmt ist dadurch nicht verboten; ein SELL über buyLmt ebenfalls
nicht. Beide Werte müssen trotzdem nach dem ursprünglichen Quellenvertrag
lesbar sein. Native Limitpreise, Kontraktmenge, Margin und Notional bleiben
verschiedene Größen. Weder Tickausrichtung noch Mark, Index, Last, Bid/Ask oder
historische Testnet-51006-Werte werden zum Ersatz für das originale Preisband.

## Übergabe und beobachtete Wirkung

Der bestehende Capture übernimmt den Preisbandträger nur für LIMIT aus derselben
bereits vorhandenen GET-Gruppe. Der zusätzliche Quellenbezug reist im bisherigen
Kontext durch die vorhandenen Prüfstellen: vor GO, vor Permitmint, vor Budgetsubmit,
vor K1, an beiden HTTP-Eintritten und nach Openerkonstruktion vor dem Socket.
Jede Inspektion verwendet einen aktuellen Auswertungszeitpunkt für alle
Aufnahmealter; die einzelnen ursprünglichen Aufnahmezeiten bleiben erhalten.
Der Readback enthält ausgewählte Seite/Feld/Wert, unveränderten Limitpreis,
beide rohe Grenzen, ts, enabled und die ursprünglichen Quellenbezüge.

Die vorhandenen zehn Pre-mutation-GETs bleiben unverändert. Der bereits bestehende
zusätzliche Positionsread nach einem Versuch bleibt ein Positionssnapshot,
kein Fill-/Ordernachweis. Es gibt keinen versteckten Refresh, Retry oder neuen
Requestzähler. Die ursprüngliche POST-Quellintegrität schützt zusätzlich beide
originalen Preisbandowner; der gespeicherte Baselinepin bleibt unverändert.

Preisfehler werden als bestehendes typisiertes POST_QUANTITY-Veto übergeben.
Sie dürfen nur denselben noch offenen PRE_SOCKET-Claim nach dem
[Originaltransportvertrag](ORIGINAL_PERMIT_TRANSPORT_ABORT_AND_BUDGET_V1.md)
negativ schließen. Nach MAY_HAVE_SENT bleibt die Wirkung ungewiss. Holds und
Freigabe bleiben beim ursprünglichen Budgetreconciler; es entsteht keine neue
Rücksetz-, Permit- oder Kapitaltransition.

## Nachweis und Grenzen

Die [Originalconsumerfälle](../../../tests/ops/test_current_post_price_band_v1.py)
prüfen beide Seiten, Gleichheit und Überschreitung, fehlende/falsche Quellen,
DataSafety/unsigned GET, abgetrennte Payloads, originale Uhr-/Bodybezüge und
alle späteren ursprünglichen Transportgrenzen. Sechs Fälle prüfen zusätzlich
den ursprünglichen vollständigen Canary-Quellenconsumer nach Auslagerung seines
skalaren Vergleichs. Der [datierte Nachweis](../evidence/CURRENT_POST_ORIGINAL_PRICE_BAND_2026_11_08.md)
bindet Ergebnisse, Gegenprobe und offene Verträge.

Die tatsächlichen LIMIT-Transporttests verwenden einen ausdrücklich synthetischen
LIMIT-Plan, den der originale dauerhafte Planwriter mit seinen Originalchecks
annimmt. Sie behaupten nicht, dass der natürliche N1-Produzent LIMIT erzeugt
oder seine frühere Risikoprüfung erneuert. Der natürliche N1-Marketpfad bleibt
eigenständig; kein zukünftiger Market-Fillpreis oder dessen Ausführungsqualität
wird aus diesem LIMIT-Vergleich abgeleitet.

Lokale Inhalts-/Referenzbindung authentifiziert keine unabhängige Venuequelle
und erzeugt kein Sendemandat. Vollständige heutige Core-/Risiko-/Altplan-/Kapital-
zulassung, unabhängige Authority/Anti-Clone-Herkunft, signierte Recovery und
autonome Hostkomposition bleiben offen. Die Racegrenze zwischen letzter Prüfung
und Venuewirkung bleibt bestehen, ebenso die breiteren historischen Acceptance-
Schulden. S6 endet weiterhin PRE_EXTERNAL_EFFECT; fünf natürliche Slots,
vollständige Double-Play-/Lernrückwirkung und physische Wiederanlaufnachweise
werden nicht durch diesen Anschluss belegt.
