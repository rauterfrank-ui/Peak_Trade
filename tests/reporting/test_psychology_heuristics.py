"""
Tests für Psychologie-Heuristik-Modul
======================================

Testet die Score-Berechnung für Trigger-Training-Events und die Aggregation
zu Cluster-Scores.

Autor: Peak_Trade Quant-Psychologie-Heuristik-Designer
Datum: Dezember 2025
"""

import pytest
from src.reporting.psychology_heuristics import (
    # Dataclasses
    TriggerTrainingPsychEventFeatures,
    TriggerTrainingPsychClusterScores,
    # Scoring-Funktionen
    score_fomo,
    score_loss_fear,
    score_impulsivity,
    score_hesitation,
    score_rule_break,
    # Aggregation
    aggregate_cluster_scores,
    build_heatmap_input_from_clusters,
    compute_psychology_heatmap_from_events,
    # Helper
    clamp_0_3,
    # Konstanten
    LATENCY_OK_S,
    LATENCY_HESITATION_S,
    MOVE_SMALL_PCT,
    MOVE_MEDIUM_PCT,
    MOVE_LARGE_PCT,
    PNL_MEDIUM_BP,
    PNL_LARGE_BP,
    LOSS_STREAK_MEDIUM,
    LOSS_STREAK_HIGH,
    SKIP_STREAK_MEDIUM,
    SKIP_STREAK_HIGH,
    # Beispiel-Events
    create_example_fomo_event,
    create_example_loss_fear_event,
    create_example_impulsivity_event,
    create_example_hesitation_event,
    create_example_rule_break_event,
    create_example_mixed_events,
)


# ============================================================================
# Helper Tests
# ============================================================================

class TestClamp:
    """Tests für clamp_0_3 Helper-Funktion."""
    
    def test_clamp_negative(self):
        """Negative Werte werden auf 0 geclamppt."""
        assert clamp_0_3(-5.0) == 0
        assert clamp_0_3(-1.0) == 0
        assert clamp_0_3(-0.1) == 0
    
    def test_clamp_zero(self):
        """Null bleibt null."""
        assert clamp_0_3(0.0) == 0
    
    def test_clamp_within_range(self):
        """Werte innerhalb [0, 3] werden korrekt gerundet."""
        assert clamp_0_3(0.4) == 0
        assert clamp_0_3(0.5) == 0  # round(0.5) = 0 in Python
        assert clamp_0_3(0.6) == 1
        assert clamp_0_3(1.4) == 1
        assert clamp_0_3(1.5) == 2
        assert clamp_0_3(2.4) == 2
        assert clamp_0_3(2.5) == 2  # round(2.5) = 2 (banker's rounding)
        assert clamp_0_3(2.6) == 3
    
    def test_clamp_above_range(self):
        """Werte über 3 werden auf 3 geclamppt."""
        assert clamp_0_3(3.1) == 3
        assert clamp_0_3(5.0) == 3
        assert clamp_0_3(100.0) == 3


# ============================================================================
# Scoring Function Tests
# ============================================================================

