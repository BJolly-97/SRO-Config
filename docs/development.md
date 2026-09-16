# Development

```bash
git clone https://github.com/BJolly-97/SRO-Config
cd SRO-Config
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Checks

```bash
ruff check .        # lint
ruff format .       # auto-format
pytest              # test suite (add --cov for coverage)
```

`pre-commit` runs `ruff` and hygiene hooks on every commit. CI runs the same plus the
test matrix (Linux / macOS / Windows × Python 3.9 / 3.11 / 3.13) and a package build.

## Layout

| Path | |
| --- | --- |
| `src/sro_config/` | the package — `dictionary`, `histograms`, `visualiser`, `cli`, `batch`, `gui/` |
| `tests/` | end-to-end regression tests + fixtures |
| `examples/` | runnable sample datasets |
| `docs/` | this documentation (MkDocs) |
| `docker/` | `Dockerfile` and its ignore file for the headless image |
| `legacy/` | frozen pre-package entry points, excluded from lint/format |
| `.github/` | CI/release workflows, Dependabot, and the `CONTRIBUTING` / `CITATION` / `RELEASING` docs |

## Notes

- The numerical core (`histograms.py`, `dictionary.py`) predates the package and carries
  a deliberately conservative `ruff` ruleset. Prefer small, test-backed changes there,
  and check `pytest` before and after.
- `git blame` ignores the bulk-reformat commit via `.git-blame-ignore-revs` — enable it
  locally with `git config blame.ignoreRevsFile .git-blame-ignore-revs`.

## Building the docs

```bash
pip install -e ".[docs]"
mkdocs serve            # live preview at http://127.0.0.1:8000
mkdocs build --strict   # what CI runs
```
