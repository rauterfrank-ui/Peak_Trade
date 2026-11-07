---
docs_token: DOCS_TOKEN_PORTFOLIO_OWNED_EXECUTION_IDENTITY_V2_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Originale Planherkunft, Executionidentity und Budgetrevisionen

Arbeitsbasis: ad63a2dc5bc5823d98e42c3b0bd72026b04aeed2 nach PR 7194.
Der erste überprüfte Zwischencommit ist 7ecf6eef0e50f33aa792d01a1c892786ab6ae13e.
Die Arbeit bleibt auf demselben Branch; dieser Nachweis erzeugt keinen eigenen PR
und erklärt weder den gesamten Außenring noch alle QB03-Anschlüsse für abgeschlossen.

Der [JSON-Nachweis](PORTFOLIO_OWNED_EXECUTION_IDENTITY_V2_2026_11_07.json) bindet
den beendeten gemeinsamen Lauf: **469 PASS, Exit 0**, darunter 44 neue V2-Fälle
und die 31 zuvor hinzugefügten Herkunftsfälle. Die Quellen blieben während des
Laufs unverändert. Ein bereits vorher fehlschlagender alter Atlas-Dokumenttest
wurde ausdrücklich deselected und bleibt offen; er wird nicht als grün gezählt.

## Ursprüngliche Konstruktion und begründete Weiterentwicklung

Die [vorherige Herkunftsprüfung](N1_ORIGINAL_PLAN_ORIGIN_BINDING_2026_11_07.md)
belegt den tatsächlichen Verlust des vollständigen N1-Intents und Venueplans am
Originalbudget. Dieser Verlust ist behoben und mit Long/Short am Originalproducer
geprüft. Der neue Träger hat einen eigenen Namen und Digest. Die alte getrennte
Kapitalguardidentity liefert weiterhin keine natürliche heutige Plan-/Attempt-
Authority; ihre Callerfelder werden nicht umbenannt oder mit Defaults aufgefüllt.

Ein neuer Vertrag ist deshalb ausdrücklich als V2 implementiert. Die
[vollständige Feldsemantik](../specs/PORTFOLIO_OWNED_EXECUTION_IDENTITY_V2.md)
benennt Bedeutung, Einheit, Identität, Zeit/Generation, zulässige Wirkung,
Originalproducer und tatsächliche Consumer für Intent, Plan, Envelope,
Planreferenz, Executionidentity und Permit. Ursprüngliche Regeln und neue
Vertragsentscheidungen bleiben unterscheidbar.

## Belegte Kette

1. N1 speichert die Originale im vorhandenen PLAN_BOUND-Link. Seine reine typisierte
   Planreferenz erreicht unverändert S5, S6 und die echte Supervisor-Rückgabe. Sie
   enthält keinen Attempt und keine Authority. Fehlende Felder bleiben leer;
   ein späterer Cycle übernimmt keine frühere Referenz.
2. Der Supervisor schließt weiterhin seinen Owner. In beiden tatsächlichen
   Long-/Short-Tests öffnet die explizite synthetische Fortsetzung denselben Store
   und durchläuft dessen originale frische Recovery mit neuen Fakten und dem
   originalen Kapitalproducer. Kein privater Admitted-Schalter wird positiv gesetzt.
3. Beide direkten Originalwrapper erhalten nur diese Planreferenz mit dem
   Originalowner und der Reservation; keine callererfundene Legacyidentity ist nötig.
   Konto, LIVE-Umgebung und vorhandene zehn GETs behalten ihre bestehenden Prüfungen.
4. Erst beim ursprünglichen Budget-Submitübergang entsteht im selben Writer eine
   neue Attempt-ID. Sie bindet Originalintent, vollständige Planherkunft, Hold,
   Slot/Cycle und exaktes tatsächlich übergebenes Einmalpermit.
5. Benannte Quell- und Submitrevisionen beziehen sich auf echte Zeilen der
   ursprünglichen Budgethistorie. Die unmittelbar folgende Submitzeile muss genau
   diese Identität tragen und auf den ursprünglichen Parentdigest zeigen. Der
   Reader prüft diese tatsächlichen Zeilen, auch beim kalten Wiederöffnen.
