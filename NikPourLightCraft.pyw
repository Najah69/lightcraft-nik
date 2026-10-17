"""Nik Collection pour LightCraft : fenêtres.

  NikPourLightCraft.exe <fichiers…>  appelé par LightCraft (Photo ▸ Edit In ▸ Edit in Other Editor, Ctrl+Alt+E) avec les
                                     copies TIFF qu'il vient de rendre et d'empiler : choisir l'appli Nik qui les ouvre.
  NikPourLightCraft.exe              la palette : Modifier dans (3 modes), HDR Efex, Copier / Appliquer les paramètres,
                                     Reprendre la retouche, sur la sélection de LightCraft.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lcnik_core as core  # noqa: E402

TITLE = "Nik Collection pour LightCraft"
MODE_LABELS = [
    ("adjusted", "Modifier une copie avec les réglages LightCraft"),
    ("copy", "Modifier une copie de l'original"),
    ("original", "Modifier l'original"),
]
MODE_HINTS = {
    "adjusted": "Copie TIFF 16 bits ProPhoto empilée sur l'original.",
    "copy": "Les réglages LightCraft ne seront pas visibles. Un raw passe en copie TIFF.",
    "original": "Les réglages LightCraft ne seront pas visibles. TIFF et JPEG seulement.",
}


def picker(files):
    """Choisir l'appli Nik pour les copies que LightCraft vient de préparer."""
    apps = core.find_apps()
    if not apps:
        messagebox.showerror(TITLE, "Aucune appli de la Nik Collection n'a été trouvée.")
        return
    cfg = core.load_config()
    root = tk.Tk()
    root.title("Modifier dans Nik Collection")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    frm = ttk.Frame(root, padding=14)
    frm.pack(fill="both")
    names = ", ".join(os.path.basename(f) for f in files[:3]) + (" …" if len(files) > 3 else "")
    ttk.Label(frm, text="Ouvrir %s dans :" % names, wraplength=360).pack(anchor="w", pady=(0, 8))

    def open_in(app):
        cfg["last_app"] = app["key"]
        core.save_config(cfg)
        for f in files:
            core.launch(app["exe"], f)
        core.log("sélecteur : %s → %s" % (app["name"], files))
        root.destroy()

    last = cfg.get("last_app")
    for app in apps.values():
        b = ttk.Button(frm, text=app["name"], width=34, command=lambda a=app: open_in(a))
        b.pack(pady=2)
        if app["key"] == last:
            b.focus_set()
            root.bind("<Return>", lambda e, a=app: open_in(a))
    ttk.Label(frm, text="Enregistrez dans Nik : LightCraft met la copie à jour à votre retour.",
              foreground="#666", wraplength=360).pack(anchor="w", pady=(8, 0))
    ttk.Button(frm, text="Annuler", command=root.destroy).pack(anchor="e", pady=(10, 0))
    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()


