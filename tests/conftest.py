# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Shared pytest fixtures for the Hydrao Custom integration test suite."""

import sys
from pathlib import Path

import pytest

# Make `custom_components.hydrao_custom` importable without installing it.
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- HA version compatibility shim -----------------------------------------
# The pinned test dependency (homeassistant==2025.1.4, the newest available
# through this sandbox's package mirror) predates
# async_clear_advertisement_history(), which the integration relies on and
# which ships in newer Home Assistant releases. This is a test-environment
# gap, not something to change in the integration: add a no-op stand-in so
# coordinator.py can be imported and exercised here. When running the suite
# against a real, up-to-date Home Assistant install this shim is inert
# (hasattr short-circuits it).
import homeassistant.components.bluetooth as _ha_bluetooth

if not hasattr(_ha_bluetooth, "async_clear_advertisement_history"):

    def _async_clear_advertisement_history_stub(hass, address):
        return None

    _ha_bluetooth.async_clear_advertisement_history = (
        _async_clear_advertisement_history_stub
    )
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
