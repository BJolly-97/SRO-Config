# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `LICENSE` (MIT), `CHANGELOG.md`, and `CITATION.cff`.
- Full packaging metadata in `pyproject.toml` (classifiers, keywords, project URLs,
  PEP 639 license declaration).
- Regression test covering 9-column, bare-10-column and bracketed-10-column
  `.rmc6f` layouts.
- Continuous integration (GitHub Actions): `ruff` lint + format check, `pytest`
  with coverage on Linux/macOS/Windows × Python 3.9/3.11/3.13, and a package
  build + `twine check`.
- `pre-commit` config, Dependabot, and `CONTRIBUTING.md`.
- MkDocs (Material) documentation site under `docs/`, built with `--strict` in CI and
  auto-deployed to GitHub Pages on every push to `main`.
- `examples/FeNi/` — a runnable synthetic dataset with a walk-through.
- Release automation: `.github/workflows/release.yml` builds and publishes to PyPI via
  Trusted Publishing (OIDC, no tokens) and cuts a GitHub Release on a `v*` tag. See
  `RELEASING.md`.
- `Dockerfile` — a headless multi-stage image for the `dict` / `config` workflow,
  built and smoke-tested in CI and pushed to GHCR on release.

### Changed
- Renamed the project ahead of the first PyPI release: distribution `sro-config`
  (formerly `gen-config`), import package `sro_config` (formerly `gen_config`),
  command `sro-config` (formerly `gen-config`), and the GitHub repository is now
  `BJolly-97/SRO-Config` (formerly `Gen_Config_Install`).
- The project is an installable package: distribution `sro-config`, import package
  `sro_config`, command `sro-config`.
- Version is now derived from git tags via `setuptools-scm` (`gen_config.__version__`
  reads it from the installed metadata); there is no version string to maintain by hand.
- Rewrote `README.md` as a concise landing page (badges, example plot, quickstart);
  the full command and output-file reference moved to the docs site.
- Moved the pre-package compatibility wrappers (`exe/`, `Batching_Scripts/`) into
  `legacy/` with an explanatory README.
- Applied `ruff format` across the codebase (whitespace/layout only; recorded in
  `.git-blame-ignore-revs`).
- Tidied the repository root: `CONTRIBUTING` / `CITATION` / `RELEASING` moved to
  `.github/`, the changelog to `docs/`, and the Dockerfile to `docker/`.

### Removed
- The `Configurational_Analysis.bat` / `.sh` launcher scripts. `pip install` /
  `pipx install` / the Docker image cover installation on every platform.

### Fixed
- `config` now reads `.rmc6f` files whose `Atoms:` section omits the optional
  site-label column (9-column layout); previously every field was read one column
  to the left and the run crashed.
- Enhancement-factor histograms label the y-axis with β, not Ψ.

## [1.0.0] - 2024

First packaged release. The previously loose analysis scripts became an installable
Python package (`src/gen_config/`) exposing a single `gen-config` command with
`dict`, `config`, `vis` and `gui` subcommands, interactive and scripted/batch
modes, a desktop GUI, and an end-to-end regression test suite.
