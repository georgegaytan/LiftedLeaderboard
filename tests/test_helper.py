from src.utils.helper import level_to_rank


def test_level_to_rank_minimum_is_bronze():
    assert level_to_rank(0) == 'Bronze'
    assert level_to_rank(-5) == 'Bronze'


def test_level_to_rank_thresholds():
    assert level_to_rank(1) == 'Bronze'
    assert level_to_rank(5) == 'Iron'
    assert level_to_rank(10) == 'Steel'
    assert level_to_rank(99) == 'Max'
