---
docs_token: DOCS_TOKEN_CURRENT_POST_NATIVE_ORDER_CONSTRAINTS_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle native Orderbedingungen: belegter Arbeitsstand

Basis: 0505217a99d93d1afbb0a096a7b2c69039613f31 nach PR 7196. Branch
fix/current-post-native-order-constraints. Arbeitsstand ohne neuen PR oder
Betriebsaktivierung. Der [Semantikvertrag](../specs/CURRENT_POST_NATIVE_ORDER_CONSTRAINTS_V1.md)
erklärt Originalkonstruktion, Einheiten, Quellen-/Zeit-/Identitätsbezüge und
tatsächliche Consumerwirkung. Der [JSON-Nachweis](CURRENT_POST_NATIVE_ORDER_CONSTRAINTS_2026_11_08.json)
bindet den abgeschlossenen Prüflauf an 405 konkrete Quell- und Testkörper.

Sieben Gegenfälle an unverändertem Basiscode reproduzieren die fehlenden
Ablehnungen: vier am ursprünglichen aktuellen Quellenkontext und drei am oberen
tatsächlichen POST-Wrapper. Die drei Wrapperfälle erreichen trotz ungültiger
aktueller Mindestmenge, Losgröße oder suspendiertem Instrument den injizierten
HTTP-Pfad. Die Gegenprobe bleibt getrennt vom später erweiterten Testkörper
und vom finalen Produktstand erhalten.

Der bestehende aktuelle Mengenconsumer prüft nun zusätzlich Mindestkontraktmenge,
exakte Losgröße, exakten Limitpreisstep, live-Status und die Wirksamkeit ausdrücklich
angekündigter Parameteränderungen. Er verwendet dieselben Originalantworten aus
den vorhandenen zehn GETs. Er verändert weder Order noch Quellenuhr und erzeugt
keinen Ersatzplan. Eine angekündigte Änderung kann die Quelle auch innerhalb
ihres bisherigen zulässigen Aufnahmealters ungültig machen.

Die vorhandenen Prüfstellen reichen von vor GO und Permitmint über ursprüngliche
Budgetmutation, K1 und beide HTTP-Eintritte bis nach Openerkonstruktion unmittelbar
vor dem Socket. Die neuen Fälle beobachten an diesen Grenzen tatsächliche
Originalwriter und ihre unveränderten Hold-/Permit-/Claimzustände. Ein typisiertes
spätes Veto schließt ausschließlich einen noch offenen PRE_SOCKET-Claim negativ.
Nach MAY_HAVE_SENT bleiben mögliche Außenwirkung und Kapitalbindung erhalten.

Finaler gemeinsamer Ownerlauf: **799 PASS, Exit 0**, darunter **72 neue Fälle**.
Die 405 gebundenen Quell-/Testdateien bleiben während des Laufs unverändert.
Der Lauf enthält die bestehenden N1-, Budget-, V1-/V2-, Safety-, Maximalmengen-,
Pending-/Account-/K1-, Transport-/Abort- und HTTP-Ownerfälle. Zwei bekannte
historische Dokumentverträge bleiben ausdrücklich deselected und offen.
Ein identischer abgeschlossener PASS wird für Dokumentation und Commit anhand
der Quellhashes wiederverwendet, ohne erneuten Ownerlauf.

Die statische Diffprüfung entdeckt zusätzlich eine geänderte importierte
Instrumentfixture außerhalb der ursprünglichen 405 Vorher-/Nachherhashes.
Ihre **13 eigenen Pre-external-Fälle bestehen** in einem separaten Lauf mit
406 vor und nach diesem Lauf gebundenen Körpern. Die bisherigen 405 Körper
stimmen dabei unverändert mit dem 799er-Nachweis überein. Der ursprüngliche
Prüfbeleg wird nicht nachträglich um eine angebliche frühere Hashaufnahme
erweitert; der ergänzende Nachweis steht im JSON getrennt.

Die Zwischenstände bleiben dokumentiert: zunächst 43 PASS am frühen Anschluss;
danach 70 PASS und zwei Fehler im neuen HTTP-Testhelper, dessen FUTURES-Antwort
fälschlich SWAP meldete. Der Helper erhält die passende ursprüngliche instType;
die Produktprüfung wird dafür nicht gelockert. Der erste gemeinsame Lauf endet
mit 798 PASS und einem bestehenden Timeout-Positivtest, dessen synthetische
Instrumentantwort minSz, lotSz, tickSz und upcChg nicht enthielt. Diese expliziten
positiven Testdaten sind ergänzt. Der ursprüngliche Timeout-/No-Retry-Vertrag
bleibt unverändert und besteht im finalen Lauf.

Die 14 vorhandenen historischen Quellkörper der Sicherheitslinie werden gegen
ihr lokales Manifest geprüft. Sie beziehen sich auf
5d1c838c15369507c5247834db4dd0df25592169; ein frischer Zugriff auf den externen
Herkunftsspeicher oder eine neue externe Quellenverifikation wird nicht behauptet.

Vollständige aktuelle Core-/Risiko-/Altplan-/Kapitalzulassung, Preisbandverbrauch,
unabhängiges Sendemandat, globale Anti-Clone-Herkunft, signierte Recovery und
autonome Hostkomposition bleiben offen. Passende native Metadaten machen die
ausdrücklich offline gebundenen Risikomodelle nicht zu produktiven Zulassungsownern.
Die Racegrenze zwischen letzter Prüfung und Venuewirkung bleibt bestehen.
Die älteren zwei Dokumentverträge, sieben Collector-/Account-Closeout-Befunde
und die frühere breite Acceptance-Schuld werden durch diesen Lauf nicht erledigt.

Alle Persistenzwriter sind temporär, GET-/K1-/HTTP-Ports injiziert und Sockets
gesperrt. Kein operativer Safetyzustand, Credential, Venuekontakt, Dienststart,
Kapitalfluss oder physischer Ausfall gehört zu diesem Nachweis.
