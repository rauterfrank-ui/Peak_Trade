---
docs_token: DOCS_TOKEN_ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Ursprüngliche Ordervorgaben am originalen Planwriter und späteren POST

Basis 76268b904ded8e1db02ed27950c8d7f46cca2f60 nach PR 7197.
Dieser Anschluss erhält die ursprüngliche deklarierte Ordersemantik. Er ist
keine erneuerte Coreentscheidung oder vollständige heutige Risiko-/Altplanzulassung.

## Originalkonstruktion und reproduzierte Lücke

Der [ursprüngliche Intentowner](../../../src/governance/canonical_order_intent_v1.py)
deklariert MARKET_ONLY und LIMIT_ONLY, EXPLICIT_NONE und EXPLICIT_PRICE sowie
getrennte Time-in-force- und Post-only-Vorgaben. Der
[ursprüngliche native Translator](../../../src/ops/full_core_live_path_composition_root_v1/venue_translation_v1.py)
überträgt den Ordertyp nach market beziehungsweise limit. Diese Körper sind
bereits am lokalen Source-Freeze c742a23c964901c1353fcf3468e618db9cb6ef42
vorhanden und bleiben bytegleich; eine früheste historische Entstehung wird
hierdurch nicht behauptet.

Der [originale Planwriter](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py)
speichert bereits Intent und Venueplan im selben bestehenden Executionlink.
Sein [Originalvalidator](../../../src/ops/portfolio_capital_reservation_budget_v1/plan_origin_v1.py)
prüft Entscheidung, Sizing, Quantity, Instrument, kanonischen Digest und den
exakten Envelope-/Wirekörper. Vor dieser Fortsetzung fehlte aber der Verbrauch
der deklarierten Order-/Preis-/Ausführungsvorgaben gegen den tatsächlichen Plan.
Ein selbstkonsistenter Digest einer widersprüchlichen Kombination genügte.

Zehn Gegenfälle am unveränderten Basiscode werden nicht abgewiesen: MARKET_ONLY
mit LIMIT-Plan, LIMIT_ONLY mit MARKET-Plan, unbekannter Ordertyp, abweichender
oder ungebundener LIMIT-Preis, Preisvorgabe bei MARKET sowie IOC, FOK, unbekannte
Time-in-force und POST_ONLY im gewöhnlichen Plan. Die bereits vorhandene
Gegenprobe für widersprüchliche Seite sperrt dagegen schon vorher. Beides bleibt
als datiertes Ergebnis erhalten; elf Gegenfälle bedeuten nicht elf neue Fehler.

## Bedeutung und native Umsetzung

Der ursprüngliche Intent bleibt vollständig im bestehenden Originalrecord.
Die neue Prüfung liest dessen vorhandene Ownerdeklarationen direkt:

- order_type_policy muss nach der ursprünglichen Ownerabbildung exakt zum
  tatsächlichen order_type im Venueplan passen. Unbekannt bleibt unzulässig.
- MARKET verlangt EXPLICIT_NONE und ein leeres Envelope-Preisfeld. Ein
  Preislimit wird weder erfunden noch stillschweigend entfernt.
- LIMIT verlangt EXPLICIT_PRICE mit einem endlichen positiven Dezimalwert.
  Dieser Wert muss numerisch exakt dem unveränderten nativen Envelopepreis
  entsprechen. Der schon bestehende Envelope-/Bodyvergleich bindet ihn zugleich
  an das tatsächliche px im ursprünglichen Venueplan.
- Die ursprünglichen Preisstrings und Wirefelder bleiben erhalten. Gleichwertige
  Dezimalschreibweisen dürfen passen; Rundung, Floatumwandlung und neue Preise
  entstehen nicht. Die Float-/Präzisionsgrenze des gesonderten strukturellen
  Offline-Adaptertransforms wird nicht zur Domain des nativen Planwriters.
- Der hier gebundene gewöhnliche market-/limit-Plan trägt keinen besonderen
  IOC-/FOK-/Post-only-Auftrag. Nur die ursprüngliche gtc-Abbildung besteht in
  dieser Oberfläche. IOC/FOK, unbekannte Time-in-force und POST_ONLY sperren;
  der Consumer ändert weder den Ordertyp noch baut er eine neue native Variante.
  GTC ist hier ein ursprünglicher Ausführungspolicybezug, kein Aufnahmezeitpunkt
  und keine neue Lebensdauer für den Handelsplan.

