import pytest

from strategy.e_levels import ELevels, calculate_e_levels


def test_e_levels_are_explicit_placeholders_until_formula_is_supplied() -> None:
    assert calculate_e_levels(high=110.0, low=90.0) == ELevels(None, None, None)


def test_e_levels_reject_invalid_wick_range() -> None:
    with pytest.raises(ValueError, match="high"):
        calculate_e_levels(high=90.0, low=110.0)