6. Der bestehende Permitwriter speichert bei V2 dieselbe vollständige Identität.
   Beide Barrieren werden zurückgelesen, bevor Transport erreichbar wird. Ein
   ausgetauschter, selbstkonsistenter fremder Attempt in der Permitdatei wird
   abgewiesen. Der vorhandene K1-Adapter prüft die exakte Permit-ID vor Keylookup.
7. Die originale Budget-Reconciliation verwendet die versionierte Identität mit
   ihren ursprünglichen Instrument-/Konto-/Mengenconsumern. Eine bestätigte
   Stornierung ohne Fill erfüllt nur mit passender frischer Evidenz den bestehenden
   Releasevertrag. Offen/teilgefüllt/gefüllt/ungeklärt behält den Hold. Die
   ursprüngliche Attempt-ID und ihre Quell-/Submitrevision bleiben bei Writeback.

## Fehlergrenzen und Kompatibilität

Die neuen Fälle prüfen fehlenden Commit, verlorene Commitbestätigung, fehlerhaften
Readback, Fehler zwischen den Barrieren und Fehler nach dem Permitverbrauch. Sie
zeigen unveränderte Kapitalholds, Sperre weiterer lokaler Versuche und die
tatsächliche kalte Originalstore-Wahrheit. Zwei gleichzeitige Budgetversuche
erhalten genau einen Winner. Der vorhandene Permitwriter serialisiert seine
Read/Check/Replace-Sequenz mit einem exklusiven lokalen Dateilock; ein zweiter
Consumer kann den gewonnenen Datensatz nicht überschreiben.

Legacy-V1 bleibt eigenständig. Unbekannte Versionen, fehlende V2-Marker und
vervollständigte Mischformen werden abgewiesen. Bestehende Legacyprovider,
Reconciler, direkte Wrapper, Originalbudget- und Recoverytests sind im gemeinsamen
Lauf enthalten. Die separate alte Post-close-Lifecyclelinie bleibt bei ihrem
eigenen V1-Vertrag und wird nicht still auf V2 erweitert.

Eine neue Testannahme reichte zunächst zusätzlich die Budgetdimension an den
ursprünglichen Observationtyp weiter. Die zwei betroffenen Tests scheiterten daran;
die Testfakten wurden auf ihre tatsächlichen Konto-/Venue-/tdMode-Felder korrigiert.
Keine ursprüngliche Produktsperre wurde dafür abgeschwächt.

Alle neuen Ports sind synthetisch, Stores temporär und Sockets gesperrt. Es gab
keinen echten Schlüsselzugriff, Venuekontakt, Dienststart, Orderversand, Testnet-
oder Kapitalbetrieb und keinen physischen Ausfalltest. Lokales COMPLETED belegt
keinen Fill; Prozesskonkurrenz belegt keinen Hostcrash oder Stromausfall.

## Offen und nicht durch diesen PASS ersetzt

Die eigenständige Authorityherkunft sowie die vollständige heutige Safety-, Risk-,
Altplan-, Mengen- und Pendingzulassung bleiben eigene offene Anschlüsse.
Gleiches gilt für Session-/GET-Ressourcenbindung, belastbare Never-submitted-
Evidence, globale Root-/Owner-Eindeutigkeit und den fortgesetzten autonomen Host-
Sendemandatsweg. S6 stoppt weiterhin PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1
und HOST_JOIN=False bleiben unverändert.

Der bekannte `test_ssot_docs_once_present` erwartet einen bereits an der Basis
fehlenden alten Atlas-Census sowie obsolete Runbooküberschriften. Er bleibt offen,
ebenso sieben frühere Collector-/Account-Closeout-Fehler, frühere breite
Abnahmebefunde und der datierte Obsidian-Projektionscheck. Keine neue Dokument-
oder Identityprüfung ersetzt diese Verträge. Runbook A–H, fünf Slots, fortgesetztes
Double Play, Learning-Apply und natürlicher Gesamtbetrieb sind nicht abgenommen.
