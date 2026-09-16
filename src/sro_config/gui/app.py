"""Entry point for the SRO-Config desktop GUI - `sro-config gui`."""

import sys


def _apply_platform_fixes():
    """Known cross-platform Tkinter rough edges, fixed up front rather than hit later."""
    if sys.platform == "win32":
        # Without this, Tkinter windows render blurry/incorrectly-scaled on high-DPI
        # displays (the #1 "why does this look wrong on Windows" Tkinter complaint).
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass  # older Windows without shcore.dll - not fatal, just unscaled


def _import_tkinter():
    try:
        import tkinter as tk
        from tkinter import ttk

        return tk, ttk
    except ImportError as exc:
        lines = ["Tkinter is required for the GUI but isn't installed."]
        if sys.platform.startswith("linux"):
            lines += [
                "Install it with your distro's package manager, e.g.:",
                "  Debian/Ubuntu:  sudo apt install python3-tk",
                "  Fedora:         sudo dnf install python3-tkinter",
                "  Arch:           sudo pacman -S tk",
            ]
        elif sys.platform == "darwin":
            lines += [
                "The system Python on macOS often bundles a very old, buggy Tk.",
                "Install Python from python.org, or `brew install python-tk`, and run the",
                "GUI with that Python instead.",
            ]
        else:
            lines.append("Reinstall Python from python.org, which bundles Tkinter.")
        print("\n".join(lines))
        raise SystemExit(1) from exc


def main():
    _apply_platform_fixes()
    tk, ttk = _import_tkinter()

    import matplotlib

    matplotlib.use("TkAgg")

    from sro_config.gui.analysis_tab import AnalysisTab
    from sro_config.gui.dictionary_tab import DictionaryTab
    from sro_config.gui.visualiser_tab import VisualiserTab

    root = tk.Tk()
    root.title("SRO-Config - Configurational Analysis")
    root.geometry("1150x760")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    notebook.add(DictionaryTab(notebook), text="Dictionary")
    notebook.add(AnalysisTab(notebook), text="Analysis")
    notebook.add(VisualiserTab(notebook), text="Visualiser")

    root.mainloop()

    # The default WM_DELETE_WINDOW handler already calls destroy() when the window is closed
    # normally, but don't rely on that being the only way mainloop() ever returns - make sure
    # it's actually gone before the gc.collect() below, or that collect can't reclaim anything.
    try:
        root.destroy()
    except tk.TclError:
        pass  # already destroyed

    # Force any now-orphaned tkinter.Variable objects (StringVar/IntVar held by the
    # tabs' widgets) to be collected now, while we're still right after the mainloop -
    # otherwise Python's cyclic GC can sweep them up arbitrarily later (e.g. mid-way
    # through an unrelated `dict`/`config` run in the same interactive-menu process),
    # and their __del__ then raises "main thread is not in main loop" (CPython gh-83274).
    import gc

    gc.collect()


if __name__ == "__main__":
    main()