class Palette:
    def __init__(self):
        self.apps = core.find_apps()
        self.cfg = core.load_config()
        self.root = tk.Tk()
        self.root.title(TITLE)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", bool(self.cfg.get("topmost", True)))
        f = ttk.Frame(self.root, padding=12)
        f.pack(fill="both")

        self.count = 0  # photos sélectionnées dans LightCraft, au dernier relevé
        self.state = ttk.Label(f, text="Connexion à LightCraft…", foreground="#666")
        self.state.grid(row=0, column=0, columnspan=2, sticky="w")

        box = ttk.LabelFrame(f, text="Modifier dans", padding=8)
        box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        names = [a["name"] for a in self.apps.values() if a["key"] != "hdr"]
        self.app = tk.StringVar(value=self._name(self.cfg.get("last_app")) or (names[0] if names else ""))
        ttk.Combobox(box, textvariable=self.app, values=names, state="readonly", width=30).pack(anchor="w")
        self.mode = tk.StringVar(value=self.cfg.get("last_mode", "adjusted"))
        for key, label in MODE_LABELS:
            ttk.Radiobutton(box, text=label, value=key, variable=self.mode, command=self._hint).pack(anchor="w")
        self.hint = ttk.Label(box, foreground="#666", wraplength=300)
        self.hint.pack(anchor="w", pady=(2, 4))
        ttk.Button(box, text="Modifier", command=self.do_edit).pack(anchor="e")

        box = ttk.LabelFrame(f, text="Autres fonctions", padding=8)
        box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(box, text="Fusion HDR Efex…", width=34, command=self.do_hdr,
                   state="normal" if "hdr" in self.apps else "disabled").pack(pady=2)
        ttk.Button(box, text="Copier les paramètres de la photo active", width=34, command=self.do_copy).pack(pady=2)
        self.show_ui = tk.BooleanVar(value=False)
        ttk.Button(box, text="Appliquer les paramètres à la sélection", width=34, command=self.do_apply).pack(pady=2)
        ttk.Checkbutton(box, text="Afficher Nik pour ajuster chaque photo", variable=self.show_ui).pack(anchor="w")
        ttk.Button(box, text="Reprendre la retouche Nik", width=34, command=self.do_reedit).pack(pady=2)
        self.saved = ttk.Label(box, foreground="#666", wraplength=300)
        self.saved.pack(anchor="w", pady=(4, 0))

        self.top = tk.BooleanVar(value=bool(self.cfg.get("topmost", True)))
        ttk.Checkbutton(f, text="Toujours au premier plan", variable=self.top, command=self._topmost).grid(row=3, column=0, sticky="w")
        self.msg = ttk.Label(f, wraplength=320)
        self.msg.grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self._hint()
        self._refresh_saved()
        self.root.after(200, self.poll)

    def _name(self, key):
        a = self.apps.get(key or "")
        return a["name"] if a else None

    def _key(self):
        return next((a["key"] for a in self.apps.values() if a["name"] == self.app.get()), None)

    def _hint(self):
        self.hint.config(text=MODE_HINTS[self.mode.get()])

    def _topmost(self):
        self.cfg["topmost"] = self.top.get()
        core.save_config(self.cfg)
        self.root.attributes("-topmost", self.top.get())

    def _refresh_saved(self):
        s = core.saved_params()
        self.saved.config(text="Paramètres copiés : " + (", ".join(x["name"] for x in s) if s else "aucun"))

    def poll(self):
        def work():
            try:
                st = core.status()
                lc = st["lightcraft"]
                self.count = len(lc.get("selection") or [])
                text = ("LightCraft connecté — %d photo(s) sélectionnée(s)" % self.count) if lc["connected"] \
                    else "LightCraft non joignable (port %d) : ouvrez-le." % lc["port"]
            except Exception as e:
                text = "État inconnu : %s" % e
            self.root.after(0, lambda: self.state.config(text=text))
        threading.Thread(target=work, daemon=True).start()
        self.root.after(4000, self.poll)

    def run(self, label, fn):
        self.msg.config(text=label + "…", foreground="#333")

        def work():
            try:
                r = fn()
                text, color = self.summary(r), "#1a7f37"
            except core.NikError as e:
                text, color = str(e), "#b42318"
            except Exception as e:
                core.log("palette : %r" % e)
                text, color = "Erreur : %r" % e, "#b42318"
            self.root.after(0, lambda: (self.msg.config(text=text, foreground=color), self._refresh_saved()))
        threading.Thread(target=work, daemon=True).start()

    @staticmethod
    def summary(r):
        if "copies" in r:
            return "%d copie(s) ouverte(s) dans %s." % (len(r["copies"]), r["app"])
        if "files" in r:
            return "%d photo(s) ouverte(s) dans %s. %s" % (len(r["files"]), r["app"], " ".join(r.get("notes", [])))
        if "imported" in r and "stacked_with" in r:
            return "HDR ajouté et empilé (photo %s)." % r["imported"]
        if "imported" in r:
            return r.get("note") or "HDR enregistré : %s" % r.get("path")
        if "plugin" in r and "params" in r:
            return "Paramètres %s copiés." % r["name"]
        if "applied" in r:
            err = "; ".join("photo %s : %s" % (e["photo"], e["error"]) for e in r["errors"])
            return "%d photo(s) traitée(s) avec %s. %s" % (len(r["applied"]), r["app"], err)
        if "photo" in r:
            return "Retouche reprise dans %s." % r["app"]
        return str(r)

    def do_edit(self):
        key = self._key()
        if not key:
            return
        if self.count > core.MAX_EDIT:
            self.msg.config(text="%d photos sélectionnées : « Modifier » en ouvre %d au plus à la fois. Sélectionnez-en "
                                 "moins, ou utilisez « Appliquer les paramètres » pour un lot." % (self.count, core.MAX_EDIT),
                            foreground="#b42318")
            return
        if self.count > 10 and not messagebox.askyesno(
                TITLE, "Ouvrir %d photos dans %s ?\nChacune s'ouvre dans sa propre fenêtre Nik." % (self.count, self.app.get()),
                parent=self.root):
            return
        self.cfg.update(last_app=key, last_mode=self.mode.get())
        core.save_config(self.cfg)
        self.run("Ouverture dans %s" % self.app.get(), lambda: core.edit(key, self.mode.get()))

    def do_hdr(self):
        self.run("HDR Efex en cours (attend sa fermeture)", lambda: core.hdr(mode="original" if self.mode.get() == "original" else "adjusted"))

    def do_copy(self):
        self.run("Lecture des paramètres", core.copy_params)

    def do_apply(self):
        self.run("Application des paramètres", lambda: core.apply_params(show_ui=self.show_ui.get(), mode=self.mode.get()))

    def do_reedit(self):
        self.run("Réouverture", core.reedit)


if __name__ == "__main__":
    files = [a for a in sys.argv[1:] if os.path.isfile(a)]
    if files:
        picker(files)
    else:
        Palette().root.mainloop()
