"""Nik Collection pour LightCraft : le moteur commun à la palette, au sélecteur et au serveur MCP.

Reproduit l'intégration de Nik Collection dans Lightroom Classic :
  - Modifier dans (copie avec les réglages LightCraft / copie de l'original / original), TIFF 16 bits ProPhoto,
    copie empilée sur l'original et rechargée quand Nik l'enregistre ;
  - HDR Efex sur plusieurs photos ;
  - Copier et appliquer les paramètres d'un effet Nik à d'autres photos ;
  - Reprendre la retouche d'un TIFF déjà passé dans Nik (non destructif).

LightCraft est piloté par son canal de contrôle (127.0.0.1:7980, LIGHTCRAFT_CONTROL_PORT) ; les rendus
passent par `lightcraft-cli render`, qui n'a pas la limite de 60 s du canal.
"""

import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import winreg
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "LightCraftNik")
PARAMS_DIR = os.path.join(DATA_DIR, "params")
LOG_FILE = os.path.join(DATA_DIR, "lcnik.log")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
LAUNCHER_EXE = os.path.join(HERE, "NikPourLightCraft.exe")
DEFAULT_PORT = 7980
LIGHTCRAFT_CLI = r"C:\Program Files\LightCraft\lightcraft-cli.exe"

# Applis Nik : clé, nom affiché (« Nik 9 Silver Efex.exe » → « Silver Efex »), suffixe des fichiers produits par
# Copier et appliquer (ceux du module Lightroom de DxO), mots qui reconnaissent l'appli dans ses paramètres.
APPS = [
    ("silver", "Silver Efex", "-sep", ("silver",)),
    ("color", "Color Efex", "-cep", ("colorefex", "color efex", "colorefexpro")),
    ("analog", "Analog Efex", "-aep", ("analog",)),
    ("viveza", "Viveza", "-vvz", ("viveza",)),
    ("hdr", "HDR Efex", "-hdr", ("hdr",)),
    ("dfine", "Dfine", "-df", ("dfine",)),
    ("sharpener", "Sharpener Output", "-sh", ("outputsharpen", "sharpener output", "shpos")),
    ("presharpener", "Presharpener", "-psh", ("presharpen", "rawpresharpening", "shprps")),
]
RAW_EXT = {
    ".3fr", ".ari", ".arw", ".bay", ".braw", ".crw", ".cr2", ".cr3", ".cap", ".dcs", ".dcr", ".dng", ".drf", ".eip",
    ".erf", ".fff", ".gpr", ".iiq", ".k25", ".kdc", ".mdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".obm", ".orf",
    ".pef", ".ptx", ".pxn", ".r3d", ".raf", ".raw", ".rwl", ".rw2", ".rwz", ".sr2", ".srf", ".srw", ".x3f",
}
# Ce que Nik sait ouvrir tel quel (« Modifier l'original »).
EDITABLE_EXT = {".tif", ".tiff", ".jpg", ".jpeg"}
MODES = ("adjusted", "copy", "original")
# Au plus 50 photos par « Modifier dans » : la limite de LightCraft (photo.editExternal), et chaque photo ouvre Nik.
MAX_EDIT = 50
NO_WINDOW = 0x08000000
DETACHED = 0x00000008


class NikError(Exception):
    pass


