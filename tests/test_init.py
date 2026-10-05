# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Lifecycle of the config entry: setup, options reload, unload, removal."""

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er

from custom_components.hydrao_custom.const import DOMAIN
from custom_components.hydrao_custom.coordinator import HydraoDataUpdateCoordinator

# 16 sensors from the descriptions + 4 dedicated ones, 1 button, 1 number, 1 switch.
EXPECTED_ENTITY_COUNT = 23


async def test_setup_loads_the_entry_and_exposes_the_coordinator(integration):
    assert integration.entry.state is ConfigEntryState.LOADED
    assert isinstance(integration.entry.runtime_data, HydraoDataUpdateCoordinator)
    assert integration.coordinator.config_entry is integration.entry


async def test_setup_creates_every_entity(hass, integration):
    registry = er.async_get(hass)

    entries = er.async_entries_for_config_entry(registry, integration.entry.entry_id)

    assert len(entries) == EXPECTED_ENTITY_COUNT
    assert {entry.platform for entry in entries} == {DOMAIN}
    assert {entry.domain for entry in entries} == {
        "sensor",
        "button",
        "number",
        "switch",
    }


async def test_setup_starts_the_background_ble_loop(integration):
    tasks = [
        task
        for task in integration.entry._background_tasks
        if "hydrao_ble_loop" in (task.get_name() or "")
    ]

    assert len(tasks) == 1
    assert not tasks[0].done()


async def test_changing_the_options_reaches_the_coordinator(hass, integration):
    hass.config_entries.async_update_entry(
        integration.entry,
        options={"min_temp_threshold": 39.0, "auto_sync_at_comfort": True},
    )
    await hass.async_block_till_done()

    assert integration.coordinator.min_temp_threshold == 39.0
    assert integration.coordinator.auto_sync_at_comfort is True


async def test_unload_stops_everything_and_unloads_the_platforms(hass, integration):
    assert await hass.config_entries.async_unload(integration.entry.entry_id)
    await hass.async_block_till_done()

    assert integration.entry.state is ConfigEntryState.NOT_LOADED
    integration.unsubscribe.assert_called_once()
    assert not any(
        not task.done() and "hydrao_ble_loop" in (task.get_name() or "")
        for task in integration.entry._background_tasks
    )


async def test_entry_can_be_reloaded(hass, integration):
    assert await hass.config_entries.async_reload(integration.entry.entry_id)
    await hass.async_block_till_done()

    assert integration.entry.state is ConfigEntryState.LOADED
    assert integration.entry.runtime_data is not integration.coordinator


async def test_removing_the_entry_is_logged(hass, integration, caplog):
    with caplog.at_level(logging.INFO):
        await hass.config_entries.async_remove(integration.entry.entry_id)
        await hass.async_block_till_done()

    assert "Successfully removed Hydrao integration" in caplog.text
    assert hass.config_entries.async_get_entry(integration.entry.entry_id) is None
