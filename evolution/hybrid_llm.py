"""
Hybrid LLM Manager - Cost-Effective Evolution Strategy

Combines DeepSeek API (high quality, paid) with local Ollama (fast, free)
for optimal cost-performance balance.

Strategy:
- Strategic generations (every N): Use DeepSeek for major architectural changes
- Tactical generations: Use Ollama for micro-optimizations
- Fallback: If Ollama fails N times consecutively, escalate to DeepSeek
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass

from evolution.code_generator import CodeGenerator


@dataclass
class HybridConfig:
    """Configuration for hybrid LLM strategy"""
    strategic_interval: int = 20  # Use DeepSeek every N generations
    fallback_threshold: int = 3   # Escalate after N consecutive failures
    ollama_temperature: float = 0.7
    deepseek_temperature: float = 0.5
    ollama_model: str = "qwen3.5:4b"
    deepseek_model: str = "deepseek-chat"


class HybridLLMManager:
    """
    Manages hybrid LLM strategy for cost-effective evolution.

    Usage:
        manager = HybridLLMManager()
        result = manager.generate(
            generation=5,
            task_spec={...},
            previous_code=...,
            consecutive_failures=0
        )
    """

    def __init__(self, config: Optional[HybridConfig] = None):
        self.config = config or HybridConfig()
        self._ollama_generator: Optional[CodeGenerator] = None
        self._deepseek_generator: Optional[CodeGenerator] = None
        self._stats = {
            "ollama_calls": 0,
            "deepseek_calls": 0,
            "ollama_failures": 0,
            "fallback_activations": 0,
        }

    def _get_ollama(self) -> CodeGenerator:
        """Get or create Ollama generator"""
        if self._ollama_generator is None:
            os.environ["LLM_BACKEND"] = "ollama"
            os.environ["OLLAMA_MODEL"] = self.config.ollama_model
            self._ollama_generator = CodeGenerator(
                backend="ollama",
                model=self.config.ollama_model,
                default_temperature=self.config.ollama_temperature
            )
        return self._ollama_generator

    def _get_deepseek(self) -> CodeGenerator:
        """Get or create DeepSeek generator"""
        if self._deepseek_generator is None:
            self._deepseek_generator = CodeGenerator(
                backend="deepseek",
                model=self.config.deepseek_model,
                default_temperature=self.config.deepseek_temperature
            )
        return self._deepseek_generator

    def should_use_deepseek(self, generation: int, consecutive_failures: int) -> bool:
        """
        Decide whether to use DeepSeek or Ollama for this generation.

        Args:
            generation: Current generation number
            consecutive_failures: Number of consecutive failed mutations

        Returns:
            True if should use DeepSeek, False for Ollama
        """
        # Strategic generation - use DeepSeek for major changes
        if generation % self.config.strategic_interval == 0:
            return True

        # Fallback - Ollama keeps failing, escalate to DeepSeek
        if consecutive_failures >= self.config.fallback_threshold:
            return True

        # Default - use Ollama for routine mutations
        return False

    def generate(
        self,
        generation: int,
        task_spec: dict,
        previous_code: Optional[str] = None,
        previous_score: Optional[dict] = None,
        failed_tests: Optional[list] = None,
        strategy: Optional[dict] = None,
        consecutive_failures: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate code using hybrid strategy.

        Args:
            generation: Current generation number
            task_spec: Task specification
            previous_code: Previous generation code
            previous_score: Previous scores
            failed_tests: Failed test cases
            strategy: Mutation strategy
            consecutive_failures: Current failure streak

        Returns:
            Dict with success, code, raw_response, error, backend_used
        """
        use_deepseek = self.should_use_deepseek(generation, consecutive_failures)

        if use_deepseek:
            generator = self._get_deepseek()
            self._stats["deepseek_calls"] += 1
            backend = "deepseek"
        else:
            generator = self._get_ollama()
            self._stats["ollama_calls"] += 1
            backend = "ollama"

        result = generator.generate(
            task_spec=task_spec,
            previous_code=previous_code,
            previous_score=previous_score,
            failed_tests=failed_tests,
            strategy=strategy,
        )

        result["backend_used"] = backend

        # Track failures
        if not result["success"]:
            if backend == "ollama":
                self._stats["ollama_failures"] += 1
        else:
            # Reset failure counter on success
            if backend == "ollama":
                self._stats["ollama_failures"] = 0

        # Track fallback activations
        if use_deepseek and consecutive_failures > 0:
            self._stats["fallback_activations"] += 1

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total = self._stats["ollama_calls"] + self._stats["deepseek_calls"]
        return {
            **self._stats,
            "total_calls": total,
            "ollama_ratio": self._stats["ollama_calls"] / total if total > 0 else 0,
            "estimated_cost_cny": self._stats["deepseek_calls"] * 0.02,  # ~0.02 CNY per call
        }

    def print_stats(self):
        """Print usage statistics"""
        stats = self.get_stats()
        print("\n" + "=" * 60)
        print("Hybrid LLM Usage Statistics")
        print("=" * 60)
        print(f"Ollama calls:    {stats['ollama_calls']:4d} (free)")
        print(f"DeepSeek calls:  {stats['deepseek_calls']:4d} (~{stats['estimated_cost_cny']:.2f} CNY)")
        print(f"Ollama failures: {stats['ollama_failures']:4d}")
        print(f"Fallback activations: {stats['fallback_activations']:4d}")
        print(f"Cost savings:    {(1 - stats['ollama_ratio']) * 100:.1f}% vs pure DeepSeek")
        print("=" * 60)


# Convenience function for quick usage
def create_hybrid_generator(
    strategic_interval: int = 20,
    fallback_threshold: int = 3,
    ollama_model: str = "qwen3.5:4b"
) -> HybridLLMManager:
    """
    Create a hybrid LLM manager with common settings.

    Args:
        strategic_interval: Use DeepSeek every N generations
        fallback_threshold: Escalate to DeepSeek after N Ollama failures
        ollama_model: Local model name

    Returns:
        Configured HybridLLMManager
    """
    config = HybridConfig(
        strategic_interval=strategic_interval,
        fallback_threshold=fallback_threshold,
        ollama_model=ollama_model,
    )
    return HybridLLMManager(config)


if __name__ == "__main__":
    # Demo hybrid strategy
    manager = create_hybrid_generator(strategic_interval=5)

    print("Hybrid LLM Strategy Demo")
    print("=" * 60)
    print(f"Strategic interval: {manager.config.strategic_interval}")
    print(f"Fallback threshold: {manager.config.fallback_threshold}")
    print()

    # Simulate 15 generations
    failures = 0
    for gen in range(1, 16):
        use_deepseek = manager.should_use_deepseek(gen, failures)
        backend = "DeepSeek" if use_deepseek else "Ollama"

        # Simulate success/failure
        if not use_deepseek:
            # Ollama has 70% success rate
            import random
            success = random.random() < 0.7
            if not success:
                failures += 1
            else:
                failures = 0
        else:
            failures = 0

        marker = "[D]" if use_deepseek else "[L]"
        print(f"Gen {gen:2d}: {marker} {backend:8s} (fail streak: {failures})")

    print()
    manager.print_stats()
