# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Diagnostics must be useful for support and must not leak identifiers."""

import json

from custom_components.hydrao_custom.diagnostics import (
    async_get_config_entry_diagnostics,
)

ADDRESS = "AA:BB:CC:DD:EE:FF"


async def test_diagnostics_redact_identifiers(hass, mock_entry, coordinator):
    coordinator.static_data["device_id"] = "0123456789abcdef"
    coordinator.async_set_updated_data(
        {"bluetooth_status": "success", "temperature": 38.5, "flow_rate": 6.0}
    )

    result = await async_get_config_entry_diagnostics(hass, mock_entry)

    dump = json.dumps(result)
    assert ADDRESS not in dump
    assert "Hydrao EEFF" not in dump
    assert "0123456789abcdef" not in dump
    assert result["entry"]["data"]["address"] == "**REDACTED**"
    assert result["coordinator"]["static_data"]["device_id"] == "**REDACTED**"


async def test_diagnostics_expose_the_state_useful_for_support(
    hass, mock_entry, coordinator
):
    coordinator.set_bt_status("success")
    coordinator.last_valid_data["temperature"] = 38.5
    coordinator.async_set_updated_data(coordinator.last_valid_data)

    result = await async_get_config_entry_diagnostics(hass, mock_entry)

    state = result["coordinator"]
    assert state["bluetooth_status"] == "success"
    assert state["min_temp_threshold"] == 33.0
    assert state["data"]["temperature"] == 38.5
    assert state["seconds_since_last_seen"] is None
    assert state["pending"]["new_shower"] is False
    assert result["entry"]["options"] == {"min_temp_threshold": 33.0}


async def test_diagnostics_report_time_since_last_seen(hass, mock_entry, coordinator):
    import time

    coordinator.last_seen_time = time.monotonic() - 12

    result = await async_get_config_entry_diagnostics(hass, mock_entry)

    assert 11 <= result["coordinator"]["seconds_since_last_seen"] <= 14
