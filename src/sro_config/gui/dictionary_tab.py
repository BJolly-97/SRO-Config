import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sro_config import dictionary

from .helpers import BackgroundJob


class DictionaryTab(ttk.Frame):
    """GUI face of dictionary.run() - pick a .cif, build equivalence groups, generate."""

    def __init__(self, master):
        super().__init__(master, padding=10)
        self._job = BackgroundJob(self)
        self._build()

    def _build(self):
        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=".cif file:").pack(side="left")
        self.cif_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.cif_var, width=60).pack(
            side="left", padx=6, fill="x", expand=True
        )
        ttk.Button(row, text="Browse...", command=self._browse_cif).pack(side="left")

        group_frame = ttk.LabelFrame(self, text="Lattice-site equivalences (optional)")
        group_frame.pack(fill="x", pady=8)

        add_row = ttk.Frame(group_frame)
        add_row.pack(fill="x", pady=4, padx=4)
        ttk.Label(add_row, text="Merge indices (e.g. 0,1):").pack(side="left")
        self.group_entry_var = tk.StringVar()
        entry = ttk.Entry(add_row, textvariable=self.group_entry_var, width=20)
        entry.pack(side="left", padx=6)
        entry.bind("<Return>", lambda e: self._add_group())
        ttk.Button(add_row, text="Add group", command=self._add_group).pack(side="left")
        ttk.Button(add_row, text="Remove selected", command=self._remove_group).pack(
            side="left", padx=6
        )

        self.group_listbox = tk.Listbox(group_frame, height=4)
        self.group_listbox.pack(fill="x", padx=4, pady=(0, 4))

        ttk.Label(
            self,
            text="Atom-type indices (0, 1, 2, ...) correspond to the order sites appear in the\n"
            ".cif file - the log below prints that list once you generate, so if you're\n"
            "unsure of the numbering, generate once with no groups, check the log, then\n"
            "add groups and re-generate.",
            foreground="#666",
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        action_row = ttk.Frame(self)
        action_row.pack(fill="x", pady=4)
        self.generate_button = ttk.Button(
            action_row, text="Generate Dictionary", command=self._generate
        )
        self.generate_button.pack(side="left")
        ttk.Button(action_row, text="Clear fields", command=self._clear_all).pack(
            side="left", padx=6
        )
        self.status_var = tk.StringVar(value="")
        ttk.Label(action_row, textvariable=self.status_var).pack(side="left", padx=10)

        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, pady=8)
        self.log_text = tk.Text(log_frame, height=16, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

    def _browse_cif(self):
        path = filedialog.askopenfilename(
            title="Select .cif file",
            filetypes=[("CIF files", "*.cif"), ("All files", "*.*")],
        )
        if path:
            self.cif_var.set(path)

    def _add_group(self):
        text = self.group_entry_var.get().strip()
        if not text:
            return
        try:
            [int(x) for x in text.split(",")]
        except ValueError:
            messagebox.showerror("Invalid group", "Enter comma-separated integers, e.g. 0,1")
            return
        self.group_listbox.insert("end", text)
        self.group_entry_var.set("")

    def _remove_group(self):
        for i in reversed(self.group_listbox.curselection()):
            self.group_listbox.delete(i)

    def _clear_all(self):
        """Resets every input field on this tab back to a blank/just-launched state, so a
        new single-instance run doesn't need leftover values from the last one cleared by hand."""
        self.cif_var.set("")
        self.group_entry_var.set("")
        self.group_listbox.delete(0, "end")
        self.status_var.set("")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _generate(self):
        cif = self.cif_var.get().strip()
        if not cif:
            messagebox.showerror("Missing .cif file", "Choose a .cif file first.")
            return

        groups = [self.group_listbox.get(i) for i in range(self.group_listbox.size())]

        self.generate_button.configure(state="disabled")
        self.status_var.set("Running...")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        def work():
            return dictionary.run(cif, equivalence=groups)

        def done(result, error):
            self.generate_button.configure(state="normal")
            if error is not None:
                self.status_var.set("Failed")
                self._log(f"\n[ERROR] {type(error).__name__}: {error}\n")
                messagebox.showerror("Dictionary generation failed", str(error))
            else:
                self.status_var.set(f"Done ({result})")

        self._job.start(work, on_log=self._log, on_done=done)