class TestScoreFOMO:
    """Tests für score_fomo()."""
    
    def test_no_fomo_on_exit(self):
        """EXIT-Events sollten keinen FOMO erzeugen (primär Entry-Phänomen)."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="EXIT", side="LONG",
            signal_strength=0.8, latency_s=10.0, latency_window_s=3.0,
            price_move_since_signal_pct=1.0,  # Großer Move
            price_max_favorable_pct=1.2, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-50.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        assert score_fomo(ev) == 0
    
    def test_low_fomo_on_time_entry_small_move(self):
        """Rechtzeitiger Entry mit kleinem Move → niedriger FOMO."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.05,  # Kleiner Move
            price_max_favorable_pct=0.1, price_max_adverse_pct=0.02,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_fomo(ev)
        assert score <= 1, f"Expected low FOMO, got {score}"
    
    def test_high_fomo_on_late_entry_large_move(self):
        """Später Entry mit großem Move → hoher FOMO."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=7.0,  # Spät
            latency_window_s=3.0,
            price_move_since_signal_pct=0.9,  # Großer Move
            price_max_favorable_pct=1.0, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-30.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_fomo(ev)
        assert score >= 2, f"Expected high FOMO, got {score}"
    
    def test_manual_fomo_mark_increases_score(self):
        """Manuelle FOMO-Markierung erhöht Score um +1."""
        # Ohne manuelle Markierung
        ev_without = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score_without = score_fomo(ev_without)
        
        # Mit manueller Markierung
        ev_with = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=True, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score_with = score_fomo(ev_with)
        
        # Sollte mindestens +1 sein (kann durch clamp_0_3 begrenzt sein)
        assert score_with >= score_without, "Manual FOMO mark should increase score"
        assert score_with == 3, "With manual mark, FOMO should be maxed"
    
    def test_example_fomo_event_scores_high(self):
        """Beispiel-FOMO-Event sollte hohen Score haben."""
        ev = create_example_fomo_event()
        score = score_fomo(ev)
        assert score >= 2, f"Expected high FOMO for example event, got {score}"


class TestScoreLossFear:
    """Tests für score_loss_fear()."""
    
    def test_no_fear_on_normal_exit(self):
        """Normaler Exit ohne Angst-Indizien."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="EXIT", side="LONG",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.3,
            price_max_favorable_pct=0.4, price_max_adverse_pct=0.15,
            pnl_vs_ideal_bp=-3.0,  # Nahe ideal
            had_valid_setup=True, entered_without_signal=False,
            opposite_to_signal=False, size_violation=False,
            risk_violation=False, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_loss_fear(ev)
        assert score <= 1, f"Expected low loss fear, got {score}"
    
    def test_high_fear_on_early_exit_small_adverse(self):
        """Früher Exit bei kleinem Adverse-Move → hohe Angst."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="EXIT", side="LONG",
            signal_strength=0.8, latency_s=1.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.05,
            price_max_favorable_pct=0.5,  # Viel Favorable
            price_max_adverse_pct=0.08,  # Wenig Adverse
            pnl_vs_ideal_bp=-35.0,  # Viel schlechter als ideal
            had_valid_setup=True, entered_without_signal=False,
            opposite_to_signal=False, size_violation=False,
            risk_violation=False, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_loss_fear(ev)
        assert score >= 2, f"Expected high loss fear, got {score}"
    
    def test_high_fear_on_skip_after_loss_streak(self):
        """NO_ACTION nach Loss-Streak → hohe Angst."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="NO_ACTION", side=None,
            signal_strength=0.9, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-40.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=5,  # Hoher Streak
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_loss_fear(ev)
        assert score >= 2, f"Expected high loss fear after streak, got {score}"
    
    def test_manual_fear_mark_increases_score(self):
        """Manuelle Fear-Markierung erhöht Score."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="EXIT", side="LONG",
            signal_strength=0.6, latency_s=1.5, latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-10.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=True,
            manually_marked_impulsive=False,
        )
        score = score_loss_fear(ev)
        assert score >= 1, f"Expected fear score with manual mark, got {score}"
    
    def test_example_loss_fear_event_scores_high(self):
        """Beispiel-Loss-Fear-Event sollte hohen Score haben."""
        ev = create_example_loss_fear_event()
        score = score_loss_fear(ev)
        assert score >= 2, f"Expected high loss fear for example event, got {score}"


class TestScoreImpulsivity:
    """Tests für score_impulsivity()."""
    
    def test_no_impulsivity_on_valid_setup(self):
        """Entry mit gültigem Setup → niedrige Impulsivität."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=2.5, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_impulsivity(ev)
        assert score == 0, f"Expected no impulsivity, got {score}"
    
    def test_high_impulsivity_on_no_setup_entry(self):
        """Entry ohne Setup → hohe Impulsivität."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.3, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.15,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0, had_valid_setup=False,  # Kein Setup
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_impulsivity(ev)
        assert score >= 1, f"Expected impulsivity without setup, got {score}"
    
    def test_high_impulsivity_on_very_fast_entry(self):
        """Sehr schneller Entry → Impulsivität."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=0.3,  # Sehr schnell
            latency_window_s=3.0,
            price_move_since_signal_pct=0.05,
            price_max_favorable_pct=0.1, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-10.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_impulsivity(ev)
        assert score >= 1, f"Expected impulsivity on fast entry, got {score}"
    
    def test_high_impulsivity_on_entry_without_signal(self):
        """Entry ohne Signal-Flag → hohe Impulsivität."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.5, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-15.0, had_valid_setup=False,
            entered_without_signal=True,  # Ohne Signal
            opposite_to_signal=False, size_violation=False,
            risk_violation=False, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_impulsivity(ev)
        assert score >= 2, f"Expected high impulsivity without signal, got {score}"
    
    def test_example_impulsivity_event_scores_high(self):
        """Beispiel-Impulsivity-Event sollte hohen Score haben."""
        ev = create_example_impulsivity_event()
        score = score_impulsivity(ev)
        assert score >= 2, f"Expected high impulsivity for example event, got {score}"


class TestScoreHesitation:
    """Tests für score_hesitation()."""
    
    def test_no_hesitation_on_timely_action(self):
        """Rechtzeitige Action → kein Zögern."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=2.0,  # Rechtzeitig
            latency_window_s=3.0,
            price_move_since_signal_pct=0.15,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_hesitation(ev)
        assert score == 0, f"Expected no hesitation, got {score}"
    
    def test_high_hesitation_on_late_action(self):
        """Späte Action → hohes Zögern."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=10.0,  # Sehr spät
            latency_window_s=3.0,
            price_move_since_signal_pct=0.4,
            price_max_favorable_pct=0.5, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-30.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_hesitation(ev)
        assert score >= 2, f"Expected high hesitation on late action, got {score}"
    
    def test_high_hesitation_on_no_action_with_setup(self):
        """NO_ACTION bei Setup → hohes Zögern."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="NO_ACTION", side=None,
            signal_strength=0.9, latency_s=8.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.6,
            price_max_favorable_pct=0.7,  # Großer Move verpasst
            price_max_adverse_pct=0.05, pnl_vs_ideal_bp=-50.0,
            had_valid_setup=True,  # Setup war da!
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_hesitation(ev)
        assert score >= 1, f"Expected hesitation on NO_ACTION with setup, got {score}"
    
    def test_high_hesitation_with_skip_streak(self):
        """Hoher Skip-Streak verstärkt Zögern."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="SKIP", side=None,
            signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.3,
            price_max_favorable_pct=0.4, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-30.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=6,  # Hoher Streak
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_hesitation(ev)
        assert score >= 2, f"Expected high hesitation with skip streak, got {score}"
    
    def test_example_hesitation_event_scores_high(self):
        """Beispiel-Hesitation-Event sollte hohen Score haben."""
        ev = create_example_hesitation_event()
        score = score_hesitation(ev)
        assert score >= 2, f"Expected high hesitation for example event, got {score}"


class TestScoreRuleBreak:
    """Tests für score_rule_break()."""
    
    def test_no_rule_break_on_compliant_trade(self):
        """Regelkonformer Trade → kein Regelbruch."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=2.5, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_rule_break(ev)
        assert score == 0, f"Expected no rule break, got {score}"
    
    def test_high_rule_break_on_opposite_signal(self):
        """Entry gegen Signal-Richtung → hoher Regelbruch."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="SHORT",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=True,  # Gegen Signal
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_rule_break(ev)
        assert score >= 1, f"Expected rule break on opposite signal, got {score}"
    
    def test_high_rule_break_on_size_violation(self):
        """Size-Violation → Regelbruch."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-15.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=True,  # Zu groß
            risk_violation=False, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_rule_break(ev)
        assert score >= 1, f"Expected rule break on size violation, got {score}"
    
    def test_high_rule_break_on_risk_violation(self):
        """Risk-Violation → Regelbruch."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-15.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=True,  # Risk verletzt
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        score = score_rule_break(ev)
        assert score >= 1, f"Expected rule break on risk violation, got {score}"
    
    def test_very_high_rule_break_on_multiple_violations(self):
        """Mehrere Violations → sehr hoher Regelbruch."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="SHORT",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.2,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-45.0,  # Sehr schlecht
            had_valid_setup=False, entered_without_signal=True,
            opposite_to_signal=True, size_violation=True,
            risk_violation=True, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        score = score_rule_break(ev)
        assert score == 3, f"Expected max rule break on multiple violations, got {score}"
    
    def test_example_rule_break_event_scores_high(self):
        """Beispiel-Rule-Break-Event sollte hohen Score haben."""
        ev = create_example_rule_break_event()
        score = score_rule_break(ev)
        assert score >= 2, f"Expected high rule break for example event, got {score}"


