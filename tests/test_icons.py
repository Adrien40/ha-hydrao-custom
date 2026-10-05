# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Icons live in icons.json (icon-translations rule), not in the Python code."""

import json
import re
from pathlib import Path

from custom_components.hydrao_custom.const import (
    BT_STATUS_CONNECTING,
    BT_STATUS_ERROR,
    BT_STATUS_REBOOTING,
    BT_STATUS_SUCCESS,
    BT_STATUS_SYNC_APPLIED,
    BT_STATUS_SYNC_FAILED,
    BT_STATUS_WAITING,
    BT_STATUS_WRITING_SYNC,
)

INTEGRATION_DIR = Path(__file__).parent.parent / "custom_components" / "hydrao_custom"
ICONS = json.loads((INTEGRATION_DIR / "icons.json").read_text())["entity"]
STRINGS = json.loads((INTEGRATION_DIR / "strings.json").read_text())["entity"]


def test_no_icon_is_hard_coded_in_the_python_code():
    pattern = re.compile(r"\bicon\s*=|_attr_icon|def icon\b|mdi:")
    for path in INTEGRATION_DIR.glob("*.py"):
        assert not pattern.search(path.read_text()), path.name


def test_every_icon_belongs_to_a_translated_entity():
    for platform, entities in ICONS.items():
        for key in entities:
            assert key in STRINGS[platform], f"{platform}.{key}"


def test_every_icon_is_a_material_design_icon_with_a_default():
    for entities in ICONS.values():
        for definition in entities.values():
            assert definition["default"].startswith("mdi:")
            for icon in definition.get("state", {}).values():
                assert icon.startswith("mdi:")


def test_bluetooth_status_has_an_icon_for_every_state():
    states = ICONS["sensor"]["bluetooth_status"]["state"]

    assert set(states) == {
        BT_STATUS_WAITING,
        BT_STATUS_CONNECTING,
        BT_STATUS_SUCCESS,
        BT_STATUS_ERROR,
        BT_STATUS_WRITING_SYNC,
        BT_STATUS_SYNC_APPLIED,
        BT_STATUS_SYNC_FAILED,
        BT_STATUS_REBOOTING,
    }
