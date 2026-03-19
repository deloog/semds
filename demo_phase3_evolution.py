#!/usr/bin/env python3
"""
SEMDS Phase 3 Demo - Multi-Generation Evolution Loop

This script demonstrates the complete evolution loop:
1. Initialize task and strategy optimizer
2. Run multiple generations of code evolution
3. Each generation: select strategy -> generate code -> evaluate -> update strategy
4. Track progress and report best result

Phase 3 Features:
- Thompson Sampling strategy selection
- Dual evaluation (intrinsic + extrinsic)
- Goodhart detection
- Multi-generation evolution with termination conditions
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "storage"))
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

# Load environment variables
from core.env_loader import load_env

load_env()

from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner
from evolution.strategy_optimizer import StrategyOptimizer
from evolution.dual_evaluator import DualEvaluator
from evolution.termination_checker import TerminationChecker, TerminationConfig
from evolution.orchestrator import EvolutionOrchestrator

# Calculator test code
CALCULATOR_TEST_CODE = """
from solution import calculate

def test_addition():
    assert calculate(2, 3, '+') == 5

def test_subtraction():
    assert calculate(5, 3, '-') == 2

def test_multiplication():
    assert calculate(4, 3, '*') == 12

def test_division():
    assert calculate(10, 2, '/') == 5.0

def test_division_by_zero():
    try:
        calculate(1, 0, '/')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_invalid_operator():
    try:
        calculate(1, 2, '%')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_negative_numbers():
    assert calculate(-3, -2, '*') == 6

def test_float_numbers():
    assert abs(calculate(0.1, 0.2, '+') - 0.3) < 1e-9

def test_large_numbers():
    assert calculate(1e10, 1e10, '+') == 2e10

def test_zero_operand():
    assert calculate(0, 5, '+') == 5

def test_return_type():
    result = calculate(4, 2, '/')
    assert isinstance(result, (int, float))
"""


def check_environment():
    """Check if environment is ready."""
    has_key = (
        os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )

    if not has_key:
        print("Error: No LLM API key configured")
        print("Set DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY")
        return False

    return True


def print_generation_result(gen_num: int, result: dict):
    """Print generation result."""
    print(f"\n  Generation {gen_num}:")
    print(f"    Strategy: {result.get('strategy', 'unknown')}")
    print(f"    Score: {result.get('score', 0):.2f}")
    print(f"    Tests: {'PASSED' if result.get('passed_tests') else 'FAILED'}")

    if result.get("evaluation"):
        eval_report = result["evaluation"]
        print(f"    Intrinsic: {eval_report.get('intrinsic_score', 0):.2f}")
        print(f"    Extrinsic: {eval_report.get('extrinsic_score', 0):.2f}")
        if eval_report.get("goodhart_detected"):
            print(f"    [WARN] Goodhart detected!")


def main():
    """Main entry point."""
    print("=" * 60)
    print("SEMDS Phase 3 - Multi-Generation Evolution Demo")
    print("=" * 60)
    print()

    # Check environment
    if not check_environment():
        sys.exit(1)

    print("Initializing evolution system...")

    # Create termination config
    term_config = TerminationConfig(
        max_generations=10,
        success_threshold=0.95,
        stagnation_generations=5,
    )

    # Create orchestrator
    task_id = f"calculator_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    orchestrator = EvolutionOrchestrator(
        task_id=task_id,
        termination_config=term_config,
    )

    print(f"  Task ID: {task_id}")
    print(f"  Max generations: {term_config.max_generations}")
    print(f"  Success threshold: {term_config.success_threshold}")
    print()

    # Requirements
    requirements = [
        "Support operators: +, -, *, /",
        "Raise ValueError on division by zero",
        "Raise ValueError on invalid operator",
        "Support negative and floating-point numbers",
    ]

    print("Starting evolution...")
    print("-" * 60)

    try:
        # Run evolution
        result = orchestrator.evolve(
            requirements=requirements,
            test_code=CALCULATOR_TEST_CODE,
        )

        print("-" * 60)
        print("\nEvolution Complete!")
        print()
        print("Summary:")
        print(f"  Total generations: {result.generations}")
        print(f"  Best score: {result.best_score:.2f}")
        print(f"  Success: {'YES' if result.success else 'NO'}")
        print(f"  Termination reason: {result.termination_reason}")
        print()

        # Show history
        print("Generation History:")
        for gen_result in result.history:
            status = "[OK]" if gen_result.score >= 0.9 else "    "
            print(
                f"  {status} Gen {gen_result.generation}: score={gen_result.score:.2f}, "
                f"strategy={gen_result.strategy.get('mutation_type', 'unknown')}"
            )

        print()

        # Show best code
        if result.best_code:
            print("Best Code:")
            print("-" * 60)
            print(result.best_code)
            print("-" * 60)

        # Show strategy stats
        print("\nStrategy Statistics:")
        strategies = orchestrator.strategy_optimizer.get_all_strategies()
        for strat in sorted(strategies, key=lambda x: -x["expected_value"])[:5]:
            print(
                f"  {strat['name']}: expected={strat['expected_value']:.2f}, "
                f"uses={strat['total_uses']}"
            )

    except KeyboardInterrupt:
        print("\n\nEvolution interrupted by user")
    except Exception as e:
        print(f"\n\nEvolution failed: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
