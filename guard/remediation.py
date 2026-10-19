#!/usr/bin/env python3
"""Say what ``remediate: pr`` came to, from the report ``saw fix --pr --json`` prints.

Every word written to an annotation or the step summary comes from the fixed tables below; nothing
from the report is printed but its known codes and a pull request's number.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

TITLE = "SAW Guard remediation"

# Least to most degraded: a run that remediated several targets is graded by its worst one.
_ORDER = ("pr", "skipped", "fork-pr", "prepared", "issue", "patch", "failed", "unknown")

_CAME_TO = {
    "fork-pr": "the fix was opened as a pull request from a fork",
    "prepared": "the fix was prepared on a branch that was not pushed",
    "issue": "an issue was filed instead of a pull request",
    "patch": "the fix was saved as a patch in `sab-patches/`",
    "failed": "no fix was delivered",
    "unknown": "what it came to is not known",
}

_CAUSES = {
    "actions-may-not-open-pull-requests": (
        "the repository does not let GitHub Actions open pull requests — turn on “Allow GitHub "
        "Actions to create and approve pull requests” in its Actions settings"),
    "forbidden": ("the token may not push to this repository — give the job `contents: write` and "
                  "`pull-requests: write`, or pass a `github-token` that can push"),
    "auth": "GitHub refused the token — check the `github-token` input",
    "workflow_scope": ("the fix changes a workflow file, which needs a `github-token` with the "
                       "`workflow` scope"),
    "signed_commits": "the repository requires signed commits, which this run cannot make",
    "occupied": "a rule on the repository refuses the fix branch",
    "private_email": "GitHub refuses the commit's private email address",
    "network": "GitHub could not be reached",
    "rate_limited": "GitHub's rate limit was reached",
    "issue-not-filed": "no issue could be filed either — give the job `issues: write`",
}

_NEWER_SCANNER = "set `version` to a release whose `saw fix` takes `--json`"
_SCANNER_CANNOT_SAY = f"the installed scanner cannot report it — {_NEWER_SCANNER}"
_SCANNER_CANNOT_SAY_WHY = f"the installed scanner cannot say why — {_NEWER_SCANNER}"
_NO_REPORT = "`saw fix` did not report it — see this step's log"
_KEEP_THE_PATCH = " Set `upload-artifact: true` to keep the patch with the run."


@dataclass(frozen=True)
class Remediation:
    """What remediation came to, why it fell short of a pull request, and the pull request."""

    outcome: str
    cause: str = ""
    pull_request: int | None = None
    note: str = ""


def read(report: str | None, *, patches: bool) -> Remediation:
    """Read what remediation came to. Takes the text ``saw fix --pr --json`` printed, or None when
    the installed scanner cannot print it, and whether ``sab-patches/`` holds a patch. Returns the
    worst outcome among the reported targets."""
    if report is None:
        if patches:
            return Remediation("patch", note=_SCANNER_CANNOT_SAY_WHY)
        return Remediation("unknown", note=_SCANNER_CANNOT_SAY)
    try:
        records = json.loads(report)["results"]
    except (ValueError, TypeError, KeyError):
        return Remediation("unknown", note=_NO_REPORT)
    if not isinstance(records, list):
        records = []
    graded = [_graded(r) for r in records if isinstance(r, dict)]
    if not graded:
        return Remediation("unknown", note=_NO_REPORT)
    return max(graded, key=lambda r: _ORDER.index(r.outcome))


def _graded(record: dict) -> Remediation:
    """Read one target's record. Takes it. Returns its outcome, its known cause and its pull
    request."""
    outcome = record.get("remediation")
    cause = record.get("cause")
    number = record.get("pull_request")
    return Remediation(outcome if outcome in _ORDER else "unknown",
                       cause if cause in _CAUSES else "",
                       number if isinstance(number, int) and not isinstance(number, bool) else None)


def warning(r: Remediation) -> str | None:
    """Write the workflow warning for a remediation short of a pull request. Takes the
    remediation. Returns the warning line, or None when there is nothing to warn about."""
    if r.outcome in ("pr", "skipped"):
        return None
    return f"::warning title={TITLE}::{_sentence(r)}"


def summary_line(r: Remediation) -> str:
    """Write the step-summary line for a remediation. Takes it. Returns the line."""
    if r.outcome == "pr":
        number = f" #{r.pull_request}" if r.pull_request is not None else ""
        said = f"opened or updated the rolling `security/auto-clean` pull request{number}."
    elif r.outcome == "skipped":
        said = "the default branch had nothing to fix."
    else:
        said = _sentence(r)
    return f"**{TITLE}**: {said}\n"


def _sentence(r: Remediation) -> str:
    """Say what a remediation short of a pull request came to and why. Takes it. Returns the
    sentence."""
    said = f"remediate is 'pr', but {_CAME_TO[r.outcome]}"
    why = _CAUSES[r.cause] if r.cause else r.note
    sentence = f"{said}: {why}." if why else f"{said}."
    return sentence + (_KEEP_THE_PATCH if r.outcome == "patch" else "")
