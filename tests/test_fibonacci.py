import pytest

from fibonacci.calculator import calculate_fibonacci_levels, calculate_named_fibonacci_levels


def test_low_to_high_uses_full_wick_range() -> None:
    result = calculate_fibonacci_levels(110.0, 90.0, [0, 0.25, 0.5, 1])
    assert result == {0.0: 90.0, 0.25: 95.0, 0.5: 100.0, 1.0: 110.0}


def test_high_to_low_reverses_the_calculation() -> None:
    result = calculate_fibonacci_levels(110.0, 90.0, [0, 0.25, 0.5, 1], "high_to_low")
    assert result == {0.0: 110.0, 0.25: 105.0, 0.5: 100.0, 1.0: 90.0}


def test_extension_level_is_supported() -> None:
    assert calculate_fibonacci_levels(110.0, 90.0, [1.5]) == {1.5: 120.0}


def test_invalid_wick_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        calculate_fibonacci_levels(90.0, 110.0, [0.5])


def test_equal_wicks_are_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        calculate_fibonacci_levels(100.0, 100.0, [0.5])


def test_invalid_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="direction"):
        calculate_fibonacci_levels(110.0, 90.0, [0.5], "sideways")


def test_invalid_fibonacci_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid Fibonacci"):
        calculate_fibonacci_levels(110.0, 90.0, ["not-a-level"])


def test_named_levels_keep_the_strategy_labels() -> None:
    result = calculate_named_fibonacci_levels(110.0, 90.0, {"E3": 0.0, "E4": -1.0}, "high_to_low")
    assert result == {"E3": 110.0, "E4": 130.0}
