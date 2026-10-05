# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the duration sensors: units, nullable values, restore
conversion from the former minutes-based state, and translations."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from helpers import make_frames
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorExtraStoredData,
)
from homeassistant.const import EntityCategory, UnitOfTime

from custom_components.hydrao_custom.sensor import (
    SENSOR_DESCRIPTIONS,
    HydraoSensor,
)

INTEGRATION_DIR = Path(__file__).parent.parent / "custom_components" / "hydrao_custom"

DURATION_KEYS = ("shower_duration", "shower_duration_comfort", "shower_duration_cold")


def description(key):
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


def make_sensor(coordinator, key):
    return HydraoSensor(coordinator, description(key))


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", DURATION_KEYS)
def test_session_durations_are_seconds_displayed_as_minutes(key):
    desc = description(key)

    assert desc.device_class == SensorDeviceClass.DURATION
    assert desc.native_unit_of_measurement == UnitOfTime.SECONDS
    assert desc.suggested_unit_of_measurement == UnitOfTime.MINUTES


def test_time_to_comfort_is_a_duration_in_seconds():
    desc = description("time_to_comfort")

    assert desc.device_class == SensorDeviceClass.DURATION
    assert desc.native_unit_of_measurement == UnitOfTime.SECONDS


async def test_every_duration_sensor_reports_seconds_from_live_data(coordinator):
    vol, dur, tmp = make_frames(total=100, shower=50, duration_ticks=3000, temp_c=35.0)
    coordinator._process_live_data(vol, dur, tmp, None)

    assert make_sensor(coordinator, "shower_duration").native_value == 60.0
    assert make_sensor(coordinator, "shower_duration_comfort").native_value == 60.0
    assert make_sensor(coordinator, "shower_duration_cold").native_value == 0.0


# ---------------------------------------------------------------------------
# Visibility: the two extra sensors are opt-in diagnostics
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", ["shower_duration_cold", "time_to_comfort"])
async def test_extra_duration_sensors_are_disabled_diagnostics(coordinator, key):
    """Cold duration and time to comfort overlap with existing sensors, so
    they are created disabled and filed under diagnostics: opt-in only."""
    sensor = make_sensor(coordinator, key)

    assert sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert sensor.entity_registry_enabled_default is False


@pytest.mark.parametrize("key", ["shower_duration", "shower_duration_comfort"])
async def test_main_duration_sensors_stay_visible(coordinator, key):
    """The two durations that already existed must not be hidden by the
    addition of the new ones."""
    sensor = make_sensor(coordinator, key)

    assert sensor.entity_category is None
    assert sensor.entity_registry_enabled_default is True


# ---------------------------------------------------------------------------
# time_to_comfort: None is a real answer, not a missing value
# ---------------------------------------------------------------------------


async def test_time_to_comfort_none_is_not_replaced_by_a_restored_value(coordinator):
    sensor = make_sensor(coordinator, "time_to_comfort")
    sensor._restored_value = 99.0
    coordinator.data = {"time_to_comfort": None}

    assert sensor.native_value is None


async def test_time_to_comfort_falls_back_to_restored_value_before_any_data(
    coordinator,
):
    sensor = make_sensor(coordinator, "time_to_comfort")
    sensor._restored_value = 99.0
    coordinator.data = {}

    assert sensor.native_value == 99.0


async def test_time_to_comfort_reports_the_live_value(coordinator):
    sensor = make_sensor(coordinator, "time_to_comfort")
    coordinator.data = {"time_to_comfort": 86}

    assert sensor.native_value == 86.0
    assert isinstance(sensor.native_value, float)


# ---------------------------------------------------------------------------
# Restoring a value stored before the switch from minutes to seconds
# ---------------------------------------------------------------------------


async def test_restored_minutes_are_converted_to_seconds(coordinator):
    sensor = make_sensor(coordinator, "shower_duration")

    assert sensor._convert_restored_duration(2.0, "min") == pytest.approx(120.0)


@pytest.mark.parametrize(
    ("value", "unit"),
    [
        (120.0, "s"),  # already native
        (120.0, None),  # unknown stored unit
        (None, "min"),  # nothing to convert
        ("not a number", "min"),  # unconvertible value
        (120.0, "furlongs"),  # unknown unit
    ],
)
async def test_restored_value_left_untouched_when_it_cannot_be_converted(
    coordinator, value, unit
):
    sensor = make_sensor(coordinator, "shower_duration")

    assert sensor._convert_restored_duration(value, unit) == value


async def test_non_duration_sensors_never_convert_restored_values(coordinator):
    sensor = make_sensor(coordinator, "temperature")

    assert sensor._convert_restored_duration(2.0, "min") == 2.0


async def test_added_to_hass_restores_old_minutes_as_seconds(coordinator):
    """End to end: a state saved as 2.5 min must come back as 150 s, not as
    2.5 s, until the first live reading arrives."""
    sensor = make_sensor(coordinator, "shower_duration_comfort")
    sensor.async_get_last_sensor_data = AsyncMock(
        return_value=SensorExtraStoredData(
            native_value=2.5, native_unit_of_measurement="min"
        )
    )

    await sensor.async_added_to_hass()

    assert sensor.native_value == pytest.approx(150.0)


# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", ["strings.json", "translations/en.json", "translations/fr.json"]
)
def test_every_sensor_translation_key_has_a_name(path):
    entities = json.loads((INTEGRATION_DIR / path).read_text(encoding="utf-8"))[
        "entity"
    ]["sensor"]

    missing = [
        d.translation_key
        for d in SENSOR_DESCRIPTIONS
        if d.translation_key and d.translation_key not in entities
    ]
    assert missing == []
