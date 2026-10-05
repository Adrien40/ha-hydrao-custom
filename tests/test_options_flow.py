# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Tests for the options flow.

The form is built from several possible sources (what the user just typed,
the live device, stored options, the entry's data); these tests check which
one wins, then every way a submission can succeed or be refused - each
refusal followed by a recovery.
"""

import logging

import pytest
import voluptuous as vol
from homeassistant.data_entry_flow import FlowResultType, section
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hydrao_custom.config_flow import HydraoOptionsFlowHandler
from custom_components.hydrao_custom.const import DOMAIN
from custom_components.hydrao_custom.coordinator import HydraoDataUpdateCoordinator

ADDRESS = "AA:BB:CC:DD:EE:FF"
FLOW_LOGGER = "custom_components.hydrao_custom.config_flow"

pytestmark = pytest.mark.usefixtures("bluetooth_loaded")

DEFAULT_THRESHOLDS = {
    "threshold_1": 10,
    "threshold_2": 20,
    "threshold_3": 30,
    "threshold_4": 40,
}
DEFAULT_COLORS = {
    "threshold_1_color": [0, 255, 0],
    "threshold_2_color": [0, 0, 255],
    "threshold_3_color": [255, 0, 180],
    "threshold_4_color": [255, 0, 0],
}

STORED_OPTIONS = {
    "min_temp_threshold": 33.0,
    "auto_sync_at_comfort": False,
    "soaping_duration": 120,
    "threshold_1": 5,
    "threshold_2": 15,
    "threshold_3": 25,
    "threshold_4": 35,
    "threshold_1_color": [1, 2, 3],
    "threshold_2_color": [4, 5, 6],
    "threshold_3_color": [7, 8, 9],
    "threshold_4_color": [10, 11, 12],
}


def make_entry(options=None, data=None) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={"address": ADDRESS, "has_connected_once": True, **(data or {})},
        options=options if options is not None else {"min_temp_threshold": 33.0},
    )


async def open_form(hass, entry):
    """Open the options flow of `entry`; returns the first form."""
    entry.add_to_hass(hass)
    return await hass.config_entries.options.async_init(entry.entry_id)


async def submit(hass, result, **sections):
    """Submit the form, as the frontend does: grouped in sections."""
    user_input = {
        "comfort": sections.pop("comfort", {}),
        "thresholds": sections.pop("thresholds", {}),
        "colors": sections.pop("colors", {}),
        **sections,
    }
    return await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )


async def call_step_directly(hass, entry, user_input):
    """Call the step without the frontend's schema validation in between."""
    entry.add_to_hass(hass)
    flow = HydraoOptionsFlowHandler()
    flow.hass = hass
    flow.handler = entry.entry_id
    return await flow.async_step_init(user_input)


def fields(result):
    """The form's fields, flattened out of their sections:
    {name: (marker, selector)}."""
    flat = {}
    for marker, value in result["data_schema"].schema.items():
        if isinstance(value, section):
            for inner, selector in value.schema.schema.items():
                flat[str(inner.schema)] = (inner, selector)
        else:
            flat[str(marker.schema)] = (marker, value)
    return flat


def default_of(result, name):
    marker, _ = fields(result)[name]
    return marker.default()


def is_known(result, name):
    """True when the field is editable (the value is known), False when it is
    only shown as a not-yet-known placeholder."""
    marker, _ = fields(result)[name]
    return isinstance(marker, vol.Required)


def make_coordinator(hass, entry):
    coordinator = HydraoDataUpdateCoordinator(hass, entry)
    entry.runtime_data = coordinator
    return coordinator


# ---------------------------------------------------------------------------
# What the form shows, and where the values come from
# ---------------------------------------------------------------------------


async def test_form_for_a_device_not_read_yet_leaves_device_fields_unknown(hass):
    result = await open_form(hass, make_entry())

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert not result["errors"]
    for name in (
        "soaping_duration",
        *DEFAULT_THRESHOLDS,
        *DEFAULT_COLORS,
    ):
        assert not is_known(result, name), name
    # what is stored by Home Assistant alone is always editable
    assert default_of(result, "min_temp_threshold") == 33.0
    assert default_of(result, "auto_sync_at_comfort") is False
    assert default_of(result, "reset_to_defaults") is False


async def test_form_is_prefilled_from_the_stored_options(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    assert default_of(result, "soaping_duration") == 120
    assert default_of(result, "threshold_1") == 5
    assert default_of(result, "threshold_4") == 35
    assert default_of(result, "threshold_2_color") == [4, 5, 6]


async def test_form_falls_back_on_the_entry_data_when_options_are_empty(hass):
    entry = make_entry(
        options={},
        data={
            **{k: v for k, v in STORED_OPTIONS.items() if k != "min_temp_threshold"},
            "min_temp_threshold": 36.0,
            "auto_sync_at_comfort": True,
        },
    )

    result = await open_form(hass, entry)

    assert default_of(result, "min_temp_threshold") == 36.0
    assert default_of(result, "auto_sync_at_comfort") is True
    assert default_of(result, "soaping_duration") == 120
    assert default_of(result, "threshold_3") == 25
    assert default_of(result, "threshold_3_color") == [7, 8, 9]


async def test_form_uses_defaults_when_nothing_is_stored_anywhere(hass):
    result = await open_form(hass, make_entry(options={}))

    assert default_of(result, "min_temp_threshold") == 33.0
    assert default_of(result, "auto_sync_at_comfort") is False


async def test_form_shows_the_live_device_values_first(hass):
    entry = make_entry(options=dict(STORED_OPTIONS))
    entry.add_to_hass(hass)
    coordinator = make_coordinator(hass, entry)
    coordinator.min_temp_threshold = 35.0
    coordinator.auto_sync_at_comfort = True
    coordinator.static_data.update(
        soaping_duration=90,
        thresholds=[11, 22, 33, 44],
        colors=[(21, 22, 23), (24, 25, 26), (27, 28, 29), (30, 31, 32)],
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert default_of(result, "min_temp_threshold") == 35.0
    assert default_of(result, "auto_sync_at_comfort") is True
    assert default_of(result, "soaping_duration") == 90
    assert default_of(result, "threshold_2") == 22
    assert default_of(result, "threshold_4_color") == [30, 31, 32]


async def test_form_falls_back_when_live_values_are_incomplete(hass, caplog):
    entry = make_entry(options=dict(STORED_OPTIONS))
    entry.add_to_hass(hass)
    coordinator = make_coordinator(hass, entry)
    coordinator.static_data.update(thresholds=[11], colors=[(21, 22, 23)])

    with caplog.at_level(logging.WARNING, logger=FLOW_LOGGER):
        result = await hass.config_entries.options.async_init(entry.entry_id)

    assert default_of(result, "threshold_1") == 11  # live value
    assert default_of(result, "threshold_2") == 15  # fell back on the options
    assert default_of(result, "threshold_2_color") == [4, 5, 6]
    assert "Could not read live threshold value for threshold_2" in caplog.text
    assert "Could not read live color value for threshold_2_color" in caplog.text


async def test_form_treats_unusable_stored_values_as_unknown(hass, caplog):
    entry = make_entry(
        options={
            "min_temp_threshold": 33.0,
            "threshold_1": "abc",
            "threshold_2": None,
            "threshold_1_color": 5,
            "threshold_2_color": None,
        },
        data={"threshold_3_color": 7},
    )

    with caplog.at_level(logging.WARNING, logger=FLOW_LOGGER):
        result = await open_form(hass, entry)

    for name in (
        "threshold_1",
        "threshold_2",
        "threshold_1_color",
        "threshold_2_color",
        "threshold_3_color",
    ):
        assert not is_known(result, name), name
    assert "Stored value for threshold_1 is invalid" in caplog.text
    assert "Stored value for threshold_2 is invalid" in caplog.text
    assert "Stored color for threshold_1_color is invalid" in caplog.text
    assert "Stored color for threshold_3_color is invalid" in caplog.text


async def test_form_keeps_what_was_typed_after_a_refused_submission(hass):
    entry = make_entry(options=dict(STORED_OPTIONS))
    result = await open_form(hass, entry)

    result = await submit(
        hass,
        result,
        comfort={
            "min_temp_threshold": 36.5,
            "soaping_duration": 5,  # refused: out of range
            "auto_sync_at_comfort": True,
        },
        thresholds={"threshold_1": 7},
        colors={"threshold_1_color": [200, 100, 50]},
    )

    assert result["type"] == FlowResultType.FORM
    assert default_of(result, "min_temp_threshold") == 36.5
    assert default_of(result, "soaping_duration") == 5
    assert default_of(result, "auto_sync_at_comfort") is True
    assert default_of(result, "threshold_1") == 7
    assert default_of(result, "threshold_1_color") == [200, 100, 50]


async def test_form_ignores_submitted_values_it_cannot_read(hass, caplog):
    """Not reachable through the frontend (its schema rejects such values
    first), but the form must still fall back on stored values, not crash."""
    entry = make_entry(options=dict(STORED_OPTIONS))

    with caplog.at_level(logging.WARNING, logger=FLOW_LOGGER):
        result = await call_step_directly(
            hass, entry, {"threshold_1": float("nan"), "threshold_1_color": 5}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["threshold_1"] == "value_out_of_range"
    assert default_of(result, "threshold_1") == 5  # the stored value
    assert default_of(result, "threshold_1_color") == [1, 2, 3]
    assert "Invalid submitted value for threshold_1" in caplog.text
    assert "Invalid submitted color for threshold_1_color" in caplog.text


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------


async def test_submit_saves_the_changes_and_keeps_other_options(hass):
    entry = make_entry(options={**STORED_OPTIONS, "unrelated": "kept"})
    result = await open_form(hass, entry)

    result = await submit(
        hass,
        result,
        comfort={
            "min_temp_threshold": 36.0,
            "soaping_duration": 150,
            "auto_sync_at_comfort": True,
        },
        thresholds={"threshold_1": 6, "threshold_2": 16, "threshold_3": 26},
        colors={"threshold_4_color": [9, 9, 9]},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        **STORED_OPTIONS,
        "unrelated": "kept",
        "min_temp_threshold": 36.0,
        "soaping_duration": 150,
        "auto_sync_at_comfort": True,
        "threshold_1": 6,
        "threshold_2": 16,
        "threshold_3": 26,
        "threshold_4_color": [9, 9, 9],
    }
    assert "reset_to_defaults" not in result["data"]


async def test_submit_on_a_device_not_read_yet_saves_only_what_is_editable(hass):
    result = await open_form(hass, make_entry())

    result = await submit(
        hass,
        result,
        comfort={"min_temp_threshold": 34.0, "auto_sync_at_comfort": True},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {"min_temp_threshold": 34.0, "auto_sync_at_comfort": True}


async def test_submit_ignores_fields_left_empty(hass):
    """A field submitted empty must not erase the value stored for it."""
    entry = make_entry(options=dict(STORED_OPTIONS))

    result = await call_step_directly(
        hass,
        entry,
        {
            "min_temp_threshold": 34.0,
            "soaping_duration": None,
            "threshold_1": None,
            "threshold_1_color": None,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {**STORED_OPTIONS, "min_temp_threshold": 34.0}


# ---------------------------------------------------------------------------
# Reset to factory defaults
# ---------------------------------------------------------------------------


async def test_reset_restores_factory_values_but_keeps_comfort_settings(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(
        hass,
        result,
        comfort={"min_temp_threshold": 37.0, "auto_sync_at_comfort": True},
        reset_to_defaults=True,
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "min_temp_threshold": 37.0,
        "auto_sync_at_comfort": True,
        "soaping_duration": 180,
        **DEFAULT_THRESHOLDS,
        **DEFAULT_COLORS,
    }


async def test_reset_without_comfort_values_leaves_them_untouched(hass):
    entry = make_entry(options={**STORED_OPTIONS, "auto_sync_at_comfort": True})

    result = await call_step_directly(hass, entry, {"reset_to_defaults": True})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["min_temp_threshold"] == 33.0
    assert result["data"]["auto_sync_at_comfort"] is True
    assert result["data"]["threshold_1"] == 10


async def test_reset_rejects_an_out_of_range_temperature_then_recovers(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(
        hass, result, comfort={"min_temp_threshold": 60.0}, reset_to_defaults=True
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        "min_temp_threshold": "min_temp_out_of_range",
        "base": "min_temp_out_of_range",
    }
    assert default_of(result, "reset_to_defaults") is True  # the choice is kept

    result = await submit(
        hass, result, comfort={"min_temp_threshold": 35.0}, reset_to_defaults=True
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["min_temp_threshold"] == 35.0
    assert result["data"]["soaping_duration"] == 180


# ---------------------------------------------------------------------------
# Refused submissions, each followed by a recovery
# ---------------------------------------------------------------------------


async def test_thresholds_must_increase(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(
        hass,
        result,
        thresholds={
            "threshold_1": 30,
            "threshold_2": 20,
            "threshold_3": 35,
            "threshold_4": 40,
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        "threshold_2": "thresholds_not_increasing",
        "base": "thresholds_not_increasing",
    }

    result = await submit(
        hass,
        result,
        thresholds={
            "threshold_1": 10,
            "threshold_2": 20,
            "threshold_3": 35,
            "threshold_4": 40,
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["threshold_1"] == 10


@pytest.mark.parametrize(
    ("field", "refused", "accepted"),
    [
        ("threshold_1", 0, 1),
        ("threshold_4", 101, 100),
    ],
)
async def test_thresholds_must_stay_between_1_and_100_liters(
    hass, field, refused, accepted
):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(hass, result, thresholds={field: refused})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        field: "value_out_of_range",
        "base": "value_out_of_range",
    }

    result = await submit(hass, result, thresholds={field: accepted})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][field] == accepted


async def test_comfort_temperature_must_be_a_valid_temperature(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(hass, result, comfort={"min_temp_threshold": 60.0})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        "min_temp_threshold": "min_temp_out_of_range",
        "base": "min_temp_out_of_range",
    }

    result = await submit(hass, result, comfort={"min_temp_threshold": 35.0})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["min_temp_threshold"] == 35.0


async def test_soaping_duration_must_be_in_range_then_recovers(hass):
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(hass, result, comfort={"soaping_duration": 700})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {
        "soaping_duration": "soaping_duration_out_of_range",
        "base": "soaping_duration_out_of_range",
    }

    result = await submit(hass, result, comfort={"soaping_duration": 600})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["soaping_duration"] == 600


async def test_the_banner_error_is_the_first_one_found(hass):
    """Several things are wrong at once: each field gets its own message and
    the banner repeats the first of them (thresholds are checked first)."""
    result = await open_form(hass, make_entry(options=dict(STORED_OPTIONS)))

    result = await submit(
        hass,
        result,
        comfort={"min_temp_threshold": 60.0, "soaping_duration": 700},
        thresholds={"threshold_1": 30, "threshold_2": 20},
    )

    assert result["errors"] == {
        "threshold_2": "thresholds_not_increasing",
        "soaping_duration": "soaping_duration_out_of_range",
        "min_temp_threshold": "min_temp_out_of_range",
        "base": "thresholds_not_increasing",
    }