# ============================================================================
# Aggregation Tests
# ============================================================================

class TestAggregateClusterScores:
    """Tests für aggregate_cluster_scores()."""
    
    def test_empty_events_returns_empty_list(self):
        """Leere Event-Liste → leere Cluster-Liste."""
        result = aggregate_cluster_scores([])
        assert result == []
    
    def test_single_event_single_cluster(self):
        """Ein Event → ein Cluster."""
        ev = create_example_fomo_event()
        result = aggregate_cluster_scores([ev])
        
        assert len(result) == 1
        assert result[0].cluster == ev.cluster
        assert 0 <= result[0].fomo <= 3
        assert 0 <= result[0].loss_fear <= 3
        assert 0 <= result[0].impulsivity <= 3
        assert 0 <= result[0].hesitation <= 3
        assert 0 <= result[0].rule_break <= 3
    
    def test_multiple_events_same_cluster(self):
        """Mehrere Events im gleichen Cluster → ein Cluster-Score."""
        ev1 = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.6,
            price_max_favorable_pct=0.7, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-25.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=True, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        ev2 = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        
        result = aggregate_cluster_scores([ev1, ev2])
        
        assert len(result) == 1
        assert result[0].cluster == "Test"
        # FOMO sollte hoch sein (ev1 hat manual mark + high latency/move)
        assert result[0].fomo >= 1
    
    def test_multiple_events_different_clusters(self):
        """Mehrere Events in verschiedenen Clustern → mehrere Cluster-Scores."""
        events = create_example_mixed_events()
        result = aggregate_cluster_scores(events)
        
        # Sollte mehrere Cluster haben
        assert len(result) >= 2
        
        # Jeder Cluster sollte valide Scores haben
        for cluster in result:
            assert isinstance(cluster.cluster, str)
            assert 0 <= cluster.fomo <= 3
            assert 0 <= cluster.loss_fear <= 3
            assert 0 <= cluster.impulsivity <= 3
            assert 0 <= cluster.hesitation <= 3
            assert 0 <= cluster.rule_break <= 3
    
    def test_aggregation_clamps_scores(self):
        """Aggregation sollte Scores im Bereich [0, 3] halten."""
        # Erstelle Events mit extremen Werten
        events = [create_example_rule_break_event() for _ in range(10)]
        result = aggregate_cluster_scores(events)
        
        assert len(result) == 1
        # Trotz vieler extremer Events: Scores sollten <= 3 sein
        assert result[0].rule_break <= 3
        assert result[0].fomo <= 3
        assert result[0].loss_fear <= 3
        assert result[0].impulsivity <= 3
        assert result[0].hesitation <= 3


