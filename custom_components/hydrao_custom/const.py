# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

DOMAIN = "hydrao_custom"
PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SWITCH]

# Typed alias for the config entry, so entry.runtime_data is correctly
# typed as our coordinator wherever this alias is used instead of the
# plain ConfigEntry. Written as a plain generic alias (not the `type`
# statement) to stay compatible with Python < 3.12.
HydraoConfigEntry = ConfigEntry["HydraoDataUpdateCoordinator"]

CHAR_FIRMWARE = "00002a26-0000-1000-8000-00805f9b34fb"
CHAR_VOLUME_AND_DURATION = "0000ca1c-0000-1000-8000-00805f9b34fb"
CHAR_CONFIG = "0000ca1d-0000-1000-8000-00805f9b34fb"
CHAR_NEW_SHOWER = "0000ca20-0000-1000-8000-00805f9b34fb"
CHAR_HARDWARE = "0000ca24-0000-1000-8000-00805f9b34fb"
CHAR_DURATION_RAW = "0000ca26-0000-1000-8000-00805f9b34fb"
CHAR_UNIQUE_ID = "0000ca28-0000-1000-8000-00805f9b34fb"
CHAR_FLOW_RAW = "0000ca31-0000-1000-8000-00805f9b34fb"
CHAR_TEMPERATURE_RAW = "0000ca32-0000-1000-8000-00805f9b34fb"
CHAR_SOAPING_DURATION = "0000ca33-0000-1000-8000-00805f9b34fb"

DEFAULT_SOAPING_DURATION = 180

DEFAULT_MIN_TEMP_THRESHOLD = 33.0

MAX_NEW_SHOWER_ATTEMPTS = 2

BT_STATUS_WAITING = "waiting"
BT_STATUS_CONNECTING = "connecting"
BT_STATUS_SUCCESS = "success"
BT_STATUS_ERROR = "error"
BT_STATUS_WRITING_SYNC = "writing_sync"
BT_STATUS_SYNC_APPLIED = "sync_applied"
BT_STATUS_SYNC_FAILED = "sync_failed"
BT_STATUS_REBOOTING = "rebooting"
