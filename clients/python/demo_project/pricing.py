# Swarm Lab, Copyright (c) 2026 Joe El Khoury. All rights reserved.
# Licensed under the Swarm Lab License (source-available). See LICENSE and NOTICE.md.
# https://github.com/joeaelkhoury/SwarmLab
"""Order arithmetic; intentionally regressed for the workflow exercise."""


def total(lines):
    """Sum (unit_price, quantity) pairs; empty input totals zero."""
    return sum(price for price, quantity in lines)
