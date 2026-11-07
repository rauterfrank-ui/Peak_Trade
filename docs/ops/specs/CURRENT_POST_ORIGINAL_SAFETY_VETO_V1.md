---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_SAFETY_VETO_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Originales aktuelles Safetyveto am direkten POST-Pfad

Basis: 6fe3d4e4c34b232790097988890daaf746614850 nach PR 7195. Dieser neue
Consumeranschluss verbindet den vorhandenen dauerhaften FILEGATE-Reader mit den
bereits bestehenden direkten Wrappern und der letzten HTTP-Grenze. Ein Veto ist
keine unabhängige Sendebefugnis. Der autonome Hostanschluss bleibt offen.

## Belegte Ursache und historische Variante

Der vorhandene [Permitproducer](../../../src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py)
kann übergebene Kill-/FILEGATE-Evidence ablehnen. Die direkten Wrapper übergaben
hier bislang keine Originalevidence und verwendeten dessen günstige Defaults.
Der tatsächliche HTTP-Adapter hatte vor opener.open keine erneute Vetoprüfung.
Sechs neue synthetische Gegenfälle am unveränderten Basiscode erreichen deshalb
den direkten Aufruf trotz KILLED, RECOVERING, fehlender oder beschädigter Datei,
DISABLED beziehungsweise widersprüchlicher Zustandsfelder.

Die gesonderte historische Linie 5d1c838c15369507c5247834db4dd0df25592169
enthält ein spätes PreSendSafetyGate, einen globalen Claim, signierte ACTIVE-
Recovery und einen gesonderten Reduktionsnachweis. Ihre Quellkörper sind lokal
gegen das ursprüngliche Quellenmanifest geprüft. Diese stärkere Gesamtkonstruktion
ist nicht vollständig im heutigen Checkout vorhanden. Eine unveränderte Kopie
würde fremde Claim-/Key-/Recovery-/Policyverträge voraussetzen.

Die hier gewählte Weiterentwicklung konsumiert deshalb den tatsächlich vorhandenen
[Originalreader](../../../src/ops/full_core_live_path_composition_root_v1/durable_filegate_join_v1.py)
und dessen [kanonischen Pfad-/Booleanreader](../../../src/ops/gates/risk_gate.py).
Sie stellt den fehlenden aktuellen Vetoanschluss her. Unabhängige Authentizität,
signierte Recovery, globale Authority und bewiesene Reduktionsausnahmen bleiben
gesonderte offene Verträge; sie werden nicht durch neue positive Defaults ersetzt.

## Bedeutung und Herkunft der neuen Referenz

[CurrentPostSafetyContextV1](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_post_safety_veto_v1.py)
besitzt genau zwei Felder:

- `envelope`: das exakte bereits erzeugte FinalOrderEnvelope. Instrument, native
  Kontraktmenge, Preis, Seite, clOrdId, Positionswirkung, Quellen- und Zeitbezüge
  bleiben unverändert. Der Kontext führt keine neue Finanz- oder Mengenrechnung
  und erneuert keine fachliche Core-/Riskentscheidung.
- `state_path`: der beim Eintritt aus dem vorhandenen kanonischen Reader
  aufgelöste absolute Pfad. Er identifiziert die für diesen Aufruf ausgewählte
  Originalquelle. Die Originalkonfiguration mit ihren bestehenden Env-Selektoren
  wird nicht zur global authentifizierten Root-/Owneridentität erklärt. Ein späterer
  Wechsel der aufgelösten Quelle durch Env oder Arbeitsverzeichnis sperrt denselben
  Kontext, auch wenn die andere Datei ebenfalls ACTIVE enthält.

Beide Referenzen sind ohne numerische Einheit und ohne eigene Autoritätsgeneration.
Der Kontext enthält keinen positiven Freigabeschalter, keine Attempt-ID, keinen
erneuerten Zeitstempel und kein Senderecht. Gleichheit und Typ werden gegen das
Originalenvelope geprüft. Der HTTP-Consumer prüft zusätzlich Envelopereferenz,
Digest und exakt denselben Wirebody mit der ursprünglichen Envelopeprojektion.