Das prüft deklarierte Order-/Preisidentität und die unterstützte Ausführungsform.
Eine numerische Slippagegrenze, Ausführungsqualität, künftiger MARKET-Fillpreis
oder die fachliche Aktualität der erklärten Policy werden damit nicht belegt.
Insbesondere ist ein korrekter Preisvertrag noch keine aktuelle Risikoentscheidung.

## Producer, Speicherung, Wiederaufnahme und tatsächlicher Consumer

Der unveränderte N1-Producer erzeugt seinen ursprünglichen Intent und Venueplan.
Die zusätzliche Prüfung läuft im vorhandenen Planvalidator vor dessen erstem
Originalwrite. Ablehnung verändert keinen Hold, keinen Executionlink und keine
Writersequenz. Es gibt keinen zweiten Writer, neuen Zustand, Schemawechsel oder
neues positives Zulassungsreceipt. Die ursprüngliche V1-/V2-Unterscheidung bleibt.

Derselbe Validator wird beim kalten Originalbudget-Readback, vor Submit und im
[aktuellen Originalbudgetreadback](CURRENT_POST_ORIGINAL_BUDGET_ADMISSION_V1.md)
wieder konsumiert. Ein nachträglich selbstkonsistent neu gehashter Widerspruch
wird auch dort abgewiesen. Alte widersprüchliche Records mit plan_origin werden
nicht automatisch migriert oder als noch passend umgedeutet; ihr Recovery bleibt
gesperrt. Der vollständig ungebundene Legacyweg ohne Ursprung erhält dadurch
keine neue Herkunft oder Zulassung und bleibt offen.

Die Actual-POST-Proben ändern ausschließlich einen temporären Originalrecord
vor GET, nach GET, während injizierter K1-Aufnahme oder bei Openerkonstruktion.
Die vorhandenen frühen und späten Ownerconsumer müssen dann stoppen, bevor ein
Socket erreicht wird. Der originale typed POST_BUDGET-Abbruch bleibt auf denselben
noch offenen PRE_SOCKET-Claim begrenzt. Vor Claimnahme entsteht kein negativer
Ersatzbeweis; nach MAY_HAVE_SENT bleiben mögliche Außenwirkung und Holds bestehen.
Der neue Anschluss führt keinen neuen Abort oder Kapitalrelease ein.

Die unveränderte deklarierende Intentdatei wird zusätzlich von der bestehenden
[Quellintegritätsoberfläche](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py)
geschützt. Lokale Inhaltstreue ist kein Beweis unabhängiger Authorityherkunft.

## Korrektur der synthetischen LIMIT-Probe

Der frühere [Preisbandanschluss](CURRENT_POST_ORIGINAL_PRICE_BAND_V1.md)
verwendete ausdrücklich einen synthetischen LIMIT-Plan bei unveränderten früheren
Sizing-/Intentreferenzen. Die bisherige Probe war an ihrem Stand erfolgreich;
sie belegte nicht, dass die Ordervorgaben des Intents mit diesem LIMIT-Plan
übereinstimmten. Der Testproducer trägt jetzt ausdrücklich LIMIT_ONLY und den
wirklichen EXPLICIT_PRICE:10.03 samt richtigem kanonischem Digest. Die vorherigen
Sizing-, Entscheidungs- und Instrumentreferenzen bleiben erhalten. Sämtliche
positiven, negativen und späten Preisbandprüfungen bleiben bestehen. Es wird
weiterhin keine natürliche N1-LIMIT-Erzeugung oder erneuerte Risikoprüfung behauptet.

## Verifikation und verbleibende Grenzen

[Originalconsumerfälle](../../../tests/ops/test_original_plan_order_policy_binding_v1.py)
prüfen Widersprüche trotz passendem Digest, endliche positive Preise, exakte hohe
Dezimalpräzision bei geringem Decimal-Kontext, unveränderte Wirestrings, kalten
Originalreadback und vier tatsächliche spätere POST-Grenzen. Der
[datierte Nachweis](../evidence/ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_2026_11_08.md)
bindet Ausgangsfehler, Korrektur und vollständiges finales Ergebnis an Quellenhashes.

Aktuelle Core-/Risk-/Altplan-/Kapitalzulassung, unabhängige Sendemandate,
signierte Recovery, vollständige Pending-Custody, globale Anti-Clone-Herkunft und
autonomer Host bleiben offen. Es entsteht keine pauschale creation_epoch-TTL,
kein Refresh, GET, Retry, Resizing oder operativer Safety-/Credentialzugriff.
S6 endet weiterhin PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False
bleiben. Breitere historische Acceptance-Fehler und zwei datierte ausgeschlossene
Dokumentverträge werden durch diesen Teilanschluss nicht geschlossen.
