# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the soaping-duration bounds enforced by the options flow."""

import pytest
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hydrao_custom.config_flow import HydraoOptionsFlowHandler
from custom_components.hydrao_custom.const import (
    DOMAIN,
    MAX_SOAPING_DURATION,
    MIN_SOAPING_DURATION,
)


@pytest.fixture
def entry():
    """An entry whose device configuration is already known, as on an
    installation that has connected at least once (thresholds and colors
    are what the options form is built from)."""
    options = {"min_temp_threshold": 33.0}
    for i, (litres, color) in enumerate(
        [(10, [0, 255, 0]), (20, [0, 0, 255]), (30, [255, 0, 255]), (40, [255, 0, 0])],
        start=1,
    ):
        options[f"threshold_{i}"] = litres
        options[f"threshold_{i}_color"] = color
    return MockConfigEntry(
        domain=DOMAIN,
        data={"address": "AA:BB:CC:DD:EE:FF", "has_connected_once": True},
        options=options,
    )


async def submit(hass, entry, user_input):
    """Run the options flow's init step with the given submitted values."""
    entry.add_to_hass(hass)
    flow = HydraoOptionsFlowHandler()
    flow.hass = hass
    flow.handler = entry.entry_id
    return await flow.async_step_init(user_input)


@pytest.mark.parametrize(
    "value", [MIN_SOAPING_DURATION - 1, MAX_SOAPING_DURATION + 1, 0, 70_000]
)
async def test_out_of_range_soaping_duration_is_rejected(hass, entry, value):
    result = await submit(hass, entry, {"soaping_duration": value})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["soaping_duration"] == "soaping_duration_out_of_range"
    assert result["errors"]["base"] == "soaping_duration_out_of_range"


@pytest.mark.parametrize("value", [MIN_SOAPING_DURATION, 180, MAX_SOAPING_DURATION])
async def test_in_range_soaping_duration_is_accepted(hass, entry, value):
    result = await submit(hass, entry, {"soaping_duration": value})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["soaping_duration"] == value
