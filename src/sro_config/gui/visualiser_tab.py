import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from sro_config import visualiser

from .helpers import read_config_labels, read_finsub


class VisualiserTab(ttk.Frame):
    """GUI face of visualiser.build_figure() - select a sub-lattice and any number of
    Configuration labels, and each selected one opens as its own tab in the notebook on
    the right, all independently rotatable, none of them blocking the others."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Dictionary directory:").pack(side="left")
        self.dict_dir_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.dict_dir_var, width=45).pack(
            side="left", padx=6, fill="x", expand=True
        )
        ttk.Button(row, text="Browse...", command=self._browse_dict_dir).pack(side="left")

        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Sub-lattice:").pack(side="left")
        self.sublattice_var = tk.StringVar()
        self.sublattice_combo = ttk.Combobox(
            row2, textvariable=self.sublattice_var, state="readonly", width=30
        )
        self.sublattice_combo.pack(side="left", padx=6)
        self.sublattice_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_labels())
        ttk.Button(row2, text="Refresh", command=self._refresh_sublattices).pack(side="left")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, pady=8)

        left = ttk.LabelFrame(body, text="Configurations")
        left.pack(side="left", fill="y", padx=(0, 8))
        self.labels_listbox = tk.Listbox(
            left, selectmode="extended", width=14, height=24, exportselection=False
        )
        self.labels_listbox.pack(fill="y", padx=4, pady=4)

        btn_col = ttk.Frame(left)
        btn_col.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(btn_col, text="Plot selected", command=self._plot_selected).pack(fill="x")
        ttk.Button(btn_col, text="Close all tabs", command=self._close_all).pack(
            fill="x", pady=(4, 0)
        )
        ttk.Button(btn_col, text="Clear fields", command=self._clear_fields).pack(
            fill="x", pady=(4, 0)
        )

        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        self.plot_notebook = ttk.Notebook(right)
        self.plot_notebook.pack(fill="both", expand=True)

    def _browse_dict_dir(self):
        path = filedialog.askdirectory(title="Select dictionary directory")
        if path:
            self.dict_dir_var.set(path)
            self._refresh_sublattices()

    def _refresh_sublattices(self):
        dict_dir = self.dict_dir_var.get().strip()
        if not dict_dir:
            return
        try:
            entries = read_finsub(dict_dir)
        except FileNotFoundError as exc:
            messagebox.showerror("No dictionary found", str(exc))
            return
        values = [f"{idx}: {label}" for idx, label in entries]
        self.sublattice_combo.configure(values=values)
        if values:
            self.sublattice_combo.current(0)
            self._refresh_labels()

    def _selected_sublattice_index(self):
        value = self.sublattice_var.get()
        if not value:
            return None
        return value.split(":", 1)[0].strip()

    def _refresh_labels(self):
        dict_dir = self.dict_dir_var.get().strip()
        sub_num = self._selected_sublattice_index()
        if not dict_dir or sub_num is None:
            return
        try:
            labels = read_config_labels(dict_dir, sub_num)
        except FileNotFoundError as exc:
            messagebox.showerror("No dictionary found", str(exc))
            return
        self.labels_listbox.delete(0, "end")
        for label in labels:
            self.labels_listbox.insert("end", label)

    def _plot_selected(self):
        dict_dir = self.dict_dir_var.get().strip()
        sub_num = self._selected_sublattice_index()
        selected = [self.labels_listbox.get(i) for i in self.labels_listbox.curselection()]

        if not dict_dir or sub_num is None:
            messagebox.showerror(
                "Missing input", "Choose a dictionary directory and sub-lattice first."
            )
            return
        if not selected:
            messagebox.showerror(
                "No configurations selected",
                "Select one or more configurations to plot (Ctrl/Shift-click for several).",
            )
            return

        for label in selected:
            try:
                fig = visualiser.build_figure(dict_dir, sub_num, label)
            except Exception as exc:
                messagebox.showerror("Plot failed", f"C{label}: {type(exc).__name__}: {exc}")
                continue
            if fig is None:
                messagebox.showwarning(
                    "Not found", f"Configuration label '{label}' not found for this sub-lattice."
                )
                continue
            self._add_tab(fig, label)

    def _add_tab(self, fig, label):
        tab = ttk.Frame(self.plot_notebook)
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, tab, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        self.plot_notebook.add(tab, text=f"C{label}")
        self.plot_notebook.select(tab)

    def _close_all(self):
        for tab_id in self.plot_notebook.tabs():
            self.plot_notebook.forget(tab_id)

    def _clear_fields(self):
        """Resets the dictionary directory, sub-lattice, and configuration list back to a
        blank/just-launched state, so picking a different dictionary doesn't leave stale
        values lying around. Leaves any already-plotted tabs open - use "Close all tabs"
        for those."""
        self.dict_dir_var.set("")
        self.sublattice_combo.configure(values=[])
        self.sublattice_var.set("")
        self.labels_listbox.delete(0, "end")
