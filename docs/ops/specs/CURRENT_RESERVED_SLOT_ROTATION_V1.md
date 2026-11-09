---
docs_token: DOCS_TOKEN_CURRENT_RESERVED_SLOT_ROTATION_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Fester vorgemerkter Instrumentwechsel je Slot

Frank hat am 9. November 2026 die unmittelbare Umsetzung beauftragt: feste
Zuordnung von Slot, bisherigem Instrument und Ersatzkandidat, eine Wartefrist
ab Vormerkung, Aufhebung bei Erholung und Erhalt der ursprünglichen Handels-
und Wiederanlaufkette. Die zuletzt gewählte Frist ist **1.800 Sekunden**.
Diese Fortschreibung erzeugt keine Live-, Testnet-, Order- oder Kapitalfreigabe.
Die Freeze-Tags und ihre ursprünglichen Quellbestände bleiben erhalten.

## Ein laufender Vorgang

Der [Vormerkungsowner](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/rotation_plan_v1.py)
benutzt den bereits gehaltenen ursprünglichen Topologiewriter. Er speichert
genau einen laufenden Vorgang unter dessen Checkpointwurzel, mit atomarem
Schreiben, Readback-Digest und ursprünglicher Quellbindung. Eine eigene
Vorgangs-ID bindet Slot, bisheriges Instrument, Ersatzkandidat, Accountscope,
erste Ranking-/Auswahlnachweise sowie Beginn und Ende der Wartefrist.

Die Slotnummer ist eine Adresse, kein Rang. Bei der ersten Vormerkung wählt der
ursprüngliche [Membershipselector](../../../src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py)
anhand seines zugelassenen Rankings und seiner Beobachtungshysterese das
schwächere gehaltene Instrument. Die Vormerkung bindet dessen wirklichen Slot.
Danach bleiben beide Instrumente und dieser Slot fest. Ein später stärkerer
Kandidat oder ein mittlerweile schwächerer anderer Slot verschiebt den Vorgang
nicht. Es entsteht keine Warteschlange alter Kandidatensnapshots.

Der ursprüngliche Membershipowner erhält dafür einen ausdrücklichen Modus
für das reservierte Instrumentpaar. Seine Rangwerte werden weder neu berechnet
noch umsortiert. Der Modus und die beiden IDs sind Bestandteil der
Policyidentität des neuen Membershipartefakts. Die ursprüngliche Policy bleibt
für Aufrufe ohne diesen Zusatz lesbar und unverändert definiert.

## Wartefrist, Aufhebung und Close

Die 1.800 Sekunden beginnen bei der festen Vormerkung, nicht beim Entryfill,
bei der früheren Slotbelegung oder beim Neustart. Das bisherige Instrument
setzt seine normalen Double-Play-Zyklen während der Wartezeit fort. Ein neuer
Positionszyklus oder eine Metadatenfortschreibung desselben gebundenen
Instruments setzt die Vormerkung nicht zurück.

Die neue Rotationsprüfung verlangt ein vollständiges, instrument- und
universumsgebundenes Originalranking. Für diesen zusätzlichen Zweck darf es
höchstens ein ursprüngliches Ranking-Refreshintervall alt sein; am Bezugsstand
sind das 300 Sekunden. Das ist eine ausdrückliche neue Frischebedingung des
Rotationsvergleichs, keine Umdeutung der allgemeinen Cap23-24-Stunden-Grenze.
Zukünftige, regressive oder widersprüchlich wiederverwendete Snapshotidentitäten
werden abgewiesen. Wiederlesen ist keine neue Marktbeobachtung.

Wird das bisherige Instrument gegenüber **seinem reservierten Ersatz** wieder
mindestens gleich gut eingeordnet, wird die Vormerkung aufgehoben. Ein frisch
als unzulässig beobachteter Ersatz hebt sie ebenfalls auf. Fehlende oder alte
Daten sind kein Erholungsbeweis: Sie behalten die Vormerkung und erlauben keinen
neuen rotationsbedingten Close. Derselbe Snapshot eröffnet nach einer Aufhebung
nicht sofort einen weiteren Vorgang.

Nach Ablauf der Frist benötigt der Close weiterhin einen frischen positiven
Vergleich genau dieses Paars. Der [Quellenadapter](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_rotation_close_v1.py)
übergibt ihn an den bestehenden Exitproducer und die ursprüngliche
Double-Play-Exitpolicy. Der Zeitablauf allein ist im neuen N5-Kompositionspfad
kein Time-Exit. Die unveränderten ursprünglichen direkten Legacyaufrufe und
bereits verbindlich vorgemerkte ältere Exits behalten ihre eigenen Verträge.

