import os

# Must happen before matplotlib (and therefore sro_config.visualiser) is imported anywhere,
# so plt.show() doesn't try to open a real display window during tests.
os.environ.setdefault("MPLBACKEND", "Agg")
