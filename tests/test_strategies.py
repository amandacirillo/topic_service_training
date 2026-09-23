import datetime
from dataclasses import dataclass

import pytest

from app.strategies import (
    STRATEGIES,
    least_used,
    random_strategy,
    select,
    sequential,
    weighted_random,
)


@dataclass
class FakeTopic:
    name: str
    uses: int
    created_at: datetime.datetime

    def usage_count(self) -> int:
        return self.uses


def make_topics():
    base = datetime.datetime(2024, 1, 1)
    return [
        FakeTopic('a', uses=5, created_at=base),
        FakeTopic('b', uses=1, created_at=base + datetime.timedelta(days=1)),
        FakeTopic('c', uses=1, created_at=base + datetime.timedelta(days=2)),
        FakeTopic('d', uses=8, created_at=base + datetime.timedelta(days=3)),
    ]


def test_least_used_returns_none_for_empty_list():
    assert least_used([]) is None


def test_least_used_only_picks_among_minimum_usage():
    topics = make_topics()
    for _ in range(20):
        chosen = least_used(topics)
        assert chosen.name in ('b', 'c')


def test_random_strategy_returns_none_for_empty_list():
    assert random_strategy([]) is None


def test_random_strategy_can_pick_any_candidate():
    topics = make_topics()
    seen = {random_strategy(topics).name for _ in range(200)}
    assert seen == {'a', 'b', 'c', 'd'}


def test_sequential_picks_lowest_usage_then_oldest():
    topics = make_topics()
    chosen = sequential(topics)
    assert chosen.name == 'b'  # tied with 'c' on usage, but created first


def test_sequential_empty_list_returns_none():
    assert sequential([]) is None


def test_weighted_random_favors_less_used_topics():
    topics = make_topics()
    counts = {}
    for _ in range(500):
        chosen = weighted_random(topics)
        counts[chosen.name] = counts.get(chosen.name, 0) + 1
    # 'b' and 'c' (usage=1) should be picked far more often than 'd' (usage=8)
    assert counts.get('b', 0) + counts.get('c', 0) > counts.get('d', 0)


def test_weighted_random_empty_list_returns_none():
    assert weighted_random([]) is None


def test_select_dispatches_to_named_strategy():
    topics = make_topics()
    chosen = select('sequential', topics)
    assert chosen.name == 'b'


def test_select_unknown_strategy_raises():
    with pytest.raises(ValueError):
        select('not_a_real_strategy', make_topics())


def test_all_registered_strategies_handle_empty_list():
    for name, strategy in STRATEGIES.items():
        assert strategy([]) is None, f'{name} should return None for an empty candidate list'