def log(msg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S  ") + msg + "\n")


def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------------------------- Nik

def nik_bin_dir():
    """Le dossier bin de la Nik Collection la plus récente (registre, sinon Program Files)."""
    candidates = []
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            key = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        except OSError:
            continue
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                sub = winreg.OpenKey(key, winreg.EnumKey(key, i))
                name = winreg.QueryValueEx(sub, "DisplayName")[0]
                loc = winreg.QueryValueEx(sub, "InstallLocation")[0]
            except OSError:
                continue
            if "nik" in name.lower() and loc:
                candidates.append(os.path.join(loc, "bin"))
    candidates += sorted(glob.glob(r"C:\Program Files\DxO\Nik Collection*\bin"), reverse=True)
    for d in candidates:
        if glob.glob(os.path.join(d, "Nik * *.exe")):
            return d
    return None


def find_apps():
    """{clé: {"key", "name", "exe", "suffix"}} des applis Nik installées (la version la plus haute de chacune)."""
    d = nik_bin_dir()
    found = {}
    if not d:
        return found
    for key, name, suffix, _ in APPS:
        exes = glob.glob(os.path.join(d, "Nik * " + name + ".exe"))
        if exes:
            found[key] = {"key": key, "name": name, "exe": sorted(exes)[-1], "suffix": suffix}
    return found


def app_for(key_or_name):
    apps = find_apps()
    k = (key_or_name or "").strip().lower()
    for a in apps.values():
        if k in (a["key"], a["name"].lower()) or k == os.path.basename(a["exe"]).lower():
            return a
    raise NikError("appli Nik inconnue ou absente : %r (disponibles : %s)" % (key_or_name, ", ".join(apps) or "aucune"))


def plugin_from_params(text):
    """L'appli Nik qui a produit des paramètres (fichier écrit par nondestructive_util)."""
    names = []
    try:
        data = json.loads(text)
        stack = [data]
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                for k, x in v.items():
                    if k.lower() in ("pluginname", "plugin", "name", "product") and isinstance(x, str):
                        names.append(x)
                    stack.append(x)
            elif isinstance(v, list):
                stack.extend(v)
    except ValueError:
        pass
    hay = " ".join(names + [text[:4000]]).lower().replace("_", "")
    for key, _, _, words in APPS:
        if any(w in hay for w in words):
            return key
    return None


# ---------------------------------------------------------------------------------------- LightCraft

class LightCraft:
    """Client du canal de contrôle (JSON par lignes) de l'application LightCraft ouverte."""

    def __init__(self, port=None, timeout=90):
        self.port = int(port or os.environ.get("LIGHTCRAFT_CONTROL_PORT") or load_config().get("port") or DEFAULT_PORT)
        self.timeout = timeout
        self.sock = None
        self.buf = b""
        self.next_id = 0

    def _connect(self):
        try:
            self.sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        except OSError:
            raise NikError(
                "LightCraft ne répond pas sur 127.0.0.1:%d. Ouvrez LightCraft (lancé avec --control %d ou la variable "
                "LIGHTCRAFT_CONTROL_PORT=%d)." % (self.port, self.port, self.port)
            )
        self.sock.settimeout(self.timeout)
        self.buf = b""

    def request(self, method, params=None):
        if self.sock is None:
            self._connect()
        self.next_id += 1
        msg = {"id": self.next_id, "method": method}
        if params is not None:
            msg["params"] = params
        try:
            self.sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
            while b"\n" not in self.buf:
                chunk = self.sock.recv(1 << 20)
                if not chunk:
                    raise OSError("connexion fermée")
                self.buf += chunk
        except OSError as e:
            self.close()
            raise NikError("échange avec LightCraft interrompu (%s) : vérifiez son état avant de recommencer" % e)
        line, self.buf = self.buf.split(b"\n", 1)
        reply = json.loads(line.decode("utf-8"))
        if not reply.get("ok"):
            raise NikError("LightCraft : %s" % reply.get("error"))
        return reply.get("result")

    def run(self, command, params=None):
        return self.request("engine.execute", {"command": command, "params": params or {}})

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    # -- raccourcis

    def selection(self):
        sel = (self.run("library.state") or {}).get("selection") or {}
        return sel.get("ids") or [], sel.get("active")

    def targets(self, ids=None):
        if ids:
            return [int(i) for i in ids]
        sel, active = self.selection()
        if not sel and active is not None:
            sel = [active]
        if not sel:
            raise NikError("aucune photo sélectionnée dans LightCraft")
        return sel

    def photo_path(self, pid):
        source = (self.run("photo.inspect", {"id": pid}) or {}).get("source") or {}
        path = source.get("path") if source.get("type") == "file" else None
        if not path:
            raise NikError("la photo %s n'a pas de fichier (photo de démonstration ?)" % pid)
        return path

    def develop(self, pid):
        return self.run("develop.get", {"id": pid})

    def import_and_stack(self, path, original):
        r = self.run("library.import", {"paths": [path], "mode": "add"}) or {}
        new = (r.get("imported") or [None])[0]
        if new is None:
            raise NikError("LightCraft n'a pas pu ajouter %s" % path)
        # comme Edit In de LightCraft : la retouche au-dessus de l'original, pile dépliée
        self.run("stack.group", {"ids": [new, original], "top": new, "collapsed": False})
        return new

    def reload(self, ids):
        return self.run("photo.reload", {"ids": list(ids)})

    def ensure_editor_setting(self):
        """Settings ▸ External Editing ▸ Other editor = le sélecteur Nik, en TIFF 16 bits ProPhoto (comme Lightroom)."""
        if not os.path.isfile(LAUNCHER_EXE):
            return False
        current = (self.request("ui.set", {}) or {}).get("settings") or {}
        editor = (current.get("externalEditor") or "").strip()
        if editor and not editor.lower().endswith("nikpourlightcraft.exe"):
            return False  # un autre éditeur choisi par l'utilisateur : ne pas y toucher
        if editor == LAUNCHER_EXE and (current.get("externalFile") or {}).get("colorSpace") == "proPhoto":
            return True
        self.request("ui.set", {"settings": {
            "externalEditor": LAUNCHER_EXE,
            "externalFile": {"format": "tiff", "colorSpace": "proPhoto", "bitDepth": 16},
        }})
        return True


# ------------------------------------------------------------------------------------------ outils

def unique_path(path):
    stem, ext = os.path.splitext(path)
    n, out = 1, path
    while os.path.exists(out):
        out = "%s-%d%s" % (stem, n, ext)
        n += 1
    return out


def render_tiff(lc, pid, out):
    """Rend la photo `pid` avec ses réglages LightCraft en TIFF 16 bits ProPhoto, pleine taille."""
    src = lc.photo_path(pid)
    settings = lc.develop(pid) or {}
    fd, sfile = tempfile.mkstemp(suffix=".json", prefix="lcnik-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(settings, f)
    try:
        cmd = [LIGHTCRAFT_CLI, "render", src, "-o", out, "--settings", sfile,
               "--opt", "colorSpace=proPhoto", "--opt", "bitDepth=16", "--opt", "tiffCompression=none",
               "--opt", "metadata=all"]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
        if p.returncode != 0 or not os.path.isfile(out):
            raise NikError("rendu de %s impossible : %s" % (os.path.basename(src), (p.stderr or p.stdout).strip()[-400:]))
    finally:
        os.remove(sfile)
    return out


def launch(exe, *args):
    return subprocess.Popen([exe] + list(args), creationflags=DETACHED)


def nik_running(exe):
    name = os.path.basename(exe)
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + name, "/NH", "/FO", "CSV"], capture_output=True,
                         text=True, errors="replace", creationflags=NO_WINDOW).stdout
    return name.lower() in out.lower()


