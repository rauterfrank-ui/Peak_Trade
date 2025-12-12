#!/usr/bin/env python3
"""
Generate demo ConfigPatch objects for testing the Promotion Loop.

This script creates realistic test patches that can be used for
the first production cycle of the Promotion Loop in manual_only mode.

Usage:
    python scripts/generate_demo_patches_for_promotion.py [--cycle N]
    
    --cycle N: Generate patches for specific cycle (1-10)
               Default: Generates generic patches
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import List

from src.meta.learning_loop.models import ConfigPatch, PatchStatus


def generate_demo_patches(cycle: int = 1) -> List[ConfigPatch]:
    """
    Generate realistic demo patches for Promotion Loop testing.
    
    These patches represent typical parameter adjustments that the Learning Loop
    might recommend based on TestHealth, Trigger-Training, or other analysis.
    
    Args:
        cycle: Cycle number (1-10) to generate specific variants
    
    Returns:
        List of ConfigPatch objects with APPLIED_OFFLINE status
    """
    now = datetime.utcnow()
    
    # Cycles 1-5: Identical patches for consistency testing
    if cycle <= 5:
        patches = [
            # Patch 1: Leverage-Anpassung (konservativ)
            ConfigPatch(
                id="patch_demo_001",
                target="portfolio.leverage",
                old_value=1.0,
                new_value=1.25,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="TestHealth zeigt konsistent positive Performance mit leicht erhöhtem Leverage. Backtest-Evidenz über 90 Tage.",
                source_experiment_id="test_health_2025_12_11",
                confidence_score=0.85,
                meta={
                    "backtest_sharpe": 1.42,
                    "backtest_days": 90,
                    "drawdown_increase": 0.02,
                }
            ),
            
            # Patch 2: Trigger-Delay-Optimierung
            ConfigPatch(
                id="patch_demo_002",
                target="strategy.trigger_delay",
                old_value=10.0,
                new_value=8.0,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Trigger-Training zeigt, dass 8.0s Delay bessere Entry-Points bietet ohne False-Positive-Erhöhung.",
                source_experiment_id="trigger_training_2025_12_11",
                confidence_score=0.78,
                meta={
                    "avg_slippage_reduction": 0.0015,
                    "false_positive_rate": 0.12,
                    "training_samples": 450,
                }
            ),
            
            # Patch 3: Macro-Regime-Gewichtung
            ConfigPatch(
                id="patch_demo_003",
                target="macro.regime_weight",
                old_value=0.0,
                new_value=0.25,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="InfoStream-Analyse zeigt signifikante Regime-Shifts. Moderate Gewichtung verbessert Risk-Adjusted-Returns.",
                source_experiment_id="infostream_macro_2025_12_11",
                confidence_score=0.72,
                meta={
                    "regime_detection_accuracy": 0.68,
                    "profit_factor_improvement": 0.15,
                    "tested_regimes": ["bull", "bear", "sideways"],
                }
            ),
            
            # Patch 4: Risk-Limit-Anpassung (wird abgelehnt - zu aggressiv)
            ConfigPatch(
                id="patch_demo_004",
                target="risk.max_position",
                old_value=0.1,
                new_value=0.25,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Experimentelle Anpassung - hohe Varianz in Backtests, unsicher für Live.",
                source_experiment_id="risk_experiment_2025_12_11",
                confidence_score=0.45,
                meta={
                    "backtest_sharpe": 1.15,
                    "max_drawdown": 0.35,
                    "stability_score": 0.52,
                }
            ),
        ]
    
    # Cycle 6: Threshold boundary testing
    elif cycle == 6:
        patches = [
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_001",
                target="portfolio.leverage",
                old_value=1.0,
                new_value=1.15,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Kleine Leverage-Erhöhung. Confidence knapp über Threshold.",
                source_experiment_id=f"test_health_cycle_{cycle}",
                confidence_score=0.751,  # Just above threshold
                meta={"backtest_sharpe": 1.25, "backtest_days": 60}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_002",
                target="strategy.stop_loss",
                old_value=0.02,
                new_value=0.015,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Engerer Stop-Loss. Confidence knapp unter Threshold.",
                source_experiment_id=f"risk_analysis_cycle_{cycle}",
                confidence_score=0.749,  # Just below threshold
                meta={"backtest_sharpe": 1.18, "max_drawdown": 0.12}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_003",
                target="strategy.take_profit",
                old_value=0.05,
                new_value=0.06,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Höheres Take-Profit-Target basierend auf Volatility-Analysis.",
                source_experiment_id=f"volatility_study_cycle_{cycle}",
                confidence_score=0.82,
                meta={"avg_profit_per_trade": 0.042, "win_rate": 0.58}
            ),
        ]
    
    # Cycle 7: Different strategies
    elif cycle == 7:
        patches = [
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_001",
                target="strategy.ma_fast_period",
                old_value=10,
                new_value=12,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="MA-Crossover-Optimierung: Längere Fast-Period reduziert False-Positives.",
                source_experiment_id=f"ma_optimization_cycle_{cycle}",
                confidence_score=0.79,
                meta={"false_positive_reduction": 0.15, "signal_count": 320}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_002",
                target="strategy.ma_slow_period",
                old_value=30,
                new_value=35,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="MA-Crossover-Optimierung: Längere Slow-Period für besseren Trend-Filter.",
                source_experiment_id=f"ma_optimization_cycle_{cycle}",
                confidence_score=0.76,
                meta={"sharpe_improvement": 0.12, "drawdown_reduction": 0.03}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_003",
                target="portfolio.rebalance_frequency",
                old_value="daily",
                new_value="weekly",
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Wöchentliches Rebalancing reduziert Transaction-Costs signifikant.",
                source_experiment_id=f"cost_analysis_cycle_{cycle}",
                confidence_score=0.88,
                meta={"cost_reduction": 0.35, "performance_impact": -0.02}
            ),
        ]
    
    # Cycle 8: Macro & Regime parameters
    elif cycle == 8:
        patches = [
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_001",
                target="macro.regime_weight",
                old_value=0.0,
                new_value=0.35,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Höhere Regime-Gewichtung basierend auf macro_regime_integration Tests.",
                source_experiment_id=f"macro_regime_cycle_{cycle}",
                confidence_score=0.81,
                meta={"regime_detection_accuracy": 0.75, "sharpe_improvement": 0.18}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_002",
                target="macro.bull_market_leverage",
                old_value=1.2,
                new_value=1.4,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Bull-Market-Phasen: Höherer Leverage bei niedrigem Risiko.",
                source_experiment_id=f"regime_leverage_cycle_{cycle}",
                confidence_score=0.77,
                meta={"bull_market_sharpe": 1.85, "max_drawdown_bull": 0.08}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_003",
                target="macro.bear_market_leverage",
                old_value=0.8,
                new_value=0.5,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Bear-Market-Phasen: Deutlich reduzierter Leverage für Capital-Preservation.",
                source_experiment_id=f"regime_leverage_cycle_{cycle}",
                confidence_score=0.91,
                meta={"bear_market_drawdown_reduction": 0.45, "capital_preservation": 0.88}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_004",
                target="macro.crisis_mode_threshold",
                old_value=0.7,
                new_value=0.65,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Frühere Crisis-Mode-Aktivierung verhindert große Drawdowns.",
                source_experiment_id=f"crisis_detection_cycle_{cycle}",
                confidence_score=0.68,  # Below threshold
                meta={"false_positive_rate": 0.22, "drawdown_prevention": 0.38}
            ),
        ]
    
    # Cycle 9: High confidence & bounds testing
    elif cycle == 9:
        patches = [
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_001",
                target="portfolio.leverage",
                old_value=1.0,
                new_value=2.5,  # Large step - tests max_step bound
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="AGGRESSIVE: Sehr hoher Leverage basierend auf optimistischen Backtests. WARNUNG: Großer Schritt!",
                source_experiment_id=f"aggressive_test_cycle_{cycle}",
                confidence_score=0.65,  # Low confidence for aggressive change
                meta={"backtest_sharpe": 1.95, "max_drawdown": 0.28, "warning": "large_step"}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_002",
                target="strategy.trigger_delay",
                old_value=10.0,
                new_value=5.0,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Halbierung des Trigger-Delays für schnellere Entry-Points.",
                source_experiment_id=f"trigger_optimization_cycle_{cycle}",
                confidence_score=0.94,  # Very high confidence
                meta={"latency_improvement": 0.5, "false_positive_impact": 0.05}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_003",
                target="portfolio.max_positions",
                old_value=5,
                new_value=8,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Mehr Positionen für bessere Diversifikation.",
                source_experiment_id=f"diversification_cycle_{cycle}",
                confidence_score=0.86,
                meta={"correlation_reduction": 0.18, "sharpe_improvement": 0.09}
            ),
        ]
    
    # Cycle 10: Mixed bag + blacklist testing
    elif cycle == 10:
        patches = [
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_001",
                target="strategy.position_size",
                old_value=0.02,
                new_value=0.025,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Leichte Erhöhung der Position-Size basierend auf stabiler Performance.",
                source_experiment_id=f"position_sizing_cycle_{cycle}",
                confidence_score=0.83,
                meta={"risk_adjusted_return": 1.45, "volatility_impact": 0.08}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_002",
                target="live.api_keys.binance",  # BLACKLISTED target!
                old_value="old_key_xxx",
                new_value="new_key_yyy",
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="API-Key-Rotation (SOLLTE ABGELEHNT WERDEN - Blacklist!)",
                source_experiment_id=f"security_test_cycle_{cycle}",
                confidence_score=0.99,  # High confidence but blacklisted!
                meta={"security_test": True, "should_be_rejected": True}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_003",
                target="risk.stop_loss",  # Also potentially blacklisted
                old_value=0.02,
                new_value=0.01,
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Engerer Stop-Loss (KRITISCHER PARAMETER - sollte manuell reviewed werden)",
                source_experiment_id=f"risk_management_cycle_{cycle}",
                confidence_score=0.87,
                meta={"risk_reduction": 0.25, "win_rate_impact": -0.08}
            ),
            ConfigPatch(
                id=f"patch_cycle_{cycle:02d}_004",
                target="reporting.email_frequency",
                old_value="daily",
                new_value="weekly",
                status=PatchStatus.APPLIED_OFFLINE,
                generated_at=now,
                applied_at=now,
                reason="Wöchentliche statt tägliche Reports reduzieren Noise.",
                source_experiment_id=f"reporting_optimization_cycle_{cycle}",
                confidence_score=0.92,
                meta={"operator_satisfaction": 0.85, "noise_reduction": 0.70}
            ),
        ]
    
    else:
        # Default: Use cycle 1-5 patches
        return generate_demo_patches(cycle=1)
    
    return patches


def save_demo_patches_to_json(patches: List[ConfigPatch], output_path: Path) -> None:
    """
    Save demo patches to JSON file for inspection.
    
    Args:
        patches: List of ConfigPatch objects
        output_path: Path to JSON output file
    """
    import json
    from dataclasses import asdict
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    patches_data = []
    for patch in patches:
        patch_dict = asdict(patch)
        # Convert datetime to ISO string
        if patch_dict.get("generated_at"):
            patch_dict["generated_at"] = patch_dict["generated_at"].isoformat()
        if patch_dict.get("applied_at"):
            patch_dict["applied_at"] = patch_dict["applied_at"].isoformat()
        if patch_dict.get("promoted_at"):
            patch_dict["promoted_at"] = patch_dict["promoted_at"].isoformat() if patch_dict["promoted_at"] else None
        patches_data.append(patch_dict)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(patches_data, f, indent=2, sort_keys=True)
    
    print(f"[demo_patches] Saved {len(patches)} demo patches to {output_path}")


def main() -> None:
    """Generate and save demo patches."""
    parser = argparse.ArgumentParser(description="Generate demo patches for Promotion Loop testing")
    parser.add_argument("--cycle", type=int, default=1, help="Cycle number (1-10) for variant generation")
    args = parser.parse_args()
    
    patches = generate_demo_patches(cycle=args.cycle)
    
    output_path = Path("reports/learning_snippets/demo_patches_for_promotion.json")
    save_demo_patches_to_json(patches, output_path)
    
    print(f"\n[demo_patches] Generated {len(patches)} demo patches for Cycle #{args.cycle}:")
    for patch in patches:
        print(f"  - {patch.id}: {patch.target} ({patch.old_value} -> {patch.new_value})")
        print(f"    Confidence: {patch.confidence_score:.3f}")
        print(f"    Reason: {patch.reason[:80]}...")
        print()
    
    # Show summary
    high_confidence = [p for p in patches if p.confidence_score >= 0.85]
    medium_confidence = [p for p in patches if 0.75 <= p.confidence_score < 0.85]
    low_confidence = [p for p in patches if p.confidence_score < 0.75]
    
    print(f"\n[demo_patches] Summary:")
    print(f"  High Confidence (>=0.85): {len(high_confidence)}")
    print(f"  Medium Confidence (0.75-0.85): {len(medium_confidence)}")
    print(f"  Low Confidence (<0.75): {len(low_confidence)}")
    print(f"  Expected Accepted: {len(high_confidence) + len(medium_confidence)}")
    print(f"  Expected Rejected: {len(low_confidence)}")


if __name__ == "__main__":
    main()
