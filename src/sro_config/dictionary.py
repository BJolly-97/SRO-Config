"""
Created on Tue Aug 22 13:57:07 2023

@author: CDT3
"""

# %%Modules

import copy
import itertools
import os
import re
import sys
from fractions import Fraction

import numpy as np
import pandas as pd
from tqdm import tqdm

# %%


# Disable
def blockPrint():
    sys.stdout = open(os.devnull, "w")


# Restore
def enablePrint():
    sys.stdout = sys.__stdout__


# %% Functions:


def Polar_dict(cartesian_frame, a, b, c, alpha, beta, gamma, col1="x", col2="y", col3="z"):
    """
    Acts to find an atom in the generated supercell - with conditions to prevent edge cases - and find the number of nearest neighbours for each sublattice
    Args:       cartesian_frame  - List of fractional coordinates, as taken from the .cif file, for each atom-type   (Type: Dictionary)
                a               - Unit cell length a                                                                (Type: Float)
                b               - Unit cell length b                                                                (Type: Float)
                c               - Unit cell length c                                                                (Type: Float)
                alpha           - Internal angle alpha                                                              (Type: Float)
                beta            - Internal angle beta                                                               (Type: Float)
                gamma           - Internal angle gamma                                                              (Type: Float)
    Returns:    polar_list      - New list of coordinates in polar/orthogonal form                                  (Type: List)
    """
    import numpy as np

    x, y, z = cartesian_frame[col1], cartesian_frame[col2], cartesian_frame[col3]

    alp = alpha * (np.pi / 180)
    bet = beta * (np.pi / 180)
    gam = gamma * (np.pi / 180)

    cos_a_star = (np.cos(bet) * np.cos(gam) - np.cos(alp)) / (np.sin(bet) * np.sin(gam))
    sin_a_star = (1 - (cos_a_star**2)) ** 0.5

    X = (x * a) + (y * b * np.cos(gam)) + (z * c * np.cos(bet))

    Y = (y * b * np.sin(gam)) - (z * c * np.sin(bet) * cos_a_star)

    Z = z * c * np.sin(bet) * sin_a_star

    cartesian_frame[col1] = X
    cartesian_frame[col2] = Y
    cartesian_frame[col3] = Z

    # Reverted to the original literal `1**(-5)` (== 1.0) tolerance on request - this is the
    # exact original calculation, not the 1e-5 fix proposed and then reverted earlier.
    zero_tol = 1 ** (-5)
    for col in (col1, col2, col3):
        near_zero = cartesian_frame[col].abs() < zero_tol
        cartesian_frame.loc[near_zero, col] = 0.0

    return cartesian_frame


# %%%


# Define the function to clean the string
def clean_expression(expression):
    """


    Parameters
    ----------
    expression : TYPE
        DESCRIPTION.

    Returns
    -------
    cleaned_expression : TYPE
        DESCRIPTION.

    """
    # Find all valid matches ('x', 'y', 'z', '+x', '+y', '+z', '-x', '-y', '-z')
    valid_terms = re.findall(r"[+-]?[xyz]", expression)

    # Join the valid terms back together
    cleaned_expression = "".join(valid_terms)

    return cleaned_expression


def parse_cif_numeric_value(line):
    """
    Extracts the numeric value from a CIF header line (e.g. '_cell_length_a   5.4310(2)\n'),
    stripping any uncertainty brackets/whitespace, and returns it as a float.
    """
    raw = line.split()[1::2][0]
    return float(re.sub(r"[()\n]", "", raw))


# %%% Nearest Neighbours
def N_N(dictionary, no, cen_atom_dict, super_dim, len_a, len_b, len_c):
    """
    Acts to find an atom in the generated supercell - with conditions to prevent edge cases - and find the number of nearest neighbours for each sublattice
    Args:       dictionary      - The supercell dictionary with all sublattices (Type: Dictionary)
                k               - The number of sublattices, i.e. the length of the dictionary (Type: Integer)
                cen_atom_dict   - The location to store the located atom's coordinates (Type: Dictionary)
                super_dim       - The supercell dimensions (nx, ny, nz), in unit cells (Type: Tuple)
                len_a, len_b, len_c - Unit cell lengths (Type: Float)
    Returns:    count           - The number of nearest neighbours (Type: Integer)
                min_val         - The distance of the nearest neighbours from the located atom (Type: Float)
                Atom            - The index of the central atom (Type: Integer)
    """
    # Reverted to the original atom-selection loop on request (exact original calculation).
    Atom = round(0.5 * len(dictionary[no]))  # Find atom at roughly half way through dataframe

    while (
        (dictionary[no]["x"].iloc[Atom] == 0.0)
        or (dictionary[no]["x"].iloc[Atom] == super_dim[0] * len_a)
        or (dictionary[no]["y"].iloc[Atom] == 0.0)
        or (dictionary[no]["y"].iloc[Atom] == super_dim[1] * len_b)
        or (dictionary[no]["z"].iloc[Atom] == 0.0)
        or (dictionary[no]["z"].iloc[Atom] == super_dim[2] * len_c)
    ):
        Atom = Atom + 1  # If atom along edge, add a few on to ensure it's an atom in the body

    cen_atom_dict[no] = pd.DataFrame(dictionary[no].iloc[Atom])

    # This calculates the distance from the selected atom using r = sqrt(x^2 + y^2 +z^2), and uses that to locate the number of atoms with the shortest distance from
    # the 'origin' atom in question
    ax, ay, az = dictionary[no].loc[Atom, ["x", "y", "z"]]
    dictionary[no]["r"] = np.round(
        np.sqrt(
            (dictionary[no]["x"] - ax) ** 2
            + (dictionary[no]["y"] - ay) ** 2
            + (dictionary[no]["z"] - az) ** 2
        ),
        2,
    ).astype("float")

    min_val = dictionary[no].loc[dictionary[no]["r"] > 0.0, "r"].min()

    count = dictionary[no]["r"].value_counts()[min_val]

    return count, min_val, Atom


# %%% Vectorise Nearest Neighbours


def NN_vector(NN_dict, cen_atom_dict, length):
    """
    Produces a new basis set of nearest neighbours, using unit cell vector values
    Args:       NN_dict         - The nearest neighbour dictionary, as produced by the N_N function
                cen_atom_dict   - The dictionary of located atoms produced by the N_N function
                length          - The lengths of the unit cell in directions a, b and c
    Returns:    NN_dict, in unit vector form
    """

    for i in range(len(NN_dict)):
        for j in range(len(NN_dict[i])):
            for k in [0, 1, 2]:
                NN_dict[i].loc[j, k] = float(
                    NN_dict[i][k].iloc[j] - cen_atom_dict[i][k].iloc[0]
                )  # Takesw each x, y, z value for each NN atom and subtracts the x, y, z coordinates of the centre atom, to produce atomic coordinates in real-distance units

    for i in range(len(NN_dict)):
        for k in [0, 1, 2]:
            NN_dict[i][k] = round((NN_dict[i][k] / length[k]), 7)


