"""
Shared helpers for the SRO-Config GUI: reading dictionary metadata for combo/list boxes,
and a small thread+queue pattern (BackgroundJob) for running the existing run()/run_batch()
functions without freezing the Tkinter main loop during a real analysis.
"""

import os
import queue
import sys
import threading


def read_finsub(dict_dir):
    """Returns [(index_str, label), ...] parsed from the .finsub file in dict_dir (e.g.
    [('0', 'Fe/Ni')]), or raises FileNotFoundError if there isn't one yet."""
    finsub_name = None
    for stemname in os.listdir(dict_dir):
        if stemname.endswith(".finsub"):
            finsub_name = stemname

    if finsub_name is None:
        raise FileNotFoundError(
            f"No '.finsub' file found in '{dict_dir}'. Run Dictionary generation first."
        )

    entries = []
    with open(os.path.join(dict_dir, finsub_name)) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: "Sub-lattice 0:\tFe/Ni"
            head, _, label = line.partition("\t")
            index = head.replace("Sub-lattice", "").replace(":", "").strip()
            entries.append((index, label))
    return entries


def read_config_labels(dict_dir, sublattice):
    """Returns the sorted list of unique Configuration labels available for one
    sub-lattice, read from its .cfgdictN file (numeric labels sort numerically)."""
    sub_num = str(sublattice)
    clapp_ext = None
    for stemname in os.listdir(dict_dir):
        if stemname.endswith(".cfgdict" + sub_num):
            clapp_ext = stemname

    if clapp_ext is None:
        raise FileNotFoundError(f"No '.cfgdict{sub_num}' file found in '{dict_dir}'.")

    labels = []
    seen = set()
    with open(os.path.join(dict_dir, clapp_ext)) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue
            label = parts[1]
            if label not in seen:
                seen.add(label)
                labels.append(label)

    def sort_key(label):
        try:
            return (0, int(label))
        except ValueError:
            return (1, label)

    return sorted(labels, key=sort_key)


class _QueueWriter:
    """A minimal file-like object that pushes each write() onto a queue, used to redirect
    stdout from a background worker thread into the GUI's log widget (Tkinter widgets can
    only safely be touched from the main thread, so the worker never writes to one
    directly)."""

    def __init__(self, q):
        self._q = q

    def write(self, text):
        if text:
            self._q.put(("log", text))

    def flush(self):
        pass


class BackgroundJob:
    """
    Runs a callable in a background thread so the window doesn't freeze during a real
    dictionary-generation or (potentially long) batch-analysis run, capturing its stdout
    and any progress events into a thread-safe queue that the Tkinter main thread drains
    via a self-rescheduling poll() (widget.after(...)).

    Usage:
        job = BackgroundJob(some_widget)
        # if the target accepts a progress hook (e.g. histograms.run_batch's on_progress=),
        # thread job.progress_callback into it when building `work`:
        def work():
            return histograms.run_batch(dict_dir, sub, paths, on_progress=job.progress_callback)
        job.start(work, on_log=log_widget_append, on_progress=update_progress_bar, on_done=finished)
    """

    def __init__(self, tk_widget):
        self._widget = tk_widget
        self._queue = queue.Queue()

    def progress_callback(self, *args):
        """Pass this as the target's progress-reporting hook. Safe to call from the
        worker thread - just enqueues the event for the main thread to pick up."""
        self._queue.put(("progress", args))

    def start(self, fn, on_log=None, on_progress=None, on_done=None):
        """Runs the zero-argument callable `fn` in a background thread."""

        def worker():
            writer = _QueueWriter(self._queue)
            old_stdout = sys.stdout
            sys.stdout = writer
            result, error = None, None
            try:
                result = fn()
            except Exception as exc:  # noqa: BLE001 - deliberately broad: surface any failure to the GUI rather than losing it in a background thread
                error = exc
            finally:
                sys.stdout = old_stdout
            self._queue.put(("done", (result, error)))

        threading.Thread(target=worker, daemon=True).start()
        self._poll(on_log, on_progress, on_done)

    def _poll(self, on_log, on_progress, on_done):
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log" and on_log is not None:
                    on_log(payload)
                elif kind == "progress" and on_progress is not None:
                    on_progress(*payload)
                elif kind == "done":
                    result, error = payload
                    if on_done is not None:
                        on_done(result, error)
                    return  # job finished - stop polling
        except queue.Empty:
            pass
        self._widget.after(100, lambda: self._poll(on_log, on_progress, on_done))
