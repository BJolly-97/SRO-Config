"""
Tests for the species-labelled plot titles/axes added to histograms.run().

The FeNi fixture only has two species, so it can only exercise the lone-species-vs-rest
branch of the labelling rule ("Fe:Ψ"); the "both sides spelled out" branch
(e.g. "Ni-Cr : Co-Fe" for a 4-element system) is covered by test_pseudo_binary_label_matches_examples
below, which reproduces the same modulo_sep-based grouping logic directly against the
worked examples from the request that prompted this feature.
"""

import shutil
from pathlib import Path

import pytest

from sro_config import dictionary, histograms

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    shutil.copy(FIXTURES / "FeNi.cif", tmp_path / "FeNi.cif")
    shutil.copy(FIXTURES / "FeNi_config.rmc6f", tmp_path / "run1.rmc6f")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_plots_are_titled_and_labelled(workdir, monkeypatch):
    """dict -> config against the two-species fixture; every Figure saved along the way
    should have a title/axis labels naming a real species, not just a bare numeric
    partition index. histograms.py builds each Figure directly (not via pyplot - see the
    threading-safety comment in histograms.py's plotting section) and never returns them
    (they're only ever fig.savefig()'d), so this intercepts Figure.savefig() to capture
    each figure's real Axes state at the moment it would have been written to disk."""
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    saved_figures = []
    original_savefig = Figure.savefig

    def spy_savefig(self, *a, **k):
        saved_figures.append(self)
        return original_savefig(self, *a, **k)

    monkeypatch.setattr(Figure, "savefig", spy_savefig)

    dictionary.run("FeNi.cif", equivalence=[[0, 1]])
    histograms.run(".", sublattice="0", rmc6f="run1.rmc6f")

    calls = {
        "title": [fig.axes[0].get_title() for fig in saved_figures],
        "xlabel": [fig.axes[0].get_xlabel() for fig in saved_figures],
        "ylabel": [fig.axes[0].get_ylabel() for fig in saved_figures],
        "legend": sum(1 for fig in saved_figures if fig.axes[0].get_legend() is not None),
    }

    # 4 plots per partition (Tot, A, B, AB) x 1 partition for a 2-species system. Which
    # species ends up "A" vs "B" isn't fixed by this test - only that the labelling is
    # internally consistent and every plot names a real species, never a bare index.
    tot_title, a_title, b_title, ab_title = calls["title"]
    assert len(calls["title"]) == 4
    # 2 species -> the partition is "one species vs everything else", labelled "<species>:Ψ"
    # (see _group_label() in histograms.py; Ψ = "the other side").
    assert tot_title in ("Fe:Ψ", "Ni:Ψ")
    assert ab_title == tot_title  # the combined plot reuses the same overall partition title
    assert {a_title, b_title} == {f"{tot_title}\ncentred on Fe", f"{tot_title}\ncentred on Ni"}
    assert a_title != b_title  # the two sides of the partition must be labelled differently

    # Every title should name a real species (Fe or Ni), never be blank or purely numeric.
    for title in calls["title"]:
        assert ("Fe" in title) or ("Ni" in title), f"title {title!r} doesn't mention a species"
        assert not title.strip().isdigit()

    assert calls["xlabel"], "no x-axis label was set"
    assert calls["ylabel"], "no y-axis label was set"
    assert calls["legend"] == 1, "the combined A/B plot should have exactly one legend"


def test_pseudo_binary_label_matches_examples():
    """Reproduces the modulo_sep-based grouping logic standalone (independent of a full
    dict/config run) against the worked examples from the feature request: a quaternary
    Ni/Co/Cr/Fe system's Ni-Cr:Co-Fe partition, and a ternary Ni/Co/Cr system's
    single-species-vs-rest partitions."""
    from sro_config.histograms import modulo_sep

    def label(n1, no_types_new, species_names):
        red = modulo_sep(n1, 2, no_types_new)
        group_a = [species_names[i] for i in range(no_types_new) if red[i] == 0]
        group_b = [species_names[i] for i in range(no_types_new) if red[i] == 1]
        if min(len(group_a), len(group_b)) == 1:
            return group_a[0] if len(group_a) == 1 else group_b[0]
        return "-".join(group_a) + " : " + "-".join(group_b)

    quaternary = ["Ni", "Co", "Cr", "Fe"]
    titles = [label(n1, 4, quaternary) for n1 in range(1, 8)]
    assert "Ni-Cr : Co-Fe" in titles
    assert "Ni-Co : Cr-Fe" in titles
    assert "Ni-Fe : Co-Cr" in titles
    assert set(titles) & {"Ni", "Co", "Cr", "Fe"} == {
        "Ni",
        "Co",
        "Cr",
        "Fe",
    }  # each single-species case also appears

    ternary = ["Ni", "Co", "Cr"]
    ternary_titles = {label(n1, 3, ternary) for n1 in range(1, 4)}
    assert ternary_titles == {"Ni", "Co", "Cr"}