def start_watch(exe, pairs, port=None):
    """Surveille en arrière-plan (processus détaché) les fichiers ouverts dans Nik et les recharge dans LightCraft."""
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = sys.executable
    spec = json.dumps({"exe": exe, "pairs": pairs, "port": port})
    subprocess.Popen([pythonw, "-I", os.path.abspath(__file__), "watch", spec], creationflags=DETACHED | NO_WINDOW,
                     close_fds=True)


def watch(spec):
    """Recharge chaque photo dont le fichier change, tant que l'appli Nik tourne (3 h au plus)."""
    exe, pairs, port = spec["exe"], spec["pairs"], spec.get("port")
    mtimes = {p: os.path.getmtime(p) if os.path.exists(p) else 0 for _, p in pairs}
    start, absent = time.time(), 0
    while time.time() - start < 3 * 3600:
        time.sleep(2)
        changed = [pid for pid, p in pairs if os.path.exists(p) and os.path.getmtime(p) != mtimes[p]]
        if changed:
            time.sleep(1)  # laisser Nik finir d'écrire
            for _, p in pairs:
                if os.path.exists(p):
                    mtimes[p] = os.path.getmtime(p)
            try:
                lc = LightCraft(port)
                lc.reload(changed)
                lc.close()
                log("rechargé %s" % changed)
            except NikError as e:
                log("rechargement impossible : %s" % e)
        absent = 0 if nik_running(exe) else absent + 1
        if absent >= 3 and time.time() - start > 10:
            break


