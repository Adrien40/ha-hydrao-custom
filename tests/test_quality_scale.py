# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""Guards for quality_scale.yaml: it must list every rule exactly once with a
valid status, justify every `todo` / `exempt`, and agree with the code on the
rules that can be checked mechanically - so it cannot silently drift."""

import json
import re
from pathlib import Path

import pytest
import yaml

from custom_components.hydrao_custom import button, number, sensor, switch
from custom_components.hydrao_custom.entity import HydraoEntity

ROOT = Path(__file__).parent.parent
INTEGRATION_DIR = ROOT / "custom_components" / "hydrao_custom"

# Official rule list, by tier:
# https://developers.home-assistant.io/docs/core/integration-quality-scale/rules
TIERS = {
    "bronze": [
        "action-setup",
        "appropriate-polling",
        "brands",
        "common-modules",
        "config-flow-test-coverage",
        "config-flow",
        "dependency-transparency",
        "docs-actions",
        "docs-triggers",
        "docs-conditions",
        "docs-high-level-description",
        "docs-installation-instructions",
        "docs-removal-instructions",
        "entity-event-setup",
        "entity-unique-id",
        "has-entity-name",
        "runtime-data",
        "test-before-configure",
        "test-before-setup",
        "unique-config-entry",
    ],
    "silver": [
        "action-exceptions",
        "config-entry-unloading",
        "docs-configuration-parameters",
        "docs-installation-parameters",
        "entity-unavailable",
        "integration-owner",
        "log-when-unavailable",
        "parallel-updates",
        "reauthentication-flow",
        "test-coverage",
    ],
    "gold": [
        "devices",
        "diagnostics",
        "discovery-update-info",
        "discovery",
        "docs-data-update",
        "docs-examples",
        "docs-known-limitations",
        "docs-supported-devices",
        "docs-supported-functions",
        "docs-troubleshooting",
        "docs-use-cases",
        "dynamic-devices",
        "entity-category",
        "entity-device-class",
        "entity-disabled-by-default",
        "entity-translations",
        "exception-translations",
        "icon-translations",
        "reconfiguration-flow",
        "repair-issues",
        "stale-devices",
    ],
    "platinum": [
        "async-dependency",
        "inject-websession",
        "strict-typing",
    ],
}
ALL_RULES = [rule for rules in TIERS.values() for rule in rules]
TIER_ORDER = list(TIERS)

PLATFORMS = [sensor, button, number, switch]


@pytest.fixture(scope="module")
def rules():
    data = yaml.safe_load((INTEGRATION_DIR / "quality_scale.yaml").read_text())
    return data["rules"]


def status_of(rules, name):
    value = rules[name]
    return value if isinstance(value, str) else value["status"]


def comment_of(rules, name):
    value = rules[name]
    return None if isinstance(value, str) else value.get("comment")


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_every_official_rule_is_listed_and_nothing_else(rules):
    assert sorted(rules) == sorted(ALL_RULES)


def test_every_status_is_valid(rules):
    for name in ALL_RULES:
        assert status_of(rules, name) in {"done", "todo", "exempt"}, name


def test_todo_and_exempt_rules_are_justified(rules):
    for name in ALL_RULES:
        if status_of(rules, name) in {"todo", "exempt"}:
            assert comment_of(rules, name), f"{name} needs a comment"


# ---------------------------------------------------------------------------
# No premature claim
# ---------------------------------------------------------------------------


def test_manifest_does_not_claim_a_tier_that_has_open_rules(rules):
    """If manifest.json declares a quality_scale, every rule of that tier and
    of the tiers below must be done or exempt."""
    manifest = json.loads((INTEGRATION_DIR / "manifest.json").read_text())
    claimed = manifest.get("quality_scale")
    if claimed is None:
        return

    assert claimed in TIER_ORDER
    for tier in TIER_ORDER[: TIER_ORDER.index(claimed) + 1]:
        for name in TIERS[tier]:
            assert status_of(rules, name) != "todo", f"{name} is still todo"


# ---------------------------------------------------------------------------
# Statuses that can be checked against the code
# ---------------------------------------------------------------------------


def test_parallel_updates_status_matches_the_platforms(rules):
    defined = all(hasattr(platform, "PARALLEL_UPDATES") for platform in PLATFORMS)

    assert (status_of(rules, "parallel-updates") == "done") is defined


def test_diagnostics_status_matches_the_code(rules):
    exists = (INTEGRATION_DIR / "diagnostics.py").exists()

    assert (status_of(rules, "diagnostics") == "done") is exists


def test_icon_translations_status_matches_the_code(rules):
    exists = (INTEGRATION_DIR / "icons.json").exists()

    assert (status_of(rules, "icon-translations") == "done") is exists


def test_brands_status_matches_the_code(rules):
    exists = all(
        (INTEGRATION_DIR / "brand" / name).exists() for name in ("icon.png", "logo.png")
    )

    assert (status_of(rules, "brands") == "done") is exists


def test_integration_owner_status_matches_the_manifest(rules):
    manifest = json.loads((INTEGRATION_DIR / "manifest.json").read_text())

    assert (status_of(rules, "integration-owner") == "done") is bool(
        manifest.get("codeowners")
    )


def test_discovery_status_matches_the_manifest(rules):
    manifest = json.loads((INTEGRATION_DIR / "manifest.json").read_text())

    assert (status_of(rules, "discovery") == "done") is bool(manifest.get("bluetooth"))


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
def test_removal_instructions_status_matches_the_readmes(rules, readme):
    text = (ROOT / readme).read_text(encoding="utf-8")
    has_section = bool(
        re.search(
            r"^#+ .*(removal|uninstall|suppression|désinstall)",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    )

    assert (status_of(rules, "docs-removal-instructions") == "done") is has_section


def test_common_modules_status_matches_the_entity_classes(rules):
    entity_classes = [
        sensor.HydraoSensor,
        sensor.HydraoBluetoothStatusSensor,
        sensor.HydraoRealTimeRSSISensor,
        sensor.HydraoSoapingDurationSensor,
        sensor.HydraoPendingConfigSensor,
        button.HydraoButton,
        number.HydraoNumberEntity,
        switch.HydraoAutoSyncSwitch,
    ]
    shared = all(issubclass(cls, HydraoEntity) for cls in entity_classes)

    assert (status_of(rules, "common-modules") == "done") is shared


def test_test_coverage_status_matches_the_ci_threshold(rules):
    """`test-coverage` may only be `done` while the Tests workflow really fails
    the build below the 95% the rule asks for."""
    workflow = (ROOT / ".github" / "workflows" / "tests.yaml").read_text()
    found = re.search(r"--cov-fail-under=(\d+)", workflow)
    threshold = int(found.group(1)) if found else 0

    assert (status_of(rules, "test-coverage") == "done") is (threshold >= 95)


def test_coverage_is_measured_on_the_integration_with_branches():
    config = (ROOT / ".coveragerc").read_text()

    assert "source = custom_components/hydrao_custom" in config
    assert "branch = True" in config


def test_strict_typing_status_matches_the_typing_workflow(rules):
    workflow = (ROOT / ".github" / "workflows" / "mypy.yaml").read_text()
    enforced = "mypy --strict custom_components/hydrao_custom" in workflow

    assert (status_of(rules, "strict-typing") == "done") is enforced


def test_entity_disabled_by_default_status_matches_the_code(rules):
    """`done` only while some entity really is disabled by default."""
    disabled = (
        any(
            not description.entity_registry_enabled_default
            for description in sensor.SENSOR_DESCRIPTIONS
        )
        or not sensor.HydraoRealTimeRSSISensor._attr_entity_registry_enabled_default
    )

    assert (status_of(rules, "entity-disabled-by-default") == "done") is disabled