class TestBuildHeatmapInput:
    """Tests für build_heatmap_input_from_clusters()."""
    
    def test_converts_to_dict_format(self):
        """Konvertiert Cluster-Scores in Dict-Format."""
        clusters = [
            TriggerTrainingPsychClusterScores(
                cluster="Test Cluster",
                fomo=2,
                loss_fear=1,
                impulsivity=3,
                hesitation=0,
                rule_break=2,
            )
        ]
        
        result = build_heatmap_input_from_clusters(clusters)
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Cluster"
        assert result[0]["fomo"] == 2
        assert result[0]["loss_fear"] == 1
        assert result[0]["impulsivity"] == 3
        assert result[0]["hesitation"] == 0
        assert result[0]["rule_break"] == 2
    
    def test_multiple_clusters(self):
        """Mehrere Cluster korrekt konvertiert."""
        clusters = [
            TriggerTrainingPsychClusterScores(
                cluster="Cluster A", fomo=1, loss_fear=2,
                impulsivity=0, hesitation=1, rule_break=0,
            ),
            TriggerTrainingPsychClusterScores(
                cluster="Cluster B", fomo=3, loss_fear=0,
                impulsivity=2, hesitation=2, rule_break=3,
            ),
        ]
        
        result = build_heatmap_input_from_clusters(clusters)
        
        assert len(result) == 2
        assert result[0]["name"] == "Cluster A"
        assert result[1]["name"] == "Cluster B"


