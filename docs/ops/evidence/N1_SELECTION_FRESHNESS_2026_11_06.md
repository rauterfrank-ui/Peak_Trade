---
docs_token: DOCS_TOKEN_N1_SELECTION_FRESHNESS_2026_11_06
status: bounded_offline_verified
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
authority: NONE
runtime_authorization_effect: NONE
---

# N1-Auswahlfrische bei gehaltenem Instrument

## Problem und Ursache

Am Ausgangsstand fe0b1659fb5ea8cf5c353cfaebc9ffad1d3caf97 konnte eine
lange gehaltene Auswahl trotz neuem zulässigem Ranking abgelaufen bleiben.
Cap23 verwendete den ursprünglichen Instrumenteintritt zugleich als Basis
der Gültigkeitsfrist. Cap24 lehnte diese Auswahl korrekt als abgelaufen ab;
der nächste tatsächliche Coreaufruf wurde nicht erreicht.

## Änderung am zuständigen Owner

Die [Auswahlfunktion](../../../src/ops/single_selected_future_policy_v1/selection_v1.py)
erhält bei Retention den ursprünglichen selected_at_event_time und valid_from.
Die aktuelle Gültigkeitsfrist stützt sich auf ranking.event_time und den
unveränderten bestehenden Maximalwert aus Refresh und Mindesthaltezeit.
So verlängert eine frische zulässige Bewertung das Validitätsfenster, ohne
die Mindesthaltung erneut zu starten. Ein erneuter Blick auf dasselbe
Ranking kann die Frist nicht mit der Beobachtungsuhr verschieben.

Die Rankingvalidierung weist zusätzlich zukünftige Ereigniszeiten als
RANKING_SNAPSHOT_INVALID ab. Alte und korrupte Rankings bleiben gesperrt.
Ohne geeigneten Kandidaten erhält der bestehende Exit-only-Pfad keine neue
Zulassung. Es ändern sich keine numerischen Policydefaults, kein Ranking,
keine Positionsgrenze und keine finanzielle Menge.

Die Auswahlfunktion ist zugleich eine indizierte Policyquelle. Die
Policyprojektion führt ihre neue, exakte Entwicklungsbindung zusätzlich
zum bestehenden CI-Siegelmanifest ausdrücklich auf. Der eingefrorene
Policykatalog und seine Original-Gitobjekte bleiben unverändert. Falsche
Vorher-/Nachher-Hashes, ungebundene Bytes und die Änderung einer anderen
Policyquelle werden weiterhin abgewiesen.

## Producer, Persistenz und tatsächliche Wirkung

Der aktualisierte [N1-Anschlussfall](../../../tests/ops/test_productive_n1_post_close_continuation_v1.py)
prüft die originale gespeicherte Auswahl zunächst direkt am Cap24-Gate:
SELECTION_EXPIRED bleibt eine Ablehnung. Anschließend führt ein neuer
zulässiger Rankingreview über den ursprünglichen Cap23-Writer, Readback,
Publication, Cap24 und Budget-Recovery bis zum tatsächlichen S7/Coreaufruf.
Instrument und ursprünglicher Haltebeginn bleiben erhalten. Der bestätigte
Replay erzeugt keinen zweiten Consumeraufruf und verändert die gespeicherte
Auswahl nicht.

Die Mengen- und Kapitalevidence ist injizierter Testinput. Der Originalowner
verarbeitet den bestätigten Close; der Wert 75 ist kein beobachteter Gewinn.
Post und externe Wirkung bleiben im geprüften Fall gesperrt.

## Prüfungen und bestehender Testbefund

Die [neuen Ownerfälle](../../../tests/ops/test_single_selected_future_selection_freshness_v1.py)
prüfen Keep, Mindesthaltung, Hysterese, zukünftiges/altes/korruptes Ranking
und die feste Frist bei identischer Reobservation. Vor der Korrektur
scheiterten die fünf betroffenen neuen Unitfälle und der korrigierte
Integrationsfall an der bisherigen Frist beziehungsweise der fehlenden
Zukunftsablehnung. Ein anfänglicher falscher Testhelper-Aufruf wurde vor
dem kausalen Integrationsnachweis korrigiert.

Der vorhandene No-candidates-Test scheiterte auch mit der unveränderten
Auswahlfunktion des Ausgangsstands: Er benutzte einen inzwischen erlaubten
Bitcoin-Kandidaten als vermeintlich leere Auswahl. Der Test nutzt jetzt ein
wirklich suspendiertes Instrument; seine ursprünglichen Ablehnungsasserts
bleiben erhalten. Die Assetpolicy wurde nicht verändert.

Die vier Owner-/N1-/Cap24-Dateien bestehen zusammen mit 89 Fällen. Ruff
0.15.22 und die weiteren Integrationsprüfungen werden am finalen Kandidaten
gebunden; Einzelheiten und Quellhashes stehen im
[maschinenlesbaren Beleg](N1_SELECTION_FRESHNESS_2026_11_06.json).

## Reichweite und Grenzen

Geprüft ist ein begrenzter Offlinepfad mit Originalwritern und tatsächlichem
Coreconsumer unter injizierten Inputs. Bereits persistierte Receipts werden
nicht rückwirkend geändert. Eine automatische Migration alter fehlgeschlagener
Checkpoints, fehlendes Core-ACK, durchgängiger aktiver Scope-/SideState-Carry
über neue Bindungsgenerationen, natürlicher Dauerbetrieb, N5 und physischer
Stromausfall bleiben gesonderte Fragen.

Der bestehende Freeze, sein Katalog, Core-Siegel, Laufzeitzustand und die
zurückgestellte historische Link-/Krakenrecherche bleiben erhalten. Die
[N1-Spezifikation](../specs/PRODUCTIVE_N1_POST_CLOSE_CONTINUATION_V1.md)
beschreibt die unveränderten weiteren Anschlussgrenzen.
