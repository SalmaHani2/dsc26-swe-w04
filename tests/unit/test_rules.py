
import pytest

from nour_transfers.rules import (
    days_of_cover,
    priority,
    can_transfer,
)


# days_of_cover

def test_days_of_cover_calculates_float():
    result = days_of_cover(100, 20)

    assert result == 5.0
    assert isinstance(result, float)


def test_days_of_cover_returns_none_when_sales_are_zero():
    assert days_of_cover(100, 0) is None


def test_days_of_cover_returns_none_for_zero_stock_and_sales():
    assert days_of_cover(0, 0) is None


@pytest.mark.parametrize(
    "stock, sales",
    [
        (-1, 10),
        (10, -1),
        (-1, -1),
    ],
)
def test_days_of_cover_rejects_negative_inputs(stock, sales):
    with pytest.raises(ValueError):
        days_of_cover(stock, sales)


# priority

def test_priority_is_urgent_for_chronic_item_below_three_days():
    assert priority(True, 2.9) == "urgent"


def test_priority_is_not_urgent_for_non_chronic_item_below_three_days():
    assert priority(False, 2.9) == "high"


def test_priority_at_exactly_three_days_is_high():
    assert priority(True, 3.0) == "high"


def test_priority_below_seven_days_is_high():
    assert priority(False, 6.9) == "high"


def test_priority_at_exactly_seven_days_is_normal():
    assert priority(True, 7.0) == "normal"


def test_priority_none_cover_is_normal():
    assert priority(True, None) == "normal"


# can_transfer

def test_can_transfer_when_remaining_stock_equals_reserve():
    assert can_transfer(10, 5, 5) is True


def test_can_transfer_rejects_zero_quantity():
    assert can_transfer(10, 0, 5) is False


def test_can_transfer_rejects_quantity_below_one():
    assert can_transfer(10, -1, 5) is False


def test_can_transfer_rejects_transfer_below_reserve():
    assert can_transfer(10, 6, 5) is False


def test_can_transfer_returns_real_bool():
    result = can_transfer(10, 5, 5)

    assert type(result) is bool
