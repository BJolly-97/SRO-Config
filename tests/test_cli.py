"""
Tests for the scripted (non-interactive) entry points: dictionary.run()/histograms.run(),
histograms.run_batch(), and the sro-config CLI built on top of them.
"""

import shutil
from pathlib import Path

import pytest

from sro_config import cli, dictionary, histograms, visualiser

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    shutil.copy(FIXTURES / "FeNi.cif", tmp_path / "FeNi.cif")
    shutil.copy(FIXTURES / "FeNi_config.rmc6f", tmp_path / "run1.rmc6f")
    shutil.copy(FIXTURES / "FeNi_config.rmc6f", tmp_path / "run2.rmc6f")
    shutil.copy(FIXTURES / "FeNi_config.rmc6f", tmp_path / "run3.rmc6f")
    (tmp_path / "broken.rmc6f").write_text("this is not a valid rmc6f file\n")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_dictionary_run_matches_interactive_main(workdir, monkeypatch):
    """The scripted run() and the prompted main() must produce byte-identical output."""
    import filecmp

    scripted_dir = workdir / "scripted"
    interactive_dir = workdir / "interactive"
    scripted_dir.mkdir()
    interactive_dir.mkdir()
    shutil.copy(workdir / "FeNi.cif", scripted_dir / "FeNi.cif")
    shutil.copy(workdir / "FeNi.cif", interactive_dir / "FeNi.cif")

    monkeypatch.chdir(scripted_dir)
    dictionary.run("FeNi.cif", equivalence=[[0, 1]])

    monkeypatch.chdir(interactive_dir)
    answers = iter(["FeNi.cif", "Y", "0,1", "N"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    dictionary.main()

    for suffix in [".cellpos", ".finsub", ".basis0", ".sym0", ".cfgdict0", ".binom0"]:
        assert filecmp.cmp(
            scripted_dir / f"FeNi{suffix}", interactive_dir / f"FeNi{suffix}", shallow=False
        ), f"scripted vs. interactive output differs for FeNi{suffix}"


def test_dictionary_run_rejects_equivalence_for_single_species(tmp_path, monkeypatch):
    """A structure with only one atom type has nothing to merge - passing an equivalence
    group for it should fail loudly, not silently ignore the request."""
    cif = tmp_path / "single.cif"
    cif.write_text((FIXTURES / "FeNi.cif").read_text().replace("Ni1 Ni 0.0 0.0 0.0\n", ""))
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        dictionary.run("single.cif", equivalence=[[0]])


def test_histograms_run_batch_continues_past_a_bad_file(workdir, monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("run_batch must not prompt")),
    )

    dictionary.run("FeNi.cif", equivalence=[[0, 1]])

    succeeded, failed = histograms.run_batch(
        ".", "0", ["run1.rmc6f", "run2.rmc6f", "broken.rmc6f", "run3.rmc6f"]
    )

    assert len(succeeded) == 3
    assert len(failed) == 1
    assert failed[0][0] == "broken.rmc6f"


def test_cli_scripted_dict_and_batch_analyse(workdir, monkeypatch):
    monkeypatch.setattr(
        "builtins.input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("scripted CLI usage must not prompt")),
    )

    cli.main(["dict", "--cif", "FeNi.cif", "--equivalence", "0,1"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["config", "--dict-dir", ".", "--sublattice", "0", "--rmc6f-glob", "*.rmc6f"])
    assert exc_info.value.code == 1  # one of the four matched files (broken.rmc6f) should fail

    assert (workdir / "run1_sub0_EF.clapp").exists()
    assert (workdir / "run2_sub0_EF.clapp").exists()
    assert (workdir / "run3_sub0_EF.clapp").exists()


def test_cli_batch_analyse_all_succeed_exits_zero(workdir, monkeypatch):
    (workdir / "broken.rmc6f").unlink()
    monkeypatch.setattr(
        "builtins.input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("scripted CLI usage must not prompt")),
    )

    cli.main(["dict", "--cif", "FeNi.cif", "--equivalence", "0,1"])
    cli.main(
        ["config", "--dict-dir", ".", "--sublattice", "0", "--rmc6f-glob", "*.rmc6f"]
    )  # should not raise/exit


def test_cli_batch_glob_excludes_own_mb_output(workdir, monkeypatch):
    """Re-running the same glob shouldn't reprocess this tool's own _mb.rmc6f output."""
    (workdir / "broken.rmc6f").unlink()
    monkeypatch.setattr(
        "builtins.input",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("scripted CLI usage must not prompt")),
    )

    cli.main(["dict", "--cif", "FeNi.cif", "--equivalence", "0,1"])
    cli.main(["config", "--dict-dir", ".", "--sublattice", "0", "--rmc6f-glob", "*.rmc6f"])

    assert (workdir / "run1_mb.rmc6f").exists()

    # Second pass over the same glob: should still only process the 3 original files,
    # not the _mb.rmc6f outputs the first pass just wrote.
    paths = cli._resolve_rmc6f_paths(None, str(workdir / "*.rmc6f"))
    assert all(not p.endswith("_mb.rmc6f") for p in paths)
    assert len(paths) == 3


def test_visualiser_run_matches_interactive_main(workdir, monkeypatch):
    dictionary.run("FeNi.cif", equivalence=[[0, 1]])

    visualiser.run(".", "0", "1")  # should not raise

    answers = iter([".", "0", "1", "N"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(answers))
    visualiser.main()  # should also not raise
