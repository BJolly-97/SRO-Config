# Installation

`sro-config` requires **Python 3.9 or newer**. It depends only on `numpy`, `pandas`,
`matplotlib` and `tqdm`, all of which install as wheels on Windows, macOS and Linux.

## From PyPI

```bash
python -m pip install --user pipx
python -m pipx ensurepath

# Close your terminal and open a new one

python -m pipx install sro-config

# Close the terminal and reopen again

sro-config --help
```

For an isolated install of just the command-line tool (recommended if you only want to run it, not import it):

```bash
uv tool install sro-config
```
??? info "New to pipx? (optional reading)"

    As a note, installation via pip may throw an error if the installed version of Python
    doesn't add its `Scripts` folder to `PATH` by default. Typing `sro-config` in-terminal
    may therefore behave unexpectedly. This should not be a concern for those who have used
    the python.org installer, which adds to `PATH` automatically.

    This is avoided when using pipx.

    pipx is a separate installation tool that downloads Python command-line
    packages into isolated environments, so `sro-config` and its dependencies
    never clash with anything else on your system. If you intend to use pipx,
    see the [pipx installation guide](https://pipx.pypa.io/latest/how-to/install-pipx.html).


## From source

```bash
git clone https://github.com/BJolly-97/SRO-Config
cd SRO-Config
pip install -e ".[dev]"
```

## Docker

A headless image (published to GHCR on each release) runs the `dict` and `config`
commands with no Python install on the host — useful for reproducible batch runs on a
cluster or in CI. Mount your working directory at `/data`:

```bash
docker run --rm -v "$PWD:/data" ghcr.io/bjolly-97/sro-config \
    config --dict-dir . --sublattice 0 --rmc6f run.rmc6f
```

The interactive `vis` viewer and the desktop GUI need a display and are not usable from
the container.

## What you get

A single command, **`sro-config`**. The importable package is `sro_config`:

```python
from sro_config import dictionary, histograms, visualiser
```

The pre-package script names (`Histograms_v2_2.py`, `Configuration_Master.py`, …) still
exist as thin wrappers under `legacy/`, purely so old scripts keep working.

## The GUI

`sro-config gui` opens a desktop GUI (Dictionary / Analysis / Visualiser tabs). It needs
Tkinter:

- **Windows / macOS** — bundled with the python.org installer.
- **Linux** — install separately, e.g. `sudo apt install python3-tk`.
- **macOS system Python** often ships an old, buggy Tk; prefer the python.org build or
  `brew install python-tk`.
