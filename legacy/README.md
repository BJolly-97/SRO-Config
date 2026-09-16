# Legacy entry points

Before this project became an installable package, it was a set of loose scripts
run by filename (`Histograms_v2_2.py`, `Configuration_Master.py`, …) and a couple
of `.bat` helpers. Everything they did now lives in `src/sro_config/` and is driven
by the single `sro-config` command (see the top-level [README](../README.md)).

These files are kept **only** so existing scripts, notes, and muscle memory that
point at those exact names keep working. They are thin wrappers - each one just
imports and calls the real implementation:

| Legacy file | Replacement |
| --- | --- |
| `exe/Generalised_Clapp_v2.py`, `Batching_Scripts/Generalised_Clapp_v2.py` | `sro-config dict` |
| `exe/Histograms_v2_2.py`, `Batching_Scripts/Histograms_v2_2.py` | `sro-config config` |
| `exe/Visualiser.py` | `sro-config vis` |
| `Batching_Scripts/Configuration_Master.py` | `python -m sro_config.batch` (or `sro-config config --rmc6f-glob ...`) |
| `Batching_Scripts/Requirements.bat` | `pip install -e .` (or `pip install sro-config`) |

They require the package to be installed first (`pip install -e .` from the repo
root). New work should use `sro-config` directly; this directory will be removed
in a future release.
