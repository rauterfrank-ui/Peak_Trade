# Prompt Engineering Guide for Trading AI

## Overview

This guide covers best practices for writing effective prompts for AI agents in the Peak Trade system. Well-crafted prompts are essential for getting reliable, actionable insights from LLM-powered agents.

## Prompt Structure

### Basic Template

```
You are a [role] for Peak Trade.

[Context/Data]

Your task:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Output format: [JSON/Text/Markdown]
```

### Components

1. **Role Definition**: Clearly define the agent's expertise
2. **Context**: Provide relevant data and background
3. **Task Breakdown**: List specific steps
4. **Output Format**: Specify expected response structure
5. **Constraints**: Define limits and requirements

## Strategy Research Prompts

### Finding Trading Strategies

```python
prompt = """
You are a quantitative trading researcher specializing in cryptocurrency markets.

Market Data Summary:
- Symbol: {symbol}
- Timeframe: {timeframe}
- Period: {start_date} to {end_date}
- Observations: {num_observations}
- Volatility: {volatility:.2%}
- Trend: {trend}

Historical Patterns Observed:
{patterns_summary}

Your task:
1. Analyze the market data for profitable patterns
2. Identify the market regime (trending/ranging/volatile)
3. Propose a concrete trading strategy suitable for this regime
4. Define clear entry and exit rules
5. Estimate expected performance metrics
6. Explain the rationale behind your strategy

Requirements:
- Strategy must be implementable with technical indicators
- Risk/reward ratio should be at least 2:1
- Win rate expectation should be >40%
- Maximum drawdown should be <25%

Output format (JSON):
{{
    "strategy_name": "descriptive_name",
    "strategy_type": "mean_reversion|trend_following|breakout",
    "market_regime": "trending|ranging|volatile",
    "entry_rules": [
        "Specific entry condition 1",
        "Specific entry condition 2"
    ],
    "exit_rules": [
        "Specific exit condition 1",
        "Specific exit condition 2"
    ],
    "indicators_required": [
        {{"name": "RSI", "period": 14}},
        {{"name": "SMA", "period": 50}}
    ],
    "position_sizing": "fixed_fraction",
    "risk_per_trade": 0.02,
    "expected_sharpe": 1.5,
    "expected_win_rate": 0.55,
    "expected_profit_factor": 2.0,
    "rationale": "Detailed explanation of why this strategy should work",
    "potential_risks": ["Risk 1", "Risk 2"]
}}
"""
```

### Pattern Recognition

```python
prompt = """
You are a pattern recognition expert for financial markets.

Price Data:
{ohlcv_summary}

Recent Price Action:
- 5-day return: {return_5d:.2%}
- 20-day return: {return_20d:.2%}
- Current vs 20-day MA: {ma_deviation:.2%}
- ATR (14): {atr:.2f}

Your task:
1. Identify any technical patterns (head and shoulders, double top, etc.)
2. Detect support and resistance levels
3. Assess trend strength and direction
4. Identify potential reversal signals
5. Evaluate volume patterns

Output format (JSON):
{{
    "patterns_detected": [
        {{
            "pattern_name": "double_bottom",
            "confidence": 0.85,
            "implications": "Bullish reversal signal"
        }}
    ],
    "support_levels": [48500, 47800],
    "resistance_levels": [52000, 53500],
    "trend": {{
        "direction": "bullish",
        "strength": "strong",
        "confidence": 0.80
    }},
    "key_observations": [
        "Observation 1",
        "Observation 2"
    ],
    "trading_implications": "What traders should watch for"
}}
"""
```

## Risk Analysis Prompts

### Portfolio Risk Assessment

