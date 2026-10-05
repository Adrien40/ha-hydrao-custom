# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the config flow: manual setup by the user and Bluetooth discovery.

Every way the flow can be started is covered: the happy path, each error with
a recovery, and the refusal to add the same device twice.
"""

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hydrao_custom.const import DOMAIN

ADDRESS = "AA:BB:CC:DD:EE:FF"

pytestmark = pytest.mark.usefixtures("bluetooth_loaded")


def make_service_info(
    address: str = ADDRESS, name: str | None = "HYDRAO-1234"
) -> BluetoothServiceInfoBleak:
    """A Bluetooth advertisement as Home Assistant hands it to a discovery flow."""
    device = BLEDevice(address, name, {})
    advertisement = AdvertisementData(
        local_name=name,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        tx_power=None,
        rssi=-60,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak.from_device_and_advertisement_data(
        device, advertisement, "local", 0.0, True
    )


def existing_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS, "name": "Hydrao EEFF"},
    )


async def start_user_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def start_discovery_flow(hass, service_info):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=service_info,
    )


def default_of(result, field):
    """The pre-filled value of a field of the form shown by `result`."""
    for marker in result["data_schema"].schema:
        if marker.schema == field:
            return marker.default()
    raise AssertionError(f"{field} is not in the form")


# ---------------------------------------------------------------------------
# Started by the user
# ---------------------------------------------------------------------------


async def test_user_flow_creates_an_entry(hass, mock_setup_entry):
    result = await start_user_flow(hass)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff", "min_temp_threshold": 35.0},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hydrao EEFF"
    assert result["data"] == {CONF_ADDRESS: ADDRESS, "name": "Hydrao EEFF"}
    assert result["options"] == {"min_temp_threshold": 35.0}
    assert result["result"].unique_id == ADDRESS
    mock_setup_entry.assert_awaited_once()


@pytest.mark.parametrize(
    "typed",
    ["AA:BB:CC:DD:EE:FF", "aa:bb:cc:dd:ee:ff", "aa-bb-cc-dd-ee-ff", "aabbccddeeff"],
)
async def test_user_flow_accepts_the_usual_mac_notations(hass, typed):
    result = await start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: typed, "min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDRESS] == ADDRESS


async def test_user_flow_rejects_an_invalid_mac_then_recovers(hass):
    result = await start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: "not-a-mac", "min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_mac"}
    # what the user typed is kept in the form so they can correct it
    assert default_of(result, CONF_ADDRESS) == "not-a-mac"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, "min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_user_flow_rejects_an_out_of_range_temperature_then_recovers(hass):
    result = await start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, "min_temp_threshold": 60.0}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"min_temp_threshold": "min_temp_out_of_range"}
    assert default_of(result, "min_temp_threshold") == 60.0

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS, "min_temp_threshold": 35.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["options"] == {"min_temp_threshold": 35.0}


async def test_user_flow_reports_both_errors_at_once(hass):
    result = await start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: "nope", "min_temp_threshold": -5.0}
    )

    assert result["errors"] == {
        "base": "invalid_mac",
        "min_temp_threshold": "min_temp_out_of_range",
    }


@pytest.mark.parametrize("typed", [ADDRESS, "aa-bb-cc-dd-ee-ff"])
async def test_user_flow_aborts_when_the_device_is_already_configured(hass, typed):
    existing_entry().add_to_hass(hass)
    result = await start_user_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: typed, "min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# ---------------------------------------------------------------------------
# Started by Bluetooth discovery
# ---------------------------------------------------------------------------


async def test_discovery_flow_creates_an_entry(hass, mock_setup_entry):
    result = await start_discovery_flow(hass, make_service_info())

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["description_placeholders"] == {
        "name": "HYDRAO-1234",
        "address": ADDRESS,
    }
    flow = hass.config_entries.flow.async_get(result["flow_id"])
    assert flow["context"]["title_placeholders"] == {"name": "HYDRAO-1234"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_temp_threshold": 34.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "HYDRAO-1234"
    assert result["data"] == {CONF_ADDRESS: ADDRESS, "name": "HYDRAO-1234"}
    assert result["options"] == {"min_temp_threshold": 34.0}
    assert result["result"].unique_id == ADDRESS
    mock_setup_entry.assert_awaited_once()


async def test_discovery_flow_names_a_nameless_device_after_its_address(hass):
    info = make_service_info()
    info.name = ""  # an advertisement that carries no name at all

    result = await start_discovery_flow(hass, info)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hydrao EEFF"
    assert result["data"]["name"] == "Hydrao EEFF"


async def test_discovery_flow_rejects_an_out_of_range_temperature_then_recovers(hass):
    result = await start_discovery_flow(hass, make_service_info())

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_temp_threshold": 51.0}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] == {"min_temp_threshold": "min_temp_out_of_range"}
    assert default_of(result, "min_temp_threshold") == 51.0

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"min_temp_threshold": 33.0}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY


async def test_discovery_flow_aborts_when_the_device_is_already_configured(hass):
    existing_entry().add_to_hass(hass)

    result = await start_discovery_flow(hass, make_service_info())

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
