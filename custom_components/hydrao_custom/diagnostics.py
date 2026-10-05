# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Diagnostics support for Hydrao Custom."""

from __future__ import annotations

import time
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .const import HydraoConfigEntry

# The Bluetooth address identifies the device (and its owner's home), the
# name embeds its last four digits and the device id is the serial number.
TO_REDACT = {CONF_ADDRESS, "name", "title", "device_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HydraoConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    seen_ago: float | None = None
    if coordinator.last_seen_time > 0:
        seen_ago = round(time.monotonic() - coordinator.last_seen_time, 1)

    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "coordinator": async_redact_data(
            {
                "bluetooth_status": coordinator.last_valid_data.get("bluetooth_status"),
                "is_new_entry": coordinator.is_new_entry,
                "min_temp_threshold": coordinator.min_temp_threshold,
                "auto_sync_at_comfort": coordinator.auto_sync_at_comfort,
                "seconds_since_last_seen": seen_ago,
                "raw_frames": coordinator.last_raw_frames,
                "static_data": coordinator.static_data,
                "data": coordinator.data,
                "pending": {
                    "thresholds": coordinator.pending_thresholds,
                    "colors": coordinator.pending_colors,
                    "soaping_duration": coordinator.pending_soaping_duration,
                    "new_shower": coordinator.pending_new_shower,
                    "new_shower_attempts": coordinator.new_shower_attempts,
                },
            },
            TO_REDACT,
        ),
    }
