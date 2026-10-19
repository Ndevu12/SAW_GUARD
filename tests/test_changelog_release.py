#!/usr/bin/env python3
"""check_changelog_release — a vX.Y.Z tag is released only when CHANGELOG.md has its section."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import tempfile
import unittest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / ".github" / "scripts" / "check_changelog_release.py"
_spec = importlib.util.spec_from_file_location("check_changelog_release", _SCRIPT)
ccr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccr)

CHANGELOG = """\
# Changelog

## [Unreleased]

### Added
- a thing not released yet

## [0.2.0] — 2026-10-19

### Added
- a released thing

## [0.1.4] — 2026-07-15
"""


class TestIsCut(unittest.TestCase):
    def test_a_released_version_is_cut_with_or_without_its_v(self):
        for tag in ("0.2.0", "v0.2.0", "v0.1.4"):
            with self.subTest(tag=tag):
                self.assertTrue(ccr.is_cut(tag, CHANGELOG))

    def test_a_version_only_under_unreleased_is_not_cut(self):
        self.assertFalse(ccr.is_cut("v0.2.1", CHANGELOG))

    def test_the_version_is_matched_exactly(self):
        for tag in ("v0.2", "v0.2.00", "v0X2X0", "v0.1.40"):
            with self.subTest(tag=tag):
                self.assertFalse(ccr.is_cut(tag, CHANGELOG))

    def test_a_mention_in_prose_is_not_a_section(self):
        self.assertFalse(ccr.is_cut("v0.3.0", CHANGELOG + "\nSee [0.3.0] later.\n"))


class TestMain(unittest.TestCase):
    def _main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ccr.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def _changelog(self) -> str:
        path = pathlib.Path(tempfile.mkdtemp()) / "CHANGELOG.md"
        path.write_text(CHANGELOG, encoding="utf-8")
        return str(path)

    def test_a_cut_version_passes(self):
        rc, out, _ = self._main(["v0.2.0", self._changelog()])
        self.assertEqual(rc, 0)
        self.assertIn("[0.2.0]", out)

    def test_an_uncut_version_fails_with_an_annotation(self):
        rc, _, err = self._main(["v0.2.1", self._changelog()])
        self.assertEqual(rc, 1)
        self.assertTrue(err.startswith("::error::"))

    def test_an_unreadable_changelog_fails(self):
        self.assertEqual(self._main(["v0.2.0", "/nonexistent/CHANGELOG.md"])[0], 1)

    def test_no_tag_is_a_usage_error(self):
        self.assertEqual(self._main([])[0], 2)


if __name__ == "__main__":
    unittest.main()