Sobald der ursprüngliche Exitowner den Close dauerhaft vorgemerkt hat, wird
dieser Vorgang erhalten. Neue Rangbewegungen heben einen bereits begonnenen
Close oder einen unbekannten Ausführungsausgang nicht auf. Ein schon bestätigtes
Flat benötigt keinen zweiten Close; eine neue Entryzulassung des bisherigen
Instruments bleibt an einem fälligen Übergang gesperrt, bis dessen ursprüngliche
Flat-/Reconciliation-/Kapitalübergabe vorliegt.

## Fester Nachfolger und ursprüngliche Handelskette

Der Post-Close-Pfad prüft weiterhin Originalfill, Flat, Reconciliation und
Kapitalfortschreibung. Der neue Policyzusatz begrenzt die anschließende
Membershipentscheidung auf das reservierte Paar. Er berechtigt weder einen
anderen Slotwechsel noch ein Umhängen der vier übrigen Instrumente.
Andere normale Positionsabschlüsse dürfen während der Vormerkung ihren
bisherigen Instrumentkreis fortsetzen; sie starten keinen zweiten gewöhnlichen
Rotationsvorgang. Die vorhandenen Sicherheits- und Ausschlussregeln bleiben
eigene Bedingungen.

Der Ersatz durchläuft die ursprüngliche Instrument-/Datenzulassung und erhält
seinen eigenen aktuellen Marktkontext. Der Marktpreis stammt aus der gebundenen
Marktquelle. Der ursprüngliche zustandslose GGE berechnet daraus mit der
zugelassenen Volatilität seine Basisgeometrie; der ursprüngliche Scope-/L6-Pfad
verarbeitet seine Dynamic-Scope-Zustände. Danach greifen die ursprüngliche
Double-Play- und C3-Bestätigung. Zwei unterschiedliche zugelassene Beobachtungen
derselben Richtung sind erforderlich. Die vorherige Scope- oder Long-/Short-
Freigabe des ausgetauschten Instruments wird nicht übernommen. Finanzielle
Mengen-/Kostenadmission und Ausführungsrechte bleiben anschließende eigene Gates.

Der N5-Host verarbeitet im neuen Pfad bestehende Positionen vor neuen Entries,
jeweils stabil nach Slotnummer und weiterhin nacheinander. Ein Kandidat
unterbricht keinen laufenden Aufruf. Der GGE erhält keine neue globale
Instrumentauswahl- oder Versandautorität. Vormerkungsdaten sind kein Cache
einer später gültigen Handelsfreigabe.

## Wiederaufnahme und Abschluss des Vorgangs

Ein neuer Owner liest denselben Vorgang und dieselbe ursprüngliche Frist.
Eine unlesbare Rotationsdatei wird nicht als freie Vormerkung behandelt und
nicht still überschrieben. Der Controller meldet `UNREADABLE`, sperrt neue
Entries und gewöhnliche Wechsel und lässt weiterhin die ursprünglichen
Positions-/Risiko-/Exitpfade laufen. Deren eigene Quellen- und Speicherprüfungen
gelten weiterhin. Eine beschädigte Vormerkung wird nicht geraten.
Originale Slot-/Instrument-, Exit-, Budget- und Reconciliationzustände werden
weiter durch ihre bisherigen Owner gelesen. Die Vormerkung ersetzt deren
Wiederanlauf nicht. Terminale Vorgänge werden vor Freigabe des Index archiviert.

Nach dem neuen Binding bleibt der Vorgang auf `AWAITING_ENTRY`. Erst ein
erfolgreicher ursprünglicher Core-/Managementaufruf mit eigener bestätigter
Openingepisode und passender beobachteter Position schließt ihn ab. Ein
Planlabel, eine zweifache Bestätigung ohne Fill oder allein das neue Binding
schließt ihn nicht. Danach darf eine neue Prüfung am aktuellen Ranking beginnen.

Diese Fortschreibung gehört zur präzisierten Rotationssemantik innerhalb von
[BWP 1](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md). Sie schließt die noch
offene gesamte Kosten-/Funding-/Margin- und native Wirtschaftsrahmenzulassung
nicht. Lokale simulierte Verbundprüfungen sind kein Nachweis unbegrenzten
Livebetriebs oder eines physischen Stromausfalls.
