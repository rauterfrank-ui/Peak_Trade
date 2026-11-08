---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_SAFETY_VETO_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Originales Safetyveto bis zur tatsächlichen HTTP-Grenze

Basis: 6fe3d4e4c34b232790097988890daaf746614850 nach PR 7195.
Arbeitsbranch: fix/current-post-safety-veto-handoff. Dies ist ein geprüfter
Arbeitszwischenstand ohne neuen PR und keine Gesamtabnahme des Außenrings.
Der [JSON-Nachweis](CURRENT_POST_ORIGINAL_SAFETY_VETO_2026_11_08.json) bindet
Gegenprobe, Quellstand, tatsächliche Consumer und den vollständig beendeten Ownerlauf.
Die gemeinsame Prüfung endet mit **519 PASS, Exit 0**; zwei ausdrücklich
ausgeklammerte ältere Dokumenttests bleiben offen und zählen nicht als PASS.

## Ursprüngliche Konstruktion, tatsächliche Lücke und Entscheidung

Der vorhandene Permitproducer besitzt Kill-/FILEGATE-Inputs; die beiden direkten
Wrapper verwendeten bislang deren günstige Defaults. Der vorhandene HTTP-Adapter
las vor opener.open keinen aktuellen Safetyzustand. Sechs tatsächliche synthetische
Counterfälle am unveränderten Basiscode scheitern deshalb: KILLED, RECOVERING,
fehlende Datei, beschädigte Datei, DISABLED und Widerspruch stoppen den direkten
Aufruf nicht. Sockets und echte Credentialports sind in diesen Fällen gesperrt.

Die gesonderte historische Variante an 5d1c838c15369507c5247834db4dd0df25592169
enthält spätes Veto, globalen Claim, signierte ACTIVE-Recovery und bewiesene
Reduktionsausnahmen. Ihre gesicherten Quellkörper sind gegen das frühere Original-
manifest geprüft. Diese Quellen sind Herkunftsbelege; sie wurden nicht kopiert
oder als vollständig funktionierende aktuelle Installation ausgegeben.

Die gewählte Änderung verbindet den bereits vorhandenen dauerhaften Reader mit
dem tatsächlichen heutigen Consumer. Originaler Killwriter, Budgetwriter,
Autorisierung und globale Claim-/Recoveryaufgaben behalten getrennte Zuständigkeit.
Die [vollständige Semantik](../specs/CURRENT_POST_ORIGINAL_SAFETY_VETO_V1.md)
nennt Herkunft, Einheiten, Identitäts-/Zeitbezüge und erlaubte Wirkung der neuen
Referenz sowie aller tatsächlich verwendeten Originalevidencefelder.

## Producer → Übergabe → Consumer → beobachtete Wirkung

1. Der vorhandene kanonische Pfadreader liefert die ausgewählte Originalquelle.
   Eine neue reine Referenz bindet ihren aufgelösten Pfad und das unveränderte
   Originalenvelope. Sie enthält keinen positiven Autorisierungswert.
2. Der obere Wrapper prüft die aktuelle Quelle vor eigenen GO-/Sendestore-
   Mutationen. Nach den vorhandenen zehn GETs prüft er erneut vor GO-Verbrauch.
3. Der bestehende Einmalwrapper erhält dieselbe Referenz. Seine Permitausgabe
   verwendet tatsächlich gelesene Kill-/FILEGATE-Werte anstelle günstiger Defaults.
4. Vor dem ursprünglichen Budgetübergang erfolgt ein neuer Read derselben Quelle.
   Die beiden bisherigen dauerhaften Barrieren und die V2-Attemptidentity bleiben
   anschließend bei ihren Originalwritern und werden unverändert zurückgelesen.
5. Der vorhandene K1-Adapter prüft erneut. Der tatsächliche HTTP-Consumer verlangt
   die typisierte Referenz und denselben Envelopedigest und Wirebody. Nach
   Openerkonstruktion liest er unmittelbar vor Zähler und opener.open erneut.
6. Ein State-/Quellenwechsel sperrt den tatsächlichen späteren Consumer. Früher
   verbrauchte GO-/Permitmarker und Holds werden dadurch nicht zurückgesetzt.
   Der Replaybeweis erhält exakt das wirklich gemintete Permitobjekt, auch wenn
   nach einem möglichen Transport ein Kill gesetzt wird.
