from decimal import Decimal

import pytest

from core import NonFiniteValueError, round_area_ha


def test_rounding_uses_half_up_at_exact_half() -> None:
    assert round_area_ha(Decimal("1.23445")) == Decimal("1.2345")


def test_rounding_below_half_rounds_down() -> None:
    assert round_area_ha(Decimal("1.23444")) == Decimal("1.2344")


def test_rounding_preserves_exactly_four_decimal_places() -> None:
    assert format(round_area_ha(1), "f") == "1.0000"


@pytest.mark.parametrize("invalid_value", ["NaN", "Infinity", "-Infinity"])
def test_rounding_rejects_non_finite_values(invalid_value: str) -> None:
    with pytest.raises(NonFiniteValueError):
        round_area_ha(invalid_value)
