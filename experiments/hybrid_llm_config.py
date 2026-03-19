"""
Hybrid LLM Configuration for Cost-Effective Evolution

Strategy:
- High-level decisions: DeepSeek API (every N generations)
- Low-level mutations: Local Qwen2.5 4B (every generation)
"""

import os
from enum import Enum


class LLMMode(Enum):
    DEEPSEEK_ONLY = "deepseek"  # Current mode - highest quality, ¥30-60/1000gen
    LOCAL_ONLY = "local"  # Qwen2.5 4B only - free but lower quality
    HYBRID_SMART = "hybrid"  # Recommended - strategic DeepSeek + tactical local


HYBRID_CONFIG = {
    "mode": LLMMode.HYBRID_SMART,
    # DeepSeek is called every N generations for major architectural changes
    "strategic_interval": 20,  # Every 20 gens use DeepSeek
    # Local model for routine mutations
    "local_model": "qwen2.5:4b",
    "local_temperature": 0.7,
    # When to escalate to DeepSeek automatically
    "escalate_on_failures": 3,  # If local fails 3 times in a row, use DeepSeek
    # Cost estimation
    "estimated_cost_per_1000gen": "¥2-5",  # vs ¥30-60 for pure DeepSeek
}


def should_use_deepseek(generation: int, consecutive_failures: int) -> bool:
    """
    Decide whether to use DeepSeek or local model for this generation.

    Args:
        generation: Current generation number
        consecutive_failures: Number of consecutive failed mutations

    Returns:
        True if should use DeepSeek, False for local model
    """
    config = HYBRID_CONFIG

    # Always use DeepSeek for strategic generations
    if generation % config["strategic_interval"] == 0:
        return True

    # Escalate if local model keeps failing
    if consecutive_failures >= config["escalate_on_failures"]:
        return True

    # Otherwise use local model
    return False


# Example cost comparison
COST_COMPARISON = """
Cost Comparison for 1000 generations:

+--------------------+---------------+---------------+-------------+
| Mode               | DeepSeek Calls| Local Calls   | Est. Cost   |
+--------------------+---------------+---------------+-------------+
| DeepSeek Only      | ~3000         | 0             | 30-60 CNY   |
| Local Only         | 0             | ~3000         | FREE        |
| Hybrid (Recommended)| ~150         | ~2850         | 2-5 CNY     |
+--------------------+---------------+---------------+-------------+

Quality Trade-offs:
- DeepSeek Only: ***** Best algorithms, highest cost
- Local Only: *** Code quality varies, may get stuck
- Hybrid: **** Good balance, 90% cost reduction
"""

if __name__ == "__main__":
    print(COST_COMPARISON)

    # Simulate decision logic
    print("\nExample decision log for generations 1-25:")
    failures = 0
    for gen in range(1, 26):
        use_deepseek = should_use_deepseek(gen, failures)
        model = "DeepSeek" if use_deepseek else "Qwen2.5-4B"

        # Simulate success rate
        if not use_deepseek:
            # Local model has 70% success rate
            import random

            success = random.random() < 0.7
            if not success:
                failures += 1
            else:
                failures = 0
        else:
            failures = 0

        marker = "[D]" if use_deepseek else "[L]"
        print(f"Gen {gen:2d}: {marker} {model:12s} (fail streak: {failures})")
