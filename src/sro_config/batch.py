"""
High-throughput batch entry point.

Equivalent to the old legacy/Batching_Scripts/Configuration_Master.py, but calls the
dictionary/histograms modules directly instead of exec()-ing separate script files
sharing one global namespace.

@author: Ben Jolly
"""

from sro_config import dictionary, histograms
from sro_config._prompts import prompt_yes_no


def main():
    print("\n====================================================================\n")
    print("\t\tConfigurational Analysis - v1.0 (2024)\n")
    print("\t   Developed by: Benjamin E. Jolly; Lewis R. Owen\n")
    print("\t\t    University of Sheffield, UK\n")
    print("====================================================================\n")

    if prompt_yes_no("Generate Configurational Dictionary files? (Y/N):\t"):
        dictionary.main()

    if prompt_yes_no("\nCalculate Enhancement Factors and generate Histograms? (Y/N):\t"):
        histograms.main()

    print("\n--------------End---------------\n\n")


if __name__ == "__main__":
    main()
