"""
OpenAI API Pricing Module for Real-time Cost Tracking

This module provides current OpenAI API pricing rates and cost calculation
functions that stay synchronized with actual OpenAI pricing instead of
relying on static configuration files.

Updated: January 2025 with GPT-5, GPT-4.1, o1 series pricing and reasoning effort levels.
"""

from typing import Dict, Any, Optional
from datetime import datetime


# Current OpenAI API Pricing (January 2025) - Per Million Tokens
OPENAI_PRICING = {
    # GPT-5 Series (Released August 2025)
    # Note: reasoning_effort affects reasoning token usage, all reasoning tokens billed as output
    "gpt-5": {
        "input": 1.25,
        "output": 10.0,
        "cached": 0.125,  # 90% discount for recent cache hits
        "reasoning": 10.0,  # Same as output tokens
    },
    "gpt-5-mini": {
        "input": 0.25,
        "output": 2.0,
        "cached": 0.025,  # 90% discount
        "reasoning": 2.0,
    },
    "gpt-5-nano": {
        "input": 0.05,
        "output": 0.40,
        "cached": 0.005,  # 90% discount
        "reasoning": 0.40,
    },
    
    # GPT-4.1 Series (Released April 2025)
    "gpt-4.1": {
        "input": 2.0,
        "output": 8.0,
        "cached": 0.50,  # 75% discount
        "reasoning": 8.0,
    },
    "gpt-4.1-nano": {
        "input": 0.10,
        "output": 0.40,
        "cached": 0.025,  # 75% discount
        "reasoning": 0.40,
    },
    
    # GPT-4o Series
    "gpt-4o": {
        "input": 2.5,
        "output": 10.0,
        "cached": 1.25,  # 50% discount
        "reasoning": 10.0,
    },
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "cached": 0.075,  # 50% discount
        "reasoning": 0.60,
    },
    
    # O-series (Reasoning Models)
    "o1": {
        "input": 15.0,
        "output": 60.0,
        "cached": 7.5,  # 50% discount
        "reasoning": 60.0,
    },
    "o1-mini": {
        "input": 1.10,
        "output": 4.40,
        "cached": 0.55,  # 50% discount
        "reasoning": 4.40,
    },
    "o1-preview": {
        "input": 15.0,
        "output": 60.0,
        "cached": 7.5,  # 50% discount
        "reasoning": 60.0,
    },
    "o1-pro": {
        "input": 150.0,
        "output": 600.0,
        "cached": 75.0,  # 50% discount
        "reasoning": 600.0,
    },
    "o3-mini": {
        "input": 1.10,
        "output": 4.40,
        "cached": 0.55,  # 50% discount
        "reasoning": 4.40,
    },
    
    # Legacy models (for backward compatibility)
    "gpt-4-turbo": {
        "input": 10.0,
        "output": 30.0,
        "cached": 5.0,  # 50% discount
        "reasoning": 30.0,
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50,
        "cached": 0.25,  # 50% discount
        "reasoning": 1.50,
    },
}

# Model aliases for common variations
MODEL_ALIASES = {
    "gpt-5": "gpt-5",
    "gpt5": "gpt-5",
    "gpt-5-mini": "gpt-5-mini",
    "gpt5-mini": "gpt-5-mini",
    "gpt-5-nano": "gpt-5-nano", 
    "gpt5-nano": "gpt-5-nano",
    "gpt-4o": "gpt-4o",
    "gpt4o": "gpt-4o",
    "gpt-4.1": "gpt-4.1",
    "gpt4.1": "gpt-4.1",
    "o1": "o1",
    "o1-preview": "o1-preview",
    "o1-mini": "o1-mini",
    "o3-mini": "o3-mini",
}

# Reasoning effort impact on token usage (approximate multipliers)
REASONING_EFFORT_MULTIPLIERS = {
    "minimal": 1.0,   # No reasoning, fast response
    "low": 1.5,       # Light reasoning
    "medium": 2.0,    # Default level (balanced)
    "high": 3.0,      # Deep reasoning, more tokens
}


def get_model_pricing(model: str) -> Dict[str, float]:
    """
    Get current pricing for a specific model.
    
    Args:
        model: Model name (e.g., "gpt-5", "gpt-4o", "gpt-5-mini")
        
    Returns:
        Dictionary with pricing rates per million tokens
    """
    # Normalize model name
    normalized_model = MODEL_ALIASES.get(model, model)
    
    if normalized_model not in OPENAI_PRICING:
        # Fallback to gpt-5 pricing for unknown models
        normalized_model = "gpt-5"
    
    return OPENAI_PRICING[normalized_model].copy()


def estimate_reasoning_tokens(base_output_tokens: int, reasoning_effort: str = "medium") -> int:
    """
    Estimate reasoning tokens based on base output and effort level.
    
    Args:
        base_output_tokens: Base output tokens without reasoning
        reasoning_effort: One of "minimal", "low", "medium", "high"
        
    Returns:
        Estimated reasoning token count
    """
    multiplier = REASONING_EFFORT_MULTIPLIERS.get(reasoning_effort, 2.0)
    # Reasoning tokens are typically a fraction of output tokens
    estimated_reasoning = int(base_output_tokens * (multiplier - 1.0) * 0.3)
    return max(0, estimated_reasoning)


