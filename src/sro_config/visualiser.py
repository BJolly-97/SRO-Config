"""
Created on Mon Jun 24 13:18:40 2024

@author: CDT3
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure


def _load_basis_and_config(dict_dir, sublattice):
    """Reads the .basisN/.cfgdictN files for one sub-lattice. Returns (basis_df, config_df)."""
    filepath = dict_dir.strip('"')
    sub_num = str(sublattice)

    basis_ext = None
    clapp_ext = None

    # Loop through files in the folder
    for stemname in os.listdir(filepath):
        if stemname.endswith(".basis" + sub_num):
            basis_ext = stemname
        if stemname.endswith(".cfgdict" + sub_num):
            clapp_ext = stemname

    if basis_ext is None or clapp_ext is None:
        raise FileNotFoundError(
            f"No '.basis{sub_num}'/'.cfgdict{sub_num}' files found in '{filepath}' for sub-lattice {sub_num}."
        )

    basis = open(os.path.join(filepath, basis_ext))
    line_read = basis.readlines()
    basis.close()

    lines = line_read.copy()
    del lines[0:2]
    del lines[-1]

    basis_df = pd.DataFrame(lines)
    basis_df = basis_df[0].str.split("\\s+", expand=True)
    basis_df.drop([0, 4, 5], axis=1, inplace=True)
    basis_df.rename(columns={1: "x", 2: "y", 3: "z", 5: "Atom No."}, inplace=True)

    config_dict = open(os.path.join(filepath, clapp_ext))
    config_read = config_dict.readlines()
    config_dict.close()

    config_df = pd.DataFrame(config_read)
    config_df = config_df[0].str.split("\\s+", expand=True)

    return basis_df, config_df


def _plotting_df_for_label(basis_df, config_df, label):
    """Looks up `label` (a Configuration label, e.g. '12') in config_df and returns the
    basis positions joined with their occupied(1)/empty(0) state as a DataFrame, or None
    if the label doesn't exist for this sub-lattice."""
    input_dec = None
    for n in range(len(config_df)):
        if config_df[1][n] == label:
            input_dec = int(config_df[0][n])
            break

    if input_dec is None:
        return None

    input_bin = bin(input_dec)
    full_bin = input_bin[2:].zfill(len(basis_df))
    full_bin = list(full_bin)
    bin_df = pd.DataFrame(full_bin)
    bin_df.rename(columns={0: "Bin"}, inplace=True)

    return pd.concat([basis_df, bin_df], axis=1)


def _draw_configuration(ax, plotting_df, label):
    """Draws the occupied(red)/empty(black) nearest-neighbour scatter for one configuration
    onto an existing 3D Axes."""
    for i in range(len(plotting_df)):
        if plotting_df["Bin"][i] == "1":
            ax.scatter(
                float(plotting_df["x"].iloc[i]),
                float(plotting_df["y"].iloc[i]),
                float(plotting_df["z"].iloc[i]),
                color="r",
                s=500,
            )
        elif plotting_df["Bin"][i] == "0":
            ax.scatter(
                float(plotting_df["x"].iloc[i]),
                float(plotting_df["y"].iloc[i]),
                float(plotting_df["z"].iloc[i]),
                color="black",
                s=500,
            )

    ax.scatter(0, 0, 0, marker="X", color="black", s=150)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("C" + label)


def build_figure(dict_dir, sublattice, label):
    """
    Builds a standalone matplotlib Figure for one Configuration label, without touching
    pyplot's global "current figure" state - safe to embed in a GUI (e.g. via
    FigureCanvasTkAgg(fig, master=...)) rather than only usable as a plt.show() popup.

    Args:   dict_dir    - Directory containing the .basisN/.cfgdictN files.        (Type: str)
            sublattice  - Which sub-lattice number to visualise.          (Type: int | str)
            label       - A single Configuration label (e.g. "12").              (Type: str)
    Returns:    A matplotlib.figure.Figure, or None if `label` doesn't exist for this
                sub-lattice.
    """
    basis_df, config_df = _load_basis_and_config(dict_dir, sublattice)
    plotting_df = _plotting_df_for_label(basis_df, config_df, label)
    if plotting_df is None:
        return None

    fig = Figure()
    ax = fig.add_subplot(projection="3d")
    _draw_configuration(ax, plotting_df, label)
    return fig


def run(dict_dir, sublattice, config):
    """
    Plots the given Clapp Configuration(s) for one sub-lattice as interactive 3D scatter
    plots (occupied neighbour = red, empty = black), one pop-up window per label.

    Args:   dict_dir    - Directory containing the .basisN/.cfgdictN files.        (Type: str)
            sublattice  - Which sub-lattice number to visualise (as printed in .finsub). (Type: int | str)
            config      - Configuration label(s) to plot. Either a comma-separated string
                          ("0,12,34") or a list of labels.              (Type: str | list[str])
    """
    basis_df, config_df = _load_basis_and_config(dict_dir, sublattice)

    input_config = config.split(",") if isinstance(config, str) else list(config)

    for label in input_config:
        plotting_df = _plotting_df_for_label(basis_df, config_df, label)

        if plotting_df is None:
            print(f"\nConfiguration label '{label}' not found for this sub-lattice - skipping.")
            continue

        axes = [1, 1, 1]
        data = np.ones(axes)
        data = data * 0.5

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        _draw_configuration(ax, plotting_df, label)

        plt.show()


def main(dict_dir=None):
    """Interactive entry point: repeatedly prompts for a sub-lattice and configuration
    label(s) to plot, offering to continue after each round, exactly as before. Delegates
    the actual plotting of each round to run()."""
    print("\n====================================================================\n")
    print("\t\tConfigurational Analysis - v1.0 (2024)\n")
    print("\t\t Graphical Configuration Visualiser\n")
    print("\t   Developed by: Benjamin E. Jolly; Lewis R. Owen\n")
    print("\t\t    University of Sheffield, UK\n")
    print("====================================================================\n")

    if dict_dir is None:
        dict_dir = input("Input Directory:\t")
    filepath = dict_dir.strip('"')

    sublattice_labels = None
    for stemname in os.listdir(filepath):
        if stemname.endswith(".finsub"):
            sublattice_labels = stemname

    if sublattice_labels is None:
        raise FileNotFoundError(
            f"No '.finsub' file found in '{filepath}'. Run 'dict' first to generate the dictionary files."
        )

    sublab_file = open(os.path.join(filepath, sublattice_labels))
    sublab_read = sublab_file.readlines()
    sublab_file.close()

    sublab = pd.DataFrame(sublab_read)

    exit_cond = 0

    while exit_cond == 0:
        print("\nEnter desired sublattice for analysis (e.g. 0):\n")
        for i in range(len(sublab)):
            print(sublab.loc[i, 0])

        sub_num = str(input())

        input_config_list = input(
            "\nInput desired configuration(s) (NB: For multiple configuration plots, separate values using commas.):\t"
        )

        run(dict_dir, sub_num, input_config_list)

        A = input("\nContinue with visualisation for selected sublattice? (Y/N)\n").strip().upper()
        if A == "Y":
            pass
        elif A == "N":
            exit_cond += 1
        else:
            print("\nInvalid Input.\n")
            exit_cond += 1

    print("\n--------------End---------------\n\n")


if __name__ == "__main__":
    main()
