"""Order arithmetic; intentionally regressed for the workflow exercise."""


def total(lines):
    """Sum (unit_price, quantity) pairs; empty input totals zero."""
    return sum(price for price, quantity in lines)
