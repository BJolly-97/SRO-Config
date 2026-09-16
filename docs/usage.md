# Usage

Everything goes through one command, **`sro-config`**, with three subcommands:
`dict`, `config` and `vis`. Each works two ways — **interactively** (run it with no
flags and answer prompts) or **scripted** (pass flags, no prompts). One dataset and
several hundred go through the same code path.

A complete, runnable walk-through is in
[`examples/FeNi/`](https://github.com/BJolly-97/SRO-Config/tree/main/examples/FeNi).

## `dict` — structure dictionaries

Generates the per-structure lookup files the analysis needs. Requires a `.cif`.

```bash
sro-config dict --cif FeNi.cif --equivalence 0,1
```

- `--cif PATH` — the structure file. Omit to be prompted.
- `--equivalence I,J,...` — merge these constituent-atom indices into one combined
  sub-lattice (e.g. Fe and Ni sharing a site in a solid solution). Repeat the flag for
  several independent merge groups. Omit to be prompted; pass `--no-equivalence` to skip
  without prompting.

Interactively, `dict` prints the crystal information it extracts, lists the constituent
atom types `0…x`, and asks (Y/N) for equivalent lattice sites, which you enter as
`0,1,2…`.

## `config` — enhancement-factor analysis

Runs the Clapp analysis for one or many `.rmc6f` configurations against a dictionary
directory.

```bash
# one file
sro-config config --dict-dir . --sublattice 0 --rmc6f run001.rmc6f

# every matching file, in one process
sro-config config --dict-dir . --sublattice 0 --rmc6f-glob "configs/*.rmc6f"
```

- `--dict-dir PATH` — directory holding the files `dict` produced.
- `--sublattice N` — which sub-lattice to analyse (as printed in `.finsub`).
- `--rmc6f PATH [PATH ...]` — one or more configuration files.
- `--rmc6f-glob PATTERN` — a glob matching many files.

Batch behaviour:

- One bad file does not abort the run; a per-file success/failure summary is printed at
  the end and the command exits non-zero if **any** file failed (so `&&` / CI can detect
  a partial failure).
- The tool's own `_mb.rmc6f` outputs are skipped when resolving `--rmc6f-glob`, so
  re-running the same glob in the same directory won't reprocess last run's outputs.

!!! note "One structure at a time"
    Batching is supported across many `.rmc6f` files for **one** structure, not across
    different `.cif` files — `--equivalence` indices depend on the atom-type order in
    each `.cif`, which isn't guaranteed consistent between structures.

Outputs land next to each input file. See [Output files](output-files.md).

## `vis` — 3D configuration viewer

Plots Clapp configurations for a sub-lattice as interactive, rotatable 3D scatter plots
(one pop-up window per label; occupied neighbour = red, empty = black).

```bash
sro-config vis --dict-dir . --sublattice 0 --config 1,12,34
```

- `--config LABELS` — comma-separated Configuration labels, in any order.

## Interactive menu

Run `sro-config` with **no arguments** for a prompt-driven menu offering `dict`,
`config`, `vis`, `gui` and `exit` — the same prompts as each subcommand run flagless.

## Desktop GUI

```bash
sro-config gui
```

opens the Dictionary / Analysis / Visualiser tabs in one window. See
[Installation → The GUI](installation.md#the-gui) for the Tkinter requirement.

## Legacy batch orchestrator

`python -m sro_config.batch` (the old `legacy/Batching_Scripts/Configuration_Master.py`)
still works as a Y/N-prompted dict-then-config runner, but `sro-config config
--rmc6f-glob` is the more direct way to do real batch work.
