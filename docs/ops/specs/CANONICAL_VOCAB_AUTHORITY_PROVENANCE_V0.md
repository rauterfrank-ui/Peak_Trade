# Canonical Vocabulary / Authority / Provenance v0

## 1) Ziel und Geltungsbereich

Dieses Dokument normiert den gemeinsamen Begriffsraum sowie Authority- und Provenance-Grenzen fuer Peak_Trade v0, damit Architektur-, Governance- und Ops-Aussagen konsistent bleiben.  
Es definiert Begriffe und Abgrenzungen normativ, ersetzt jedoch keine subsystem-spezifischen Detail-Spezifikationen.

## 2) Canonical Vocabulary

- **Universe Selection**: Auswahl des analysierten Marktuniversums.
- **Scan / Ranking / Top-N Promotion**: Pipeline zur Bewertung und Auswahl in eine priorisierte Top-N-Menge.
- **Doubleplay Core**: Kernlogik fuer Doubleplay-Signalerzeugung und -Bewertung.
- **Bull Specialist**: Strategiebaustein fuer bullische Marktlagen.
- **Bear Specialist**: Strategiebaustein fuer baerische Marktlagen.
- **Switch-Gate**: Gate-Mechanismus fuer Freigabe oder Blockade von Strategiewechseln.
- **Regime Detection**: Erkennung des Marktregimes.
- **Strategy Switching**: Entscheidung und Umschaltung zwischen Strategiezustaenden.
- **Strategy Embedding**: Einbettung einer Strategie in ein uebergeordnetes Systemkonzept.
- **Scope / Capital Envelope**: Kapital- und Einsatzrahmen auf Portfolio- oder Mandatsebene.
- **Risk / Exposure Caps**: Harte Risiko- und Expositionsobergrenzen.
- **Safety / Kill-Switches**: Sicherheitsmechanismen inklusive Not-Aus-Semantik.
- **Governance / Live Mode Gate**: Governance-Freigabelogik fuer Live-Betrieb.
- **Execution Pipeline**: Technische Ausfuehrungskette bis zur Order- bzw. Aktionsuebermittlung.
- **Business Decision Core**: Fachliche Entscheidungsinstanz fuer Handels- oder Allokationsentscheidungen.
- **AI Orchestrator**: Orchestrierung von Analyse-, Entscheidungs- und Kontrollschritten durch KI-Komponenten.
- **Replay / Provenance**: Reproduzierbarkeit, Herkunftsnachweis und Nachvollziehbarkeit von Daten und Entscheidungen.

## 3) Forbidden Equalities

Die folgenden Gleichsetzungen sind unzulaessig und duerfen in Specs, Runbooks und Reviews nicht als austauschbar behauptet werden:

- Regime Detection != Doubleplay
- Strategy Switching != Strategy Embedding
- Switch-Gate != finale Trade-Autoritaet
- Scope / Capital Envelope != Risk Limits
- Governance != Safety != Kill Switch
- Execution Pipeline != Business Decision Core
- AI Orchestration != Execution Authority
- lokale Replay-Faehigkeit != E2E-Provenance
- im Repo vorhanden != kanonisch integriert

## 4) Ambiguity / Confusion / Interpretation Risk Map v0

Diese Map benennt typische Review- und Lesarten, die zu semantischer Drift fuehren. Sie **normiert keine neuen Regeln**; sie verdichtet die Trennungen aus Abschnitt 2 und 3 sowie die Claim-Klassen aus Abschnitt 6.  
Klassifikation bezieht sich auf die **typische Fehlinterpretationslage**, nicht auf eine technische Repo-Zuordnung.

**E1 — Doubleplay Core vs Regime Detection / Strategy Switching**

- **Confusing terms / boundary:** Doubleplay-Signale oder -Kernlogik mit Regime-Etiketten, Regime-Wechseln oder der Umschaltentscheidung zwischen Strategien gleichsetzen.
- **Confusion risk:** Falsche Architektur- und Review-Claims ueber Timing, Zustaendigkeit und Signalbedeutung.
- **Canonical distinction:** **Regime Detection** und **Doubleplay Core** sind unterschiedliche Begriffe; **Strategy Switching** ist nicht automatisch Doubleplay (vgl. Abschnitt 2 und 3).
- **Claim discipline / caution:** Keine Gleichsetzung der verbotenen Paare aus Abschnitt 3; Runtime- oder E2E-Aussagen nur in den Provenance-Klassen aus Abschnitt 6 formulieren.
- **Classification:** cross-cutting

**E2 — Scope / Capital Envelope vs Risk / Exposure Caps**

