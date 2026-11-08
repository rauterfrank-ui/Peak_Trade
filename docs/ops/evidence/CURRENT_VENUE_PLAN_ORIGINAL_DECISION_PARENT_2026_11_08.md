---
docs_token: DOCS_TOKEN_CURRENT_VENUE_PLAN_ORIGINAL_DECISION_PARENT_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Tatsächlicher Planbinder verbraucht den ursprünglichen Entscheidungsparent

Basis 9978959a6e5edffa6f6f332b15384e046d09d84f, bestehender Arbeitsbranch
fix/original-plan-order-semantics; kein neuer PR oder Betriebsstart.
[Semantik](../specs/CURRENT_VENUE_PLAN_ORIGINAL_DECISION_PARENT_V1.md) und
[JSON-Beleg](CURRENT_VENUE_PLAN_ORIGINAL_DECISION_PARENT_2026_11_08.json) binden
Originalkonstruktion, tatsächlichen Consumer, Ergebnisse und offene Grenzen.

13 Gegenfälle am unveränderten Basiscode liefern trotz fremdem Parent, Epoche,
Aktion, Referenz, Bindingmarker oder falschem Kind-/Parentdigest einen Plan.
Eine positive Originalprobe besteht. Der vorhandene Composer validiert nun
Originalparent, wirklichen Intent, Originalsizingskörper und deren tatsächliche
Links. Logische Epoche, Kompositionsbezug und spätere Envelopezeit bleiben
verschieden. BOUND_OFFLINE bleibt ein ursprünglicher Bindungsmarker und wird
nicht zur produktiven Core-/Risikoadmission umgedeutet.

Die erste Anschlussprüfung hat 92 PASS und einen alten Dokumentfehler. Die
32 erweiterten neuen Fälle bestehen. Sechs Fälle durch den tatsächlichen
N1-/Supervisorpfad prüfen beide Seiten und fremde Decision-ID, logische Epoche
oder entgegengesetzte Entryaktion. Es entsteht kein Originalplanwrite oder
Commit des Sendeplans. Der ursprüngliche Budgetowner verwendet seinen bestehenden
Plan-Failure-Release für den noch nicht gesendeten Hold. Die ursprünglichen
Close-/Positionsgrenzen bestehen zusätzlich mit 39 Fällen.

Der finale gebundene Lauf endet mit **1091 PASS, drei ausdrücklich deselected
historischen Dokumenttests, Exit 0**. Er umfasst die vorherigen 973 Originalowner-
Fälle, 32 neue Parentfälle, 47 funktionale Venueplanfälle und 39 Close-/Positionsfälle.
1896 Source-/Testkörper sind gebunden, darunter alle 1830 im Testprozess
tatsächlich geladenen Repo-Pythonmodule. Ein Hashinventar vor dem Lauf und der
Readback danach belegen unveränderte gebundene Quellen. Kommando, ausgeführte
Pytestargumente, Wrapper-/Runner-/Inventar- und Loghash stehen im JSON. Derselbe
abgeschlossene PASS wird für Dokumentation und Commit wiederverwendet.

**Gesondert offen:** Eine ältere Kompositionssuite hat weiterhin 25 FAIL und
11 PASS. Dieselben 25 fehlschlagenden Testadressen sind mit dem exakten Original-
Kompositionsowner der Basis reproduziert. Dazu kommt der alte unveränderte
Venueplan-Dokumenttest mit entferntem historischen Runbook-Header. Diese Prüfung
ersetzt deren Fehler nicht und zählt sie nicht als PASS. Die vollständigen
Testadressen, Originalsource-/Loghashes und Gegenüberstellung stehen im JSON.
Die zwei vorher ausgeschlossenen Dokumenttests, sieben älteren Collector-/Account-
Verträge und frühere breite Abnahmefehler bleiben ebenfalls offen.

Die Parentprüfung erfolgt an der tatsächlichen Planbildung. Eine fortdauernde
Zulassung gegenüber späteren Core-/Risk-/Marktänderungen ist damit nicht belegt.
Es wird kein zusätzlicher vollständiger Coreparent im Budget persistiert und
keine unabhängige Authority erfunden. Altplan-Re-Admission, Legacyherkunft,
signierte Recovery, vollständige Custody und autonomer Host bleiben offen.
S6 endet PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False bleiben.
Alle neuen Quellen/Writer sind injiziert oder temporär, Netzwerkports gesperrt.
Kein realer Safetyzustand, Credential, Venuekontakt, Dienst, Kapitalfluss oder
Aktivierungszustand wurde für diese Verifikation verändert.