def run(cif, equivalence=None):
    """
    Generates the Configurational Dictionary files for one .cif structure - the .cellpos,
    .initsub, .finsub, .basisX, .symX, .cfgdictX, and .binomX files described in the README.

    Args:   cif          - Path to the .cif file to analyse.                    (Type: str)
            equivalence  - Lattice-site equivalences to merge into combined sub-lattices,
                            e.g. [[0, 1]] merges sites 0 and 1 into one disordered
                            sub-lattice, [[0, 1], [2, 3]] merges two separate pairs. Each
                            group may be a list of ints or a comma-separated string ("0,1").
                            None (the default) prompts for this interactively, matching the
                            original behaviour; [] explicitly skips equivalencing without
                            prompting.                              (Type: list[list[int]] | None)
    Returns:    filename_stem - The .cif path with its extension stripped, i.e. the common
                                 prefix of every file this call writes.               (Type: str)
    """

    # %%Read .cif file

    # filename = input("Input .cif file path (w/out apostrophes): ")

    # filename = r"G:\My Drive\Code_General\ICSD_CollCode291.cif" #Primitive _+ Weird
    # filename = r"G:\My Drive\Code_General\Testing\EntryWithCollCode14754.cif" #BCC
    # filename = r"G:\My Drive\Code_General\ICSD_CollCode37502.cif" #FCC
    # filename= r"G:\My Drive\Code_General\Testing\LN_structurefromGEMdata_24-02-20.cif"
    # filename = r"G:\My Drive\Code_General\Testing\EntryWithCollCode29734.cif" #HCP
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\1510113.cif" #P4/mmm Tetragonal CuAu, with equivalencies required
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\CuAu_mp-522_symmetrized.cif" #Tetragonal, P4/mmm (AuCu)
    # filename = r"G:/My Drive/Code_General/Testing/Improved_Version/New_CIFs/I4mmm_test.cif" #I4/mmm gamma with tetragonal distortion
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\EntryWithCollCode95729.cif" #Pmmm Orthorhombic
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\EntryWithCollCode290661.cif" #P1 triclinic
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\EntryWithCollCode113.cif" #P21/c Monoclinic

    # ------------------------------------------------------------------ERIN FILES FOR TESTING ------------------------------------------------------------------------------------------------

    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\monoclinic P2m Ce0.33NbO3.cif" #Monoclinic P2m
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\Orthrhombic Cmmm La0.33NbO3.cif"
    # filename = r"G:\My Drive\Code_General\Testing\Improved_Version\New_CIFs\Tetragonal P4mmm La0.25Na0.25NbO3.cif"

    # %%

    filename = cif.strip('"')

    with open(filename, encoding="utf-8") as file:
        line_read = file.readlines()

    # file = open(filename, "r")

    # file.seek(0) #Go back to start of file with 0
    # 0
    # line_read = file.readlines()

    # file.close()

    lines = line_read.copy()

    filenamex = filename.split(".")
    filename_stem = filename.replace("." + str(filenamex[-1]), "")
    print("Stem is " + str(filename_stem))
    print("\n")

    # %%

    for line in line_read:
        if (
            "_atom_site_aniso_label\n" in line
        ):  # Noticed some files of more complex crystal structures have aniso sections - leaving it in the file for now in case I need it later
            A = line_read.index(line)
            # print(A)
            lines.pop(A - 1)

    # %% Find relevant information in .cif file
    sym_ops = []

    for line in lines:
        if "_chemical_name_common" in line:
            chem_nm = line.split("'")[1::2]
            if len(chem_nm) == 0:
                print("No chemical name found.")
            else:
                print("Chemical Name:", chem_nm[0])

        elif (
            "_space_group_name_H-M" in line
        ):  # Finds and prints space group by identifying line with space group text, then finding the characters BETWEEN the apostrophes
            sp_gr = re.split("'| ", line)
            print("Space Group:", sp_gr[-1])

        elif (
            "_space_group_IT_number" in line
        ):  # Finds and prints arbitrary indexing of space group, again by identifying relevant text and then printing the digit section
            it_no = [int(i) for i in line.split() if i.isdigit()]
            print("IT no.:", it_no[0])

        elif (
            "_cell_length_a" in line
        ):  # Cell length/angle values, incl. any CIF uncertainty brackets e.g. 5.4310(2)
            len_a = parse_cif_numeric_value(line)
            print("Cell Length a: ", len_a, "Ang")

        elif "_cell_length_b" in line:
            len_b = parse_cif_numeric_value(line)
            print("Cell Length b: ", len_b, "Ang")

        elif "_cell_length_c" in line:
            len_c = parse_cif_numeric_value(line)
            print("Cell Length c: ", len_c, "Ang")

        elif "_cell_angle_alpha" in line:
            ang_a = parse_cif_numeric_value(line)
            print("Angle alpha: ", ang_a, "deg")

        elif "_cell_angle_beta" in line:
            ang_b = parse_cif_numeric_value(line)
            print("Angle beta: ", ang_b, "deg")

        elif "_cell_angle_gamma" in line:
            ang_c = parse_cif_numeric_value(line)
            print("Angle gamma: ", ang_c, "deg")

        all_line = line.split(
            "'"
        )[
            1::2
        ]  # Takes all lines with characters between apostrophes, as I think all .cif files have symmetry operations in apostrophes (Note: They do not.)

        if len(all_line) == 0:
            if ("x" in line) and ("y" in line) and ("z" in line) and ("," in line):
                sym_ops.append(line)

        else:
            for line2 in all_line:
                if (
                    ("x" in line2)
                    and ("y" in line2)
                    and ("z" in line2)
                    and all(vowel not in line2 for vowel in "aeiouAEIOU")
                ):  # Takes all lines with characters between apostrophes and containing x,y,z to isolate symmetry operators
                    sym_ops.append(line2)

    # %% Pick out atomic positions and establish identity matrix

    for i in range(len(lines)):
        lines[i] = lines[i].lstrip(" ")

    lengths = [len_a, len_b, len_c]  # Produce list of unit cell lengths for later usage

    from itertools import filterfalse

    ident = np.identity(3)  # Create identity matrix (1s on diagonal) of size 3x3

    index_line_start = lines.index(
        "_atom_site_label\n"
    )  # Finds instance of atomic_site_label, which is always first in list

    index_line_end = lines.index(
        "_atom_site_fract_x\n"
    )  # Finds instance of atom_site_fract_x, which is always the first coordinate

    final_loop_index = max(
        index for index, item in enumerate(lines) if item == "loop_\n"
    )  # Finds the final instance of the 'loop_' command, which always precedes the atomic positions section of the file

    coord_list = lines[(final_loop_index + 1) :]

    new_list = [s[0:] for s in coord_list if (s[0:1] == "_") or s[0:1] == "#"]

    new_coord_list = list(
        filterfalse(new_list.__contains__, coord_list)
    )  # The last several lines produce a list of everything after the loop command, removes the atomic positions, and creates new list populated by the atomic positions

    coord_df = pd.DataFrame(new_coord_list, columns=["Full Line"])

    coord_df = coord_df[
        "Full Line"
    ].str.split(
        expand=True
    )  # These lines produce a dataframe of the atomic position lines and then split the line into individual objects delimited by space, for the coordinates
    coord_df = coord_df.drop_duplicates(subset=[0], keep="first").reset_index(drop=True)
    coord_df = coord_df.dropna()  # Ensures empty rows are lost

    for col in range(
        len(coord_df.columns)
    ):  # This section of code removes brackets from atomic positions that extend to a number of degrees of precision (i.e. 0.0000(01))
        for row in range(len(coord_df)):
            value = str(coord_df.iloc[row, col])  # Convert to string
            # Use regex to remove all parentheses
            value = re.sub(r"[()]", "", value)
            coord_df.iloc[row, col] = value

            # if ("(" in coord_df[col][row]):
            #     coord_df[col][row] = coord_df[col][row].replace("(", "")
            # if (")" in coord_df[col][row]):
            #     coord_df[col][row] = coord_df[col][row].replace(")", "")

    # %% Converting symmetry operators to index matrices

    sym_ops_df = pd.DataFrame(sym_ops, columns=["Symmetry Operations"])  # Created dataframe

    D = {}  # Create dictionary

    store_chem_index = {}

    coord_index_start = new_list.index("_atom_site_fract_x\n")

    for val in range(len(coord_df)):
        chem_index = [
            coord_df[coord_index_start][val],
            coord_df[coord_index_start + 1][val],
            coord_df[coord_index_start + 2][val],
        ]  # Creates the atomic position arrays for x y z

        chem_index = [float(val) for val in chem_index]  # Converts array/list to floats

        chem_index = [Fraction(val).limit_denominator(8) for val in chem_index]

        store_chem_index[val] = pd.DataFrame(chem_index)
        store_chem_index[val] = store_chem_index[val].transpose()

        tot_sym_op = (
            ((-chem_index[2]) * ident[0])
            + ((chem_index[0]) * ident[1])
            + ((-chem_index[1]) * ident[2])
        )
        # This needs to be per symmetry operation; i.e.:
        # x, y, z = (chem_index[0]*ident[0]) + (chem_index[1]*ident[1]) + (chem_index[2]*ident[2])
        # z, x, y = (chem_index[2]*ident[0]) + (chem_index[0]*ident[1]) + (chem_index[1]*ident[2])
        # -x, -z, y = (-chem_index[0]*ident[0]) + (-chem_index[2]*ident[1]) + (chem_index[1]*ident[2])

        sym_ops_df_loop = sym_ops_df.copy(deep=True)  # Created duplicate dataframe
        sym_ops_df_loop[["x", "y", "z"]] = sym_ops_df_loop["Symmetry Operations"].str.split(
            ",", expand=True
        )  # Separates symmetry operators by comma
        sym_ops_df_loop[["x", "y", "z"]] = sym_ops_df_loop[["x", "y", "z"]].astype(
            object
        )  # .str.split gives strict string-dtype columns on pandas 3.x, but the loop below assigns Fraction objects into them below

        char_to_replace = {
            "x": str(chem_index[0]),
            "-x": str(-chem_index[0]),
            "y": str(chem_index[1]),
            "-y": str(-chem_index[1]),
            "z": str(chem_index[2]),
            "-z": str(-chem_index[2]),
        }  # , '1/2':str(0.5)}
        columns_A = ["x", "y", "z"]
        # Creates dictionary of symmetry operators and their equivalent atomic positions as given by .cif file
        # Columns defined just to convert columns in dataframe to float eventually

        for key, value in char_to_replace.items():
            for i in columns_A:
                for j in range(len(sym_ops)):
                    sym_ops_df_loop.loc[j, i] = sym_ops_df_loop.loc[j, i].replace(
                        key, value
                    )  # Goes through the dataframe columns and replaces all instances of x, y and z with the atomic positions from the .cif file, effectively generating the symmetric positions

        for i in columns_A:
            for j in range(len(sym_ops)):
                sym_ops_df_loop.loc[j, i] = str(
                    eval(sym_ops_df_loop.loc[j, i])
                )  # In theory, takes any symmetry operation involving + or - some fraction and evaluates for exact position
                sym_ops_df_loop.loc[j, i] = Fraction(sym_ops_df_loop.loc[j, i]).limit_denominator(8)

        D[val] = sym_ops_df_loop  # Produce individual dictionary entries for each atom type

    # %% Reducing the atomic positions by equivalence

    asym_unitcell = {}  # Create new dictionary for reduced atomic positions

    for num in range(len(D)):
        asym_unitcell[num] = D[num].drop(["Symmetry Operations"], axis=1)
        for j in ["x", "y", "z"]:
            asym_unitcell[num][j] = asym_unitcell[num][j].astype("float")
        asym_unitcell[num] = asym_unitcell[
            num
        ].drop_duplicates()  # Reduce the duplicated positions in each array to leave unique positions
        asym_unitcell[num] = asym_unitcell[num].reset_index()
        asym_unitcell[num] = asym_unitcell[num].drop(["index"], axis=1)

    for i in range(len(asym_unitcell)):
        for j in range(len(asym_unitcell[i])):
            if asym_unitcell[i].loc[j, "x"] < 0:
                asym_unitcell[i].loc[j, "x"] = asym_unitcell[i].loc[j, "x"] + 1
            if asym_unitcell[i].loc[j, "y"] < 0:
                asym_unitcell[i].loc[j, "y"] = asym_unitcell[i].loc[j, "y"] + 1
            if asym_unitcell[i].loc[j, "z"] < 0:
                asym_unitcell[i].loc[j, "z"] = asym_unitcell[i].loc[j, "z"] + 1

    asym_unitcell_dict = {}
    for k in range(len(asym_unitcell)):
        asym_unitcell_dict[k] = asym_unitcell[k].drop_duplicates()
        asym_unitcell_dict[k].reset_index()

    asym_file = open(filename_stem + ".cellpos", "w")
    for i in range(len(asym_unitcell_dict)):
        for j in range(len(asym_unitcell_dict[i])):
            asym_file.write(
                str(asym_unitcell_dict[i]["x"].iloc[j])
                + ","
                + str(asym_unitcell_dict[i]["y"].iloc[j])
                + ","
                + str(asym_unitcell_dict[i]["z"].iloc[j])
                + "\n"
            )

    asym_file.close()  # Writes a basis set file for reconstructing the configurations from binary
    print("Unit Cell Positions have been saved (.cellpos).")

    # %% Continue making Unit Cell

    unitcell = copy.deepcopy(asym_unitcell)

    for k in range(len(unitcell)):
        unitcell[k]["x"] = unitcell[k]["x"].multiply(
            len_a
        )  # This turns the standard asymmetric cell, which contains coords from 0-1, into a unit cell of specified size
        unitcell[k]["y"] = unitcell[k]["y"].multiply(len_b)
        unitcell[k]["z"] = unitcell[k]["z"].multiply(len_c)

    # %% Produce 2x2x2 supercell of asymmetric unit cell, to condense into unit cell

    unitcell_dict = {}  #  Creates empty dictionary to store DataFrames for each atom type in the supercell

    unit_dim = (2, 2, 2)  # Define the dimensions of the supercell (e.g., 3x3x3)

    for (
        atom_type,
        atom_df,
    ) in (
        unitcell.items()
    ):  # Iterate through the 'supercell' dictionary (copied from E to preserve initial unit cell)
        unitcell_atoms = []  # Create a list to store copies of the atom DataFrames for the supercell

        for i in range(unit_dim[0]):  # Iterate through each cell in the supercell
            for j in range(unit_dim[1]):
                for k in range(unit_dim[2]):
                    unitcell_df = (
                        atom_df.copy()
                    )  # Copy the atom DataFrame and adjust the coordinates

                    unitcell_df["x"] += i * len_a
                    unitcell_df["y"] += j * len_b
                    unitcell_df["z"] += k * len_c

                    unitcell_atoms.append(
                        unitcell_df
                    )  # Append the modified DataFrame to the supercell list

        unitcell_df = pd.concat(
            unitcell_atoms, ignore_index=True
        )  # Combine all the DataFrames into a single DataFrame

        unitcell_dict[atom_type] = (
            unitcell_df  # Store the supercell DataFrame in the supercell dictionary
        )

    # %%

    for k in range(len(unitcell_dict)):
        unitcell_dict[k] = unitcell_dict[k].drop_duplicates()
        unitcell_dict[k].reset_index(drop=True, inplace=True)

    # %% Create final unit cell dictionary

    unitcell_dict_final = copy.deepcopy(
        unitcell_dict
    )  # Final unit cell dictionary of atomic positions, from 0 to unit cell length

    for k in range(len(unitcell_dict)):
        for i in range(len(unitcell_dict[k])):
            if (
                (unitcell_dict[k]["x"].iloc[i] > len_a)
                or (unitcell_dict[k]["y"].iloc[i] > len_b)
                or (unitcell_dict[k]["z"].iloc[i] > len_c)
            ):  # I.e. locate atoms outside of unit cell size in each direction
                unitcell_dict_final[k].drop([i], inplace=True)

        unitcell_dict_final[k].reset_index(drop=True, inplace=True)

    # %% Create and save dataframes for supercell

    supercell = unitcell_dict_final.copy()

    for i in range(len(coord_df)):
        print(str(i) + ")\t" + str(coord_df[0].iloc[i]))

    # %% Set Equivalences

    super_answer = []

    atom_name_storage = list(coord_df[1])

    def _apply_equivalence_group(answer_list):
        """Merges the sub-lattices named in `answer_list` (a list of ints) into one combined
        sub-lattice, appending it to `supercell`/`atom_name_storage` in place."""
        merge_df = pd.DataFrame()
        for i in answer_list:
            merge_df = pd.concat([merge_df, supercell[i]], axis=0)

        joined_element = "/".join(atom_name_storage[i] for i in answer_list)
        atom_name_storage.append(joined_element)

        merge_df.drop_duplicates(inplace=True)
        merge_df.reset_index(inplace=True)
        merge_df.drop(["index"], axis=1, inplace=True)
        supercell[len(supercell)] = merge_df

    if len(coord_df) <= 1:
        if equivalence:
            raise ValueError(
                "`equivalence` was given, but this structure only has one constituent atom type - there is nothing to merge."
            )
        answer = "None."

    elif equivalence is not None:
        # Scripted path: use the given groups directly, no prompting.
        for group in equivalence:
            answer_list = [int(x) for x in (group.split(",") if isinstance(group, str) else group)]
            super_answer.append(answer_list)
            _apply_equivalence_group(answer_list)

        if super_answer:
            super_answer_merge = list(itertools.chain.from_iterable(super_answer))
            super_answer_merge = list(dict.fromkeys(super_answer_merge))
            for i in super_answer_merge:
                del supercell[i]
            supercell = {i: v for i, v in enumerate(supercell.values())}
            answer = "Y"
        else:
            answer = "N"

    else:
        # Interactive path: prompt for each equivalence group in turn.
        answer = (
            input("\nWould you like to set any lattice-site equivalences? (Y/N):\t").strip().upper()
        )

        if answer == "N":
            pass
        elif answer == "Y":
            exit_condition = 0
            while exit_condition == 0:
                answer_2 = input(
                    "Select equivalent atomic sublattices, in the form '0,1,2,...,N':\t"
                )
                answer_list = [int(x) for x in answer_2.split(",")]
                super_answer.append(answer_list)
                _apply_equivalence_group(answer_list)

                answer_3 = (
                    input("Would you like to select another equivalency? (Y/N):\t").strip().upper()
                )

                if answer_3 == "Y":
                    continue
                else:
                    super_answer_merge = list(itertools.chain.from_iterable(super_answer))
                    super_answer_merge = list(dict.fromkeys(super_answer_merge))
                    for i in super_answer_merge:
                        del supercell[i]
                    supercell = {i: v for i, v in enumerate(supercell.values())}
                    exit_condition += 1

        else:
            print("Invalid input.\n")
            sys.exit()

    atom_name = pd.DataFrame(atom_name_storage)

    if (len(coord_df) > 1) and (answer == "Y"):
        for i in super_answer_merge:
            atom_name = atom_name.drop(i)

        atom_name.reset_index(inplace=True)
        atom_name.drop(["index"], axis=1, inplace=True)

    else:
        pass

    # %%

    sub_file = open(filename_stem + ".initsub", "w")
    for i in range(len(atom_name)):
        sub_file.write("Sub-lattice " + str(i) + ":\t" + atom_name.loc[i, 0] + "\n")
    sub_file.close()
    print("\n")
    print("Initial sub-lattice labels file saved (.initsub).")

    # %%

    supercell_dict = {}  #  Creates empty dictionary to store DataFrames for each atom type in the supercell

    super_dim = (5, 5, 5)  # Define the dimensions of the supercell (e.g., 3x3x3)

    for (
        atom_type,
        atom_df,
    ) in (
        supercell.items()
    ):  # Iterate through the 'supercell' dictionary (copied from E to preserve initial unit cell)
        supercell_atoms = []  # Create a list to store copies of the atom DataFrames for the supercell

        for i in range(super_dim[0]):  # Iterate through each cell in the supercell
            for j in range(super_dim[1]):
                for k in range(super_dim[2]):
                    cell_df = atom_df.copy()  # Copy the atom DataFrame and adjust the coordinates

                    cell_df["x"] += i * len_a
                    cell_df["y"] += j * len_b
                    cell_df["z"] += k * len_c

                    supercell_atoms.append(
                        cell_df
                    )  # Append the modified DataFrame to the supercell list

        supercell_df = pd.concat(
            supercell_atoms, ignore_index=True
        )  # Combine all the DataFrames into a single DataFrame

        supercell_dict[atom_type] = (
            supercell_df  # Store the supercell DataFrame in the supercell dictionary
        )
        supercell_dict[atom_type].drop_duplicates()

    # %%

    supercell_new = {}
    for k in range(len(supercell_dict)):
        supercell_new[k] = supercell_dict[k]
        for j in ["x", "y", "z"]:
            supercell_new[k][j] = round(supercell_new[k][j], 6)

        supercell_new[k].drop_duplicates(inplace=True)
        supercell_new[k].reset_index(inplace=True)
        supercell_new[k].drop(["index"], axis=1, inplace=True)

    # %%

    supercell_storage = copy.deepcopy(supercell_new)

    for i in range(len(supercell_new)):
        supercell_new[i]["x"] = supercell_new[i]["x"] / len_a
        supercell_new[i]["y"] = supercell_new[i]["y"] / len_b
        supercell_new[i]["z"] = supercell_new[i]["z"] / len_c

    for k in range(len(supercell_new)):
        supercell_new[k] = Polar_dict(supercell_new[k], len_a, len_b, len_c, ang_a, ang_b, ang_c)

    # %%Nearest Neighbours

    Near_N = []
    cen_atom = {}

    for k in range(len(supercell_new)):
        NN = N_N(supercell_new, k, cen_atom, super_dim, len_a, len_b, len_c)
        NN = np.asarray(NN)
        Near_N.append(NN)
        print(
            "No. Nearest Neighbours ", atom_name[0].iloc[k], ": ", NN
        )  # Using this function allows the number of nearest neighbours (and the distance) to be stored for each atom type

    for i in range(len(Near_N)):
        if int(Near_N[i][0] == 1):
            print(
                "\nSublattice "
                + str(atom_name[0].iloc[i])
                + " has only one nearest neighbour atom. Configurational analysis for this sublattice is therefore halted."
            )
            fail_basis_file = open(filename_stem + ".halt" + str(i), "w")
            fail_basis_file.write(
                "The "
                + str(atom_name[0].iloc[i])
                + " sublattice has only one nearest neighbour. Configurational analysis for this sublattice is therefore halted.\n"
            )
            fail_basis_file.close()
            del supercell_new[i]
            del cen_atom[i]
            del supercell_storage[i]
            atom_name = atom_name.drop(index=[i])
        else:
            pass

    Near_N = [x for x in Near_N if x[0] != 1]

    supercell_new = {i: v for i, v in enumerate(supercell_new.values())}
    cen_atom = {i: v for i, v in enumerate(cen_atom.values())}
    supercell_storage = {i: v for i, v in enumerate(supercell_storage.values())}
    atom_name.reset_index(inplace=True)
    atom_name.drop(["index"], axis=1, inplace=True)

    # %%

    sub_file = open(filename_stem + ".finsub", "w")
    for i in range(len(atom_name)):
        sub_file.write("Sub-lattice " + str(i) + ":\t" + atom_name.loc[i, 0] + "\n")
    sub_file.close()
    print("\n")
    print("Final sub-lattice labels file saved (.finsub).")

    # %%

    N_N_List_super = {}  # Create super dictionary of nearest neighbour for all lattices
    cols_list = {}

    for k in range(len(supercell_new)):
        N_N_List = pd.DataFrame()  # Create dictionary for each set of nearest neighbours

        for i in range(len(supercell_new[k])):
            if supercell_new[k]["r"].iloc[i] == Near_N[k][1]:
                N_N_List[i] = pd.DataFrame(
                    supercell_new[k].iloc[i]
                )  # Store coordinates of all NN atoms
            elif (supercell_new[k]["r"].iloc[i] < Near_N[k][1] + 0.015) and (
                supercell_new[k]["r"].iloc[i] > 0.0
            ):
                N_N_List[i] = pd.DataFrame(supercell_new[k].iloc[i])

        N_N_List_super[k] = (
            N_N_List  # Store each list of NN atoms as dataframe in NN_super dictionary; each row is ultimately one set of coordinates
        )
        cols_list[k] = N_N_List_super[k].columns.values

    for k in range(len(N_N_List_super)):
        N_N_List_super[k] = N_N_List_super[k].drop_duplicates()
        N_N_List_super[k].columns = range(N_N_List_super[k].columns.size)
        N_N_List_super[k].reset_index(inplace=True)
        N_N_List_super[k].drop(["index"], axis=1, inplace=True)
        N_N_List_super[k] = N_N_List_super[k].transpose()

    for k in range(len(cen_atom)):
        cen_atom[k].columns = range(cen_atom[k].columns.size)
        cen_atom[k].reset_index(inplace=True)
        cen_atom[k].drop(["index"], axis=1, inplace=True)
        cen_atom[k] = cen_atom[k].transpose()

    # %%

    Frac_Supercell = {}

    for i in range(len(cols_list)):
        Frac_Supercell[i] = supercell_storage[i].loc[
            cols_list[i]
        ]  # single indexed lookup instead of rescanning the whole supercell per NN atom

    for k in range(len(Frac_Supercell)):
        Frac_Supercell[k].columns = range(Frac_Supercell[k].columns.size)
        Frac_Supercell[k].reset_index(inplace=True)
        Frac_Supercell[k].drop(["index"], axis=1, inplace=True)

    cen_atom_frac = {}

    for i in range(len(cen_atom)):
        cen_atom_frac[i] = pd.DataFrame(supercell_storage[i].iloc[int(Near_N[i][2])])
        cen_atom_frac[i].reset_index(inplace=True)
        cen_atom_frac[i].drop(["index"], axis=1, inplace=True)
        cen_atom_frac[i] = cen_atom_frac[i].transpose()
        cen_atom_frac[i].reset_index(inplace=True)
        cen_atom_frac[i].drop(["index"], axis=1, inplace=True)

    # %% Convert atom positions into atomic coordinates from central atom of NN group

    NN_v = copy.deepcopy(Frac_Supercell)

    if (ang_a == 90.0) and (ang_b == 90.0) and (ang_c == 90.0):
        NN_vector(
            NN_v, cen_atom, lengths
        )  # Re-writes NN_v, a copy of the nearest neighbour dataframes, to be given in atomic coordinates
    else:
        NN_vector(NN_v, cen_atom_frac, lengths)

    # %%Create and save Basis Set

    for i in range(len(NN_v)):
        NN_v[i] = NN_v[i].sort_values(
            by=[2, 1, 0], ascending=[True, True, True]
        )  # Order the basis set by increasing z, y, then x coordinates
        NN_v[i].reset_index(inplace=True)
        NN_v[i].drop(["index"], axis=1, inplace=True)

    for i in range(len(NN_v)):
        # Numbers the atoms of the basis set for use in nearest neighbour symmetry operations and the production of configurations.
        # (Was `NN_v[i]['Atom No.'] = ""` then a per-row loop - as of pandas 3.x that "" initializes
        # a strict string-dtype column, and assigning an int into it raises TypeError. Assigning the
        # whole numbered range at once sidesteps that and is also faster.)
        NN_v[i]["Atom No."] = range(1, len(NN_v[i]) + 1)

    for i in range(len(NN_v)):
        basis_file = open(filename_stem + ".basis" + str(i), "w")
        basis_file.write(str(atom_name.loc[i, 0]) + "\n")  # atom_name[0].iloc[number]
        with pd.option_context(
            "display.max_rows", None
        ):  # otherwise str() truncates NN shells >60 atoms (pandas default display.max_rows), corrupting the file
            basis_file.write(str(NN_v[i]) + "\n")
        basis_file.write("\n")
        basis_file.close()  # Writes a basis set file for reconstructing the configurations from binary

        print("Basis Set for sub-lattice " + str(i) + " has been saved (.basis" + str(i) + ").")

    # %% Produce Dictionary

    sym_ops_NN = sym_ops_df.copy(deep=True)  # Created duplicate dataframe

    sym_ops_NN[["x", "y", "z"]] = ""
    for i in range(len(sym_ops_NN)):
        split_list = re.split(",|, ", sym_ops_NN["Symmetry Operations"][i])
        sym_ops_NN.loc[i, "x"] = split_list[0]
        sym_ops_NN.loc[i, "y"] = split_list[1]
        sym_ops_NN.loc[i, "z"] = split_list[2]

    # %%

    NN_v_transform = copy.deepcopy(NN_v)

    # %% Resolve origin issue when merging lattices

    if answer == "Y":
        for i in range(len(super_answer)):
            closeness = []
            for j in super_answer[i]:
                calc_dist = np.sqrt(
                    (float(store_chem_index[j].loc[0, 0])) ** 2
                    + (float(store_chem_index[j].loc[0, 1])) ** 2
                    + (float(store_chem_index[j].loc[0, 2])) ** 2
                )
                closeness.append(calc_dist)

            finder = closeness.index(min(closeness))
            finder_2 = super_answer[i][finder]
            store_chem_index[len(store_chem_index)] = store_chem_index[finder_2].copy()

        for i in super_answer_merge:
            del store_chem_index[i]
        store_chem_index = {i: v for i, v in enumerate(store_chem_index.values())}

    else:
        pass

    # %%

    list_lets = ["x", "y", "z"]
    symmetry_collect_dict = {}
    for number in range(len(NN_v)):
        # Create a 'dumping' DataFrame that can be used to store the atomic coordinates
        Symmetries_file = open(filename_stem + ".sym" + str(number), "w")

        Origin_dump = store_chem_index[number].copy()
        Origin_dump.rename(columns={0: "x", 1: "y", 2: "z"}, inplace=True)
        Origin_sym_dump = pd.DataFrame(columns=["x", "y", "z"])

        symmetry_collect = []

        for j in range(len(sym_ops_NN)):
            for k in list_lets:
                x = Origin_dump["x"]
                y = Origin_dump["y"]
                z = Origin_dump["z"]

                # Every branch below evaluated the identical `eval(sym_ops_NN[k][j])` regardless of
                # which axis letter (or sign) matched - the only real question is whether an x/y/z
                # variable is present at all, so that's collapsed to one guard.
                if any(letter in sym_ops_NN[k][j] for letter in ("x", "y", "z")):
                    result = eval(sym_ops_NN[k][j])
                    Origin_sym_dump[k] = result
                else:
                    # A valid general-position symmetry operator can't have a component with no
                    # x/y/z at all (the rotation part must be invertible, so no coordinate's linear
                    # part can vanish) - reaching here means this CIF's symmetry operators are
                    # malformed or non-standard. Fail loudly rather than silently mis-assigning
                    # the remaining axes.
                    raise ValueError(
                        f"Unrecognised symmetry operator component '{sym_ops_NN[k][j]}' (axis '{k}', operation {j}) - expected an expression containing x, y, or z."
                    )

            # Checks whether the symmetry-transformed position matches the original atom position
            # up to a +1 lattice translation independently on each axis (periodic boundary: an atom
            # at fractional coordinate 0 and one at 1 along the same axis are the same site). The
            # 8 branches below were every combination of "add 1 or don't" across x/y/z - collapsed
            # to a loop over those same 8 (0/1) offset combinations.
            add = 1
            for offset in itertools.product([0, add], repeat=3):
                if (
                    (offset[0] + Origin_sym_dump["x"][0] == Origin_dump["x"][0])
                    and (offset[1] + Origin_sym_dump["y"][0] == Origin_dump["y"][0])
                    and (offset[2] + Origin_sym_dump["z"][0] == Origin_dump["z"][0])
                ):
                    symmetry_collect.append(
                        [sym_ops_NN["x"].iloc[j], sym_ops_NN["y"].iloc[j], sym_ops_NN["z"].iloc[j]]
                    )
                    break

        symmetry_collect = pd.DataFrame(symmetry_collect)
        symmetry_collect.rename(columns={0: "x", 1: "y", 2: "z"}, inplace=True)
        symmetry_collect_dict[number] = symmetry_collect
        NN_sym_dump = pd.DataFrame(columns=["x", "y", "z", "Atom No."])

        print(
            "\nGenerating symmetrically equivalent configurations for sublattice "
            + str(atom_name[0].iloc[number])
        )

        for j in tqdm(
            range(len(symmetry_collect)),
            desc="Establishing valid symmetry operations for each sub-lattice.",
        ):
            for k in list_lets:
                symmetry_collect.loc[j, k] = clean_expression(symmetry_collect.loc[j, k])

                x = NN_v_transform[number][0]
                y = NN_v_transform[number][1]
                z = NN_v_transform[number][2]

                # See the equivalent branch above (Origin_sym_dump loop) - every branch here was
                # also the identical `eval(symmetry_collect[k][j])`, so collapsed to one guard.
                if any(letter in symmetry_collect[k][j] for letter in ("x", "y", "z")):
                    result = eval(symmetry_collect[k][j])
                    NN_sym_dump[k] = result
                else:
                    # See the equivalent branch above - this shouldn't be reachable for a valid
                    # general-position symmetry operator. Fail loudly rather than silently
                    # mis-assigning the remaining axes.
                    raise ValueError(
                        f"Unrecognised symmetry operator component '{symmetry_collect[k][j]}' (axis '{k}', operation {j}) - expected an expression containing x, y, or z."
                    )

            for k in range(len(NN_sym_dump)):
                for vi in range(len(NN_v[number])):
                    if (
                        (round(NN_sym_dump["x"].iloc[k], 6) == round(NN_v[number][0].iloc[vi], 6))
                        and (
                            round(NN_sym_dump["y"].iloc[k], 6) == round(NN_v[number][1].iloc[vi], 6)
                        )
                        and (
                            round(NN_sym_dump["z"].iloc[k], 6) == round(NN_v[number][2].iloc[vi], 6)
                        )
                    ):
                        NN_sym_dump.at[k, "Atom No."] = NN_v[number].loc[vi, "Atom No."]

            # print('____________________________________')
            # print(NN_sym_dump)
            # print('____________________________________')

            Num_array = np.asarray(NN_sym_dump["Atom No."])

            for item in Num_array:
                Symmetries_file.write(str(item) + " ")
            Symmetries_file.write("\n")

        Symmetries_file.close()
        print(
            "\nSymmetry File for the "
            + str(atom_name[0].iloc[number])
            + "  sub-lattice has been saved (.sym"
            + str(number)
            + ")."
        )

    # %%Open symmetries files generated above for atomic positions
    pos_file_read = {}

    for i in range(len(NN_v)):
        file_rot = open(filename_stem + ".sym" + str(i))
        rot_read = file_rot.readlines()
        file_rot.close()  # Load in the symmetries file, which now contains some number of combinations of 123456 (615243 etc.) corresponding to the rotations of the nearest neighbours
        pos_file_read[i] = rot_read

    for i in range(len(pos_file_read)):
        for j in range(len(pos_file_read[i])):
            pos_file_read[i][j] = re.sub(
                "[^0-9]", " ", pos_file_read[i][j]
            )  # Replace any non-numerical characters

    # %% Create Binaries

    def DecToBin(
        n, o
    ):  # Input: n = 2^(no. nearest neighbours), producing a range 0-(2^(n)-1), o = no. nearest neighbours; used to create binary positions
        # Converting decimal to binary and removing the prefix(0b)
        ran = list(range(n))
        binary_list = []
        for i in ran:
            binary_list.append(bin(i)[2:].zfill(o))
        return binary_list

    def ListSplit(dictionary):  # Splits any set of characters into integer values in a list
        for i in range(len(dictionary)):
            for j in range(len(dictionary[i])):
                if " " in dictionary[i][j]:
                    dictionary[i][j].replace("\n", "")
                    dictionary[i][j] = [v for v in dictionary[i][j].split(" ")]
                else:
                    dictionary[i][j] = list(map(int, dictionary[i][j]))
        return dictionary

    binaries_dict = {}
    for i in range(len(NN_v)):
        binaries_dict[i] = DecToBin((2 ** len(NN_v[i])), len(NN_v[i]))

    blockPrint()
    ListSplit(binaries_dict)
    ListSplit(pos_file_read)
    enablePrint()  # Applies the split of the strings using the list split function, whilst suppressing print commands

    for i in range(len(pos_file_read)):
        for j in range(len(pos_file_read[i])):
            pos_file_read[i][j] = [int(x) for x in pos_file_read[i][j] if x != ""]
            if len(pos_file_read[i][j]) == 1:
                pos_file_read[i][j] = list(pos_file_read[i][j])

    # %%This section creates the dictionary of equivalent clapp configurations per sublattice in binary, and sorts them into number of occupied positions (i.e. multiplicity)

    Configs_dict = {}  # Creates dictionary for equivalent configurations per sublattice
    binaries_copy = copy.deepcopy(binaries_dict)

    for num in range(len(binaries_copy)):
        Configs_list = []

        for i in range(len(binaries_copy[num])):
            key_dict = dict(
                enumerate(binaries_copy[num][i], 1)
            )  # Creates a dictionary to assign each numbered position either a 0 (unoccupied) or a 1 (occupied)
            vals_store = []
            for k in range(len(pos_file_read[num])):
                mapped_vals = [
                    key_dict[position] for position in pos_file_read[num][k]
                ]  # Maps the 0s and 1s on to positions 1-N for all possible configurations under symmetry operators (i.e. from symmetries files)
                vals_store.append(mapped_vals)
            unique_lists_set = set(map(tuple, vals_store))
            vals_store_2 = [list(muaddib) for muaddib in unique_lists_set]

            Configs_list.append(vals_store_2)

        configs_final = []
        seen = set()

        for sublist in Configs_list:
            unique_sublist = []
            for inner_list in sublist:
                inner_tuple = tuple(inner_list)
                if inner_tuple not in seen:
                    seen.add(inner_tuple)
                    unique_sublist.append(inner_list)
            configs_final.append(unique_sublist)

        configs_final = [x for x in configs_final if x != []]

        Configs_dict[num] = configs_final

    # %%Triple check for empty lists

    for i in range(len(Configs_dict)):
        Configs_dict[i] = [[inner for inner in outer if inner] for outer in Configs_dict[i]]

    # %% Multiplicities

    W_k_dict = {}

    for i in range(len(Configs_dict)):
        W_k_list = []
        for j in range(len(Configs_dict[i])):
            A = len(Configs_dict[i][j])
            W_k_list.append(A)
        W_k_dict[i] = pd.DataFrame(W_k_list)  # Creates dictionary of dataframes of multiplicities

    # %%This section identifies the number of nearest neighbours per nearest neighbour atom (NNNN) for use in ordering rules
    from collections import Counter

    NNNN_dict = {}
    df_test_save_dict = {}
    for num in range(len(NN_v)):
        test_list = []
        NN_at_list = []
        for i in range(len(NN_v[num])):
            for j in range(i + 1, len(NN_v[num]), 1):
                test_coords = NN_v[num].iloc[i] - NN_v[num].iloc[j]
                test_list.append(
                    test_coords
                )  # Finds and appends the differences between coordinates of every pair of atoms
                NN_at_list.append([i + 1, j + 1])  # Appends the relevant atom labels

        df_test = pd.DataFrame(test_list)
        for i in range(len(NN_at_list)):
            df_test["Atoms"] = NN_at_list

        df_test["Dist"] = ((df_test[0] ** 2) + (df_test[1] ** 2) + (df_test[2] ** 2)) ** (
            0.5
        )  # Finds the absolute distances between coordinate positions
        df_test_save_dict[num] = df_test
        distances = []
        for i in range(len(df_test)):
            if 1 in df_test["Atoms"][i]:
                distances.append(
                    df_test["Dist"][i]
                )  # Finds all the atoms paired with atom 1, and appends the distances between 1 and the remaining atoms in the list

        dist_round = [round(elem, 8) for elem in distances]

        NNNN_df = pd.DataFrame()
        NNNN_df["Vals"] = Counter(dist_round).keys()  # Finds the unique distances
        NNNN_df["Count"] = Counter(dist_round).values()  # Counts instances of unique distances
        NNNN_df["Calc Val"] = NNNN_df["Count"] * len(
            NN_v
        )  # Creates numbers as required for calculation
        NNNN_dict[num] = NNNN_df

    # %%Dis_NN

    sigma_dict = {}

    for num in range(len(Configs_dict)):
        sigma_test = []
        for i in range(len(Configs_dict[num])):
            sigma_test.append(Configs_dict[num][i][0])
        sigma_test = pd.DataFrame(sigma_test)

        for i in range(len(sigma_test)):
            for j in range(len(sigma_test.columns)):
                if sigma_test.iloc[i, j] == 0:
                    sigma_test.iloc[i, j] += 1
                else:
                    sigma_test.iloc[i, j] += -2

        sigma_dict[num] = sigma_test

    # %%

    Dis_dict_fin = {}
    Combined_Dis = {}

    for val in range(len(sigma_dict)):
        Dislike_dict = {}

        for i in NNNN_dict[val]["Vals"]:
            Dis_NN_list = []
            dummy_atom_pairs = []

            for j in range(len(df_test_save_dict[val])):
                if round(df_test_save_dict[val]["Dist"].iloc[j], 8) == i:
                    dummy_atom_pairs.append(df_test_save_dict[val]["Atoms"].iloc[j])

            for num in range(len(sigma_dict[val])):
                ones_list = []

                for k in range(len(dummy_atom_pairs)):
                    C_test = (
                        sigma_dict[val].iloc[num][dummy_atom_pairs[k][0] - 1]
                        * sigma_dict[val].iloc[num][dummy_atom_pairs[k][1] - 1]
                    )
                    ones_list.append(C_test)
                    count = ones_list.count(-1)
                Dis_NN_list.append(count)

            Dislike_dict[i] = pd.DataFrame(Dis_NN_list)

        Dislike_dict = {i: v for i, v in enumerate(Dislike_dict.values())}
        Dis_dict_fin[val] = Dislike_dict
        Combined_Dis[val] = pd.concat(Dis_dict_fin[val].values(), axis=1)

        Combined_Dis[val].columns = range(Combined_Dis[val].columns.size)

    # %%Composition

    count_dict = {}

    for num in range(len(Configs_dict)):
        count_test = []
        for i in range(len(Configs_dict[num])):
            count_test.append(Configs_dict[num][i][0])
        count_test = pd.DataFrame(count_test)

        count_dict[num] = count_test

    count_fin = {}
    # Iterate over each DataFrame in the dictionary
    for key, df in count_dict.items():
        # Count the number of occurrences of 1 in each row and store in a new column
        count_fin[key] = df.eq(1).sum(axis=1)

    for i in range(len(count_fin)):
        count_fin[i] = pd.DataFrame(count_fin[i])

        W_k_dict[i] = pd.DataFrame(W_k_dict[i])

    # %% #Ordering using Clapp's Rules

    Master_Dict = {}

    for num in range(len(NN_v)):
        Master_Dict[num] = pd.concat([count_fin[num], Combined_Dis[num], W_k_dict[num]], axis=1)
        Master_Dict[num].columns = range(len(Master_Dict[num].columns))

        if len(Master_Dict[num].columns) % 2 == 0:
            sorting_order = (
                [True] + [False, True] * ((len(Master_Dict[num].columns) - 2) // 2) + [False]
            )  # I.e. order by ascending composition, descending 1NN shell, ascending 2NN (alternating), descending multiplicity
            Master_Dict[num] = Master_Dict[num].sort_values(
                by=list(Master_Dict[num].columns), ascending=sorting_order
            )
        else:
            sorting_order = (
                [True] + [False, True] * ((len(Master_Dict[num].columns) - 3) // 2) + [False, False]
            )  # I.e. order by ascending composition, descending 1NN shell, ascending 2NN (alternating), descending multiplicity
            Master_Dict[num] = Master_Dict[num].sort_values(
                by=list(Master_Dict[num].columns), ascending=sorting_order
            )
        Master_Dict[num]["CC"] = range(len(Master_Dict[num]))
        Master_Dict[num]["CC"] = Master_Dict[num]["CC"] + 1

        Master_Dict[num] = Master_Dict[num].reindex(list(range(len(Master_Dict[num]))))

    # %%

    CC_dict = copy.deepcopy(Configs_dict)
    for i in range(len(CC_dict)):
        CC_dict[i] = pd.DataFrame(CC_dict[i])
        for j in range(len(CC_dict[i])):
            for k in range(len(CC_dict[i].iloc[j])):
                if (
                    CC_dict[i].iloc[j][k] is None
                ):  # padding from pd.DataFrame() on ragged rows of lists
                    pass
                else:
                    CC_dict[i].loc[j, k] = "".join(map(str, CC_dict[i].iloc[j, k]))
                    CC_dict[i].loc[j, k] = int(CC_dict[i].iloc[j, k], base=2)

        CC_dict[i] = pd.concat([CC_dict[i], Master_Dict[i]["CC"]], axis=1)

    # %%Make negative CCs

    CC_dict2 = copy.deepcopy(CC_dict)

    for num in range(len(CC_dict)):
        numbs_list = []
        for i in range(len(CC_dict[num])):
            numbs_list.append(list(CC_dict[num].iloc[i]))
        for i in range(len(numbs_list)):
            numbs_list[i] = [x for x in numbs_list[i] if x is not None]
            numbs_list[i].pop()

        max_num = (2 ** len(NN_v[num])) - 1

        for i, vals in enumerate(numbs_list):
            fst_col = vals[0]
            diff = max_num - fst_col

            if Master_Dict[num][0].iloc[i] == int(len(NN_v[num]) / 2):
                pass
            else:
                for j, other_vals in enumerate(numbs_list):
                    if (j != i) and (diff in other_vals):
                        if CC_dict[num].loc[j, "CC"] > CC_dict[num].loc[i, "CC"]:
                            CC_dict[num].loc[j, "CC"] = CC_dict[num].loc[i, "CC"] * (-1)
                        else:
                            CC_dict[num].loc[i, "CC"] = CC_dict[num].loc[j, "CC"] * (-1)

    # %%Write to files

    # Write Dictionary File
    for num in range(len(CC_dict)):
        dec_list = []
        cc_list = []
        for i in range(len(CC_dict[num])):
            for j in range(len(CC_dict[num].iloc[i]) - 1):
                if (
                    CC_dict[num].iloc[i][j] is None
                ):  # padding from pd.DataFrame() on ragged rows of lists
                    continue
                else:
                    dec_list.append(CC_dict[num].iloc[i][j])
                    cc_list.append(CC_dict[num]["CC"].iloc[i])
        dec_list = pd.DataFrame(dec_list)
        cc_list = pd.DataFrame(cc_list)

        dict_write_df = pd.concat([dec_list, cc_list], axis=1)
        dict_write_df.columns = range(len(dict_write_df.columns))
        dict_write_df = dict_write_df.sort_values(by=0, ascending=True)

        dict_write_df.to_csv(
            filename_stem + ".cfgdict" + str(num), sep=" ", header=False, index=False
        )
        print(
            "Configurational Dictionary File for the "
            + str(atom_name[0].iloc[num])
            + " sub-lattice has been saved (.cfgdict"
            + str(num)
            + ")."
        )

    # Write Binomial Occupancy File

    # CC, Multiplicity, Comp (No. dislike atoms)

    for num in range(len(CC_dict)):
        CC_dict[num] = pd.concat([CC_dict[num], Master_Dict[num][0]], axis=1)
        CC_dict[num].columns = [*CC_dict[num].columns[:-1], "Comp"]

        CC_dict[num] = pd.concat([CC_dict[num], W_k_dict[num]], axis=1)
        CC_dict[num].columns = [*CC_dict[num].columns[:-1], "W"]

        binom_df = CC_dict[num][["CC", "W", "Comp"]].copy()
        binom_df.loc[len(binom_df.index)] = [0, 0, 0]
        binom_df = binom_df.sort_values(by=["CC"], ascending=True)

        binom_df.to_csv(filename_stem + ".binom" + str(num), sep=" ", header=False, index=False)
        print(
            "Binomial Occupancies File for the "
            + str(atom_name[0].iloc[num])
            + " sub-lattice has been saved (.binom"
            + str(num)
            + ")."
        )

    NN_v_copy = copy.deepcopy(NN_v)
    NN_v_copy[0].drop(["Atom No."], axis=1, inplace=True)
    list_pos = []
    for y in range(len(NN_v_copy[0])):
        tester_coord_list = NN_v_copy[0].iloc[y].values.flatten().tolist()
        list_pos.append(tester_coord_list)

    # %%%

    print("\n--------------End---------------\n\n")

    return filename_stem


def main(cif=None, equivalence=None):
    """Interactive entry point: prompts for `cif` if it wasn't supplied, then delegates to run().
    `equivalence` behaves as in run() - pass it to skip the equivalence prompts too."""
    print("\n====================================================================\n")
    print("\tConfigurational Dictionary Generator - v1.0 (2024)\n")
    print("\t   Developed by: Benjamin E. Jolly; Lewis R. Owen\n")
    print("\t\t    University of Sheffield, UK\n")
    print("====================================================================\n")

    if cif is None:
        cif = input("Input .cif filename (Including file extension):\t")

    return run(cif, equivalence=equivalence)


if __name__ == "__main__":
    main()
