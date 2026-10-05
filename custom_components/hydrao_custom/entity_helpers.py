# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from collections.abc import Callable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity


def persist_option(
    hass: HomeAssistant, entry: ConfigEntry, key: str, value: Any
) -> None:
    """Persist a single option value onto a config entry, preserving the
    rest of the existing options."""
    new_options = dict(entry.options)
    new_options[key] = value
    hass.config_entries.async_update_entry(entry, options=new_options)


def apply_and_persist(
    entity: Entity,
    hass: HomeAssistant,
    entry: ConfigEntry,
    option_key: str,
    value: Any,
    apply_fn: Callable[[Any], None],
    to_option_value: Callable[[Any], Any] = lambda v: v,
) -> None:
    """Apply a value to the coordinator immediately (so the BLE loop picks
    it up right away), write entity state, then persist the value as the
    new option.

    State is written unconditionally: async_update_entry() only notifies
    listeners when options actually change, so resubmitting an unchanged
    value would otherwise leave the UI showing a stale value. The write
    is idempotent, so a later listener-driven write (if any) is harmless.

    `to_option_value` converts to the unit stored in options, when it
    differs from the entity's native unit (e.g. seconds vs minutes).
    Shared by number.py and switch.py to avoid duplicating this logic.
    """
    apply_fn(value)
    entity.async_write_ha_state()
    persist_option(hass, entry, option_key, to_option_value(value))
