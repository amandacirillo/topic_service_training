"""Pluggable topic-selection strategies.

Each strategy is a plain function: (candidates: list[Topic]) -> Topic | None.
Registering a new strategy is just adding a function and an entry in
STRATEGIES -- callers never need an if/elif chain, and each strategy is
independently unit-testable with a plain list of fake topics.
"""
import random
from typing import Callable, Dict, List, Optional, Protocol


class HasUsageCount(Protocol):
    def usage_count(self) -> int: ...
    created_at: object


def least_used(candidates: List) -> Optional[object]:
    """Pick uniformly at random among the topics tied for the lowest usage count."""
    if not candidates:
        return None
    min_usage = min(c.usage_count() for c in candidates)
    least = [c for c in candidates if c.usage_count() == min_usage]
    return random.choice(least)


def random_strategy(candidates: List) -> Optional[object]:
    """Uniform random selection across all active candidates."""
    if not candidates:
        return None
    return random.choice(candidates)


def sequential(candidates: List) -> Optional[object]:
    """Fewest uses first; ties broken by creation order (oldest first)."""
    if not candidates:
        return None
    return min(candidates, key=lambda c: (c.usage_count(), c.created_at))


def weighted_random(candidates: List) -> Optional[object]:
    """Probability proportional to 1 / (1 + usage_count) -- newer/less-used
    topics are favoured, but nothing is ever fully excluded the way
    `least_used` effectively excludes everything but the minimum."""
    if not candidates:
        return None
    weights = [1.0 / (1 + c.usage_count()) for c in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


STRATEGIES: Dict[str, Callable[[List], Optional[object]]] = {
    'least_used': least_used,
    'random': random_strategy,
    'sequential': sequential,
    'weighted_random': weighted_random,
}

DEFAULT_STRATEGY = 'least_used'


def select(strategy_name: str, candidates: List) -> Optional[object]:
    strategy = STRATEGIES.get(strategy_name)
    if strategy is None:
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. Valid options: {', '.join(STRATEGIES)}"
        )
    return strategy(candidates)
