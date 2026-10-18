from __future__ import annotations

import queue
import socket
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from collector_engine import CollectionOptions, collect


class CollectorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Potential Evidence Finder - Field Collector")
        self.geometry("1120x760")
        self.minsize(980, 650)
        self.queue: queue.Queue = queue.Queue()
        self._build()

    def _build(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Case ID").grid(row=0, column=0, sticky="w", padx=(0,8), pady=4)
        self.case_var=tk.StringVar(); ttk.Entry(top,textvariable=self.case_var,width=28).grid(row=0,column=1,sticky="ew",pady=4)
        ttk.Label(top,text="Source ID").grid(row=0,column=2,sticky="w",padx=(18,8),pady=4)
        self.source_var=tk.StringVar(value=socket.gethostname()); ttk.Entry(top,textvariable=self.source_var,width=28).grid(row=0,column=3,sticky="ew",pady=4)
        ttk.Label(top,text="Output folder").grid(row=1,column=0,sticky="w",padx=(0,8),pady=4)
        app_dir=Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent
        self.output_var=tk.StringVar(value=str(app_dir/"results")); ttk.Entry(top,textvariable=self.output_var).grid(row=1,column=1,columnspan=2,sticky="ew",pady=4)
        ttk.Button(top,text="Browse...",command=self._browse).grid(row=1,column=3,sticky="ew",padx=(8,0),pady=4)
        top.columnconfigure(1,weight=1); top.columnconfigure(2,weight=1)

        opts=ttk.LabelFrame(self,text="Relationship artifact options",padding=10); opts.pack(fill="x",padx=12,pady=(0,8))
        ttk.Label(opts,text="Artifact / evidence source").grid(row=0,column=0,sticky="w",padx=8,pady=(0,4)); ttk.Label(opts,text="Analyze").grid(row=0,column=1,sticky="w",padx=18,pady=(0,4)); ttk.Label(opts,text="Preserve source artifact / snapshot").grid(row=0,column=2,sticky="w",padx=18,pady=(0,4))
        self.opt_vars={}; self.preserve_vars={}
        labels=[("usb","USB storage (USBSTOR)"),("mounted_devices","Mounted volumes (MountedDevices)"),("network","Network resources (Mapped drives / MountPoints2)"),("portable_devices","Portable devices (WPD)"),("bluetooth","Bluetooth known devices"),("setupapi","SetupAPI device traces")]
        for row,(key,label) in enumerate(labels,start=1):
            analyze=tk.BooleanVar(value=True); preserve=tk.BooleanVar(value=False); self.opt_vars[key]=analyze; self.preserve_vars[key]=preserve
            ttk.Label(opts,text=label).grid(row=row,column=0,sticky="w",padx=8,pady=3)
            ttk.Checkbutton(opts,variable=analyze,command=lambda k=key:self._sync_preserve_state(k)).grid(row=row,column=1,sticky="w",padx=18)
            cb=ttk.Checkbutton(opts,variable=preserve); cb.grid(row=row,column=2,sticky="w",padx=18); setattr(self,f"preserve_cb_{key}",cb)
        ttk.Label(opts,text="Default: parsed results only. Source preservation is optional. SetupAPI is copied as a source file; registry sources are saved as .reg export snapshots, not binary hive images.",wraplength=1030).grid(row=len(labels)+1,column=0,columnspan=3,sticky="w",padx=8,pady=(8,0)); opts.columnconfigure(0,weight=1)

        action=ttk.Frame(self,padding=(12,0,12,10)); action.pack(fill="x")
        self.run_btn=ttk.Button(action,text="Analyze & Create Package",command=self._start); self.run_btn.pack(side="left")
        self.progress=ttk.Progressbar(action,mode="indeterminate",length=220); self.progress.pack(side="left",padx=12)
        self.status_var=tk.StringVar(value="Ready - parsed-results-only mode"); ttk.Label(action,textvariable=self.status_var).pack(side="left")
        columns=("type","name","artifact","relation","identifier"); self.tree=ttk.Treeview(self,columns=columns,show="headings")
        headings={"type":"Entity Type","name":"Display Name","artifact":"Artifact","relation":"Relation","identifier":"Key Identifier"}; widths={"type":140,"name":290,"artifact":140,"relation":200,"identifier":310}
        for col in columns:self.tree.heading(col,text=headings[col]); self.tree.column(col,width=widths[col],anchor="w")
        self.tree.pack(fill="both",expand=True,padx=12,pady=(0,8))
        bottom=ttk.Frame(self,padding=(12,0,12,12)); bottom.pack(fill="x"); self.result_var=tk.StringVar(value="No package created yet.")
        ttk.Label(bottom,textvariable=self.result_var,wraplength=1060).pack(anchor="w"); ttk.Label(bottom,text="Prototype note: registry timestamps are recorded as key last-write times, not asserted as exact connection times.").pack(anchor="w",pady=(6,0))

    def _sync_preserve_state(self,key):
        cb=getattr(self,f"preserve_cb_{key}")
        if self.opt_vars[key].get(): cb.configure(state="normal")
        else:self.preserve_vars[key].set(False);cb.configure(state="disabled")
    def _browse(self):
        path=filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.cwd()))
        if path:self.output_var.set(path)
    def _start(self):
        case_id=self.case_var.get().strip(); source_id=self.source_var.get().strip()
        if not case_id or not source_id: messagebox.showerror("Missing information","Case ID and Source ID are required."); return
        output=Path(self.output_var.get()).expanduser(); kwargs={k:v.get() for k,v in self.opt_vars.items()}; kwargs.update({f"preserve_{k}":v.get() for k,v in self.preserve_vars.items()}); options=CollectionOptions(**kwargs)
        self.run_btn.configure(state="disabled"); self.progress.start(10); self.status_var.set("Analyzing relationship artifacts...")
        for item in self.tree.get_children(): self.tree.delete(item)
        threading.Thread(target=self._worker,args=(case_id,source_id,output,options),daemon=True).start(); self.after(100,self._poll)
    def _worker(self,case_id,source_id,output,options):
        try:self.queue.put(("ok",collect(case_id,source_id,output,options)))
        except Exception as exc:self.queue.put(("error",exc))
    def _poll(self):
        try:kind,payload=self.queue.get_nowait()
        except queue.Empty:self.after(100,self._poll);return
        self.progress.stop();self.run_btn.configure(state="normal")
        if kind=="error":self.status_var.set("Failed");messagebox.showerror("Collection failed",str(payload));return
        result=payload
        for obs in result.observations:
            id_summary=next(iter(obs.identifiers.items()),("","")); self.tree.insert("","end",values=(obs.entity_type,obs.display_name,obs.artifact_type,obs.relation_type,f"{id_summary[0]}={id_summary[1]}"))
        preserved=sum(1 for r in result.preservation_records if r.get("success")); self.status_var.set(f"Completed: {len(result.observations)} observations | preserved sources: {preserved}"); self.result_var.set(f"Package: {result.package_path}")
        if result.warnings:messagebox.showwarning("Collection completed with warnings","\n".join(result.warnings[:12])+("\n..." if len(result.warnings)>12 else ""))

def main():CollectorApp().mainloop()
if __name__=="__main__":main()