- **Confusing terms / boundary:** Kapital-/Mandatsrahmen mit harten Risiko- oder Expositionsobergrenzen verwechseln.
- **Confusion risk:** Review-Texte suggerieren identische Durchsetzung oder identische Semantik.
- **Canonical distinction:** **Scope / Capital Envelope** beschreibt den Einsatzrahmen; **Risk / Exposure Caps** sind explizite Obergrenzen (Abschnitt 2 und 3).
- **Claim discipline / caution:** — 
- **Classification:** cross-cutting

**E3 — Universe Selection vs Scan / Ranking / Top-N Promotion vs generische Markt-Scan-Hilfen**

- **Confusing terms / boundary:** Universumsauswahl mit beliebigen Scan-, Screen- oder Hilfsroutinen ohne feste Rollen im dokumentierten Ablauf gleichsetzen.
- **Confusion risk:** „Scan“ wortgleich fuer Universe-Definition, Ranking und generische Utilities verwenden.
- **Canonical distinction:** **Universe Selection** ist die Universumsfestlegung; **Scan / Ranking / Top-N Promotion** ist die Pipeline danach (Abschnitt 2); generische Utilities ersetzen diese Rollen nicht sprachlich.
- **Claim discipline / caution:** Begriffe aus Abschnitt 2 nicht mit undokumentierten Hilfsfunktionen ohne Kontext koppeln.
- **Classification:** cross-cutting

**E4 — Advisory AI / AI Orchestrator vs Business Decision Core / massgebliche Entscheidungslogik**

- **Confusing terms / boundary:** KI-Orchestrierung oder beratende KI-Schichten mit der fachlichen oder ausfuehrungsrechtlichen Endentscheidung gleichsetzen.
- **Confusion risk:** Implizite **Execution Authority** oder finale Handelsautoritaet fuer KI oder Orchestrierung unterstellt.
- **Canonical distinction:** **AI Orchestrator** ist koordinierend; **Business Decision Core** ist die fachliche Entscheidungsinstanz; **AI Orchestration != Execution Authority** (Abschnitt 3 und 5).
- **Claim discipline / caution:** Autoritaetsaussagen an Abschnitt 5 ausrichten; keine neuen Veto-Reihenfolgen behaupten.
- **Classification:** cross-cutting

**E5 — Safety / Kill-Switches vs Switch-Gate (strategisch)**

- **Confusing terms / boundary:** Sicherheits- und Not-Aus-Mechanismen mit dem Freigabe-/Blockade-Gate fuer Strategiewechsel vermischen.
- **Confusion risk:** Veto-Reihenfolge oder Wirkbereich vertauscht (Governance vs. strategische Umschaltung).
- **Canonical distinction:** **Governance != Safety != Kill Switch** (Abschnitt 3); **Switch-Gate** steuert Strategiewechsel, ist aber **nicht** die finale Trade-Autoritaet (Abschnitt 2, 3 und 5).
- **Claim discipline / caution:** Veto-Precedence nur wie in Abschnitt 5 wiedergeben.
- **Classification:** cross-cutting

**E6 — Operator-Status / Ops-Read-Modelle vs Decision Authority**

- **Confusing terms / boundary:** Operative Sichtbarkeit, Status oder Read-Modelle mit fachlicher oder ausfuehrungsrechtlicher Entscheidungsmacht gleichsetzen.
- **Confusion risk:** Implizite Autoritaet aus „Sichtbarkeit“ oder Dashboard-Kontext ableiten.
- **Canonical distinction:** Lesende Ops-Darstellungen ersetzen weder **Business Decision Core** noch **Execution Pipeline** noch die Veto-Ketten aus Abschnitt 5.
- **Claim discipline / caution:** Operator- oder Review-Sprache klar als dokumentarisch/`operator-stated` kennzeichnen, wo noetig; keine erweiterte Autoritaet behaupten.
- **Classification:** doc-only (typische Lesart); cross-cutting, sobald Implementierungs- oder Test-Claims Autoritaet vermischen.

**E7 — Learning Loops vs Runtime Decision Loops**

- **Confusing terms / boundary:** Experiment-, Training- oder Feedback-Schleifen mit dem produktiven Entscheidungs- oder Gate-Zyklus identifizieren.
- **Confusion risk:** Verbesserungs- oder Forschungsprozesse als kanonischen Live-Entscheidungspfad darstellen.
- **Canonical distinction:** Lern- oder Evidenzschleifen sind von der normierten Entscheidungs- und Gate-Kette (Abschnitt 2 und 5) inhaltlich zu trennen; keine automatische Gleichsetzung.
- **Claim discipline / caution:** Keine E2E- oder Runtime-Gleichsetzung ohne Provenance-Klasse aus Abschnitt 6.
- **Classification:** cross-cutting