`stage` benennt nur die konkrete Prüfstelle in Fehlermeldungen. Es ist kein
Sicherheitszustand, keine Uhrzeit, keine Policyversion und keine Freigabe.
`minted_permit` im bestehenden OneShotJoinProbe referenziert exakt das tatsächlich
vom ursprünglichen Lower-Producer erzeugte Permitobjekt. Es dient dem Replaybeweis,
auch nach einem ungewissen Transport; dafür wird kein neues Permit aus Defaults
oder aus einer früheren Safetybeobachtung erzeugt. Eine Probe ist kein neuer Ledger.

## Originalevidence und aktuelle Consumerwirkung

Jede Prüfung liest den vorhandenen dauerhaften Reader erneut. Seine ursprünglichen
Felder behalten ihre Bedeutung:

- `evidence_status`: MISSING, UNKNOWN_BLOCKED, CONTRADICTORY oder TRUSTED_PRESENT
  sind Readerbefunde. Ein nicht vorhandener Wert wird nicht als positives Evidence
  ergänzt.
- `blocked` und `boolean_reader_blocked`: die getrennten Original-Readbacks müssen
  exakt boolesch false sein. None und andere Typen sind kein zulässiges false.
- `state_name`: Für diesen direkten tatsächlichen POST-Consumer muss die aktuelle
  Originalquelle ACTIVE melden. KILLED und RECOVERING sperren; DISABLED bleibt der
  Backtestzustand und wird hier nicht als tatsächliche Versandzulassung verwendet.
- `state_path`: die vom Reader tatsächlich verwendete, gebundene Quelle;
  `source_reader`, `reason_codes` und `join_seam_id`: ursprüngliche Reader-/Diagnose-
  referenzen, keine neuen Autorisierungsbelege.
- `contradictory`: Ein Widerspruch bleibt ein Veto.
  `env_overlay_used_as_durable_evidence` muss false bleiben. PEAK_KILL_SWITCH=1
  ist zusätzlich jederzeit ein ausdrückliches Emergency-Deny, auch wenn die
  vorhandene Datei ACTIVE meldet. Das Envflag wird nicht zu dauerhafter Evidence.

Die alte `saved_at`-Zeit des zuständigen Statewriters ist eine Speicherzeit des
Zustandsübergangs, kein eingeführter Heartbeat und keine neue Ablaufzeit. Ein
aktuell erneut gelesener unveränderter ACTIVE-Zustand erhält hier keine pauschale
15-Sekunden- oder sonstige neue Verfallsfrist. Der vorhandene Readvertrag bleibt
maßgeblich. Ein aktueller Read beweist keine signierte Herkunft oder Kopiersicherheit.

Die [originale StatePersistence](../../../src/risk_layer/kill_switch/persistence.py)
und der [KillSwitch-Owner](../../../src/risk_layer/kill_switch/core.py) bleiben
zuständig für Schreiben und erlaubte Zustandsübergänge. Dieser Anschluss schreibt,
initialisiert, entsperrt oder restauriert keine ihrer Dateien und erzeugt keine
Recoveryattestation oder Schlüssel. Nur synthetische Tests schreiben ihren
ausdrücklich temporären Originalwriter.

## Durchgehende Reihenfolge

1. Der [obere direkte Wrapper](../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py)
   prüft zuerst seine bisherigen Owner-, Baseline-, Envelope- und Budgetkontexte.
   Danach entsteht die reine gepinnte Safetyreferenz vor eigenen Sendestore-/GO-
   Mutationen. Die öffentliche Pre-live-Prüfung konsumiert ebenfalls Originalevidence.
2. Nach den bestehenden zehn frischen GETs wird dieselbe Quelle erneut vor dem
   dauerhaften POST-GO-Verbrauch geprüft. Keine zusätzlichen Venue-GETs entstehen.
3. Der [ursprüngliche Einmalwrapper](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py)
   übernimmt genau diesen Kontext oder bindet bei direktem Eintritt die aktuelle
   Originalquelle selbst. Sein Permit erhält tatsächlich gelesene Werte für
   kill_switch_blocked, durable_kill_switch_evidence_status und filegate_denied.
