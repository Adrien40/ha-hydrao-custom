# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Keeps the Home Assistant version the integration declares in line with the
one it is tested on, so the declared minimum can never be a version the tests
(and therefore the integration) have not been run against."""

import json
import re
from pathlib import Path

import pytest
from awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as installed_version

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def declared_minimum() -> str:
    return json.loads((ROOT / "hacs.json").read_text())["homeassistant"]


def test_tests_run_on_at_least_the_declared_minimum(declared_minimum):
    assert AwesomeVersion(installed_version) >= AwesomeVersion(declared_minimum)


def test_tests_run_on_the_declared_minimum_release_series(declared_minimum):
    """Not only 'new enough': the suite is expected to run on the very release
    the integration declares as its minimum, not on something much newer."""
    installed = AwesomeVersion(installed_version)
    minimum = AwesomeVersion(declared_minimum)

    assert (installed.major, installed.minor) == (minimum.major, minimum.minor)


def test_the_test_requirements_pin_the_declared_minimum(declared_minimum):
    """requirements-test.txt documents which Home Assistant it targets in its
    comments; the plugin it pins must be the one built for that release."""
    text = (ROOT / "requirements-test.txt").read_text()

    assert re.search(r"^pytest-homeassistant-custom-component==\S+", text, re.MULTILINE)
    assert f"Home Assistant {declared_minimum.rsplit('.', 1)[0]}" in text
