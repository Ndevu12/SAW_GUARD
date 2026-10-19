# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Remediation says what it came to (#26).** A `remediation` output reports whether
  `remediate: pr` opened a pull request, a fork pull request, a patch or an issue, prepared a branch,
  had nothing to fix, or failed. Anything short of a pull request is a warning on the run that names
  the cause and what to change, such as the repository setting "Allow GitHub Actions to create and
  approve pull requests", and a pull request from a fork is warned about before the scan. The gate is
  unchanged. A failed remediation no longer skips the SARIF upload, the evidence artifact or the PR
  comment. With a scanner too old to report the outcome, the output is `unknown` and the run says to
  set `version` to a newer release.

### Changed

- **The Action is called SAW Guard everywhere.** Its name, log lines, step summary and PR comment say
  SAW Guard, and the evidence artifact is `saw-guard-evidence-<job>`; a PR comment it posted under its
  earlier name is still updated rather than posted again. The example to copy is
  `examples/saw-guard.yml`, and it and the README pin SAW Guard and `actions/checkout` by commit SHA
  and the scanner at 0.12.3, as code only; what each line does is in the text beside it.
- **Docs: point consumers at `saw guard`** (from the `stayawakebot` package) as the automated way to install and verify this gate. `saw guard setup` installs it SHA-pinned to the latest release and opens pin-bump PRs; `saw guard check` verifies it is present, SHA-pinned, current, and a required check. The manual copy-paste + hardening checklist remain the source of truth (the least-privilege `contents: read` default and remediation-as-opt-in posture are unchanged).

## [0.1.4] — 2026-07-15

### Added

- **Findings visibility (#10).** Opt-in surfaces that route findings to where a reviewer looks —
  redacted SARIF to code scanning (`upload-sarif`), a redacted evidence artifact (`upload-artifact`),
  and a sticky PR comment (`pr-comment`) — plus an always-on actionable step summary. All additive
  and non-fatal; they never change the gate, and degrade to a notice on fork PRs / missing
  permissions.
- **Redacted CI-log report (#12).** The CI log now shows the full findings breakdown (like a local
  `saw scan`), rendered from the scanner's redacted report — no evidence bytes, untrusted paths
  sanitized against ANSI / `::`-workflow-command injection, and bounded.
- **Hardening checklist + safe-by-default template (#11).** A consolidated pre-merge hardening
  checklist and a copy-paste [`examples/worm-guard.yml`](examples/worm-guard.yml).
- **Scanner pin-freshness guard.** A scheduled workflow opens/updates one deduplicated issue when
  the worm-guard gate's scanner pin drifts behind the latest PyPI release, so it can't silently rot.
- This CHANGELOG.

### Changed

- Bumped the worm-guard self-gate scanner pin **0.1.7 → 0.1.12** (the previous pin predated
  `--sarif`).
- SHA-pinned the repo's own workflow actions (`actions/checkout`, `actions/setup-python`), dogfooding
  the hardening advice the docs give consumers.
- Split the README's deep-dive sections into single-responsibility files under
  [`docs/`](docs/) (gating, surfacing findings, remediation, configuration, hardening).

## [0.1.3] — 2026-07-11

### Added

- Gating tiers (`fail-on`), verdict outputs, and `saw fix` auto-remediation (`remediate: pr`) (#8).

## [0.1.2] — 2026-07-08

### Added

- Adopt the `saw` CLI, take configuration from the repo's committed `saw` config, and self-gate the
  Strix repo with its own worm scan (dogfood) (#4, #5).

### Security

- Harden the worm-guard gate against fail-open, and coerce `summary.targets` to an int so a malformed
  count fails closed (#6, #7).

## [0.1.1] — 2026-06-24

### Changed

- Refine the action description for clarity (#1).

## [0.1.0] — 2026-06-24

### Added

- Initial release: install the published [`stayawakebot`](https://pypi.org/project/stayawakebot/)
  scanner and gate CI on its verdict.

[Unreleased]: https://github.com/Ndevu12/strix/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/Ndevu12/strix/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/Ndevu12/strix/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Ndevu12/strix/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Ndevu12/strix/releases/tag/v0.1.0
