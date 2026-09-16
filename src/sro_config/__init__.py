"""
Generalised tool for Clapp-style configurational (short-range-order) analysis of
RMCProfile large-box atomic models.

Originally developed by Benjamin E. Jolly and Lewis R. Owen, University of Sheffield.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sro-config")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "0.0.0+unknown"

del version, PackageNotFoundError
