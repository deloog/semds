"""
SEMDS Strategy Optimizer - Phase 3

Thompson Sampling strategy optimizer using multi-armed bandit algorithm.
"""

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class StrategyArm:
    """
    Thompson Sampling strategy arm.

    Uses Beta distribution for balancing exploration and exploitation.

    Attributes:
        key: Unique identifier for strategy combination
        name: Human-readable name
        alpha: Beta distribution alpha (successes + prior)
        beta: Beta distribution beta (failures + prior)
        total_uses: Total number of times used
        total_reward: Sum of all rewards (scores)
    """

    key: str
    name: str = ""
    alpha: float = 1.0
    beta: float = 1.0
    total_uses: int = 0
    total_reward: float = 0.0

    def sample(self) -> float:
        """
        Sample from Beta distribution.

        Returns:
            float: Random value between 0 and 1
        """
        # Use random.betavariate for Beta distribution sampling
        return random.betavariate(self.alpha, self.beta)

    def update(self, success: bool, reward: float = 0.0) -> None:
        """
        Update arm based on result.

        Args:
            success: Whether the strategy succeeded
            reward: Reward value (e.g., score)
        """
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0

        self.total_uses += 1
        self.total_reward += reward

    def expected_value(self) -> float:
        """
        Calculate expected value.

        Returns:
            float: Expected reward (alpha / (alpha + beta))
        """
        return self.alpha / (self.alpha + self.beta)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyArm":
        """Create from dictionary."""
        return cls(**data)


