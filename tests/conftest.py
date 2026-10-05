# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Shared pytest fixtures for the Hydrao Custom integration test suite."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make `custom_components.hydrao_custom` importable without installing it.
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom_components/ for every test automatically."""
    yield


@pytest.fixture
def mock_entry():
    """A minimal MockConfigEntry standing in for the Hydrao config entry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain="hydrao_custom",
        data={
            "address": "AA:BB:CC:DD:EE:FF",
            "name": "Hydrao EEFF",
            "has_connected_once": True,
        },
        options={"min_temp_threshold": 33.0},
    )
    return entry


@pytest.fixture
async def coordinator(hass, mock_entry):
    """A HydraoDataUpdateCoordinator wired to a mock config entry, without
    starting the real BLE loop or bluetooth listener."""
    from custom_components.hydrao_custom.coordinator import (
        HydraoDataUpdateCoordinator,
    )

    mock_entry.add_to_hass(hass)
    coord = HydraoDataUpdateCoordinator(hass, mock_entry)
    mock_entry.runtime_data = coord
    return coord


@pytest.fixture
def bluetooth_loaded(hass):
    """Declare the `bluetooth` dependency as already set up.

    The real component needs system Bluetooth (and USB) support that a test
    environment doesn't have; config and options flows only need Home
    Assistant to consider the dependency loaded."""
    hass.config.components.add("bluetooth")


@pytest.fixture
def mock_setup_entry():
    """Replace the integration's setup, so finishing a config flow doesn't
    start the Bluetooth listener and the BLE loop."""
    with patch(
        "custom_components.hydrao_custom.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@pytest.fixture
async def integration(hass, mock_entry, bluetooth_loaded):
    """Set the whole integration up through Home Assistant, with the
    Bluetooth layer stubbed out.

    The passive listener, the background BLE loop and the RSSI sensor's
    Bluetooth callbacks are replaced, so platforms, entities, services and
    the config entry lifecycle can be exercised for real without a radio.

    Yields a namespace with `entry`, `coordinator`, `unsubscribe` (what the
    coordinator's listener returned), `rssi_callbacks` (the callbacks the RSSI
    sensor registered) and `service_info` (what the RSSI sensor read at
    startup, replaceable before setup through `set_last_info`)."""
    import asyncio
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from homeassistant.config_entries import ConfigEntryState

    from custom_components.hydrao_custom.coordinator import (
        HydraoDataUpdateCoordinator,
    )

    sensor_module = "custom_components.hydrao_custom.sensor"
    unsubscribe = MagicMock(name="unsubscribe_bluetooth_listener")
    rssi_callbacks: list = []

    async def idle_loop(self) -> None:
        await asyncio.Event().wait()

    def register(hass_, callback_, matcher, mode):
        rssi_callbacks.append(callback_)
        return MagicMock(name="unsubscribe_rssi")

    mock_entry.add_to_hass(hass)
    with (
        patch.object(
            HydraoDataUpdateCoordinator,
            "async_start_bluetooth_listener",
            return_value=unsubscribe,
        ),
        patch.object(HydraoDataUpdateCoordinator, "async_run_loop", idle_loop),
        patch(
            f"{sensor_module}.async_last_service_info",
            return_value=MagicMock(rssi=-70),
        ),
        patch(f"{sensor_module}.async_register_callback", side_effect=register),
    ):
        assert await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        yield SimpleNamespace(
            entry=mock_entry,
            coordinator=mock_entry.runtime_data,
            unsubscribe=unsubscribe,
            rssi_callbacks=rssi_callbacks,
        )

        # A test may already have unloaded or removed the entry.
        if (
            hass.config_entries.async_get_entry(mock_entry.entry_id) is not None
            and mock_entry.state is ConfigEntryState.LOADED
        ):
            await hass.config_entries.async_unload(mock_entry.entry_id)
            await hass.async_block_till_done()
