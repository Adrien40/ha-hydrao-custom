# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Locks what users' entity registries depend on: every entity keeps the same
unique id, uses the entity name from translations, and belongs to the device.

Changing a unique id orphans the entity in existing installations (history,
dashboards and automations are lost), so these ids must never change."""

import pytest

from custom_components.hydrao_custom.button import BUTTON_DESCRIPTIONS, HydraoButton
from custom_components.hydrao_custom.const import DOMAIN
from custom_components.hydrao_custom.number import HydraoComfortTempNumber
from custom_components.hydrao_custom.sensor import (
    SENSOR_DESCRIPTIONS,
    HydraoBluetoothStatusSensor,
    HydraoPendingConfigSensor,
    HydraoRealTimeRSSISensor,
    HydraoSensor,
    HydraoSoapingDurationSensor,
)
from custom_components.hydrao_custom.switch import HydraoAutoSyncSwitch

ADDRESS = "AA:BB:CC:DD:EE:FF"

EXPECTED_UNIQUE_IDS = [
    f"{ADDRESS}_{key}"
    for key in (
        "temperature",
        "total_volume",
        "flow_rate",
        "wasted_volume",
        "wasted_volume_total",
        "shower_volume_comfort",
        "shower_volume_comfort_total",
        "shower_volume_raw",
        "shower_duration",
        "shower_duration_comfort",
        "shower_duration_cold",
        "time_to_comfort",
        "threshold_1",
        "threshold_2",
        "threshold_3",
        "threshold_4",
        "bluetooth_status",
        "rssi",
        "soaping_duration",
        "pending_config",
        "end_shower",
        "comfort_temperature",
        "auto_sync_at_comfort",
    )
]


@pytest.fixture
def entities(coordinator, mock_entry):
    """Every entity the integration creates, built as the platforms do."""
    built = [HydraoSensor(coordinator, desc) for desc in SENSOR_DESCRIPTIONS]
    built += [
        HydraoBluetoothStatusSensor(coordinator),
        HydraoRealTimeRSSISensor(coordinator),
        HydraoSoapingDurationSensor(coordinator),
        HydraoPendingConfigSensor(coordinator),
    ]
    built += [HydraoButton(coordinator, desc) for desc in BUTTON_DESCRIPTIONS]
    built += [
        HydraoComfortTempNumber(coordinator, mock_entry),
        HydraoAutoSyncSwitch(coordinator, mock_entry),
    ]
    return built


async def test_unique_ids_never_change(entities):
    assert [entity.unique_id for entity in entities] == EXPECTED_UNIQUE_IDS


async def test_unique_ids_are_unique(entities):
    ids = [entity.unique_id for entity in entities]

    assert len(ids) == len(set(ids))


async def test_every_entity_uses_the_translated_entity_name(entities):
    assert all(entity.has_entity_name is True for entity in entities)


async def test_every_entity_belongs_to_the_device(entities):
    for entity in entities:
        assert entity.device_info["identifiers"] == {(DOMAIN, ADDRESS)}


def test_every_state_class_is_allowed_for_its_device_class():
    """Home Assistant logs a warning at startup, and may drop long-term
    statistics, when a sensor's state class is impossible for its device
    class (e.g. `measurement` with `water`)."""
    from homeassistant.components.sensor.const import DEVICE_CLASS_STATE_CLASSES

    for desc in SENSOR_DESCRIPTIONS:
        allowed = DEVICE_CLASS_STATE_CLASSES.get(desc.device_class)
        if desc.state_class is not None and allowed:
            assert desc.state_class in allowed, desc.key