# -------------------------------------------------------------------------------------- fonctions

def status(port=None):
    apps = find_apps()
    out = {"nik_bin": nik_bin_dir(), "apps": list(apps.values()), "launcher": LAUNCHER_EXE,
           "launcher_present": os.path.isfile(LAUNCHER_EXE), "saved_params": saved_params()}
    lc = LightCraft(port)
    try:
        ids, active = lc.selection()
        out["lightcraft"] = {"connected": True, "port": lc.port, "selection": ids, "active": active,
                             "editor_set": lc.ensure_editor_setting()}
    except NikError as e:
        out["lightcraft"] = {"connected": False, "port": lc.port, "error": str(e)}
    finally:
        lc.close()
    return out


def edit(app, mode="adjusted", ids=None, port=None):
    """Photo ▸ Modifier dans ▸ <appli Nik>, avec les trois choix de Lightroom."""
    if mode not in MODES:
        raise NikError("mode inconnu %r (%s)" % (mode, ", ".join(MODES)))
    a = app_for(app)
    lc = LightCraft(port)
    try:
        targets = lc.targets(ids)
        if len(targets) > MAX_EDIT:
            raise NikError(
                "%d photos sélectionnées : « Modifier dans » en ouvre %d au plus à la fois, chacune dans sa fenêtre Nik. "
                "Sélectionnez moins de photos, ou utilisez « Appliquer les paramètres » pour traiter un lot."
                % (len(targets), MAX_EDIT))
        if mode == "adjusted":
            # LightCraft rend la copie, l'empile, lance Nik et la recharge au retour dans sa fenêtre
            r = lc.run("photo.editInExternal", {"ids": targets, "app": a["exe"], "format": "tiff",
                                                 "colorSpace": "proPhoto", "bitDepth": 16})
            copies = r.get("copies") or [{"path": r.get("path"), "id": r.get("id"), "original": r.get("original")}]
            start_watch(a["exe"], [[c["id"], c["path"]] for c in copies], lc.port)
            return {"app": a["name"], "mode": mode, "copies": copies}
        done, notes, pairs = [], [], []
        for pid in targets:
            src = lc.photo_path(pid)
            ext = os.path.splitext(src)[1].lower()
            if ext in RAW_EXT or ext not in EDITABLE_EXT:
                # comme Lightroom : un raw passe en copie TIFF avec les réglages
                out = unique_path(os.path.splitext(src)[0] + "-Edit.tif")
                render_tiff(lc, pid, out)
                new = lc.import_and_stack(out, pid)
                notes.append("%s : raw, copie TIFF avec les réglages LightCraft" % os.path.basename(src))
                pairs.append([new, out])
                done.append({"original": pid, "id": new, "path": out})
            elif mode == "copy":
                # une copie octet pour octet serait refusée à l'import comme doublon : LightCraft la fait lui-même
                new = lc.run("photo.duplicate", {"ids": [pid]})["ids"][0]
                lc.run("develop.reset", {"ids": [new]})  # comme Lightroom : la copie part de l'original, sans réglages
                lc.run("stack.group", {"ids": [new, pid], "top": new, "collapsed": False})
                out = lc.photo_path(new)
                pairs.append([new, out])
                done.append({"original": pid, "id": new, "path": out})
            else:
                pairs.append([pid, src])
                done.append({"original": pid, "id": pid, "path": src})
        for _, path in pairs:
            launch(a["exe"], path)
            time.sleep(1)
        start_watch(a["exe"], pairs, lc.port)
        return {"app": a["name"], "mode": mode, "files": done, "notes": notes}
    finally:
        lc.close()