class StrategyOptimizer:
    """
    Thompson Sampling strategy optimizer.

    Manages a set of strategy arms and selects the best one
    using Thompson Sampling algorithm.

    Example:
        >>> optimizer = StrategyOptimizer("task_123")
        >>> strategy = optimizer.select_strategy()
        >>> # Use strategy...
        >>> optimizer.update_strategy(strategy['key'], success=True, reward=0.95)
    """

    # Strategy configuration space
    STRATEGY_DIMENSIONS: Dict[str, List[Any]] = {
        "mutation_type": ["conservative", "aggressive", "hybrid"],
        "validation_mode": ["lightweight", "comprehensive"],
        "temperature": [0.2, 0.5, 0.8],
    }

    def __init__(self, task_id: str, storage_dir: str = "storage/strategies") -> None:
        """
        Initialize strategy optimizer.

        Args:
            task_id: Task identifier for isolation
            storage_dir: Directory to store strategy state
        """
        self.task_id = task_id
        self.storage_path = Path(storage_dir) / f"{task_id}_strategies.json"
        self.arms: Dict[str, StrategyArm] = {}

        self._initialize_arms()
        self._load_state()

    def _initialize_arms(self) -> None:
        """Initialize all strategy arms."""
        # Generate all combinations
        for mutation in self.STRATEGY_DIMENSIONS["mutation_type"]:
            for validation in self.STRATEGY_DIMENSIONS["validation_mode"]:
                for temp in self.STRATEGY_DIMENSIONS["temperature"]:
                    # Use JSON format for key (as expected by tests)
                    strategy_dict = {
                        "mutation_type": mutation,
                        "validation_mode": validation,
                        "generation_temperature": temp,
                    }
                    key = json.dumps(strategy_dict, sort_keys=True)
                    name = (
                        f"{mutation.title()} mutation, {validation} validation, "
                        f"T={temp}"
                    )

                    if key not in self.arms:
                        self.arms[key] = StrategyArm(
                            key=key,
                            name=name,
                            alpha=1.0,  # Prior: 1 success
                            beta=1.0,  # Prior: 1 failure
                        )

    def select_strategy(self) -> Dict[str, Any]:
        """
        Select strategy using Thompson Sampling.

        Samples from each arm's Beta distribution and selects
        the arm with highest sample value.

        Returns:
            Dict with strategy configuration
        """
        # Sample from each arm
        samples = {key: arm.sample() for key, arm in self.arms.items()}

        # Select arm with highest sample
        selected_key = max(samples, key=lambda k: samples[k])
        selected_arm = self.arms[selected_key]

        # Parse strategy key (JSON format)
        strategy_dict = json.loads(selected_key)

        # Return only the fields expected by tests
        return {
            "mutation_type": strategy_dict["mutation_type"],
            "validation_mode": strategy_dict["validation_mode"],
            "generation_temperature": strategy_dict["generation_temperature"],
        }

    def _strategy_to_key(self, strategy: Dict[str, Any]) -> str:
        """
        Convert strategy dict to key string.

        Uses JSON with sorted keys for deterministic output.

        Args:
            strategy: Strategy dictionary

        Returns:
            JSON string key
        """
        return json.dumps(strategy, sort_keys=True)

    def _key_to_strategy(self, key: str) -> Dict[str, Any]:
        """
        Convert key string back to strategy dict.

        Args:
            key: JSON string key

        Returns:
            Strategy dictionary
        """
        return json.loads(key)

    def update_strategy(self, key: str, success: bool, reward: float = 0.0) -> None:
        """
        Update strategy arm based on result.

        Args:
            key: Strategy key
            success: Whether the strategy succeeded
            reward: Reward value (e.g., score)
        """
        if key in self.arms:
            self.arms[key].update(success, reward)
            self._save_state()

    def report_result(
        self, strategy: Dict[str, Any], success: bool, score: float = 0.0
    ) -> None:
        """
        Report generation result to update strategy.

        Alias for update_strategy to match Orchestrator interface.

        Args:
            strategy: Strategy dict or key string
            success: Whether generation succeeded
            score: Score value as reward
        """
        if isinstance(strategy, dict):
            # If dict doesn't have 'key', generate it from the dict
            key = strategy.get("key") or self._strategy_to_key(strategy)
        else:
            key = strategy
        if key:
            self.update_strategy(key, success, score)

    def get_best_strategy(self) -> Dict[str, Any]:
        """
        Get strategy with highest expected value.

        Returns:
            Dict with best strategy configuration
        """
        best_key = max(self.arms.keys(), key=lambda k: self.arms[k].expected_value())
        best_arm = self.arms[best_key]

        # Parse strategy key (JSON format)
        strategy_dict = json.loads(best_key)
        return {
            "key": best_key,
            "name": best_arm.name,
            "mutation_type": strategy_dict["mutation_type"],
            "validation_mode": strategy_dict["validation_mode"],
            "temperature": strategy_dict["generation_temperature"],
            "expected_value": best_arm.expected_value(),
            "total_uses": best_arm.total_uses,
            "total_reward": best_arm.total_reward,
        }

    def get_arm_stats(self) -> List[Dict[str, Any]]:
        """
        Get all strategy arm statistics.

        Returns:
            List of arm stat dicts with keys: key, alpha, beta, uses, expected
        """
        return [
            {
                "key": key,
                "alpha": arm.alpha,
                "beta": arm.beta,
                "uses": arm.total_uses,
                "expected": arm.expected_value(),
            }
            for key, arm in sorted(self.arms.items())
        ]

    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        Get all strategies with their stats.

        Returns:
            List of strategy dicts
        """
        return [
            {
                "key": key,
                "name": arm.name,
                "expected_value": arm.expected_value(),
                "total_uses": arm.total_uses,
                "alpha": arm.alpha,
                "beta": arm.beta,
            }
            for key, arm in sorted(self.arms.items())
        ]

    def _save_state(self) -> None:
        """Save strategy state to file."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "task_id": self.task_id,
                "updated_at": datetime.now().isoformat(),
                "arms": {key: arm.to_dict() for key, arm in self.arms.items()},
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to save strategy state: {e}")

    def _load_state(self) -> None:
        """Load strategy state from file."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Restore arm states
            for key, arm_data in data.get("arms", {}).items():
                if key in self.arms:
                    self.arms[key] = StrategyArm.from_dict(arm_data)

        except Exception as e:
            print(f"[WARN] Failed to load strategy state: {e}")


# Convenience function
def create_strategy_optimizer(task_id: str) -> StrategyOptimizer:
    """
    Create a strategy optimizer for a task.

    Args:
        task_id: Task identifier

    Returns:
        StrategyOptimizer instance
    """
    return StrategyOptimizer(task_id)
