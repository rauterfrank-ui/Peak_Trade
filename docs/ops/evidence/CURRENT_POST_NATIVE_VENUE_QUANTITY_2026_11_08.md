---
docs_token: DOCS_TOKEN_CURRENT_POST_NATIVE_VENUE_QUANTITY_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle native Mengenquellen bis zur HTTP-Grenze

Basis: 42ba79cefaafd58e89c6a3288fd48d44e2acbb09 auf dem bestehenden Branch
fix/current-post-safety-veto-handoff. Ein weiterer Arbeitscommit ohne neuen PR.
Der Außenring ist nicht insgesamt abgenommen.

Der [Semantikvertrag](../specs/CURRENT_POST_NATIVE_VENUE_QUANTITY_V1.md)
führt ursprüngliche Konstruktion, Einheiten, Identitäten, Zeiten, zulässige Wirkung
und tatsächliche Consumer zusammen. Der [JSON-Beleg](CURRENT_POST_NATIVE_VENUE_QUANTITY_2026_11_08.json)
bindet Gegenprobe und vollständig beendeten exakten Ownerlauf.

Zwei neue tatsächliche obere Aufrufe scheitern als Gegenprobe am unveränderten
Basiscode: Trotz aktueller maxBuy=0 oder maxMktSz=0 erreicht die positive Order
den synthetischen HTTP-Aufruf. Der bereits existierende N1-Mengenvertrag prüft
dagegen nur seine frühere Planungsaufnahme.

Jetzt verwenden N1 und tatsächlicher Versand denselben ursprünglichen skalaren
Mengenvergleich. Die neuen Antworten aus den vorhandenen zehn GETs werden mit
ihren Originalzeiten abgetrennt und exakt an das unveränderte Envelope gebunden.
Der untere tatsächliche Wrapper, die Budgetseam, K1- und beide HTTP-Eintritte
verlangen beziehungsweise prüfen denselben Quellenbezug erneut. Eine fehlende
Quelle oder überschrittene Grenze erzeugt keinen Default und kein stilles Resizing.

Die ursprüngliche negative Transportphase akzeptiert jetzt auch tatsächliche
Mengenfehler vor der Socketgrenze. Bereits MAY_HAVE_SENT bleibt ungewiss, selbst
bei späterem typisiertem Mengenfehler. Originalbudget und aktuelle Reconciliation
bleiben allein für Kapitalfreigabe zuständig.

36 neue Fälle umfassen obere Nullgrenzen, passende Seiten-/Ordertypmaxima,
fremde/fehlerhafte Quellen, fehlende untere und öffentliche/interne HTTP-Kontexte
und dieselben Originalzeiten an allen späteren tatsächlichen Consumers. Die
bestehenden N1-, Budget-, V1-/V2-, Safety-, Abort-, Host- und Positionsfälle sind
in der gemeinsamen Prüfung enthalten. Identische bestandene Tests werden nicht
für Dokumentation oder Commit wiederholt.
Final: **618 PASS, Exit 0**, darunter 36 neue Mengenfälle und zusätzlich 37
bestehende Positionsfälle. Zwei bekannte Dokumenttests bleiben deselected und
werden nicht als PASS gezählt.

Die erste erweiterte Originalconsumerprüfung enthält 148 PASS und einen
fehlschlagenden alten Positionstest: Sein oberer Aufruf hatte keinen ausdrücklichen
temporären ACTIVE-Nachweis und stoppte daher schon am vorhandenen Safetygate.
Er bindet nun denselben synthetischen Originalwriter wie die anderen positiven
Aufruftests. Seine ursprüngliche Flat-Ablehnung und alle Assertions bleiben erhalten.
Zwei bisherige Scopeassertions nennen zusätzlich den nun tatsächlich geprüften
Mengenanteil. Der alte untere Testplan trug zudem eine kanonische ID im nativen
instId-Feld; sein ausdrücklich synthetischer Plan nutzt jetzt die native Kennung.
Body-/Order-/Unsicherheits-/Replayassertions bleiben unverändert.

Der erste gemeinsame Lauf endet mit 616 PASS und zwei fehlschlagenden alten
Timeout-Positivfixtures. Ein Port lieferte keine Maximalmengen; der andere gab
für die private Mengenquelle eine fremde Instrumentzeile zurück. Die neuen
Originalconsumer sperrten beide korrekt. Die Positivfixtures liefern jetzt
ausdrückliche passende native Maxima; keine Produktprüfung oder negative
Assertion wurde dafür abgeschwächt. Der fehlgeschlagene Lauf bleibt getrennt
vom finalen Nachweis erhalten.

Zwei historische Dokumenttests bleiben im gemeinsamen Lauf ausdrücklich deselected
und offen, ebenso sieben ältere Collector-/Account-Closeout-Verträge, frühere
breite Befunde und der datierte Obsidian-Projektionscheck. Dieser Nachweis ersetzt
keinen ihrer fehlgeschlagenen Verträge.

Alle Eingaben und Writer sind temporär beziehungsweise synthetisch, alle Socket-
Verbindungen gesperrt. Kein echter Safetyzustand, Credential, Venuekontakt,
Dienststart, Kapitalfluss oder physischer Ausfall. Aktuelle Maximalmengen sind
keine vollständige heutige Fachzulassung, keine unabhängige Authority und kein
autonomer Hostauftrag; die entsprechenden Grenzen bleiben offen.
