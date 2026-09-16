# Releasing

Versions come from git tags via `setuptools-scm` — there is no version number to edit
in `pyproject.toml`. A tag of `v1.2.3` produces version `1.2.3`; commits after it build
as `1.2.4.devN+g<sha>` (not publishable to PyPI, by design).

## One-time setup

**PyPI Trusted Publisher** (no API tokens): on <https://pypi.org>, go to your account →
*Publishing* → *Add a new pending publisher* and enter:

| Field | Value |
| --- | --- |
| PyPI project name | `sro-config` |
| Owner | `BJolly-97` |
| Repository name | `SRO-Config` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

(For a dry run first, do the same on <https://test.pypi.org> and temporarily point the
`pypa/gh-action-pypi-publish` step at it with `repository-url: https://test.pypi.org/legacy/`.)

**Optional:** in the repo's *Settings → Environments → pypi*, add a required reviewer so
a publish needs a manual click.

## Cutting a release

1. Make sure `main` is green and `docs/changelog.md` has the notes under `[Unreleased]`.
2. Move the `[Unreleased]` items under a new `## [1.2.3] - YYYY-MM-DD` heading; commit.
3. Tag and push:
   ```bash
   git tag -a v1.2.3 -m "v1.2.3"
   git push origin v1.2.3
   ```
4. The **Release** workflow then builds the sdist + wheel, publishes to PyPI, pushes the
   Docker image to `ghcr.io/bjolly-97/sro-config`, and opens a GitHub Release with the
   artifacts attached and auto-generated notes (edit them to match the changelog).

Pre-release tags (`v1.2.3-rc1`) are published to PyPI as pre-releases and marked as such
on GitHub automatically.

After the **first** release, make the GHCR package public: *Packages → sro-config →
Package settings → Change visibility → Public* (and, optionally, link it to this repo).