```python
prompt = """
You are a risk management expert specializing in cryptocurrency portfolios.

Portfolio Composition:
{portfolio_summary}

Current Metrics:
- Total Value: {total_value} EUR
- Number of Positions: {num_positions}
- Largest Position: {largest_position_pct:.1%}
- Daily VaR (95%): {var_95:.2%}
- Sharpe Ratio: {sharpe:.2f}
- Max Drawdown: {max_dd:.2%}

Risk Limits:
- Max Drawdown: {max_dd_limit:.2%}
- Max Daily Loss: {max_daily_loss:.2%}
- Max Position Size: {max_position_pct:.1%}
- Min Sharpe: {min_sharpe:.2f}

Your task:
1. Assess current portfolio risk level
2. Identify any risk limit violations
3. Check for concentration risk
4. Evaluate diversification
5. Provide risk mitigation recommendations

Output format (JSON):
{{
    "overall_risk_score": 0.65,
    "risk_level": "moderate",
    "violations": [
        {{
            "limit": "max_position_size",
            "current": 0.35,
            "threshold": 0.25,
            "severity": "medium"
        }}
    ],
    "concentration_risk": {{
        "score": 0.7,
        "top_3_concentration": 0.75,
        "assessment": "Moderate concentration in BTC/ETH"
    }},
    "diversification_score": 0.6,
    "recommendations": [
        "Reduce BTC position to below 25%",
        "Add uncorrelated assets"
    ],
    "action_required": "rebalance|monitor|none"
}}
"""
```

### Strategy Risk Validation

```python
prompt = """
You are a strategy risk validator for algorithmic trading systems.

Strategy Details:
- Name: {strategy_name}
- Type: {strategy_type}
- Backtest Period: {backtest_period}

Backtest Results:
- Total Return: {total_return:.2%}
- Sharpe Ratio: {sharpe:.2f}
- Max Drawdown: {max_dd:.2%}
- Win Rate: {win_rate:.1%}
- Profit Factor: {profit_factor:.2f}
- Total Trades: {total_trades}

Risk Profile:
- Average Trade: {avg_trade:.2%}
- Worst Trade: {worst_trade:.2%}
- Consecutive Losses: {max_consecutive_losses}

Your task:
1. Evaluate if risk metrics are acceptable
2. Check for overfitting indicators
3. Assess trade frequency and sample size
4. Identify potential failure modes
5. Recommend approval or rejection

Risk Thresholds:
- Min Sharpe: 1.0
- Max Drawdown: -25%
- Min Total Trades: 50
- Min Profit Factor: 1.3

Output format (JSON):
{{
    "approved": true,
    "confidence": 0.85,
    "risk_score": 0.35,
    "concerns": [
        "Relatively few trades (67) - consider longer backtest"
    ],
    "strengths": [
        "Good Sharpe ratio (1.8)",
        "Controlled drawdown (-15%)"
    ],
    "overfitting_indicators": [
        "Win rate suspiciously high",
        "Perfect symmetry in returns"
    ],
    "failure_modes": [
        "Regime change: strategy is mean-reversion, may fail in strong trends",
        "Liquidity: small trades may not scale"
    ],
    "recommendation": "approve|reject|modify",
    "suggested_modifications": [
        "Add trend filter to avoid counter-trend trades"
    ]
}}
"""
```

## Market Analysis Prompts

### Market Regime Detection

```python
prompt = """
You are a market regime analyst for cryptocurrency markets.

Current Market Data:
- Price: {current_price}
- 20-day Return: {return_20d:.2%}
- 50-day Return: {return_50d:.2%}
- 20-day Volatility: {vol_20d:.2%}
- 50-day Volatility: {vol_50d:.2%}
- ATR/Price: {atr_pct:.2%}

Price vs Moving Averages:
- vs 20-day MA: {ma20_dev:.2%}
- vs 50-day MA: {ma50_dev:.2%}
- vs 200-day MA: {ma200_dev:.2%}

Volume Analysis:
- Average Volume (20d): {avg_volume}
- Current Volume: {current_volume}
- Volume Trend: {volume_trend}

Your task:
1. Identify the current market regime
2. Assess regime stability
3. Predict potential regime changes
4. Recommend trading approach for this regime

Output format (JSON):
{{
    "regime": "trending_up|trending_down|ranging|high_volatility",
    "confidence": 0.85,
    "stability": "stable|transitioning|unstable",
    "regime_duration_estimate": "short|medium|long",
    "key_indicators": [
        "Strong uptrend confirmed by all MAs",
        "Volume supporting the move"
    ],
    "regime_change_signals": [
        "Watch for break below 50-day MA",
        "Declining volume would be concerning"
    ],
    "recommended_strategies": [
        "trend_following",
        "breakout"
    ],
    "strategies_to_avoid": [
        "mean_reversion"
    ],
    "risk_level": "low|medium|high"
}}
"""
```

## Decision Explanation Prompts

### Explaining AI Decisions

