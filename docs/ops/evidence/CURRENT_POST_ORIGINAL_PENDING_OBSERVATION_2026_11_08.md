---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_PENDING_OBSERVATION_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originaler Pending- und Sessionbezug erreicht den tatsächlichen POST

Basis: 720b3cb40a30e3d1bec81bb95999dc2cc276991a. Bestehender Branch
fix/current-post-safety-veto-handoff, Arbeitscommit ohne neuen PR. Keine
Gesamtabnahme des Außenrings oder Betriebsaktivierung.

Der [Semantikvertrag](../specs/CURRENT_POST_ORIGINAL_PENDING_OBSERVATION_V1.md)
bindet ursprüngliche Konstruktion, Einheiten, Identitäts-/Zeitbezüge, Producer,
native Übergabe und tatsächliche Wirkung. Der [JSON-Nachweis](CURRENT_POST_ORIGINAL_PENDING_OBSERVATION_2026_11_08.json)
enthält Gegenprobe und beendeten exakt quellengebundenen gemeinsamen Ownerlauf.

Zwei tatsächliche synthetische Aufrufe erreichen am unveränderten Basiscode
HTTP trotz vollständig fehlender Pendingbeobachtung. Der bereits vorhandene
Accountsource kann kontoübergreifende SWAP-Pendings und vier unterstützte
Algoarten beobachten; dieser Originalnachweis erreichte den späteren Consumer
bisher nicht.

Der neue Anschluss erhält den abgeschlossenen Originalreadback samt realen
ursprünglichen Aufnahmefeldern und lebendem Sourcereferenzbezug. Er trägt ihn
von Originalcollector und nativer Hostrückgabe bis vor GO, Permit, Budget, K1
und beide tatsächlichen HTTP-Eintritte beziehungsweise die letzte Socketgrenze.
Ein Sourcewechsel, neues Lesen, neues Observe, Schließen oder fehlende/alte
Identitäts-/Zeitfelder sperren. Ein einfaches pending=false wird nicht akzeptiert.

Die beiden vorhandenen Profile bleiben getrennt: dediziertes Accountbeobachter-
Credential und ausdrücklich ausgewähltes K1-Read-Profil verwenden weiter ihre
ursprünglichen Credential-/Transportprädikate. Die neue Sourceklassenbindung
verwirft beliebige Caller-Subklassen. Erwartetes Konto stammt vom Originalowner
beziehungsweise ausdrücklich konfigurierten Beobachter, niemals aus dem gerade
gelesenen UID. Auch die frischen Pre-mutation-GETs müssen dazu passen.

40 neue Fälle und die bestehenden Source-/K1-, Budget-, N1-/V1-/V2-, Safety-,
Mengen-, Abort- und Positionsfälle sind im gemeinsamen Lauf enthalten. Ein
bestandener identischer Lauf wird nicht für Metadaten oder Commit wiederholt.
Final: **727 PASS, Exit 0**, darunter 40 neue Fälle und zusätzlich 69 bestehende
Source-/K1-Fälle. Zwei historische Dokumenttests bleiben deselected und zählen
nicht als PASS.

Die ersten 43 beziehungsweise 114 Anschluss-/Originalconsumerfälle bestehen.
Die erweiterte Grenzprobe enthält 76 PASS und eine fehlschlagende neue
Testannahme: Sie erwartete zehn GETs insgesamt am oberen Readport. Tatsächlich
führt der unveränderte Wrapper nach einem Versuch zusätzlich einen alten
Positionsread aus. Der Test prüft jetzt genau zehn Pre-mutation-Reads plus
diesen einen ursprünglichen Positionssnapshot. Er gibt ihn nicht als Order-/
Fillnachweis aus und verändert dafür keinen Collector oder Requestgrenzwert.

Der erste gemeinsame Lauf endet mit 724 PASS und drei Fehlern im neuen
Positiv-Helper: Er versuchte den Beobachter auch aus absichtlich fehlenden,
falschen oder rein speicherbasierten Testownern aufzubauen. Dadurch wurden die
ursprünglichen Negativconsumer nicht erreicht. Der Helper erzeugt diese
zusätzliche positive Testquelle jetzt nur für echte dauerhafte Testowner.
Originalgates und sämtliche erwarteten Ablehnungen bleiben unverändert;
der fehlgeschlagene Lauf bleibt getrennt vom finalen Nachweis erhalten.

Die bekannten zwei historischen Dokumenttests bleiben ausdrücklich ausgeklammert
und offen. Sieben ältere Collector-/Account-Closeout-Verträge, frühere breite
Befunde und der datierte alte Obsidian-Projektionscheck werden nicht geschlossen.

Die vorhandene Beobachterphase hat sechs Baselinereads plus vier Algoqueries;
die separate Pre-mutation-Phase behält zehn Reads. Ein erschöpftes gemeinsames
Requestbudget wird nicht zurückgesetzt oder erhöht. Keine Credentialsession
oder neue Beobachtung wird automatisch geöffnet.

Alle Writer sind temporär, alle GET-/K1-/HTTP-Ports injiziert, Sockets gesperrt.
Kein realer Schlüssel, Safetyzustand, Venuekontakt, Dienststart, Kapitalfluss
oder physischer Ausfall. Andere Produkte/Bot-/Algoangebote, vollständige
Pending-Custody und die Racegrenze nach letzter Prüfung bleiben außerhalb dieses
Belegs, ebenso vollständige aktuelle Fachzulassung und autonomer Host-POST.
