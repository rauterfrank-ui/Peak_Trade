---
docs_token: DOCS_TOKEN_CURRENT_POST_ORIGINAL_CORE_SCOPE_DIRECTION_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Ursprüngliche Richtungsbereitschaft und CHOP-Scope am späteren Entry

Basis 023c8a92b385bb98c148748a55e62c0307fcb77b auf dem bestehenden Arbeitsbranch
fix/current-entry-policy-plan-revalidation. Dieser Anschluss verbraucht weitere
ursprüngliche Entrybedingungen aus dem gebundenen dauerhaften Core-Cursor.
Er ist keine vollständige aktuelle Core-/Scope-/Bestätigungs-/Risikoadmission.

## Ursprüngliche Konstruktion und tatsächlicher Anfangszustand

Der [ursprüngliche Coremapper](../../../src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py)
bildet SideState auf EntryExitDirectionState ab. Die
[ursprüngliche Entry-Policy](../../../src/trading/master_v2/double_play_entry_exit_policy_v0.py)
verlangt armed und im abschließenden Entryzweig LONG_ARMED für ENTER_LONG
beziehungsweise SHORT_ARMED für ENTER_SHORT. Aktive und blockierte Zustände sind
keine erneute Entrybereitschaft. Die ursprüngliche Abbildung von Neutralstart,
Switch-Terminal und Legacy-/Pendingidentitäten bleibt unverändert; daraus wird
keine zusätzliche Herkunft oder vollständige Pipelineadmission rekonstruiert.

Zwei tatsächliche N1-/Supervisorproben zeigen bei der Originalplanbindung
long_armed_neutral_start beziehungsweise short_armed_neutral_start. Der
ursprüngliche Parent trägt die logische Epoche 4, der persistierte Cursor 5.
Diese datierten Probegrößen sind keine heutigen Betriebsparameter. Sie belegen,
dass Current-Cursor, ursprüngliche Entscheidung und nächste logische Epoche
verschiedene Bezüge besitzen; Gleichheit ist keine neue Gültigkeitsregel.

Die [ursprüngliche CHOP-Policy](../../../src/trading/master_v2/chop_scope_event_policy_binding_v1.py)
bindet CHOP_DETECTED ausschließlich als RuntimeScopeState.chop_latched.
Sie erzeugt keine Richtung und ändert SideState nicht. Ihre ursprüngliche
Compositionprojektion liefert bei aktivem Latch CHOP_GUARD_BLOCK. Diesen Status
verweigert die ursprüngliche Entry-Policy. Der
[ursprüngliche Stateowner](../../../src/trading/master_v2/double_play_state.py)
blockiert damit Arming/Aktivierung/Switch; sein NOOP kann die Scope-Sperre
wieder aufheben, ohne eine neue Richtung herzustellen.

Diese Originalquellen sind am Source-Freeze
c742a23c964901c1353fcf3468e618db9cb6ef42 vorhanden und bleiben unverändert.
Auch die untersuchte historische Variante 5d1c838c15369507c5247834db4dd0df25592169
führt CHOP als Scope-Latch; der separate ältere SideState.CHOP_GUARD_BLOCK bleibt
dort als Legacyrest erkennbar. Historische Existenz ist keine heutige Authority
und beweist nicht die früheste Einführung.

## Gegenprobe und neuer Consumer

Zehn Gegenfälle am unveränderten Basisstand konsumieren den alten Plan trotz
CHOP, entgegengesetzter armed-Richtung, vollzogener Aktivierung, fehlendem
RuntimeScopeState oder untypisiertem CHOP-Latch. Die erwartete Ablehnung tritt
jeweils nicht ein. Die verwendeten Richtungs-/Scopeänderungen stammen aus den
ursprünglichen reinen State-/CHOP-Funktionen und dem ursprünglichen temporären
Cursorwriter. Kein echter Venue- oder operativer Statezugriff gehört dazu.

Der bestehende [späte Cursorconsumer](../../../src/ops/portfolio_capital_reservation_budget_v1/core_cursor_source_v1.py)
verbraucht jetzt zusätzlich die im ursprünglichen CanonicalIntent gespeicherte
und am Originalplan validierte Seite. Er liest denselben Cursor-Payload einmal
für alle seine Prädikate:

1. Das bestehende ausdrückliche KILL_ALL-Veto behält seine Priorität.
2. RuntimeScopeState muss vorhanden und sein rohes chop_latched ein tatsächliches
   JSON-Boolean sein. Fehlend, null, Zahl, String, Liste oder Objekt belegt kein
   inaktives Latch. Die allgemeine Bool-Konvertierung des Originalrestoreadapters
   ersetzt diese konkrete aktuelle Bedeutung nicht.