# ============================================================================
# End-to-End Tests
# ============================================================================

class TestEndToEnd:
    """End-to-End Tests für den gesamten Workflow."""
    
    def test_compute_psychology_heatmap_from_events(self):
        """End-to-End: Events → Heatmap-Data."""
        events = create_example_mixed_events()
        result = compute_psychology_heatmap_from_events(events)
        
        # Result sollte serialisierte Heatmap-Rows sein
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Jede Row sollte die richtigen Keys haben
        for row in result:
            assert "name" in row
            assert "fomo" in row
            assert "loss_fear" in row
            assert "impulsivity" in row
            assert "hesitation" in row
            assert "rule_break" in row
            
            # Jede Metrik sollte ein Dict mit heat_level, css_class, etc. sein
            for metric in ["fomo", "loss_fear", "impulsivity", "hesitation", "rule_break"]:
                assert isinstance(row[metric], dict)
                assert "heat_level" in row[metric]
                assert "css_class" in row[metric]
                assert "display_value" in row[metric]
                assert 0 <= row[metric]["heat_level"] <= 3
    
    def test_empty_events_produces_empty_heatmap(self):
        """Leere Events → leere Heatmap."""
        result = compute_psychology_heatmap_from_events([])
        assert result == []
    
    def test_specific_cluster_appears_in_output(self):
        """Spezifischer Cluster taucht im Output auf."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="My Special Cluster", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=5.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.5,
            price_max_favorable_pct=0.6, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-20.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=True, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        
        result = compute_psychology_heatmap_from_events([ev])
        
        assert len(result) == 1
        assert result[0]["name"] == "My Special Cluster"


# ============================================================================
# Example Event Tests
# ============================================================================

class TestExampleEvents:
    """Tests für die Beispiel-Event-Generatoren."""
    
    def test_all_example_events_are_valid(self):
        """Alle Beispiel-Events sollten valide sein."""
        events = [
            create_example_fomo_event(),
            create_example_loss_fear_event(),
            create_example_impulsivity_event(),
            create_example_hesitation_event(),
            create_example_rule_break_event(),
        ]
        
        for ev in events:
            assert isinstance(ev, TriggerTrainingPsychEventFeatures)
            assert isinstance(ev.cluster, str)
            assert ev.event_type in ("ENTER", "EXIT", "NO_ACTION", "SKIP")
    
    def test_example_mixed_events_contains_multiple_clusters(self):
        """Gemischte Beispiel-Events sollten mehrere Cluster abdecken."""
        events = create_example_mixed_events()
        clusters = {ev.cluster for ev in events}
        assert len(clusters) >= 2, "Should have multiple clusters"
    
    def test_example_events_score_appropriately(self):
        """Beispiel-Events sollten auf der richtigen Achse hochscoren."""
        # FOMO-Event sollte hohen FOMO-Score haben
        fomo_ev = create_example_fomo_event()
        assert score_fomo(fomo_ev) >= 2
        
        # Loss-Fear-Event sollte hohen Loss-Fear-Score haben
        fear_ev = create_example_loss_fear_event()
        assert score_loss_fear(fear_ev) >= 2
        
        # Impulsivity-Event sollte hohen Impulsivity-Score haben
        impuls_ev = create_example_impulsivity_event()
        assert score_impulsivity(impuls_ev) >= 2
        
        # Hesitation-Event sollte hohen Hesitation-Score haben
        hesit_ev = create_example_hesitation_event()
        assert score_hesitation(hesit_ev) >= 2
        
        # Rule-Break-Event sollte hohen Rule-Break-Score haben
        rule_ev = create_example_rule_break_event()
        assert score_rule_break(rule_ev) >= 2


# ============================================================================
# Edge Cases & Robustness
# ============================================================================

class TestEdgeCases:
    """Tests für Edge-Cases und Robustheit."""
    
    def test_zero_latency(self):
        """Latency = 0 sollte nicht crashen."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.8, latency_s=0.0,  # Zero latency
            latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        
        # Sollte nicht crashen
        assert score_fomo(ev) >= 0
        assert score_hesitation(ev) >= 0
        assert score_impulsivity(ev) >= 0
    
    def test_negative_pnl(self):
        """Negativer PnL sollte korrekt verarbeitet werden."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="EXIT", side="LONG",
            signal_strength=0.8, latency_s=2.0, latency_window_s=3.0,
            price_move_since_signal_pct=0.1,
            price_max_favorable_pct=0.3, price_max_adverse_pct=0.1,
            pnl_vs_ideal_bp=-100.0,  # Sehr negativ
            had_valid_setup=True, entered_without_signal=False,
            opposite_to_signal=False, size_violation=False,
            risk_violation=False, recent_loss_streak=0,
            recent_skip_streak=0, manually_marked_fomo=False,
            manually_marked_fear=False, manually_marked_impulsive=False,
        )
        
        score = score_loss_fear(ev)
        assert score >= 1  # Sollte Angst-Score erhöhen
    
    def test_all_flags_false(self):
        """Event ohne jegliche Flags sollte niedrige Scores haben."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.9, latency_s=2.5, latency_window_s=3.0,
            price_move_since_signal_pct=0.15,
            price_max_favorable_pct=0.2, price_max_adverse_pct=0.05,
            pnl_vs_ideal_bp=-5.0, had_valid_setup=True,
            entered_without_signal=False, opposite_to_signal=False,
            size_violation=False, risk_violation=False,
            recent_loss_streak=0, recent_skip_streak=0,
            manually_marked_fomo=False, manually_marked_fear=False,
            manually_marked_impulsive=False,
        )
        
        # Alle Scores sollten niedrig sein
        assert score_fomo(ev) <= 1
        assert score_loss_fear(ev) <= 1
        assert score_impulsivity(ev) == 0
        assert score_hesitation(ev) == 0
        assert score_rule_break(ev) == 0
    
    def test_all_flags_true(self):
        """Event mit allen Violations sollte hohe Scores haben."""
        ev = TriggerTrainingPsychEventFeatures(
            cluster="Test", event_type="ENTER", side="LONG",
            signal_strength=0.3, latency_s=10.0, latency_window_s=3.0,
            price_move_since_signal_pct=1.0,
            price_max_favorable_pct=1.2, price_max_adverse_pct=0.5,
            pnl_vs_ideal_bp=-100.0, had_valid_setup=False,
            entered_without_signal=True, opposite_to_signal=True,
            size_violation=True, risk_violation=True,
            recent_loss_streak=10, recent_skip_streak=10,
            manually_marked_fomo=True, manually_marked_fear=True,
            manually_marked_impulsive=True,
        )
        
        # Alle Scores sollten hoch sein
        assert score_fomo(ev) >= 2
        assert score_impulsivity(ev) >= 2
        assert score_rule_break(ev) >= 2
        # Hesitation könnte niedrig sein (da Entry stattfand, nicht NO_ACTION)
