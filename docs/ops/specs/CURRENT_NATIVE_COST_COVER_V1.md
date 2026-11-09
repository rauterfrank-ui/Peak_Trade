---
docs_token: DOCS_TOKEN_CURRENT_NATIVE_COST_COVER_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Native Kostendeckung beim ursprünglichen Budgetowner

BWP1-Fortschreibung auf dem Initialmargin-Commit
`eeb8246533fafaaeafefe755a1c10f820dd37430`. Die
[Initialmargin-Zulassung](CURRENT_NATIVE_INITIAL_MARGIN_ADMISSION_V1.md) prüft
die unveränderte kanonische Menge in der tatsächlichen Abwicklungswährung.
Ihr v1-Receipt sagt weiterhin ausdrücklich `native_cost_cover_proven=false`.
Diese zusätzliche Prüfung wird nur durch die
[Testpolicy Revision 10](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V10.json), Schema
`entry_budget_policy.v11`, mit `require_native_cost_cover=true` verlangt.
Bestehende Policies werden weder umgeschrieben noch automatisch hochgestuft.

## Bedeutung und kausaler Anschluss

Die am 9. November erneut gelesenen Obsidian-Originaltexte über Kapitalquellen
und Kausalfluss unterscheiden Notional, verfügbare Margin, Kosten, eigene Holds
und Ausführungswahrheit. Ihr Pfad ist: originale Kontobeobachtung → Treasury und
29P → ursprünglicher Sizer → atomarer Hold → unveränderte finale Menge →
separate Ausführung. Der Quellstand der Notizen bleibt datiertes Wissen,
keine Betriebsfreigabe. Die analytischen Ebenen im Vault erzeugen keinen neuen
Kapitalowner.

Der [bestehende Kostenowner](../../../src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py)
berechnet Eröffnungsgebühren und adverse Bookkosten sowie getrennte Close- und
Fundingvorsorge in USDC. Die
[native Ergänzung](../../../src/ops/portfolio_capital_reservation_budget_v1/native_cost_cover_v1.py)
rekonstruiert dieselben Formeln aus den erhaltenen Originalquellen in USDT
beziehungsweise USDC. Sie verwendet exakte Brüche für Booknotional,
Gebührenbasis und Raten. Ein gerundeter VWAP darf die erforderliche Deckung
nicht verringern. Zusätzlich bleibt mindestens das native Äquivalent der
vorhandenen USDC-Vorsorge erhalten. FX misst dabei eine Verpflichtung und
erzeugt kein Kollateral.

