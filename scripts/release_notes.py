"""Print the GitHub release notes for a version, taken from the changelog.

Usage: python scripts/release_notes.py 1.2.0 --manifest path/to/manifest.json

Fails (exit 1) when the version does not match "version" in manifest.json or
when CHANGELOG.md has no "## 1.2.0" section. CHANGELOG.fr.md is appended when
it has a section for the version too.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def section(changelog: Path, version: str) -> str | None:
    """Return the body of the "## <version>" section, or None if absent."""
    if not changelog.is_file():
        return None
    pattern = re.compile(
        rf"^##\s+v?{re.escape(version)}\b.*?$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(changelog.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    manifest_version = json.loads(args.manifest.read_text(encoding="utf-8"))["version"]
    if manifest_version != args.version:
        print(
            f"Tag {args.version} does not match manifest version {manifest_version}",
            file=sys.stderr,
        )
        return 1

    english = section(ROOT / "CHANGELOG.md", args.version)
    if not english:
        print(f"CHANGELOG.md has no section for {args.version}", file=sys.stderr)
        return 1

    notes = [english]
    french = section(ROOT / "CHANGELOG.fr.md", args.version)
    if french:
        notes.append(f"---\n\n**Français**\n\n{french}")
    print("\n\n".join(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