4. Die [Sendenaht](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
   prüft denselben Kontext vor dem originalen Budget-Submitübergang. Danach bleiben
   Originalbudget SUBMIT_MAY_HAVE_OCCURRED und Permit SENT_INITIATED die beiden
   zuständigen dauerhaften Unsicherheitsbarrieren.
5. Vor K1 prüft der vorhandene Adapter erneut. Der
   [ursprüngliche HTTP-Port](../../../src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py)
   verlangt den typisierten Kontext und dieselbe Envelope-/Bodybindung. Er liest
   vor der Signierung und nochmals nach Openerkonstruktion unmittelbar vor
   Transportzähler und opener.open. Auch sein interner Performpfad prüft den Kontext.

Ein alter Snapshot wird dadurch nicht zu einem später gültigen Permitinput. Die
letzte kleine Zeitspanne nach der letzten Prüfung bis zur Venuewirkung bleibt
eine Grenze; ein während eines bereits möglichen Transports gesetzter Kill macht
die Außenwirkung nicht rückwirkend ungeschehen.

## Dauerhaftigkeit, Replay und Integrität

Frühes Veto verbraucht weder POST-GO noch Budgetversuch oder Permit. Spätes Veto
setzt bereits gewonnene Marker nicht zurück und löst keinen Hold eigenständig.
Ein lokal bekannter fehlender HTTP-Aufruf erzeugt hier keinen erfundenen dauerhaften
Never-submitted-Receipt. Der originale Budgetreconciler verwendet weiterhin seinen
eigenen TRANSPORT_UNKNOWN-Vertrag. Der Anschluss an belastbare Abort-/Never-submitted-
Evidence bleibt offen. Nach möglicher Außenwirkung bleiben Replay, neuerlicher
Versand und automatische Kapitalfreigabe gesperrt.

Die bestehende [POST-Integritätsprüfung](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py)
schützt zusätzlich das neue Vetomodul sowie die beiden tatsächlich konsumierten
Originalreader. Der aufgezeichnete Baselinepin wird nicht verschoben. Aktuelles
origin/main, geschützte Bytes und konkrete Sendebefugnis bleiben verschiedene Aussagen.

Die generische Offline-Sendenaht bleibt für injizierte Nichtnetzwerkports nutzbar.
Ohne typisierten aktuellen Kontext öffnet der tatsächliche HTTP-Port keinen Socket.
Ein bloßes one_shot_real_post=true ersetzt diesen Kontext nicht. Kein neuer
Standing-POST- oder autonomer Hostauftrag entsteht.

## Verifikation und übrige Grenzen

[Neue Originalconsumerfälle](../../../tests/ops/test_current_post_original_safety_veto_v1.py)
prüfen die sechs Basisfehler, Zustandswechsel nach GET/GO/Mint/Budget/Permit, während
K1 und in der Openerfactory, unveränderte Holds, Kaltlesen, tatsächliches Permit
beim Replay, wechselnde Quellen, Emergency-Deny, fremde Kontexte/Wirebodies,
interne HTTP-Umgehungsversuche, alte Speicherzeit und die geschützten Readerpfade.
Bestehende positive Wrappertests binden einen expliziten temporären ACTIVE-
Originalwriter; sie lesen keinen realen operativen Safetyzustand. Ihre bisherigen
Sperr-, Reihenfolge- und No-write-Assertions bleiben erhalten.

Die erweiterte Original-FILEGATE-Prüfung korrigiert zwei datierte Testannahmen:
Der bereits an der Basis geltende DAG benennt den Treasury-Handoff als Diagnosegap,
nicht mehr die ältere 29P-Bezeichnung. Der historisch als confirmed benannte Replay
liefert tatsächlich NO_ACTION; der Compositionconsumer fasst dies als HOLD-Deny
zusammen und erzeugt keine spätere Boundary. Der Test hält beide Bedeutungen
jetzt getrennt fest und verbietet eine vorgetäuschte ENTER-/Versandwirkung.
Seine zuständigen Produktowner und ihre Regeln wurden dafür nicht verändert.
Die alte Dokumentassertion desselben Testmoduls gegen entfernte Runbooküberschriften
bleibt ausdrücklich fehlschlagend und offen.

Unabhängige Authorityherkunft und ein fortgesetztes autonomes Mandat sind weiterhin
offen, ebenso signierte Recovery/Anti-Rollback, globale Root-/Owner-Eindeutigkeit,
vollständige aktuelle Fach-/Risk-/Mengen-/Altplanzulassung, Pending-Custody,
Session-/GET-Ressourcenbindung und vollständige Never-submitted-Recovery. Es gibt
keine neue pauschale Reduce-only-Ausnahme für KILLED. Die stärkere historische
Sicherheitslinie ist nicht als Ganzes wiederhergestellt. S6 endet weiterhin an
PRE_EXTERNAL_EFFECT; der gesamte Außenring ist nicht abgenommen.
