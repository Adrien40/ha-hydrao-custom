# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""The button, number and switch platforms, driven through Home Assistant's
own services so the whole path (service call, entity, coordinator, options)
is exercised."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers import entity_registry as er

from custom_components.hydrao_custom.entity_helpers import (
    apply_and_persist,
    persist_option,
)
from custom_components.hydrao_custom.number import HydraoNumberEntity

ADDRESS = "AA:BB:CC:DD:EE:FF"


def entity_id(hass, domain: str, key: str) -> str:
    found = er.async_get(hass).async_get_entity_id(
        domain, "hydrao_custom", f"{ADDRESS}_{key}"
    )
    assert found is not None, f"no {domain} entity for {key}"
    return found


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------


async def test_pressing_the_button_ends_the_shower(hass, integration):
    coordinator = integration.coordinator
    assert coordinator.pending_new_shower is False

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": entity_id(hass, "button", "end_shower")},
        blocking=True,
    )

    assert coordinator.pending_new_shower is True
    assert coordinator.force_reset_flag is True


# ---------------------------------------------------------------------------
# Number: minimum comfort temperature
# ---------------------------------------------------------------------------


async def test_number_starts_at_the_configured_threshold(hass, integration):
    state = hass.states.get(entity_id(hass, "number", "comfort_temperature"))

    assert float(state.state) == 33.0
    assert state.attributes["min"] == 0.0
    assert state.attributes["max"] == 50.0
    assert state.attributes["step"] == 0.5


async def test_setting_the_number_updates_the_coordinator_and_the_options(
    hass, integration
):
    target = entity_id(hass, "number", "comfort_temperature")

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": target, "value": 38.5},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert integration.coordinator.min_temp_threshold == 38.5
    assert integration.entry.options["min_temp_threshold"] == 38.5
    assert float(hass.states.get(target).state) == 38.5


async def test_setting_the_same_number_again_still_refreshes_the_state(
    hass, integration
):
    target = entity_id(hass, "number", "comfort_temperature")
    call = {"entity_id": target, "value": 33.0}

    await hass.services.async_call("number", "set_value", call, blocking=True)
    await hass.async_block_till_done()

    assert float(hass.states.get(target).state) == 33.0


async def test_number_follows_changes_made_on_the_coordinator(hass, integration):
    target = entity_id(hass, "number", "comfort_temperature")

    integration.coordinator.min_temp_threshold = 41.0
    integration.coordinator.async_update_listeners()
    await hass.async_block_till_done()

    assert float(hass.states.get(target).state) == 41.0


async def test_number_pushes_its_value_to_the_coordinator_when_added(hass, integration):
    """The entity's initial value is applied to the coordinator on startup."""
    assert integration.coordinator.min_temp_threshold == 33.0


async def test_the_number_base_class_requires_its_hooks(coordinator, mock_entry):
    base = HydraoNumberEntity(coordinator, mock_entry, MagicMock(key="x"), 1.0)

    with pytest.raises(NotImplementedError):
        base._current_coordinator_value()
    with pytest.raises(NotImplementedError):
        base._apply_value(1.0)
    with pytest.raises(NotImplementedError):
        _ = base._option_key
    assert base._to_option_value(2.5) == 2.5


# ---------------------------------------------------------------------------
# Switch: comfort mode sync
# ---------------------------------------------------------------------------


async def test_switch_starts_off(hass, integration):
    state = hass.states.get(entity_id(hass, "switch", "auto_sync_at_comfort"))

    assert state.state == STATE_OFF
    assert integration.coordinator.auto_sync_at_comfort is False


async def test_turning_the_switch_on_and_off(hass, integration):
    target = entity_id(hass, "switch", "auto_sync_at_comfort")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": target}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(target).state == STATE_ON
    assert integration.coordinator.auto_sync_at_comfort is True
    assert integration.entry.options["auto_sync_at_comfort"] is True

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": target}, blocking=True
    )
    await hass.async_block_till_done()

    assert hass.states.get(target).state == STATE_OFF
    assert integration.coordinator.auto_sync_at_comfort is False
    assert integration.entry.options["auto_sync_at_comfort"] is False


async def test_switch_follows_changes_made_on_the_coordinator(hass, integration):
    target = entity_id(hass, "switch", "auto_sync_at_comfort")

    integration.coordinator.auto_sync_at_comfort = True
    integration.coordinator.async_update_listeners()
    await hass.async_block_till_done()

    assert hass.states.get(target).state == STATE_ON


async def test_switch_follows_options_changed_elsewhere(hass, integration):
    """Changing the option (e.g. from the options flow) flips the switch."""
    target = entity_id(hass, "switch", "auto_sync_at_comfort")

    hass.config_entries.async_update_entry(
        integration.entry,
        options={**integration.entry.options, "auto_sync_at_comfort": True},
    )
    await hass.async_block_till_done()

    assert hass.states.get(target).state == STATE_ON


# ---------------------------------------------------------------------------
# entity_helpers
# ---------------------------------------------------------------------------


async def test_persist_option_keeps_the_other_options(hass, mock_entry):
    mock_entry.add_to_hass(hass)

    persist_option(hass, mock_entry, "auto_sync_at_comfort", True)

    assert mock_entry.options == {
        "min_temp_threshold": 33.0,
        "auto_sync_at_comfort": True,
    }


async def test_apply_and_persist_applies_writes_state_then_persists(hass, mock_entry):
    mock_entry.add_to_hass(hass)
    calls: list[str] = []
    entity = MagicMock()
    entity.async_write_ha_state.side_effect = lambda: calls.append("state")

    def apply(value):
        calls.append(f"apply:{value}")

    with patch(
        "custom_components.hydrao_custom.entity_helpers.persist_option",
        side_effect=lambda *a: calls.append("persist"),
    ):
        apply_and_persist(
            entity, hass, mock_entry, "soaping_duration", 2, apply, lambda v: v * 60
        )

    assert calls == ["apply:2", "state", "persist"]


async def test_apply_and_persist_converts_to_the_option_unit(hass, mock_entry):
    mock_entry.add_to_hass(hass)

    apply_and_persist(
        MagicMock(),
        hass,
        mock_entry,
        "soaping_duration",
        2,
        lambda v: None,
        lambda v: v * 60,
    )

    assert mock_entry.options["soaping_duration"] == 120


async def test_apply_and_persist_stores_the_value_as_is_by_default(hass, mock_entry):
    mock_entry.add_to_hass(hass)

    apply_and_persist(
        MagicMock(), hass, mock_entry, "min_temp_threshold", 36.0, lambda v: None
    )

    assert mock_entry.options["min_temp_threshold"] == 36.0
