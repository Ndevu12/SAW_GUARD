#!/usr/bin/env python3
"""Refuse to release a vX.Y.Z tag whose version has no section in CHANGELOG.md.

The release half of `.github/workflows/release.yml`: `is_cut` is unit-tested offline
(tests/test_changelog_release.py), and `main()` reads the changelog and prints the verdict.

Usage: check_changelog_release.py <vX.Y.Z> [changelog-path]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def is_cut(version: str, changelog_text: str) -> bool:
    """Tell whether the changelog has a `## [X.Y.Z]` heading for a version. Takes the version, with
    or without its leading `v`, and the changelog's text. Returns True when the heading is there;
    `## [Unreleased]` never counts."""
    version = version.lstrip("v")
    return re.search(rf"^## \[{re.escape(version)}\]", changelog_text, re.MULTILINE) is not None


def main(argv: list[str]) -> int:
    """Check one tag against the changelog. Takes the tag and, optionally, the changelog's path.
    Returns 0 when the version's section is there, 1 when it is not or the changelog cannot be
    read, and 2 on bad usage."""
    if not argv:
        print("usage: check_changelog_release.py <vX.Y.Z> [changelog]", file=sys.stderr)
        return 2
    version = argv[0].lstrip("v")
    path = Path(argv[1]) if len(argv) > 1 else Path("CHANGELOG.md")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"::error::cannot read {path} to check the release section for {version}: {exc}",
              file=sys.stderr)
        return 1
    if is_cut(version, text):
        print(f"CHANGELOG: found the [{version}] section — OK to release.")
        return 0
    print(f"::error::CHANGELOG.md has no '## [{version}]' section for the tag being released. Cut "
          f"[Unreleased] into '## [{version}] — <date>', merge that by pull request, and tag "
          f"v{version} again.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
