"""SAW Guard action helpers — the small Python behind the composite GitHub Action.

The Action itself (``action.yml``) is a thin CI wrapper around the published ``stayawakebot``
scanner. This package holds the one piece of real logic the wrapper needs: turning the scan's
machine-readable report into an actionable, redacted, injection-safe findings summary for the
step summary and a sticky PR comment (issue #10).

Mirrors the scanner project's layout — one responsibility per module:

* :mod:`guard.config`   — the single boundary to the environment (a typed ``Config``).
* :mod:`guard.markdown` — injection-safe Markdown primitives for untrusted values.
* :mod:`guard.report`   — load / flatten the scanner's JSON report.
* :mod:`guard.summary`  — render the findings-and-remediation Markdown (pure).
* ``guard.__main__``    — the entrypoint: wire config → report → summary → file sinks.

Run as ``python3 -m guard`` with the repo root on ``PYTHONPATH`` (the action passes
``PYTHONPATH=$GITHUB_ACTION_PATH``). SAW Guard is a GitHub Action, not a distributed package, so the
helper lives at the repo root — not under ``src/`` (a build/install convention that never applies
to code run in place).
"""
