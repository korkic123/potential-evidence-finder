from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from case_db import CaseDatabase


class CaseManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Potential Evidence Finder - Case Manager")
        self.geometry("1320x790")
        self.minsize(1080, 680)
        self.db: CaseDatabase | None = None
        self.entities_cache: dict[str, dict] = {}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        toolbar = ttk.Frame(self, padding=10)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="New Case", command=self._new_case).pack(side="left")
        ttk.Button(toolbar, text="Open Case", command=self._open_case).pack(side="left", padx=6)
        self.import_btn = ttk.Button(toolbar, text="Import .pefpack", command=self._import_package, state="disabled")
        self.import_btn.pack(side="left", padx=6)
        self.case_var = tk.StringVar(value="No case open")
        ttk.Label(toolbar, textvariable=self.case_var).pack(side="left", padx=18)

        pane = ttk.Panedwindow(self, orient="vertical")
        pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        upper = ttk.Frame(pane)
        pane.add(upper, weight=3)
        columns = (
            "confidence", "confidence_score", "priority", "priority_score", "status",
            "type", "name", "sources", "artifacts", "identity",
        )
        self.entity_tree = ttk.Treeview(upper, columns=columns, show="headings")
        specs = {
            "confidence": ("Existence", 78),
            "confidence_score": ("Conf.", 55),
            "priority": ("Priority", 72),
            "priority_score": ("Pri.", 48),
            "status": ("Status", 88),
            "type": ("Entity Type", 130),
            "name": ("Potential Evidence Source", 270),
            "sources": ("Sources", 65),
            "artifacts": ("Artifacts", 65),
            "identity": ("Identity", 80),
        }
        for col, (label, width) in specs.items():
            self.entity_tree.heading(col, text=label)
            self.entity_tree.column(col, width=width, anchor="w")
        self.entity_tree.pack(fill="both", expand=True)
        self.entity_tree.bind("<<TreeviewSelect>>", self._show_observations)

        controls = ttk.Frame(upper, padding=(0, 6, 0, 0))
        controls.pack(fill="x")
        ttk.Label(controls, text="Set selected status:").pack(side="left")
        for status in ("POTENTIAL", "LOCATED", "ACQUIRED", "EXCLUDED"):
            ttk.Button(controls, text=status.title(), command=lambda s=status: self._set_status(s)).pack(side="left", padx=3)

        lower = ttk.LabelFrame(pane, text="Observations supporting selected source", padding=6)
        pane.add(lower, weight=2)
        ocols = ("source", "artifact", "relation", "name", "identifiers")
        self.obs_tree = ttk.Treeview(lower, columns=ocols, show="headings")
        for col, label, width in [
            ("source", "Collected Source", 135),
            ("artifact", "Artifact", 125),
            ("relation", "Relation", 190),
            ("name", "Observed Name", 250),
            ("identifiers", "Identifiers", 480),
        ]:
            self.obs_tree.heading(col, text=label)
            self.obs_tree.column(col, width=width, anchor="w")
        self.obs_tree.pack(fill="both", expand=True)

        self.footer_var = tk.StringVar(value="Open or create a case database.")
        ttk.Label(self, textvariable=self.footer_var, padding=(10, 0, 10, 10), wraplength=1280).pack(anchor="w")

    def _new_case(self):
        case_id = simpledialog.askstring("New Case", "Case ID:", parent=self)
        if not case_id:
            return
        path = filedialog.asksaveasfilename(
            title="Create case database",
            defaultextension=".db",
            filetypes=[("SQLite case database", "*.db"), ("All files", "*.*")],
            initialfile=f"{case_id}.db",
        )
        if not path:
            return
        self._replace_db(CaseDatabase.create(Path(path), case_id))

    def _open_case(self):
        path = filedialog.askopenfilename(
            title="Open case database",
            filetypes=[("SQLite case database", "*.db"), ("All files", "*.*")],
        )
        if path:
            self._replace_db(CaseDatabase(Path(path)))

    def _replace_db(self, db: CaseDatabase):
        if self.db:
            self.db.close()
        self.db = db
        self.case_var.set(f"Case: {db.get_meta('case_id')}   |   DB: {db.path}")
        self.import_btn.configure(state="normal")
        self._refresh()

    def _import_package(self):
        if not self.db:
            return
        paths = filedialog.askopenfilenames(
            title="Import collector packages",
            filetypes=[("PEF package", "*.pefpack"), ("All files", "*.*")],
        )
        if not paths:
            return
        warnings: list[str] = []
        try:
            for path in paths:
                warnings.extend(self.db.import_package(Path(path)))
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc))
            self._refresh()
            return
        self._refresh()
        if warnings:
            messagebox.showwarning("Integrity warnings", "\n".join(warnings))

    def _refresh(self):
        for item in self.entity_tree.get_children():
            self.entity_tree.delete(item)
        for item in self.obs_tree.get_children():
            self.obs_tree.delete(item)
        self.entities_cache.clear()
        if not self.db:
            return
        entities = self.db.entities()
        for entity in entities:
            self.entities_cache[entity["entity_id"]] = entity
            self.entity_tree.insert(
                "",
                "end",
                iid=entity["entity_id"],
                values=(
                    entity["existence_confidence"],
                    entity["existence_score"],
                    entity["acquisition_priority"],
                    entity["priority_score"],
                    entity["status"],
                    entity["entity_type"],
                    entity["display_name"],
                    entity["source_count"],
                    entity["artifact_count"],
                    entity["identity_strength"],
                ),
            )
        self.footer_var.set(
            f"Sources imported: {len(self.db.sources())} | Candidate entities: {len(entities)} | "
            "Existence Confidence and Acquisition Priority are separate experimental heuristics. "
            "Registry last-write values are used only as recency signals, not exact connection times."
        )

    def _show_observations(self, _event=None):
        for item in self.obs_tree.get_children():
            self.obs_tree.delete(item)
        selection = self.entity_tree.selection()
        if not selection:
            return
        entity = self.entities_cache.get(selection[0])
        if not entity:
            return
        for obs in entity["observations"]:
            ids = "; ".join(f"{k}={v}" for k, v in obs.identifiers.items())
            self.obs_tree.insert("", "end", values=(
                obs.source_id,
                obs.artifact_type,
                obs.relation_type,
                obs.display_name,
                ids,
            ))

    def _set_status(self, status: str):
        if not self.db:
            return
        selection = self.entity_tree.selection()
        if not selection:
            messagebox.showinfo("Select a source", "Select a potential evidence source first.")
            return
        self.db.set_entity_status(selection[0], status)
        self._refresh()

    def _close(self):
        if self.db:
            self.db.close()
        self.destroy()


def main():
    CaseManagerApp().mainloop()


if __name__ == "__main__":
    main()