7. Die vorhandene POST-Integritätsprüfung schützt zusätzlich den neuen Adapter
   und die beiden konsumierten Originalreader. Der aufgezeichnete Baselinepin
   bleibt unverändert.

Die Referenz ist kein globaler Root-/Echtheitsbeweis. ACTIVE ist hier nur der
originale zulässige Readerzustand für diesen Vetoanteil. DISABLED ist kein
tatsächlicher Livezustand; PEAK_KILL_SWITCH=1 bleibt ein zusätzliches absolutes
Deny. Kein neuer Writer, keine signierte Recovery, keine Schlüsselbeschaffung
oder Notsperrenrücksetzung wird eingeführt. Eine alte saved_at-Zeit wird weder
erneuert noch als neue Heartbeatfrist ausgewertet.

## Prüfung, Korrekturen und verbleibende Fehler

27 neue Fälle prüfen die tatsächlichen Consumer und negativen Übergänge,
einschließlich Kaltlesen, unveränderter Holds, Quellwechsel, Emergency-Deny,
Signierung/Openerfactory, tatsächlichem Permit beim Replay und Schutz der
gelesenen Quellmodule. Bestehende Originalbudget-, N1-/S5-/S6-, V1-/V2-,
Wrapper-/HTTP-, Permit- und Reconciliationfälle sind gemeinsam enthalten.
Der vollständig beendete gemeinsame Lauf und seine Quellenhashes stehen im
verlinkten JSON; identische bestandene Tests werden für Metadaten nicht wiederholt.

Vier erste bestehende No-write-Tests beanstandeten das neue Fixtureverzeichnis
im geprüften Sendestore. Der temporäre originale ACTIVE-Writer liegt jetzt in
einem getrennten Testverzeichnis. Ihre ursprünglichen Assertions bleiben erhalten.

Der erste gemeinsame Lauf enthält zusätzlich zwei fehlschlagende datierte
FILEGATE-Annahmen: einen überholten Diagnosenamen und eine erwartete spätere
Boundary bei tatsächlich vorliegendem NO_ACTION. Sie wurden anhand der
unveränderten Originalowner geklärt. Der Test bindet jetzt den bereits geltenden
Treasury-Diagnosenamen sowie Originalentscheidung NO_ACTION und Consumergrund HOLD
getrennt. Er verlangt ausdrücklich keine Venueplanung und keine spätere Boundary.
Die Produktlogik wurde nicht zugunsten eines Testlabels geändert.

Die zwei alten Dokumentverträge bleiben ausdrücklich offen: der bekannte fehlende
Atlas-Katalog mit obsoleten Runbookabschnitten und die separat reproduzierte
FILEGATE-Dokumentassertion gegen entfernte 11.2.1.J-Überschriften. Sie sind im
gemeinsamen Ownerlauf ausdrücklich deselected und werden nicht als PASS gezählt.
Auch sieben ältere Collector-/Account-Closeout-Verträge, frühere breite Abnahme-
befunde und der datierte alte Obsidian-Projektionscheck werden nicht geschlossen.

Alle Nachweise sind synthetisch: temporäre Originalwriter, injizierte GET-/K1-/
HTTP-Ports, gesperrte Sockets. Kein realer operativer Killzustand wurde für die
Proben gelesen oder geschrieben, kein echter Schlüssel, Dienst oder Handelslauf
verwendet und kein Host-/Stromausfall verursacht.

## Offen

Unabhängige Authorityherkunft, signierte Recovery/Anti-Rollback, globale Root-/Owner-
Eindeutigkeit, tatsächliche Reduktionsausnahmen, vollständige aktuelle Risk-/Mengen-/
Altplan-/Pendingzulassung, Session-/GET-Ressourcen und belastbare Never-submitted-
Evidence bleiben eigene Anschlüsse. Eine lokal gesperrte HTTP-Grenze stellt keinen
neuen dauerhaften Abortreceipt her; der Budgetreconciler nutzt weiterhin
TRANSPORT_UNKNOWN und hält die Kapitalbindung bis zu seinem eigenen Nachweis.

Der fortgesetzte autonome Hostauftrag bleibt offen. S6 endet weiterhin an
PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False bleiben
unverändert. Die stärkere historische Sicherheitslinie und Runbook A–H sind
nicht insgesamt wiederhergestellt oder abgenommen.