Die aktuelle [OKX-API-Dokumentation](https://www.okx.com/docs-v5/en/)
unterscheidet accountweite USD-Werte und `details[].availEq` je Währung.
Dieses Gate vergleicht ausschließlich das passende währungsbezogene
verfügbare Eigenkapital. `availBal`, Gesamt-Equity und ein USDC-Preiswert sind
kein Ersatz für fehlendes USDT-`availEq`. Das ist eine Zulassungsprüfung auf
beobachteter verfügbarer Equity, kein Nachweis physisch separierter Bargeldkonten.

## Entry und mehrere Slots

Unter dem ursprünglichen Ownerlock wird je Abwicklungswährung verglichen:
ursprüngliche Initialmargin + Eröffnungskosten + wirksame Closevorsorge +
wirksame Fundingvorsorge aller eigenen aktiven Holds einschließlich Kandidat.
Bei anderen Währungen erfolgt keine Verrechnung. Der erste Vergleich liegt
vor der atomaren Reservation; derselbe Anschluss wird vom späten finanziellen
Entryconsumer erneut aufgerufen. Die unveränderte kanonische Menge bleibt
die Menge des ursprünglichen Envelopes. Unterdeckung erzeugt keinen Teilhold.

Die bereits vorhandene konservative Initialmargin-Regel wird erhalten:
Ein Fill oder unbekannter Submit gewährt keine unbelegte Margin-Gutschrift.
Auch die ursprünglichen Eröffnungskosten bleiben hier konservativ angesetzt.
Die frische verfügbare Equity kann Venuebindung und bezahlte Kosten bereits
berücksichtigen; deshalb kann dieses Gate einen tatsächlich möglichen Entry
zusätzlich ablehnen. Es bucht diese Beträge nicht nochmals in das USDC-Ledger,
ändert keinen Balancewriter und gibt keine fremden Mittel frei. Eine exakte
Zuordnung von bereits bezahlten Kosten und gebundener Venuemargin zu lokalen
Holds bleibt eine gesonderte offene Erweiterung.

## Erneuerung offener Kostenreserven

Der [bestehende Erneuerungsowner](../../../src/ops/portfolio_capital_reservation_budget_v1/open_slot_cost_renewal_v1.py)
erhält optional einen typisierten privaten unfiltrierten Balance-GET.
Ohne diesen neuen Input bleibt der Kontext bytegleich Schema v1; mit Input
gilt `open_slot_cost_renewal_context.v2`. Die neue Policy benötigt diesen Input.
Kontokonfiguration, Account, Erwerbskontext, Frische und Beobachtungszeit müssen
zum aktuellen Schutz-/Kapitalvorgang passen. Das zugelassene 29P-Kapital darf
die USDC-Free-Margin dieses Inputs nicht überschreiten. Die native Balance
wird gesondert geprüft und nicht aus 29P umgerechnet.

Der Erneuerungsreceipt Schema v2 enthält die neue native Kostenrechnung,
Deckung je betroffener Währung und den Quellenbezug. Grundlage der anderen
Holds ist genau die gebundene vorherige Originalrevision. Beim betroffenen
Hold ersetzen ausschließlich neue Close-/Fundingvorsorgen die alten Werte;
bereits belegte Fundingzahlungen bleiben im ursprünglichen Accounting und
werden nicht erneut abgebucht. Nachfolgende Entryprüfungen konsumieren die
letzte tatsächlich gespeicherte native Vorsorge.

Belegte native Unterdeckung hält die bisherigen Reserven fest und erzeugt
den ursprünglichen Safety-Closebedarf für den beobachteten Slot. Fehlende
oder ungebundene Quellen lassen die Erneuerung unbelegt und sperren neue
Entries; die bisherigen Holds bleiben bestehen. Ein bereits begonnener Close
wird durch eine spätere positive Erneuerung nicht aufgehoben. Veröffentlichung
von Kapital, Vorsorgen und Schutzstatus bleibt dieselbe Originaltransaktion.
Cold Read rekonstruiert Erneuerungsbelege aus Originalquellen und der
vorherigen Revision. Neu gehashte Summen ersetzen diese Prüfung nicht;
Recoveryadmission bleibt erforderlich.

## Prüfbereich und verbleibende Grenzen

Die [verbundenen Tests](../../../tests/ops/test_native_cost_cover_v1.py)
verwenden explizite simulierte GETs und ursprüngliche N1-, Budget-,
Accounting-, Schutz- und Recoveryconsumer. Sie sind kein Venue- oder
Betriebsnachweis. Der [datierte Prüfbeleg](../evidence/CURRENT_NATIVE_COST_COVER_V1_2026-11-09.json)
bindet den endgültigen Testumfang an die konkreten Quellen.

Unterstützt bleibt ausschließlich der vorhandene lineare USDT-/USDC-Pfad
mit `acctLv=2`, Cross und Netmode. USD-X-Perp-Abrechnung, accountwirksame
Maintenance-Margin, Liquidationsdeckung, zukünftige Margin-/Ratenänderungen,
vollständige Preis-/Kostenexekutionsgarantien und authentische aktuelle
Venueinputs bleiben offen. Die ursprüngliche Initialmargin wird beim Renew
konservativ weitergeführt, nicht als neue aktuelle Marginanforderung ausgegeben.
Das gesamte vorvalidierte ökonomische Framework und damit
[BWP1](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md) bleiben in Bearbeitung.
Die zuvor einmal beobachtete SHORT-Reproduzierbarkeitsabweichung wird durch
diesen Anschluss nicht als erklärt oder behoben bezeichnet.
