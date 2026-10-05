# Copyright (c) 2026 Adrien40
# SPDX-License-Identifier: GPL-3.0-only

"""The documentation rules marked `done` must have a section in both READMEs."""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
RULES = yaml.safe_load(
    (ROOT / "custom_components" / "hydrao_custom" / "quality_scale.yaml").read_text()
)["rules"]

# rule -> heading keywords, per README
SECTIONS = {
    "docs-data-update": {
        "README.md": r"how data is updated",
        "README.fr.md": r"mise à jour des données",
    },
    "docs-examples": {
        "README.md": r"automation examples",
        "README.fr.md": r"exemples d'automatisations",
    },
    "docs-known-limitations": {
        "README.md": r"known limitations",
        "README.fr.md": r"limitations connues",
    },
    "docs-use-cases": {
        "README.md": r"use cases",
        "README.fr.md": r"cas d'usage",
    },
}


def status_of(name):
    value = RULES[name]
    return value if isinstance(value, str) else value["status"]


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
@pytest.mark.parametrize("rule", sorted(SECTIONS))
def test_docs_rule_status_matches_the_readmes(rule, readme):
    text = (ROOT / readme).read_text(encoding="utf-8")
    has_section = bool(
        re.search(
            rf"^#+ .*{SECTIONS[rule][readme]}", text, re.IGNORECASE | re.MULTILINE
        )
    )

    assert (status_of(rule) == "done") is has_section


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
def test_automation_examples_are_valid_yaml(readme):
    text = (ROOT / readme).read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, re.DOTALL)

    assert len(blocks) >= 2
    for block in blocks:
        assert yaml.safe_load(block)


# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------

REPOSITORY = "Adrien40/ha-hydrao-custom"


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
def test_badges_point_at_this_repository(readme):
    """Badges are easy to copy from another project and forget to adapt."""
    text = (ROOT / readme).read_text(encoding="utf-8")

    assert "blue-connect" not in text.lower()
    assert "blue_connect" not in text.lower()
    for repository in re.findall(r"github\.com/(Adrien40/[\w.-]+)", text):
        assert repository == REPOSITORY, repository
    for repository in re.findall(
        r"shields\.io/github/[\w-]+/(?:status/)?(Adrien40/[\w.-]+)", text
    ):
        assert repository == REPOSITORY, repository


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
def test_workflow_badges_reference_existing_workflows(readme):
    text = (ROOT / readme).read_text(encoding="utf-8")
    workflows = set(re.findall(r"actions/workflows/([\w.-]+\.ya?ml)", text))

    assert workflows
    for name in workflows:
        assert (ROOT / ".github" / "workflows" / name).is_file(), name


@pytest.mark.parametrize("readme", ["README.md", "README.fr.md"])
def test_quality_scale_badge_matches_the_manifest(readme):
    manifest = json.loads(
        (ROOT / "custom_components" / "hydrao_custom" / "manifest.json").read_text()
    )
    text = (ROOT / readme).read_text(encoding="utf-8")
    badge = re.search(r"HA%20Quality%20Scale-(\w+)-", text)

    assert badge
    assert badge.group(1).lower() == manifest["quality_scale"]
    target = re.search(r"\]\((custom_components/[^)]*quality_scale\.yaml)\)", text)
    assert target
    assert (ROOT / target.group(1)).is_file()