```python
prompt = """
You are an AI decision explainer for Peak Trade trading systems.

Agent Decision:
- Agent: {agent_name}
- Action: {action}
- Timestamp: {timestamp}
- Inputs: {inputs}
- Outputs: {outputs}
- Reasoning: {reasoning}

Your task:
Explain this agent decision in clear, understandable terms for a human trader.

Include:
1. What action was taken
2. Why this action was chosen (simplified explanation)
3. What data influenced the decision
4. What are the expected outcomes
5. What are the potential risks
6. What traders should monitor

Use simple language. Avoid technical jargon where possible.
Be concise but comprehensive.

Output format: Plain text explanation
"""
```

## Prompt Engineering Best Practices

### 1. Be Specific

❌ Bad:
```
Analyze this strategy and tell me if it's good.
```

✅ Good:
```
Analyze this mean-reversion strategy for BTC/EUR on 1-hour timeframe.
Evaluate:
1. Risk-adjusted returns (Sharpe ratio)
2. Maximum drawdown
3. Trade frequency and win rate
4. Suitability for current market conditions

Recommend approval if Sharpe > 1.5 and Max DD < -20%.
```

### 2. Provide Context

Always include:
- **What**: What you want the AI to do
- **Why**: Why this matters
- **How**: How to approach the task
- **Format**: How to structure the response

### 3. Use Examples

Show the AI what good output looks like:

```python
prompt = """
...

Example output:
{{
    "strategy_name": "RSI Mean Reversion",
    "rationale": "RSI below 30 indicates oversold conditions, historically followed by bounces",
    ...
}}
"""
```

### 4. Set Constraints

Define what NOT to do:

```python
prompt = """
...

Constraints:
- Do NOT recommend strategies with expected Sharpe < 1.0
- Do NOT use indicators requiring more than 200 bars warmup
- Do NOT suggest strategies requiring sub-minute data
"""
```

### 5. Request Confidence Scores

Always ask for confidence:

```python
{{
    "recommendation": "approve",
    "confidence": 0.85,
    "reasoning": "..."
}}
```

### 6. Handle Uncertainty

Teach the AI to express uncertainty:

```python
prompt = """
...

If you're not confident (confidence < 0.7), state this clearly and explain what
additional information would help you make a better assessment.
"""
```

## Testing Prompts

### A/B Testing Different Prompts

```python
def test_prompt_versions():
    """Test different prompt versions to find the best one."""
    
    test_data = {...}
    
    prompts = {
        "v1": prompt_version_1,
        "v2": prompt_version_2,
        "v3": prompt_version_3,
    }
    
    results = {}
    for version, prompt in prompts.items():
        response = llm.invoke(prompt.format(**test_data))
        results[version] = evaluate_response(response)
    
    return results
```

### Measuring Prompt Quality

Metrics to track:
- **Consistency**: Same input → same output?
- **Accuracy**: Matches expected result?
- **Completeness**: All required fields present?
- **Format**: Follows specified format?
- **Usefulness**: Actionable recommendations?

## Cost Optimization

### Token Management

1. **Be Concise**: Remove unnecessary words
2. **Summarize Data**: Don't include entire datasets
3. **Cache Prompts**: Reuse common prompt templates
4. **Batch Requests**: Combine related queries

### Example: Data Summarization

Instead of:
```python
# Sending 1000 rows of OHLCV data
prompt = f"Analyze this data: {df.to_json()}"  # Expensive!
```

Do:
```python
# Send summary statistics
summary = {
    "rows": len(df),
    "mean_return": df['close'].pct_change().mean(),
    "volatility": df['close'].pct_change().std(),
    "trend": "bullish" if df['close'].iloc[-1] > df['close'].iloc[0] else "bearish",
}
prompt = f"Analyze this market summary: {summary}"  # Cheap!
```

## Common Pitfalls

### 1. Vague Instructions

❌ "Find a good strategy"
✅ "Find a mean-reversion strategy for BTC with Sharpe > 1.5"

### 2. Missing Output Format

❌ No format specified
✅ "Output format: JSON with keys: strategy_name, entry_rules, exit_rules"

### 3. No Validation Criteria

❌ "Validate this strategy"
✅ "Validate: Sharpe > 1.0, Max DD < 25%, Win Rate > 40%"

### 4. Overly Complex Prompts

Break complex tasks into multiple simpler prompts.

## Further Reading

- [AI Agent Development Guide](ai_agent_development.md)
- [AI Workflows Guide](ai_workflows.md)
- Prompt templates: `src/ai/prompts/`
