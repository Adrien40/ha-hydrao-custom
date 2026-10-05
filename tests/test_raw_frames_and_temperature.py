# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Raw frames kept for support, and the handling of temperatures that cannot
be real.

Some device revisions may encode the temperature (and maybe the volumes) with
another resolution than the one the decoding was built on. A reading far
outside what water can be must not be counted as scalding hot water, and the
raw bytes must be available to work out the right decoding."""

import json
import logging
from pathlib import Path

import pytest
from helpers import make_frames

from custom_components.hydrao_custom.const import (
    ISSUE_TRACKER_URL,
    MAX_WATER_TEMP,
    MIN_WATER_TEMP,
)
from custom_components.hydrao_custom.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.hydrao_custom.sensor import SENSOR_DESCRIPTIONS, HydraoSensor
from custom_components.hydrao_custom.util import is_plausible_water_temp

INTEGRATION_DIR = Path(__file__).parent.parent / "custom_components" / "hydrao_custom"


def frames(shower=50, ticks=3000, temp=36.0):
    return make_frames(total=500, shower=shower, duration_ticks=ticks, temp_c=temp)


# ---------------------------------------------------------------------------
# is_plausible_water_temp
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("temp", [MIN_WATER_TEMP, 8.5, 38.0, 65.0, MAX_WATER_TEMP])
def test_real_water_temperatures_are_plausible(temp):
    assert is_plausible_water_temp(temp) is True


@pytest.mark.parametrize("temp", [-0.5, 100.5, 460.0, 920.0, 32767.5])
def test_impossible_temperatures_are_not_plausible(temp):
    assert is_plausible_water_temp(temp) is False


def test_the_issue_tracker_constant_matches_the_manifest():
    manifest = json.loads((INTEGRATION_DIR / "manifest.json").read_text())

    assert ISSUE_TRACKER_URL == manifest["issue_tracker"]


# ---------------------------------------------------------------------------
# Raw frames
# ---------------------------------------------------------------------------


async def test_raw_frames_are_kept_as_hex(coordinator):
    vol, dur, temp = frames()

    coordinator._process_live_data(vol, dur, temp, bytearray([0x2C, 0x01]))

    assert coordinator.last_raw_frames == {
        "volume": vol.hex(),
        "duration": dur.hex(),
        "temperature": temp.hex(),
        "flow": "2c01",
    }


async def test_a_missing_flow_frame_is_recorded_as_none(coordinator):
    coordinator._process_live_data(*frames(), None)

    assert coordinator.last_raw_frames["flow"] is None


async def test_malformed_frames_are_recorded_too(coordinator):
    """A frame of the wrong size is exactly what support needs to see."""
    coordinator._process_live_data(bytearray(2), bytearray(1), bytearray(1), None)

    assert coordinator.last_raw_frames["volume"] == "0000"
    assert coordinator.last_raw_frames["duration"] == "00"
    assert coordinator.data is None


async def test_raw_frames_are_logged_only_when_they_change(coordinator, caplog):
    with caplog.at_level(logging.DEBUG):
        coordinator._process_live_data(*frames(shower=50), None)
        coordinator._process_live_data(*frames(shower=50), None)
        coordinator._process_live_data(*frames(shower=60), None)

    logged = [r for r in caplog.records if "Raw BLE frames" in r.getMessage()]
    assert len(logged) == 2


async def test_diagnostics_include_the_raw_frames(hass, mock_entry, coordinator):
    vol, dur, temp = frames()
    coordinator._process_live_data(vol, dur, temp, None)

    result = await async_get_config_entry_diagnostics(hass, mock_entry)

    assert result["coordinator"]["raw_frames"] == {
        "volume": vol.hex(),
        "duration": dur.hex(),
        "temperature": temp.hex(),
        "flow": None,
    }


# ---------------------------------------------------------------------------
# Temperatures that cannot be real
# ---------------------------------------------------------------------------


async def test_an_implausible_temperature_is_reported_as_unknown(coordinator):
    coordinator._process_live_data(*frames(temp=920.0), None)

    assert coordinator.last_valid_data["temperature"] is None


async def test_an_implausible_temperature_is_not_counted_as_comfortable_water(
    coordinator,
):
    coordinator._process_live_data(*frames(shower=50, temp=920.0), None)

    assert coordinator.session_shower_volume_comfort == 0.0
    assert coordinator.lifetime_shower_volume_comfort_total == 0.0
    assert coordinator.session_wasted_volume == 0.0
    assert coordinator.session_shower_duration_comfort == 0.0


async def test_volume_duration_and_total_still_work_without_a_usable_temperature(
    coordinator,
):
    coordinator._process_live_data(*frames(shower=50, ticks=3000, temp=920.0), None)

    data = coordinator.last_valid_data
    assert data["raw"]["shower_volume_raw"] == 50.0
    assert data["raw"]["shower_duration"] == 60.0
    assert data["total_volume"] == 500.0


async def test_the_implausible_temperature_is_warned_about_once(coordinator, caplog):
    coordinator.static_data["firmware"] = "20200403"
    coordinator.static_data["hardware"] = "8"
    vol, dur, temp = frames(temp=920.0)

    with caplog.at_level(logging.WARNING):
        coordinator._process_live_data(vol, dur, temp, None)
        coordinator._process_live_data(vol, dur, temp, None)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "920.0" in message
    assert temp.hex() in message
    assert "firmware 20200403" in message
    assert "hardware 8" in message
    assert ISSUE_TRACKER_URL in message


async def test_a_plausible_temperature_never_warns(coordinator, caplog):
    with caplog.at_level(logging.WARNING):
        coordinator._process_live_data(*frames(temp=36.0), None)

    assert not [r for r in caplog.records if r.levelno == logging.WARNING]


@pytest.mark.parametrize("temp", [0.0, 100.0])
async def test_the_limits_of_the_range_are_accepted(coordinator, temp):
    coordinator._process_live_data(*frames(temp=temp), None)

    assert coordinator.last_valid_data["temperature"] == temp


async def test_an_implausible_temperature_does_not_trigger_the_comfort_sync(
    coordinator,
):
    """900 degrees is above any comfort threshold, but it must not be taken as
    the moment the water became comfortable."""
    coordinator.auto_sync_at_comfort = True
    coordinator._process_live_data(*frames(shower=50, ticks=3000, temp=20.0), None)
    assert coordinator.session_wasted_volume > 0

    coordinator._process_live_data(*frames(shower=60, ticks=3500, temp=920.0), None)

    assert coordinator.pending_new_shower is False
    assert coordinator._comfort_sync_sent_for_session is False


async def test_an_implausible_temperature_does_not_set_the_time_to_comfort(
    coordinator,
):
    coordinator._process_live_data(*frames(shower=50, ticks=3000, temp=20.0), None)

    coordinator._process_live_data(*frames(shower=60, ticks=3500, temp=920.0), None)

    assert coordinator.session_time_to_comfort is None
    assert coordinator._session_comfort_seen is False


async def test_the_reading_after_an_ignored_one_starts_a_fresh_interval(coordinator):
    """No interpolation across the gap: the first valid reading afterwards is
    judged on its own, like the first reading of a session."""
    coordinator._process_live_data(*frames(shower=50, ticks=3000, temp=20.0), None)
    coordinator._process_live_data(*frames(shower=60, ticks=3500, temp=920.0), None)
    assert coordinator._last_temp_raw is None

    coordinator._process_live_data(*frames(shower=80, ticks=4500, temp=36.0), None)

    # The 10 L of the ignored interval are not attributed to either side; the
    # next 20 L count entirely as comfortable, not as a cold-to-warm blend.
    assert coordinator.session_wasted_volume == 50.0
    assert coordinator.session_shower_volume_comfort == 20.0


# ---------------------------------------------------------------------------
# Temperature sensor
# ---------------------------------------------------------------------------


def temperature_sensor(coordinator):
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "temperature")
    return HydraoSensor(coordinator, description)


async def test_the_temperature_sensor_shows_unknown_for_an_undecodable_reading(
    coordinator,
):
    """None from the coordinator is an answer, not a gap to fill with the value
    restored from before the restart."""
    sensor = temperature_sensor(coordinator)
    sensor._restored_value = 25.0
    coordinator.data = {"temperature": None}

    assert sensor.native_value is None


async def test_the_temperature_sensor_still_falls_back_before_any_data(coordinator):
    sensor = temperature_sensor(coordinator)
    sensor._restored_value = 25.0
    coordinator.data = {}

    assert sensor.native_value == 25.0
