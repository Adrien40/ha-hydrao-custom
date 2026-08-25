# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from itertools import pairwise


def thresholds_strictly_increasing(values: list[int]) -> bool:
    """Return True if each value is strictly greater than the previous one."""
    return all(values[i] < values[i + 1] for i in range(len(values) - 1))


def pairwise_increasing_errors(
    values: dict[str, int | None], order: list[str], error_code: str
) -> dict[str, str]:
    """Check a sequence of optional threshold values pairwise and return a
    {field_key: error_code} mapping for any pair where both values are
    present and the sequence isn't strictly increasing.

    `values` maps each key in `order` to its submitted value (or None if
    not submitted this round). Pairs with a missing value are skipped.
    """
    errors: dict[str, str] = {}
    for prev_key, next_key in pairwise(order):
        prev_val = values.get(prev_key)
        next_val = values.get(next_key)
        if prev_val is not None and next_val is not None and next_val <= prev_val:
            errors[next_key] = error_code
    return errors


def is_valid_temp(temp: float) -> bool:
    """Check if the temperature is within the valid 0-50 C range."""
    return 0 <= temp <= 50
