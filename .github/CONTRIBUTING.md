# Contributing

## Development setup

```bash
git clone <repo>
cd SRO-Config
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Before opening a PR

```bash
ruff check .            # lint
ruff format .           # auto-format
pytest                  # test suite (add --cov for coverage)
```

`pre-commit` runs `ruff` and a few hygiene hooks on every commit; CI runs the same
checks plus the test matrix (Linux/macOS/Windows × Python 3.9/3.11/3.13) and a
package build.

## Notes

- The numerical core (`histograms.py`, `dictionary.py`) predates the package and
  carries a deliberately conservative lint ruleset (see `[tool.ruff]` in
  `pyproject.toml`). Prefer small, test-backed changes there.
- `git blame` ignores the bulk-reformat commit via `.git-blame-ignore-revs`;
  enable it locally with `git config blame.ignoreRevsFile .git-blame-ignore-revs`.
- `legacy/` holds frozen pre-package entry points and is excluded from lint/format.
