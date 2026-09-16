import glob
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sro_config import histograms

from .helpers import BackgroundJob, read_finsub


class AnalysisTab(ttk.Frame):
    """GUI face of histograms.run_batch() - one .rmc6f file or many go through the exact
    same list-of-paths widget and the exact same batch loop; this is where high-throughput
    analysis lives in the GUI."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self._job = BackgroundJob(self)
        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Dictionary directory:").pack(side="left")
        self.dict_dir_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.dict_dir_var, width=50).pack(
            side="left", padx=6, fill="x", expand=True
        )
        ttk.Button(row, text="Browse...", command=self._browse_dict_dir).pack(side="left")

        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Sub-lattice:").pack(side="left")
        self.sublattice_var = tk.StringVar()
        self.sublattice_combo = ttk.Combobox(
            row2, textvariable=self.sublattice_var, state="readonly", width=40
        )
        self.sublattice_combo.pack(side="left", padx=6)
        ttk.Button(row2, text="Refresh", command=self._refresh_sublattices).pack(side="left")

        files_frame = ttk.LabelFrame(self, text=".rmc6f file(s) to analyse")
        files_frame.pack(fill="both", pady=8)

        file_btn_row = ttk.Frame(files_frame)
        file_btn_row.pack(fill="x", padx=4, pady=4)
        ttk.Button(file_btn_row, text="Add file(s)...", command=self._browse_rmc6f_files).pack(
            side="left"
        )
        ttk.Label(file_btn_row, text="   or glob pattern:").pack(side="left")
        self.glob_var = tk.StringVar()
        glob_entry = ttk.Entry(file_btn_row, textvariable=self.glob_var, width=30)
        glob_entry.pack(side="left", padx=4)
        glob_entry.bind("<Return>", lambda e: self._add_glob_matches())
        ttk.Button(file_btn_row, text="Add matches", command=self._add_glob_matches).pack(
            side="left"
        )
        ttk.Button(file_btn_row, text="Clear list", command=self._clear_files).pack(
            side="left", padx=10
        )

        self.files_listbox = tk.Listbox(files_frame, height=6, selectmode="extended")
        self.files_listbox.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        action_row = ttk.Frame(self)
        action_row.pack(fill="x", pady=4)
        self.run_button = ttk.Button(action_row, text="Run Analysis", command=self._run)
        self.run_button.pack(side="left")
        ttk.Button(action_row, text="Clear all fields", command=self._clear_all).pack(
            side="left", padx=6
        )
        self.progress = ttk.Progressbar(action_row, length=250, mode="determinate")
        self.progress.pack(side="left", padx=10)
        self.status_var = tk.StringVar(value="")
        ttk.Label(action_row, textvariable=self.status_var).pack(side="left")

        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, pady=8)
        self.log_text = tk.Text(log_frame, height=14, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

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

    def _selected_sublattice_index(self):
        value = self.sublattice_var.get()
        if not value:
            return None
        return value.split(":", 1)[0].strip()

    def _browse_rmc6f_files(self):
        paths = filedialog.askopenfilenames(
            title="Select .rmc6f file(s)",
            filetypes=[("RMC6F files", "*.rmc6f"), ("All files", "*.*")],
        )
        existing = set(self.files_listbox.get(0, "end"))
        for p in paths:
            if p not in existing:
                self.files_listbox.insert("end", p)

    def _add_glob_matches(self):
        pattern = self.glob_var.get().strip()
        if not pattern:
            return
        # Exclude this tool's own _mb.rmc6f output, same as the CLI's --rmc6f-glob, so
        # re-adding the same pattern after a run doesn't pull in last run's outputs.
        matches = sorted(p for p in glob.glob(pattern) if not p.endswith("_mb.rmc6f"))
        if not matches:
            messagebox.showwarning("No matches", f"No (non-output) files matched: {pattern}")
            return
        existing = set(self.files_listbox.get(0, "end"))
        for p in matches:
            if p not in existing:
                self.files_listbox.insert("end", p)

    def _clear_files(self):
        self.files_listbox.delete(0, "end")

    def _clear_all(self):
        """Resets every input field on this tab (dictionary directory, sub-lattice, glob
        pattern, file list, progress/status/log), not just the file list that "Clear list"
        already handled - so a new single-instance run doesn't need leftover values cleared
        by hand."""
        self.dict_dir_var.set("")
        self.sublattice_combo.configure(values=[])
        self.sublattice_var.set("")
        self.glob_var.set("")
        self.files_listbox.delete(0, "end")
        self.progress.configure(value=0, maximum=1)
        self.status_var.set("")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_progress(self, index, total, path, status):
        self.progress.configure(maximum=total, value=index)
        self.status_var.set(f"{index}/{total}: {os.path.basename(path)} ({status})")

    def _run(self):
        dict_dir = self.dict_dir_var.get().strip()
        sub_num = self._selected_sublattice_index()
        paths = list(self.files_listbox.get(0, "end"))

        if not dict_dir or sub_num is None:
            messagebox.showerror(
                "Missing input", "Choose a dictionary directory and sub-lattice first."
            )
            return
        if not paths:
            messagebox.showerror("No files", "Add at least one .rmc6f file to analyse.")
            return

        self.run_button.configure(state="disabled")
        self.progress.configure(value=0, maximum=len(paths))
        self.status_var.set("Running...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        def work():
            return histograms.run_batch(
                dict_dir, sub_num, paths, on_progress=self._job.progress_callback
            )

        def done(result, error):
            self.run_button.configure(state="normal")
            if error is not None:
                self.status_var.set("Failed")
                self._log(f"\n[ERROR] {type(error).__name__}: {error}\n")
                messagebox.showerror("Analysis failed", str(error))
            else:
                succeeded, failed = result
                self.status_var.set(f"Done: {len(succeeded)} succeeded, {len(failed)} failed")
                if failed:
                    messagebox.showwarning(
                        "Some files failed",
                        f"{len(failed)} of {len(paths)} file(s) failed - see the log for details.",
                    )

        self._job.start(work, on_log=self._log, on_progress=self._on_progress, on_done=done)
