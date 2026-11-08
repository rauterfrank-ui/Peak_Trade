---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_ENTRY_BUDGET_POLICY_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Aktuelle ursprüngliche Entry-Budgetpolicy am gespeicherten Plan

Basis adbc67a6914558b44a7aeae98df04b79c32d5c31 nach PR 7198.
Dieser Anschluss konsumiert die bereits vorhandenen äußeren Notionalgrenzen
erneut beim späteren Versand. Er erneuert keine Coreentscheidung und ist keine
vollständige aktuelle Risiko-, Markt- oder Altplanzulassung.

## Ursprüngliche Konstruktion und Herkunft

Der [ursprüngliche Policyowner](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_entry_budget_policy_v1.py)
führt per_entry_notional_limit und aggregate_reserved_notional_limit in USDC,
revision, automatic_increase_allowed=false und expiry=UNTIL_EXPLICIT_POLICY_CHANGE.
Seine [operative Konfiguration](../../../config/ops/current_productive_entry_budget_policy_v1.json)
und sein Pythonkörper sind bereits am Source-Freeze
c742a23c964901c1353fcf3468e618db9cb6ef42 vorhanden und bleiben unverändert.
Dies belegt die dort vorhandene Konstruktion, keine früheste Entstehung.

Der ursprüngliche LIVE-29P-Join begrenzt damit die Sizingceilings nach der
fachlichen Double-Play-Entscheidung. Er verändert weder die ursprüngliche
Account-Equity noch den Coreinput und startet keine neue Strategieentscheidung.
Die [ursprünglichen Ownerfälle](../../../tests/ops/test_outer_entry_budget_policy_v1.py)
prüfen diese Trennung. Der Budgetwriter bewahrt den daraus entstandenen
USDC-Notionalhold. Eine native Kontraktmenge, Venue-IMR, aktueller Marktwert oder
Kontogewinn ist ein anderer Gegenstand.

Die separate historische NEW-RISK-/Seal-Linie an
5d1c838c15369507c5247834db4dd0df25592169 verlangt ihren eigenen zugelassenen
Guardkontext und ratifizierte Caps. Sie definiert keine gemeinsame Coreplan-TTL.
Sie wird hier nicht als gegenwärtige Authority oder fremder Kapitalwriter
importiert. Der vorhandene numerische RiskAdmissionBinding-Pfad bleibt an seine
damaligen Inputs und EXPLICIT_OFFLINE_TEST_POLICY gebunden.

## Reproduzierte spätere Lücke

Vor diesem Anschluss liest der spätere Originalplan-/POST-Consumer zwar den
lebenden Budgetowner und prüft den ursprünglichen Plan samt Sizing und Intent
erneut. Er konsumiert dabei nicht die inzwischen geltenden ursprünglichen
Entry-Policygrenzen. Acht Gegenfälle mit V1 und V2 weisen deshalb engere
Einzel-/Aggregatgrenzen sowie fehlende oder ungültige aktuelle Policy nicht ab.
Sechs ursprüngliche positive Proben bestehen bereits. Diese Gegenprobe ist
keine ausgeführte Venueorder.

## Producer, aktueller Readback und Consumerwirkung

Der bestehende Budgetowner liest unter seinem eigenen Lock:

- Die wirkliche aktive COMMITTED-Reservation des unveränderten Envelopes.
- Deren ursprünglichen Notionalbetrag in USDC.
- Die Summe aller bei diesem Originalowner gegen das Budget zählenden RESERVED-
  und COMMITTED-Holds. Der eigene Hold ist darin bereits genau einmal enthalten.
- Die jetzt durch den ursprünglichen Policyloader gelesene Policy und deren
  ursprüngliche Typ-, Schema-, Währungs- und Grenzvalidierung.

Die ursprüngliche Reservation muss die aktuelle Einzelgrenze einhalten; die
unveränderte Originalsumme muss die aktuelle Aggregatgrenze einhalten. Gleichheit
besteht. Weder wird der eigene Hold nochmals addiert noch wird ein fremder Hold
aus der Summe entfernt. Ein neuer Originalhold kann deshalb auch bei unveränderter
Policy den bestehenden Plan für den späteren Versand sperren.

Der [frühe Originalconsumer](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
prüft dies neben seinem bestehenden V1-/V2-Plan-/Identityreadback vor GET und
nach der Aufnahme sowie vor GO und Submit. Das bisherige Identitäts-/Planreceipt
bleibt unverändert. Ein neuer Policydigest wird nicht in eine neue Sendeauthority
oder einen pauschalen Revision-veto-Mechanismus verwandelt: Eine andere Revision
bei weiter eingehaltenen Grenzen besteht; ein explizit höheres Limit verändert
keine ursprüngliche Menge oder Reservation.

Der [späte Originalbudgetconsumer](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_post_budget_admission_v1.py)
liest dieselbe Policy und dieselben Originaloperanden nach Submit vor K1, an
beiden HTTP-Eintritten und nach Openerkonstruktion vor dem Socket erneut.
Die unveränderte Policyimplementierung liegt zusätzlich auf der bestehenden
POST-Quellintegritätsoberfläche. Die operative Policydatei wird nicht als
eingefrorener Quellpin behandelt; ihre gültigen expliziten Änderungen sollen
am Consumer anhand ihrer Werte ausgewertet werden.

Diese Prüfung schreibt keinen Fachzustand. Ein spätes negatives Ergebnis wird
über das vorhandene POST_BUDGET-Veto konsumiert. Nur derselbe ursprüngliche
PRE_SOCKET-Claim kann negativ abgeschlossen werden. Vor Claimnahme entsteht
kein Never-submitted-Ersatzbeweis. Nach MAY_HAVE_SENT bleiben Außenwirkung,
Permitverbrauch und Kapitalhold ungewiss beziehungsweise erhalten. Release und
Reconciliation behalten ihre ursprünglichen Owner und eigenen Eingangsprüfungen.

## Nachweise und verbleibende Grenzen

Die [Consumerfälle](../../../tests/ops/test_current_post_entry_budget_policy_v1.py)
prüfen aktuelle Policyänderungen, fehlende/ungültige Quellen, einen späteren
Originalhold bei unveränderter Policy, Gleichheit ohne doppelte Zählung,
read-only-Readback, V1/V2 und vier konkrete tatsächliche POST-Zeitpunkte.
Ein Fehler nach möglicher Socketwirkung muss UNKNOWN und den Hold erhalten.
Der [datierte Nachweis](../evidence/CURRENT_POST_ORIGINAL_ENTRY_BUDGET_POLICY_2026_11_08.md)
bindet Gegenprobe, Zwischenstände, endgültige Quellen und Ergebnis.

Es gibt keine neue finanzielle Grenze, automatische Erhöhung, Plan-TTL,
Neubewertung des ursprünglichen Notionals mit einem späteren Marktpreis, neue
Menge, Reserve-/Releasefunktion, GET, Refresh, Retry oder positiven Grant.
Policyread und Originaloperanden gehören zu einer gesperrten lokalen
Ownerinspektion; eine globale Sperre bis zur externen Venuewirkung entsteht
daraus nicht. Die letzte Racegrenze bleibt.

Vollständige spätere Core-/Risk-/Marktzulassung, unabhängige Sendemandate,
eindeutige Root-/Ownerherkunft, signierte Recovery, vollständige Pending-Custody
und autonome Hostfortsetzung bleiben offen. Ganz ohne Originalbudgetkontext
gebundene Legacywege erhalten durch diesen Anschluss keine neue Zulassung.
Sieben ältere Collector-/Account-Verträge und breitere Gesamtabnahme bleiben
offen. S6 endet PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False.
