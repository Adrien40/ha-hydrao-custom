"""Every translation file must expose the same keys as strings.json."""

import json
from pathlib import Path

import pytest

DIR = Path(__file__).parent.parent / "custom_components" / "hydrao_custom"


def _flat(data, prefix=""):
    keys = set()
    for key, value in data.items():
        if isinstance(value, dict):
            keys |= _flat(value, f"{prefix}{key}.")
        else:
            keys.add(f"{prefix}{key}")
    return keys


@pytest.mark.parametrize(
    "path", sorted((DIR / "translations").glob("*.json")), ids=lambda p: p.stem
)
def test_translation_has_all_keys(path):
    reference = _flat(json.loads((DIR / "strings.json").read_text(encoding="utf-8")))
    keys = _flat(json.loads(path.read_text(encoding="utf-8")))
    assert reference - keys == set(), "missing keys"
    assert keys - reference == set(), "unknown keys"
