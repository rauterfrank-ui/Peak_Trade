---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_BUDGET_ADMISSION_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originales Budgetveto erreicht die späte Versandgrenze

Basis c1802ac7c21444aa78cea67c06f487e778d14361, bestehender Branch
fix/current-post-native-order-constraints. Arbeitsstand ohne neuen PR oder
Betriebsaktivierung. [Semantik](../specs/CURRENT_POST_ORIGINAL_BUDGET_ADMISSION_V1.md)
und [JSON-Beleg](CURRENT_POST_ORIGINAL_BUDGET_ADMISSION_2026_11_08.json) trennen
ursprüngliche Konstruktion, tatsächliche Wirkung und verbleibende Grenzen.

Zwei synthetische Gegenfälle sperren den originalen dauerhaften V2-Budgetowner
während K1-Acquisition beziehungsweise Openerkonstruktion. Der unveränderte
Basiscode weist diese späten Sperren nicht ab und erreicht den injizierten
HTTP-Pfad. Der bereits vorhandene aktuelle Ownerreader war nur früher erreicht.

Der neue Kontext trägt denselben lebenden Originalowner, Reservation, exakte
V1-/V2-Identität, Originalenvelope, tatsächliches Permit und exklusiven Originalclaim.
Der originale gestartete Attemptreader bleibt der gemeinsame Validator. Die
Prüfung erfolgt vor K1, an beiden HTTP-Eintritten und nach Openerkonstruktion
vor dem Socket. V2 am direkten HTTP-Port kann diesen Ownerbezug nicht auslassen.
Eine vollständig ungebundene Legacyfläche bleibt ausdrücklich NOT_ASSESSED.

Die ersten 134 Anschluss-/Originalconsumerfälle bestehen. Die erweiterte
Grenzprobe enthält 45 PASS und einen Fehler in der neuen Testannahme: Sie
erwartete den oberen Wrapperfehler auch dort, wo der schon vorher vorhandene
V2-Reader vor Claimnahme mit seinem ursprünglichen ValueError sperrt. Der Test
erwartet jetzt für genau diesen früheren Pfad dessen vorhandenen Vertrag und
prüft den weiterhin ungewissen SENT_INITIATED-Zustand ohne erfundenen Claim.
Produktgate und Originalübergang werden dafür nicht geändert.

Der finale gemeinsame Lauf endet mit **942 PASS, Exit 0**, darunter 46 neue Fälle.
Er bindet die bisherigen 896 Fälle und die neuen Fälle an den exakten Quellstand.
Zwei bekannte historische Dokumentverträge bleiben
ausgeklammert und offen; sie zählen nicht als PASS. Das endgültige Ergebnis
und die Quell-/Loghashes stehen im JSON-Beleg. Ein identischer abgeschlossener
PASS wird für Dokumentation und Commit wiederverwendet.

Die neuen Fälle prüfen V1 und V2 ohne Umbenennung, aktuelle Recovery-/Closed-/
Storage-/Admission-Sperren, fehlende oder fremde Originalreferenzen und sämtliche
späten Grenzen. Ein offener PRE_SOCKET-Claim darf negativ geschlossen werden.
Vor Claimnahme gibt es diesen Nachweis noch nicht; nach MAY_HAVE_SENT bleibt
mögliche Außenwirkung bestehen. Holds bleiben am Originalbudget. Die zehn
Pre-mutation-GETs bleiben erhalten; der positive Timeout-Fall hat weiterhin den
ursprünglichen zusätzlichen Positionsread nach einem Versuch.

Die Untersuchung trennt zudem offene Owner: Das numerische Risikomodell verlangt
EXPLICIT_OFFLINE_TEST_POLICY, seine gespeicherte Nachrechnung ist historisch.
Der separate Full-Core-Kapitalguard besitzt eigene Offline-/Observe-Modi und
verbietet LIVE_POST. Weder dessen Konfiguration noch historische Seal-/Pilot-
Belege werden zu fremder aktueller Core-/Risikoauthority umgedeutet. Es entsteht
keine neue globale Plan-TTL. Vollständige aktuelle Fachzulassung, natürliche
Core-/Risk-Zulieferung, unabhängige Authority, signierte Recovery und autonomer
Host bleiben offen, ebenso die breitere historische Acceptance-Schuld.

Alle Writer sind temporär, GET-/K1-/HTTP-Ports injiziert und die neuen Actual-
POST-Fälle socketsperrend. Kein realer Schlüssel, operativer Safetyzustand,
Venuekontakt, Dienststart, Kapitalfluss oder physischer Ausfall gehört zu
dieser Verifikation.