def hdr(ids=None, mode="adjusted", port=None, wait=True):
    """Fichier ▸ Exporter avec un préréglage ▸ Nik HDR Efex : fusionne les photos et ajoute le résultat empilé."""
    a = app_for("hdr")
    lc = LightCraft(port)
    try:
        targets = lc.targets(ids)
        work = tempfile.mkdtemp(prefix="lcnik-hdr-")
        inputs = []
        for pid in targets:
            src = lc.photo_path(pid)
            if mode == "original":
                inputs.append(src)
            else:
                inputs.append(render_tiff(lc, pid, os.path.join(work, os.path.splitext(os.path.basename(src))[0] + ".tif")))
        first = lc.photo_path(targets[0])
        out_dir = os.path.dirname(first)
        results = os.path.join(work, "results.txt")
        cfg = os.path.join(work, "hdr.xml")
        lines = ["<configuration>", ' <group name="general">', '  <key name="input-images" type="string_array">']
        lines += ["   <string value=%s/>" % quoteattr(p) for p in inputs]
        lines += ["  </key>", '  <key name="output-path" type="string" value=%s/>' % quoteattr(out_dir),
                  '  <key name="run-results-file" type="string" value=%s/>' % quoteattr(results), " </group>",
                  "</configuration>"]
        with open(cfg, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        log("HDR : %d images, config %s" % (len(inputs), cfg))
        before = set(glob.glob(os.path.join(out_dir, "*")))
        t0 = time.time()
        proc = launch(a["exe"], "--host-lightroom", cfg)
        if not wait:
            return {"app": a["name"], "started": True, "config": cfg, "inputs": inputs}
        proc.wait()
        # une appli qui passe la main à une instance déjà ouverte rend tout de suite : attendre son fichier résultat
        while not os.path.exists(results) and nik_running(a["exe"]) and time.time() - t0 < 3 * 3600:
            time.sleep(2)
        res = {}
        if os.path.exists(results):
            with open(results, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.split("=", 1)
                        res[k.strip().lower()] = v.strip()
        made = res.get("filename")
        if made and not os.path.isabs(made):
            made = os.path.join(out_dir, made)
        if not made or not os.path.exists(made):
            fresh = [p for p in set(glob.glob(os.path.join(out_dir, "*"))) - before
                     if os.path.getmtime(p) >= t0 and os.path.splitext(p)[1].lower() in (".tif", ".tiff", ".jpg", ".jpeg")]
            made = max(fresh, key=os.path.getmtime) if fresh else None
        if not made:
            return {"app": a["name"], "imported": None, "results": res, "note": "HDR Efex n'a rien enregistré (annulé ?)"}
        if res.get("reimport", "true").lower() in ("false", "no", "0"):
            return {"app": a["name"], "path": made, "imported": None, "results": res}
        new = lc.run("library.import", {"paths": [made], "mode": "add"})["imported"][0]
        if res.get("stack", "true").lower() not in ("false", "no", "0"):
            lc.run("stack.group", {"ids": [new] + targets, "top": new, "collapsed": False})
        shutil.rmtree(work, ignore_errors=True)
        return {"app": a["name"], "path": made, "imported": new, "stacked_with": targets, "results": res}
    finally:
        lc.close()


def extract_params(tiff):
    util = os.path.join(nik_bin_dir() or "", "nondestructive_util.exe")
    if not os.path.isfile(util):
        raise NikError("nondestructive_util.exe introuvable dans la Nik Collection")
    if os.path.splitext(tiff)[1].lower() not in (".tif", ".tiff"):
        raise NikError("%s n'est pas un TIFF : seuls les TIFF enregistrés par Nik portent ses paramètres" % os.path.basename(tiff))
    fd, out = tempfile.mkstemp(suffix=".params", prefix="lcnik-")
    os.close(fd)
    p = subprocess.run([util, tiff, out], capture_output=True, text=True, errors="replace", creationflags=NO_WINDOW)
    text = ""
    if os.path.exists(out):
        with open(out, encoding="utf-8", errors="replace") as f:
            text = f.read()
    if not text.strip():
        os.remove(out)
        raise NikError("%s ne contient pas de paramètres Nik (code %s %s)" % (os.path.basename(tiff), p.returncode,
                                                                            (p.stderr or p.stdout).strip()[:300]))
    return out, text


def copy_params(pid=None, port=None):
    """Copier les paramètres Nik de la photo active (un TIFF retouché dans Nik)."""
    lc = LightCraft(port)
    try:
        if pid is None:
            pid = lc.targets()[0] if lc.selection()[1] is None else lc.selection()[1]
        src = lc.photo_path(pid)
    finally:
        lc.close()
    tmp, text = extract_params(src)
    key = plugin_from_params(text)
    if not key:
        os.remove(tmp)
        raise NikError("impossible de savoir quelle appli Nik a produit ces paramètres")
    os.makedirs(PARAMS_DIR, exist_ok=True)
    dest = os.path.join(PARAMS_DIR, key + ".params")
    shutil.move(tmp, dest)
    with open(os.path.join(PARAMS_DIR, key + ".json"), "w", encoding="utf-8") as f:
        json.dump({"source": src, "photo": pid, "copied": time.strftime("%Y-%m-%d %H:%M:%S")}, f, ensure_ascii=False)
    return {"plugin": key, "name": dict((k, n) for k, n, _, _ in APPS)[key], "source": src, "params": dest}


def saved_params():
    out = []
    for key, name, _, _ in APPS:
        p = os.path.join(PARAMS_DIR, key + ".params")
        if os.path.exists(p):
            meta = {}
            try:
                with open(os.path.join(PARAMS_DIR, key + ".json"), encoding="utf-8") as f:
                    meta = json.load(f)
            except (OSError, ValueError):
                pass
            out.append({"plugin": key, "name": name, "params": p, "source": meta.get("source"), "copied": meta.get("copied")})
    return out


def apply_params(ids=None, plugin=None, show_ui=False, mode="adjusted", port=None):
    """Appliquer les paramètres copiés aux photos sélectionnées ; chaque résultat est empilé sur sa photo."""
    saved = saved_params()
    if not saved:
        raise NikError("aucun paramètre copié : utilisez d'abord Copier les paramètres")
    if plugin:
        entry = next((s for s in saved if s["plugin"] == app_for(plugin)["key"]), None)
        if not entry:
            raise NikError("aucun paramètre copié pour %s" % plugin)
    else:
        entry = max(saved, key=lambda s: s.get("copied") or "")
    a = app_for(entry["plugin"])
    lc = LightCraft(port)
    results, errors = [], []
    try:
        for pid in lc.targets(ids):
            try:
                src = lc.photo_path(pid)
                ext = os.path.splitext(src)[1].lower()
                tmpdir = tempfile.mkdtemp(prefix="lcnik-apply-")
                if mode == "original" and ext in EDITABLE_EXT:
                    inp = src
                elif mode == "copy" and ext in EDITABLE_EXT:
                    inp = shutil.copy2(src, os.path.join(tmpdir, os.path.basename(src)))
                else:
                    inp = render_tiff(lc, pid, os.path.join(tmpdir, "in.tif"))
                out = unique_path(os.path.splitext(src)[0] + a["suffix"] + ".tif")
                cmd = [a["exe"], "--paste", "--input", inp, "--params", entry["params"], "--output", out]
                if show_ui:
                    cmd.append("--showUI")
                p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                if not os.path.exists(out):
                    raise NikError("%s n'a rien produit (code %s) %s" % (a["name"], p.returncode, (p.stderr or "").strip()[:300]))
                new = lc.import_and_stack(out, pid)
                results.append({"original": pid, "id": new, "path": out})
                shutil.rmtree(tmpdir, ignore_errors=True)
            except NikError as e:
                errors.append({"photo": pid, "error": str(e)})
        return {"app": a["name"], "params_from": entry.get("source"), "applied": results, "errors": errors}
    finally:
        lc.close()


def reedit(pid=None, port=None):
    """Rouvrir un TIFF retouché dans l'appli Nik qui l'a produit, qui reprend ses réglages (non destructif)."""
    lc = LightCraft(port)
    try:
        if pid is None:
            ids, active = lc.selection()
            pid = active if active is not None else lc.targets()[0]
        src = lc.photo_path(pid)
    finally:
        lc.close()
    tmp, text = extract_params(src)
    os.remove(tmp)
    key = plugin_from_params(text)
    if not key:
        raise NikError("impossible de savoir quelle appli Nik a produit %s" % os.path.basename(src))
    a = app_for(key)
    launch(a["exe"], src)
    start_watch(a["exe"], [[pid, src]], port)
    return {"app": a["name"], "photo": pid, "path": src}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "watch":
        try:
            watch(json.loads(sys.argv[2]))
        except Exception as e:  # processus détaché : tout finit dans le journal
            log("surveillance arrêtée : %r" % e)
    else:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
