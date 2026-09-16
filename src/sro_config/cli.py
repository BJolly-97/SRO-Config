"""
Single entry point for SRO-Config: `sro-config`.

- No arguments: the interactive command menu (equivalent to the old .bat/.sh launchers) -
  dict/config/vis/exit, each falling through to that module's fully-interactive main().
- A subcommand with no flags: the same interactive prompts as that menu command.
- A subcommand with flags: scripted, no prompts.
- `config`/`analyse` given more than one .rmc6f path (via repeated --rmc6f or --rmc6f-glob):
  batch mode - looped in-process via histograms.run_batch(), one dataset at a time, with
  per-file error handling so one bad file doesn't lose the whole run. A batch of one file
  and a batch of two hundred go through this exact same code path.
"""

import argparse
import glob as glob_module
import importlib.resources
import shutil
import sys
from pathlib import Path

from sro_config import dictionary, histograms, visualiser


def _run_repl():
    """The interactive command menu - equivalent to the old .bat/.sh launchers."""
    while True:
        command = (
            input(
                "> Enter command (i.e. dict (Configurational Dictionaries), "
                "config (Configurational Analysis), vis (Configuration Visualiser), "
                "gui (Desktop GUI), examples (Copy Example Data) or exit): "
            )
            .strip()
            .lower()
        )

        if command == "dict":
            dictionary.main()
        elif command == "config":
            histograms.main()
        elif command == "vis":
            visualiser.main()
        elif command == "gui":
            from sro_config.gui.app import (
                main as gui_main,
            )  # lazy: don't force a Tkinter/display dependency on plain CLI usage

            gui_main()
        elif command == "examples":
            _run_examples("examples")
        elif command == "exit":
            break
        else:
            print(f"Invalid command: {command}")


def _parse_equivalence(groups):
    """Turns repeated --equivalence "0,1" flags into [[0, 1], ...] for dictionary.run()/main()."""
    if groups is None:
        return None
    return [group.split(",") for group in groups]


def _resolve_rmc6f_paths(rmc6f, rmc6f_glob):
    paths = list(rmc6f) if rmc6f else []
    if rmc6f_glob:
        matched = sorted(glob_module.glob(rmc6f_glob))
        # Exclude this tool's own "_mb.rmc6f" output (histograms.run() writes one per input
        # file, alongside the .rmc6f itself) - otherwise re-running the same glob in the same
        # directory reprocesses last run's outputs as new inputs, growing every time.
        skipped = [p for p in matched if p.endswith("_mb.rmc6f")]
        matched = [p for p in matched if not p.endswith("_mb.rmc6f")]
        if skipped:
            print(
                f"Note: --rmc6f-glob matched {len(skipped)} of this tool's own '_mb.rmc6f' output file(s) - skipping those."
            )
        if not matched:
            print(f"Warning: --rmc6f-glob '{rmc6f_glob}' matched no (non-output) files.")
        paths.extend(matched)
    return paths


def _run_examples(dest):
    """Copies the bundled example dataset(s) out of the installed package to `dest`."""
    dest_dir = Path(dest)
    bundled = importlib.resources.files("sro_config") / "data" / "examples"

    dest_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for entry in sorted(bundled.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        target = dest_dir / entry.name
        if target.exists():
            print(f"Skipping '{target}': already exists.")
            continue
        with importlib.resources.as_file(entry) as source:
            shutil.copytree(source, target)
        copied.append(target)

    if copied:
        print(f"Copied {len(copied)} example(s) to '{dest_dir}':")
        for target in copied:
            print(f"  - {target}")
    else:
        print(f"No new examples copied (nothing to copy, or all already present in '{dest_dir}').")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="sro-config",
        description="Clapp-style configurational analysis of RMCProfile large-box models. "
        "Run with no arguments for the interactive menu.",
    )
    sub = parser.add_subparsers(dest="command")

    p_dict = sub.add_parser(
        "dict", help="Generate configurational dictionary files from a .cif structure."
    )
    p_dict.add_argument("--cif", help="Path to the .cif file. Omit to be prompted.")
    p_dict.add_argument(
        "--equivalence",
        action="append",
        metavar="I,J,...",
        help="Merge these sub-lattice indices into one combined sub-lattice (e.g. --equivalence 0,1). "
        "Repeat for multiple separate merge groups. Omit to be prompted interactively.",
    )
    p_dict.add_argument(
        "--no-equivalence",
        action="store_true",
        help="Explicitly skip equivalencing without prompting.",
    )

    p_analyse = sub.add_parser(
        "config",
        aliases=["analyse"],
        help="Run enhancement-factor analysis for one or many .rmc6f configurations.",
    )
    p_analyse.add_argument("--dict-dir", help="Directory containing the dictionary files.")
    p_analyse.add_argument(
        "--sublattice", help="Sub-lattice number to analyse (as printed in .finsub)."
    )
    p_analyse.add_argument(
        "--rmc6f", nargs="+", metavar="PATH", help="One or more .rmc6f files to analyse."
    )
    p_analyse.add_argument(
        "--rmc6f-glob",
        metavar="PATTERN",
        help='Glob pattern matching many .rmc6f files, e.g. "configs/*.rmc6f".',
    )

    p_vis = sub.add_parser("vis", help="Plot Clapp configurations for a sub-lattice.")
    p_vis.add_argument("--dict-dir", help="Directory containing the dictionary files.")
    p_vis.add_argument("--sublattice", help="Sub-lattice number to visualise.")
    p_vis.add_argument(
        "--config", help='Configuration label(s) to plot, comma-separated, e.g. "0,12,34".'
    )

    sub.add_parser(
        "gui", help="Launch the desktop GUI (Dictionary/Analysis/Visualiser as one window)."
    )

    p_examples = sub.add_parser(
        "examples", help="Copy the bundled example dataset(s) to a local directory."
    )
    p_examples.add_argument(
        "--dest",
        default="examples",
        help="Directory to copy the examples into (default: ./examples).",
    )

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        _run_repl()
        return

    if args.command == "dict":
        equivalence = [] if args.no_equivalence else _parse_equivalence(args.equivalence)
        dictionary.main(cif=args.cif, equivalence=equivalence)

    elif args.command in ("config", "analyse"):
        rmc6f_paths = _resolve_rmc6f_paths(args.rmc6f, args.rmc6f_glob)

        if not rmc6f_paths:
            # Nothing given via flags -> fully interactive, one file (today's exact prompts).
            histograms.main(dict_dir=args.dict_dir, sublattice=args.sublattice)
        else:
            if not args.dict_dir:
                parser.error("config: --dict-dir is required when --rmc6f/--rmc6f-glob is given.")
            if args.sublattice is None:
                parser.error("config: --sublattice is required when --rmc6f/--rmc6f-glob is given.")

            _succeeded, failed = histograms.run_batch(args.dict_dir, args.sublattice, rmc6f_paths)
            if failed:
                sys.exit(1)

    elif args.command == "vis":
        if args.dict_dir and args.sublattice is not None and args.config:
            visualiser.run(args.dict_dir, args.sublattice, args.config)
        else:
            visualiser.main(dict_dir=args.dict_dir)

    elif args.command == "gui":
        from sro_config.gui.app import (
            main as gui_main,
        )  # lazy: don't force a Tkinter/display dependency on plain CLI usage

        gui_main()

    elif args.command == "examples":
        _run_examples(args.dest)


if __name__ == "__main__":
    main()
