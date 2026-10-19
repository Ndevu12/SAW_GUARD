#!/usr/bin/env python3
"""guard.remediation — what ``remediate: pr`` came to is an output, anything short of a pull
request is a warning naming its cause, and nothing from the scanner's report reaches the run but
its known codes."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from guard import remediation
from guard.remediation import Remediation, read, summary_line, warning

SETTING = "Allow GitHub Actions to create and approve pull requests"


def _report(*records: dict) -> str:
    return json.dumps({"results": list(records)})


def _record(remediation_: str, cause: str = "", pull_request=None) -> dict:
    return {"repository": "/home/runner/work/r/r", "remediation": remediation_, "cause": cause,
            "pull_request": pull_request, "url": ""}


class TestWhatRemediationCameTo(unittest.TestCase):
    def test_an_opened_pull_request_raises_no_warning_and_names_its_number(self):
        came_to = read(_report(_record("pr", pull_request=4)), patches=False)
        self.assertEqual(came_to.outcome, "pr")
        self.assertIsNone(warning(came_to))
        self.assertIn("#4", summary_line(came_to))

    def test_nothing_to_fix_raises_no_warning(self):
        self.assertIsNone(warning(read(_report(_record("skipped")), patches=False)))

    def test_every_rung_short_of_a_pull_request_warns(self):
        for outcome in ("fork-pr", "prepared", "issue", "patch", "failed"):
            with self.subTest(outcome=outcome):
                said = warning(read(_report(_record(outcome)), patches=False))
                self.assertTrue(said.startswith(f"::warning title={remediation.TITLE}::"))

    def test_a_pull_request_actions_may_not_open_names_the_setting(self):
        came_to = read(_report(_record("failed", "actions-may-not-open-pull-requests")),
                       patches=False)
        self.assertIn(SETTING, warning(came_to))
        self.assertIn(SETTING, summary_line(came_to))

    def test_a_patch_names_why_and_how_to_keep_it(self):
        said = warning(read(_report(_record("patch", "forbidden")), patches=True))
        self.assertIn("contents: write", said)
        self.assertIn("upload-artifact: true", said)

    def test_the_worst_target_decides(self):
        came_to = read(_report(_record("pr", pull_request=4), _record("patch", "forbidden")),
                       patches=True)
        self.assertEqual((came_to.outcome, came_to.cause), ("patch", "forbidden"))

    def test_an_older_scanner_is_unknown_unless_it_left_a_patch(self):
        self.assertEqual(read(None, patches=False).outcome, "unknown")
        self.assertIn("--json", warning(read(None, patches=False)))
        self.assertEqual(read(None, patches=True).outcome, "patch")
        self.assertIn("cannot say why", warning(read(None, patches=True)))

    def test_an_unreadable_report_is_unknown(self):
        for report in ("", "not json", "[]", '{"results": 3}', '{"results": []}', '"x"'):
            with self.subTest(report=report):
                self.assertEqual(read(report, patches=False).outcome, "unknown")


class TestNothingFromTheReportReachesTheRun(unittest.TestCase):
    HOSTILE = "x\n::error::forged%0A::set-output name=a::b"

    def test_unknown_codes_and_text_are_never_printed(self):
        came_to = read(_report({"repository": self.HOSTILE, "remediation": self.HOSTILE,
                                "cause": self.HOSTILE, "pull_request": self.HOSTILE}),
                       patches=False)
        self.assertEqual(came_to, Remediation("unknown"))
        for said in (warning(came_to), summary_line(came_to)):
            with self.subTest(said=said):
                self.assertNotIn("forged", said)
                self.assertNotIn("set-output", said)

    def test_every_warning_is_one_line_with_one_command(self):
        for outcome in ("fork-pr", "prepared", "issue", "patch", "failed", "unknown"):
            for cause in ("", *remediation._CAUSES):
                with self.subTest(outcome=outcome, cause=cause):
                    said = warning(Remediation(outcome, cause))
                    self.assertNotIn("\n", said)
                    self.assertNotIn("%", said)
                    self.assertEqual(said.count("::"), 2)

    def test_a_pull_request_number_must_be_a_number(self):
        for number in ("4", True, 4.0, None):
            with self.subTest(number=number):
                self.assertIsNone(read(_report(_record("pr", pull_request=number)),
                                       patches=False).pull_request)


class TestTheRemediationCommand(unittest.TestCase):
    def _run(self, report: str | None, patches: str = "false"):
        from guard.__main__ import run_remediation
        from guard.config import Config
        folder = tempfile.mkdtemp()
        output, step_summary = os.path.join(folder, "output"), os.path.join(folder, "summary")
        path = ""
        if report is not None:
            path = os.path.join(folder, "remediation.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(report)
        printed = StringIO()
        with redirect_stdout(printed):
            run_remediation(Config(remediation_report=path, github_output=output,
                                   step_summary=step_summary, patches=patches))
        with open(output, encoding="utf-8") as fh, open(step_summary, encoding="utf-8") as sh:
            return fh.read(), printed.getvalue(), sh.read()

    def test_a_refused_pull_request_sets_the_output_and_warns(self):
        output, printed, step_summary = self._run(
            _report(_record("failed", "actions-may-not-open-pull-requests")))
        self.assertEqual(output, "remediation=failed\n")
        self.assertIn(SETTING, printed)
        self.assertIn(SETTING, step_summary)

    def test_an_opened_pull_request_sets_the_output_without_a_warning(self):
        output, printed, _ = self._run(_report(_record("pr", pull_request=4)))
        self.assertEqual((output, printed), ("remediation=pr\n", ""))

    def test_an_older_scanner_sets_unknown(self):
        output, printed, _ = self._run(None)
        self.assertEqual(output, "remediation=unknown\n")
        self.assertIn("::warning", printed)


if __name__ == "__main__":
    unittest.main()
