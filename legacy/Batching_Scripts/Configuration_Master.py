"""Thin compatibility wrapper - the real implementation now lives in sro_config.batch.

Requires the package to be installed first: run `pip install -e .` from the repo root
(the launcher scripts do this for you), or install sro_config normally.
"""
from sro_config.batch import main

if __name__ == "__main__":
    main()