**E8 — Model Orchestration vs Strategy Selection / Strategy Switching**

- **Confusing terms / boundary:** Routing, Bindung oder Auswahl von Modellen mit Strategiewahl oder **Strategy Switching** verwechseln.
- **Confusion risk:** Fachliche Strategiezustaende mit ML-Infrastruktur oder Modell-Orchestrierung vermischen.
- **Canonical distinction:** **Strategy Switching** und **Strategy Embedding** sind eigene Begriffe (Abschnitt 2); Modell-Orchestrierung ersetzt diese Semantik nicht.
- **Claim discipline / caution:** Strategie- vs. Modell-Ebene in Claims und Reviews explizit halten.
- **Classification:** cross-cutting

## 5) Authority / Veto Precedence

- **Governance / Live Mode Gate** hat Veto-Prioritaet gegenueber Betriebsfreigaben.
- **Safety / Kill-Switches** haben Veto-Prioritaet gegenueber Ausfuehrungspfaden.
- **Risk / Exposure Caps** begrenzen zulaessige Entscheidungs- und Ausfuehrungsraeume.
- **Switch-Gate** wirkt als Umschalt-Gate, aber nicht als finale Trade-Autoritaet.
- **Business Decision Core** ist nicht identisch mit der **Execution Pipeline**; Entscheidung und Ausfuehrung bleiben getrennte Autoritaetsdomaenen.
- **AI Orchestrator** ist koordinierend, aber keine eigenstaendige Execution Authority.

## 6) Provenance Boundary Notes

- **nachweisbar**: Es existieren lokale Artefakte fuer Replay-/Provenance-Bausteine, die Teilaspekte der Nachvollziehbarkeit dokumentieren.
- **teilweise nachweisbar**: Mehrere Begriffe und Kontrollgrenzen sind in unterschiedlichen Dokumenten beschrieben, aber nicht durchgaengig als einheitlicher End-to-End-Strang belegt.
- **unklar**: Einzelne Authority-Uebergaenge zwischen Decision-, Gate- und Execution-Ebenen sind dokumentarisch nicht in jeder Richtung explizit verknuepft.
- **nicht als kanonischer End-to-End-Pfad nachgewiesen**: Eine vollstaendig kanonisch integrierte E2E-Kette aus Vocabulary, Authority und Provenance wird hier nicht behauptet.

## 7) Offene Luecken / nicht nachgewiesene Punkte

- Vollstaendige E2E-Provenance ueber alle Subsystem-Grenzen ist nicht als kanonisch abgeschlossen nachgewiesen.
- Die verbindliche Kopplung zwischen Strategy Switching, Switch-Gate und finaler Ausfuehrungsautoritaet ist als Boundary definiert, aber nicht als einheitlicher kanonischer Pfad belegt.
- Die Trennung von Governance, Safety und Kill-Switch ist normativ festgelegt; die durchgaengige Evidenzkette bleibt teilweise nachzuweisen.
- Vorhandene Repo-Artefakte werden nicht automatisch als kanonische Integration interpretiert.

## 8) Guardrails before runtime work

- Keine Runtime-Ableitung aus diesem Dokument ohne subsystem-spezifische Spezifikation.
- Keine Gleichsetzung der in Abschnitt 3 verbotenen Paare in Design-, Implementierungs- oder Review-Claims.
- Claims sind ausschliesslich in den Klassen **nachweisbar**, **teilweise nachweisbar**, **unklar** oder **nicht als kanonischer End-to-End-Pfad nachgewiesen** zu formulieren.
- Jede spaetere Runtime-Arbeit muss die Authority-Veto-Hierarchie sowie die Provenance-Boundaries explizit referenzieren.

## Verifizierte Cross-Links (knapp)

- [AI_AUTONOMY_GO_NO_GO_OVERVIEW](../../governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md)
- [GATES_UND_DATENFLUSS_UEBERSICHT](../GATES_UND_DATENFLUSS_UEBERSICHT.md)
- [PHASE_42_TOPN_PROMOTION](../../PHASE_42_TOPN_PROMOTION.md)
- [REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28](../../REGIME_DETECTION_AND_STRATEGY_SWITCHING_PHASE_28.md)
- [double_play runbook](../runbooks/double_play.md)
- [DETERMINISTIC_REPLAY_PACK](../../execution/DETERMINISTIC_REPLAY_PACK.md)
- [AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2](../../governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md)
