"""
Prompt templates for AI agents.
"""

from typing import Dict, Any


# Strategy Research Prompts
STRATEGY_RESEARCH_PROMPT = """
You are a quantitative trading researcher for Peak Trade.

Objective: {objective}

Market Data Summary:
{data_summary}

Your task:
1. Analyze the provided market data
2. Identify profitable patterns or anomalies
3. Propose a concrete trading strategy
4. Explain the rationale behind your strategy
5. Estimate expected performance metrics

Output format (JSON):
{{
    "strategy_name": "descriptive_name",
    "strategy_type": "mean_reversion|trend_following|breakout|other",
    "entry_rules": ["rule 1", "rule 2", ...],
    "exit_rules": ["rule 1", "rule 2", ...],
    "indicators": ["indicator 1", "indicator 2", ...],
    "rationale": "why this strategy should work",
    "expected_sharpe": 0.0,
    "expected_win_rate": 0.0,
    "risk_level": "low|medium|high"
}}
"""


# Risk Analysis Prompt
RISK_ANALYSIS_PROMPT = """
You are a risk management expert for Peak Trade.

Portfolio/Strategy Data:
{portfolio_data}

Your task:
1. Analyze the risk metrics
2. Identify potential risk factors
3. Check against risk limits
4. Provide recommendations

Risk Limits:
- Max Drawdown: {max_drawdown}
- Max Daily Loss: {max_daily_loss}
- Max Position Size: {max_position_size}

Output format (JSON):
{{
    "risk_score": 0.0,  // 0-1 scale
    "violations": ["violation 1", ...],
    "warnings": ["warning 1", ...],
    "recommendation": "approve|reject|modify",
    "reasoning": "detailed explanation",
    "suggested_modifications": ["modification 1", ...]
}}
"""


# Strategy Optimization Prompt
STRATEGY_OPTIMIZATION_PROMPT = """
You are a strategy optimization specialist for Peak Trade.

Current Strategy:
{strategy_definition}

Backtest Results:
{backtest_results}

Your task:
1. Analyze the backtest results
2. Identify weaknesses or areas for improvement
3. Suggest parameter optimizations
4. Provide reasoning for suggestions

Output format (JSON):
{{
    "current_performance": {{
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "win_rate": 0.0
    }},
    "weaknesses": ["weakness 1", ...],
    "suggested_changes": [
        {{
            "parameter": "param_name",
            "current_value": "value",
            "suggested_value": "value",
            "reasoning": "why this change"
        }}
    ],
    "expected_improvement": "description"
}}
"""


# Market Analysis Prompt
MARKET_ANALYSIS_PROMPT = """
You are a market analyst for Peak Trade.

Market Data:
{market_data}

Time Period: {time_period}
Symbols: {symbols}

Your task:
1. Analyze current market conditions
2. Identify market regime (trending/ranging/volatile)
3. Detect anomalies or unusual patterns
4. Provide trading insights

Output format (JSON):
{{
    "market_regime": "trending_up|trending_down|ranging|high_volatility",
    "confidence": 0.0,  // 0-1 scale
    "key_observations": ["observation 1", ...],
    "anomalies": ["anomaly 1", ...],
    "trading_recommendations": ["recommendation 1", ...],
    "reasoning": "detailed analysis"
}}
"""


# Decision Explanation Prompt
DECISION_EXPLANATION_PROMPT = """
You are an AI decision explainer for Peak Trade.

Agent Decision:
{decision_data}

Your task:
Explain this agent decision in clear, understandable terms for a human trader.

Include:
1. What action was taken
2. Why this action was chosen
3. What data influenced the decision
4. What are the expected outcomes
5. What are the potential risks

Output format (plain text):
"""


# Template registry
PROMPT_TEMPLATES: Dict[str, str] = {
    "strategy_research": STRATEGY_RESEARCH_PROMPT,
    "risk_analysis": RISK_ANALYSIS_PROMPT,
    "strategy_optimization": STRATEGY_OPTIMIZATION_PROMPT,
    "market_analysis": MARKET_ANALYSIS_PROMPT,
    "decision_explanation": DECISION_EXPLANATION_PROMPT,
}


def get_prompt_template(name: str) -> str:
    """
    Get a prompt template by name.
    
    Args:
        name: Template name
        
    Returns:
        Prompt template string
        
    Raises:
        KeyError: If template not found
    """
    if name not in PROMPT_TEMPLATES:
        raise KeyError(f"Prompt template not found: {name}")
    return PROMPT_TEMPLATES[name]


def format_prompt(name: str, **kwargs) -> str:
    """
    Format a prompt template with provided values.
    
    Args:
        name: Template name
        **kwargs: Values to format into template
        
    Returns:
        Formatted prompt string
    """
    template = get_prompt_template(name)
    return template.format(**kwargs)


def list_prompt_templates() -> list:
    """
    List all available prompt templates.
    
    Returns:
        List of template names
    """
    return list(PROMPT_TEMPLATES.keys())
