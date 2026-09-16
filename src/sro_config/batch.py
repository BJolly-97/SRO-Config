"""
High-throughput batch entry point.

Equivalent to the old legacy/Batching_Scripts/Configuration_Master.py, but calls the
dictionary/histograms modules directly instead of exec()-ing separate script files
sharing one global namespace.

@author: Ben Jolly
"""

from sro_config import dictionary, histograms


def ask_yes_no(prompt):
    """Prompts for a Y/N answer; returns True/False, or None for anything else."""
    answer = input(prompt).strip().upper()
    if answer == "Y":
        return True
    if answer == "N":
        return False
    return None


def main():
    print("\n====================================================================\n")
    print("\t\tConfigurational Analysis - v1.0 (2024)\n")
    print("\t   Developed by: Benjamin E. Jolly; Lewis R. Owen\n")
    print("\t\t    University of Sheffield, UK\n")
    print("====================================================================\n")

    gen_dict = ask_yes_no("Generate Configurational Dictionary files? (Y/N):\t")

    if gen_dict is None:
        print("\nInvalid input.")
    else:
        if gen_dict:
            dictionary.main()

        run_hist = ask_yes_no("\nCalculate Enhancement Factors and generate Histograms? (Y/N):\t")

        if run_hist is None:
            print("\nInvalid input.")
        elif run_hist:
            histograms.main()

    print("\n--------------End---------------\n\n")


if __name__ == "__main__":
    main()
