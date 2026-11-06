# Kausale Fortsetzung — G2, Meta-Suchwirkung und MI

Dieses Quellen-/Untersuchungspaket ergänzt den bestehenden Blueprint in Abschnitt 36. Vergleichscommit f69fc6f6d2cd5276d6447b24c0cff9b250a535f0. Keine neue operative SSOT oder Endfassungsentscheidung. Produktcode, Konfiguration und Tests bleiben unverändert.

## Geprüfte Grenzen

CF01: G2 sollte ein mechanischer Offline-Evidence-Adapter ohne DDO-Fixture-Ersatz sein. Seine Fassung vom 26.09. ist unverändert. Die am 30.09. eingeführten vier Herkunftspflichtfelder fehlen weiterhin. Die genaue historische Vertragsänderung ist mit Original-Code/Mapping/Spec belegt. Die neue Double-Play-Konfiguration verursachte diesen unmittelbaren Konflikt nicht. Der passende künftige Review-/Outcome-Zielvertrag bleibt offen; Ablehnung erhalten.

CF02: Tatsächlich vom SL11-Builder erzeugte synthetische Meta-Proposals wurden durch den SL12-Builder geführt. Ganze-Region-Digest blieb ohne lokalen Treffer, einheitliche +20 änderten die gewählte Region nicht; kombiniert hoben sich in diesem Fixture +20/-20 auf. Ein künstlicher Einzelwert-Kontrolltarget änderte dagegen die Budgetaufnahme. Dies ist keine ratifizierte Übersetzung zwischen ganzen Regionen und Einzelwerten. Wissenschaftlicher Claim, adressierter Proposal, Priorität, Budgetaufnahme, Request und tatsächliche Ausführung sind getrennte Wirkungen.

CF03: Standard-, föderierte und MI-Crossing-Replay-Varianten erhalten voriges Feedback, verwenden lokal aber gelieferte Requests/Evidence/Orchestrator-Inputs. Der föderierte Weg führt kein M4 aus. Forschungsbudget ist keine Kapitalallokation. Äußere oder dynamische Request-Producer bleiben zu untersuchen.

CF04: MI-Forecast, N_BARS-Referenzjoin und numerisches Realized-Label sind verschiedene Inputs. Derselbe Fixture-Forecast/Outcome-Bezug ergibt mit geliefertem UP/DOWN unterschiedliche Brier-Werte (0,5/0,7). Der aktuelle Kalibrierer verwendet das Caller-Label; daraus folgt weder eine fehlerhafte natürliche Messung noch, dass ein vorhandener vorgelagerter Label-Producer fehlt. MI-only-Export enthält keinen kanonischen DDO-Record. Die drei geöffneten Caller-Pfade und ihre Bedeutung sind in investigation.json erfasst.

CF05: MI-M4-Intake verlangt getrennte validierte MI- und kanonische Learning-Evidence. Der gelesene Wrapper reicht den Plane-Request unverändert an M4 und hängt Lineage an. Andere kausal wirksame MI-Consumer bleiben offen.

## Belege und Grenzen

investigation.json enthält fünf Grenzdossiers, 25 aktuelle Funktionsanker und zehn historische Git-Quell-/Vertragsfassungen. historical_git_sources.json bindet genaue Revision/Pfad/Hash-Kombinationen. previous_reconstruction enthält erneut geöffnete frühere Detailbefunde, keine neuen Anweisungen. scoped_consumer_search.json dokumentiert begrenzte namentliche Navigation; sie schließt dynamische/anders benannte/externe Consumer nicht aus.

mi_tests.xml enthält 28 zusätzlich bestandene vorhandene Tests. Die alten 242 PASS / 9 FAIL bleiben im vorherigen Paket erhalten und wurden für unveränderte Quellen wiederverwendet, nicht erneut ausgeführt oder behoben. Die Probe-Skripte und JSON-Ergebnisse verwenden synthetische Fixture-Daten; keine natürlichen Markt-/Lernläufe und keine tatsächliche Experimentausführung. Netzwerköffnungen sind in den kontrollierten Probes blockiert; Ledger-Herkunft bleibt unverändert.

Wiederholbare Quellen-/Ankerprüfung vom Repo aus:

```sh
./scripts/pt - < docs/ops/evidence/architecture_causal_followthrough_v1_2026_11_04/verify.py.txt
```

Die beiden Probes können analog über stdin mit dem kanonischen Launcher ausgeführt werden. Sie schreiben ausschließlich ihre diagnostische JSON-Ausgabe unter /tmp. Der Prüfer benötigt keine Originalpfade auf externen Medien. Änderungen an Codeankern oder Fixture-Dateien verlangen erneuten Abgleich. Quellenintegrität ist keine vollständige Semantik-/Runtime-Prüfung.

Führende Arbeitsdarstellung: [Blueprint Abschnitt 36](../../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md). Operative Grenzen: [Master Runbook](../../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md). Frühere Evidence bleibt unverändert: [erster Architekturabgleich](../architecture_reconstruction_alignment_v1_2026_11_04/README.md).