3. Die ursprüngliche CHOP-Compositionprojektion darf keinen CHOP_GUARD_BLOCK
   liefern. Ein aktiver Scope-Latch bleibt von Richtung und FILEGATE getrennt.
4. Der ursprüngliche SideState-Mapper und das ursprüngliche armed-Prädikat der
   Entry-Policy müssen Bereitschaft ergeben. Die gemappte Richtung muss außerdem
   exakt zur unveränderten ursprünglichen Intentseite passen, wie im ursprünglichen
   Long-/Short-Entryzweig. Es entsteht weder ein umgedrehter Intent noch eine
   neue Menge oder Strategieentscheidung.

Der Scope des Teilbefunds lautet CURRENT_ORIGINAL_CORE_ENTRY_STATE_VETOES_ONLY.
Originaler SideState, gemappte Richtung und ursprüngliche Intentseite werden
getrennt benannt. Authority bleibt NONE. Das unveränderte bestehende Plancontext-
Receipt wird nicht durch ein neues positives Core-GO ersetzt.

## Fortschritt, Aktivierung und externe Wirkung

Ein ursprünglicher Kandidatenübergang kann seine Scope-Stabilitätsdaten und die
logische Epoche fortschreiben, ohne die armed-Richtung oder den CHOP-Status zu
ändern. Dieser Fortschritt allein sperrt den alten Plan nicht. Ein legitimer
Stateübergang zu ACTIVE setzt dagegen kein neues Entryrecht: Die hier weiterhin
bevorstehende externe Entryorder muss die ursprüngliche Entrybereitschaft
einhalten. Die fortgesetzte Core-/Positionsverwaltung wird dadurch nicht zu einem
neuen Entry umgedeutet. Insbesondere ist ein ACTIVE-SideState kein bestätigter
Venuefill; dessen Wahrheit bleibt beim tatsächlichen Exchange-/Positionsowner.

NOOP-Clearing eines CHOP-Latchs wird beim nächsten Readback konsumiert. Es mintet
kein Permit, restauriert keinen verbrauchten Einmalversuch und gibt keinen Hold
frei. Ein bereits ABORTED-BEFORE-TRANSPORT konsumierter Versuch bleibt auch nach
Clearing gesperrt.

Dieselben bestehenden frühen Planreader und die vier späten Budgetreadbacks
vor K1, an beiden HTTP-Eintritten und nach Openerkonstruktion konsumieren den
Teilbefund. Ein negatives Ergebnis erreicht den vorhandenen POST_BUDGET-Pfad.
Nur derselbe ursprüngliche offene PRE_SOCKET-Claim kann negativ abgeschlossen
werden. Nach möglicher Socketwirkung bleiben UNKNOWN, Permitverbrauch und
Kapitalhold bestehen. Reconciliation, Release und Full-Close behalten ihre
ursprünglichen getrennten Owner.

## Quellenbindung und Grenzen

Der Source-Bezug aus Origin v2 und sein bestehender Digest werden unverändert
weitergeführt. Keine neue Originversion, neue Persistenz, Uhr, gemeinsame TTL,
Policygrenze, Reservefunktion, GET, Retry oder positive Authority entsteht.
Die unveränderten ursprünglichen Mapper-/Policy-/Projectionquellen werden
zusätzlich von der bestehenden POST-Quellintegritätsoberfläche geschützt.

Die [Consumerfälle](../../../tests/ops/test_current_post_core_scope_direction_v1.py)
und der [datierte Nachweis](../evidence/CURRENT_POST_ORIGINAL_CORE_SCOPE_DIRECTION_2026_11_08.md)
binden natürliche N1-Long-/Short-Producer, ursprüngliche State-/CHOP-Produktion,
rohe Typen, normale Fortsetzung, Clearing, tatsächliche POST-Zeitpunkte und
irreversible Ungewissheit. Die Original-CHOP-Verträge und die beiden ursprünglichen
positiven Long-/Short-Entryfälle werden zusätzlich ausgewählt.

Die Quelle ist der zuletzt dauerhaft geschriebene Cursor, kein vollständiger
neuer Core-Entscheidungsframe mit allen heute verfügbaren Marktinformationen.
Andere blockierte oder ungebundene Scopeereignisse und Policyzustände lassen
sich nicht allein aus einem false-Latch rekonstruieren. Vollständige aktuelle
Scope-/Regime-/C3-Confirmation-/Survival-/Suitabilityadmission, frische unabhängige
Markt-/Finanzinputs und produktive numerische Riskpolicy bleiben offen. Die
Offline-Riskpolicy wird nicht produktiv umbenannt. Legacy ohne gebundene Quelle,
globale Root-/Ownerherkunft, Sendemandate, signierte Recovery, vollständige Custody,
autonomer Host und die sieben älteren Collector-/Account-Verträge bleiben offen.
S6 endet PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False bleiben.
