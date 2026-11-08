---
docs_token: DOCS_TOKEN_ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originale Ordervorgaben erreichen den ursprünglichen Plan- und POST-Consumer

Basis 76268b904ded8e1db02ed27950c8d7f46cca2f60 nach PR 7197. Arbeitsstand auf
fix/original-plan-order-semantics; kein neuer PR oder Betriebsstart.
[Semantik](../specs/ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_V1.md) und
[JSON-Beleg](ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_2026_11_08.json) binden
Originalkonstruktion, Gegenproben, Quellen und Verifikationsgrenzen.

Der originale Budgetwriter akzeptierte trotz passenden Digests Widersprüche
zwischen der ursprünglichen Ordervorgabe und dem gespeicherten nativen Plan.
Die erste Gegenprobe endet mit fünf fehlenden Ablehnungen und einem bereits
korrekt gesperrten Seitenwiderspruch. Die erweiterte Gegenprobe belegt zehn
fehlende Ablehnungen sowie dieselbe schon vorhandene Seitensperre.

Der vorhandene Originalvalidator verbraucht nun die bereits deklarierten
Ordertyp- und Preisvorgaben gegen Venueplan und Envelope. Nicht abgebildete
IOC-/FOK-/Post-only-Aufträge sperren. Exakte native Dezimalpreise und Wirestrings
bleiben unverändert; die Präzisionsgrenze des gesonderten strukturellen
Floatadapters wird nicht in den nativen Owner importiert. Der ursprüngliche
Intentowner bleibt bytegleich und wird am tatsächlichen POST quellengebunden.

Der vorhandene synthetische LIMIT-Testplan erhält ausdrücklich LIMIT_ONLY und
EXPLICIT_PRICE:10.03 samt richtigem kanonischem Digest. Seine bisherigen
Preisband-, Sizing-, Hold- und Unsicherheitsprüfungen bleiben bestehen; eine
natürliche N1-LIMIT-Erzeugung wird weiterhin nicht behauptet. Frühere PASS-Belege
bleiben an ihren damaligen Quellstand gebunden.

Die erste Anschlussprüfung besteht mit 126 Fällen. Die erweiterte neue
Fallgruppe besteht mit 31 Fällen. Der finale gemeinsame Ownerlauf belegt
**973 PASS, zwei ausdrücklich deselected historische Dokumenttests, Exit 0**
und 413 exakt gebundene Source-/Testkörper. Die neuen 31 Fälle prüfen
verlorene Vorgaben, ungültige Preise, exakte Dezimalwerte bei geringer
Kontextpräzision, kalte Originalwiederaufnahme und vier tatsächliche späte
POST-Grenzen. Der vollständige Befehl und alle Quell-/Loghashes stehen im JSON.
Derselbe abgeschlossene PASS wird für Dokumentation und Commit wiederverwendet.

Alte widersprüchliche Records mit gespeicherter Planherkunft werden beim
Originalreadback gesperrt und nicht automatisch migriert. Es gibt keinen neuen
Writer, State, Schematransfer, Permit, Release, Refresh oder GET. Vor einem
exklusiven PRE_SOCKET-Claim entsteht kein negativer Nachweis; nach MAY_HAVE_SENT
bleiben mögliche Außenwirkung und Holds erhalten. Der völlig ungebundene Legacy-
weg bleibt offen. Aktuelle Core-/Risk-/Altplan-/Kapitalzulassung, quantitative
Slippagewirkung, unabhängige Authority, signierte Recovery, vollständige Custody
und autonomer Host sind weiterhin nicht belegt. Keine pauschale Plan-TTL.

Die zwei historischen Dokumenttests, sieben ältere Collector-/Account-Verträge
und breitere Abnahmeschulden bleiben offen. Alle neuen Writer/Ports sind temporär
oder injiziert und die Actual-POST-Fälle socketsperrend. Keine echten Credentials,
operativer Safetyzustand, Venuekontakte, Dienste oder Kapitalbewegungen wurden
für diese Verifikation verwendet.
