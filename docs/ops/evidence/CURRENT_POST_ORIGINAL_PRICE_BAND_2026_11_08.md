---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_PRICE_BAND_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originales aktuelles Preisband bis zur HTTP-Grenze

Basis f2fd836a9a1d4ea01ff66fe275dcd650bf050194, bestehender Branch
fix/current-post-native-order-constraints. Arbeitsstand ohne neuen PR oder
Betriebsaktivierung. Der [Semantikvertrag](../specs/CURRENT_POST_ORIGINAL_PRICE_BAND_V1.md)
beschreibt Ursprung, Einheiten, Quellen-/Identitäts-/Zeitbezüge und tatsächliche
Consumerwirkung. Der [JSON-Beleg](CURRENT_POST_ORIGINAL_PRICE_BAND_2026_11_08.json)
bindet Gegenprobe und abgeschlossenen gemeinsamen Ownerlauf an konkrete Körper.

Vier erwartete Ablehnungen fehlen am unveränderten Basiscode: BUY über buyLmt,
SELL unter sellLmt, enabled=false und fehlender Venuezeitstempel. Die bisherige
GET-Gruppe enthält die Quelle bereits; der aktuelle POST verbrauchte ihre
Preisfelder nicht. Die ursprüngliche skalare Seitengrenze besitzt nun einen
gemeinsamen Helper für den bestehenden Canaryconsumer und den aktuellen POST.
Die ursprünglichen Canary-Quellenprüfungen bleiben eigenständig.

Der bisherige aktuelle Kontext trägt zusätzlich einen abgetrennten ursprünglichen
Preisbandträger. LIMIT verlangt ihn; MARKET bekommt keinen erfundenen Limitpreis.
Capture bindet vorhandenes GET, ursprüngliche Aufnahme-ID/Uhr/Bodyhash, DataSafety
und unsigned Public-Status. Die späteren Consumer prüfen erneut Aufnahmealter,
exakten Query, eindeutiges Instrument, instType, enabled, rohe numerische Grenzen
und das ursprüngliche ts-Feld. Es entsteht keine neue Venuezeit-TTL und kein
Ersatzband aus Markpreis, Tick oder Prozentwerten. Die Order bleibt unverändert.

Final: **896 PASS, Exit 0**, darunter **84 neue Fälle**. Der gemeinsame Lauf
enthält die bisherigen 799 Ownerfälle, die 13 Originalfälle des geänderten
Fixturemoduls und die neuen Preisbandfälle. Sechs davon prüfen zusätzlich den
ursprünglichen vollständigen Canary-Quellenconsumer nach Auslagerung seines
skalaren Vergleichs. Alle gebundenen Quell-/Testkörper bleiben während des
Laufs unverändert. Zwei bekannte historische Dokumentverträge bleiben
ausdrücklich deselected und offen. Ein identischer abgeschlossener PASS wird
für Dokumentation und Commit anhand seiner Hashes wiederverwendet.

Die ersten 112 Anschlussfälle bestehen. Die erweiterte Grenzprobe enthält
78 PASS und fünf Fehler in der neuen Testzeitannahme: Eine 14 Sekunden alte
Preisbandaufnahme war schon vor der vorgesehenen späteren Grenze nach der
vorhandenen Fünfsekundenregel unzulässig. Der Test bindet seine positive
Ausgangsaufnahme jetzt an die bestehende NUMERIC_EQUITY_TTL_SECONDS-Konstante
und lässt ausschließlich diese Quelle später die vorhandene Grenze überschreiten.
Der Produktgrenzwert bleibt unverändert. Die anschließenden 83 Grenzfälle
bestehen; der finale 896er-Lauf enthält zusätzlich den neuen Integritätsfall
und die ergänzten Originaluhr-/Bodyhashassertionen.

Die tatsächlichen synthetischen LIMIT-Aufrufe prüfen vor GO, Mint, Budget, K1,
beiden HTTP-Eintritten und nach Openerkonstruktion. Die zehn Pre-mutation-GETs
bleiben erhalten. Der positive Timeout-Fall beobachtet zusätzlich den bestehenden
elften Positionsread nach einem Versuch; er ist kein Fillnachweis. Ein spätes
typisiertes Veto schließt nur den offenen ursprünglichen PRE_SOCKET-Claim.
Nach MAY_HAVE_SENT bleiben Außenwirkung ungewiss und Kapital gebunden.

Die LIMIT-Tests verwenden einen ausdrücklich synthetischen Plan mit originalen
Sizing-/Intentbezügen, den der originale dauerhafte Planwriter annimmt. Sie
behaupten keine natürliche LIMIT-Produktion des N1-Hosts und erneuern keine
historische Risikoentscheidung. Vollständige aktuelle Core-/Risiko-/Altplan-/
Kapitalzulassung, unabhängiges Sendemandat, Anti-Clone-Herkunft, signierte Recovery,
autonome Hostkomposition und die Racegrenze nach letzter Prüfung bleiben offen.
Die älteren zwei Dokumentverträge, sieben Collector-/Account-Closeout-Befunde
und die breitere Acceptance-Schuld werden durch diesen Lauf nicht geschlossen.

Alle Writer sind temporär und die GET-/K1-/HTTP-Ports injiziert. Sockets sind
in den neuen Actual-POST-Fällen gesperrt. Kein realer Schlüssel, operativer
Safetyzustand, Venuekontakt, Dienststart, Kapitalfluss oder physischer Ausfall
gehört zu dieser Verifikation.