def calculate_cost_from_usage(usage: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate cost from OpenAI Agents SDK usage object.
    
    Args:
        usage: Usage dictionary with token counts
        model: Model name (defaults to usage.get('model') or 'gpt-5')
        
    Returns:
        Dictionary with detailed cost breakdown
    """
    # Extract model name
    model = model or usage.get("model", "gpt-5")
    pricing = get_model_pricing(model)
    
    # Extract token counts with proper fallbacks
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    
    # Handle detailed token breakdown
    input_cached_tokens = int(usage.get("input_cached_tokens", 0))
    reasoning_tokens = int(usage.get("reasoning_tokens", 0))
    
    # Get reasoning effort if available
    reasoning_effort = usage.get("reasoning_effort", "medium")
    
    # Calculate fresh (non-cached) input tokens
    fresh_input_tokens = max(input_tokens - input_cached_tokens, 0)
    
    # If no reasoning tokens provided but model supports reasoning, estimate
    if reasoning_tokens == 0 and model.startswith(("gpt-5", "o1", "o3")):
        reasoning_tokens = estimate_reasoning_tokens(output_tokens, reasoning_effort)
    
    # Calculate costs (convert from per-million to per-token)
    input_cost = fresh_input_tokens * pricing["input"] / 1_000_000
    cached_cost = input_cached_tokens * pricing["cached"] / 1_000_000
    output_cost = output_tokens * pricing["output"] / 1_000_000
    reasoning_cost = reasoning_tokens * pricing["reasoning"] / 1_000_000
    
    total_cost = input_cost + cached_cost + output_cost + reasoning_cost
    
    return {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "pricing_rates": pricing,
        "token_counts": {
            "input_tokens": input_tokens,
            "fresh_input_tokens": fresh_input_tokens,
            "input_cached_tokens": input_cached_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": input_tokens + output_tokens + reasoning_tokens,
        },
        "costs_breakdown": {
            "input_cost_usd": round(input_cost, 6),
            "cached_cost_usd": round(cached_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "reasoning_cost_usd": round(reasoning_cost, 6),
            "total_cost_usd": round(total_cost, 6),
        },
        "calculated_at": datetime.now().isoformat(),
        "cost_optimization_notes": _generate_cost_optimization_notes(model, reasoning_effort, usage),
    }


def _generate_cost_optimization_notes(model: str, reasoning_effort: str, usage: Dict[str, Any]) -> list:
    """Generate cost optimization suggestions based on usage patterns."""
    notes = []
    
    # Reasoning effort optimization
    if reasoning_effort == "high" and model.startswith("gpt-5"):
        notes.append("Consider using 'medium' or 'low' reasoning_effort for cost savings if task doesn't require deep reasoning")
    
    # Model tier suggestions
    if model == "gpt-5" and usage.get("output_tokens", 0) < 500:
        notes.append("Consider gpt-5-mini for simple tasks to reduce costs by 80%")
    
    # Caching optimization
    cached_tokens = usage.get("input_cached_tokens", 0)
    total_input = usage.get("input_tokens", 0)
    if cached_tokens == 0 and total_input > 1000:
        notes.append("Consider structuring repeated prompts to benefit from 90% caching discount")
    
    return notes


def get_all_model_pricing() -> Dict[str, Dict[str, float]]:
    """Get pricing for all supported models."""
    return OPENAI_PRICING.copy()


def validate_usage_object(usage: Dict[str, Any]) -> bool:
    """
    Validate that usage object has required fields.
    
    Args:
        usage: Usage dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["input_tokens", "output_tokens"]
    return all(field in usage for field in required_fields)



if __name__ == "__main__":
    # Test the pricing module with different scenarios
    
    # GPT-5 with high reasoning effort
    test_usage_gpt5_high = {
        "model": "gpt-5",
        "reasoning_effort": "high",
        "input_tokens": 1000,
        "input_cached_tokens": 200,
        "output_tokens": 500,
        "reasoning_tokens": 300,
    }
    
    # GPT-5-mini with minimal reasoning
    test_usage_gpt5_mini = {
        "model": "gpt-5-mini", 
        "reasoning_effort": "minimal",
        "input_tokens": 1000,
        "input_cached_tokens": 0,
        "output_tokens": 300,
        "reasoning_tokens": 0,
    }
    
    print("=== OpenAI Pricing Test ===")
    
    cost1 = calculate_cost_from_usage(test_usage_gpt5_high)
    print(f"\nGPT-5 (high reasoning): ${cost1['costs_breakdown']['total_cost_usd']:.6f}")
    print(f"Optimization notes: {cost1['cost_optimization_notes']}")
    
    cost2 = calculate_cost_from_usage(test_usage_gpt5_mini)
    print(f"\nGPT-5-mini (minimal reasoning): ${cost2['costs_breakdown']['total_cost_usd']:.6f}")
    print(f"Optimization notes: {cost2['cost_optimization_notes']}")
    
    print(f"\nCost difference: {cost1['costs_breakdown']['total_cost_usd'] / cost2['costs_breakdown']['total_cost_usd']:.1f}x more expensive")