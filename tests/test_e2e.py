"""Essai de bout en bout de lcnik_core contre un LightCraft isolé (port 7981) et un faux Nik."""
import json
import os
import sys
import time

T = os.path.abspath(sys.argv[1])  # dossier de travail préparé par run-tests.ps1
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lcnik_core as core  # noqa: E402

PORT = 7981
FAKE = os.path.join(T, "FakeNik.exe")
core.PARAMS_DIR = os.path.join(T, "params")
core.find_apps = lambda: {k: {"key": k, "name": n, "exe": FAKE, "suffix": s} for k, n, s, _ in core.APPS}
ok = True


def check(label, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(("OK    " if cond else "ÉCHEC ") + label + (("  — " + str(detail)) if detail and not cond else ""))


# le port s'ouvre avant que LightCraft ait fini de démarrer (GPU) : attendre qu'il réponde vraiment
for _ in range(30):
    try:
        probe = core.LightCraft(PORT)
        probe.selection()
        probe.close()
        break
    except core.NikError:
        time.sleep(1)

lc = core.LightCraft(PORT)
st = core.status(PORT)
check("status : LightCraft connecté", st["lightcraft"]["connected"], st["lightcraft"])
check("status : autre éditeur réglé", st["lightcraft"].get("editor_set"))
ui = lc.request("ui.set", {})
check("réglage externalEditor = lanceur", ui["settings"]["externalEditor"] == core.LAUNCHER_EXE, ui["settings"].get("externalEditor"))
check("réglage TIFF 16 bits ProPhoto", ui["settings"]["externalFile"] == {"format": "tiff", "colorSpace": "proPhoto", "bitDepth": 16},
      ui["settings"]["externalFile"])

imp = lc.run("library.import", {"paths": [os.path.join(T, "photos")], "mode": "add"})
ids = imp["imported"]
check("import des 3 photos de test", len(ids) == 3, imp)
p1, p2, p3 = ids

r = core.edit("silver", "adjusted", [p1], PORT)
copy1 = r["copies"][0]
check("adjusted : copie TIFF rendue", copy1["path"].endswith("-Edit.tif") and os.path.exists(copy1["path"]), r)

lc.run("library.select", {"ids": [p2], "active": p2})
lc.run("develop.set", {"values": {"light.exposure": 1.0}})  # un réglage que la copie ne doit pas garder
r = core.edit("color", "copy", [p2], PORT)
f2 = r["files"][0]
check("copy : copie -copy.jpg créée et importée", f2["path"].endswith("-copy.jpg") and f2["id"] != p2, r)
exposure = ((lc.develop(f2["id"]) or {}).get("light") or {}).get("exposure", 0)
check("copy : la copie repart sans les réglages LightCraft", exposure == 0, exposure)
stack = (lc.run("photo.inspect", {"id": f2["id"]}) or {}).get("stack") or {}
check("copy : empilée au-dessus de l'original", stack.get("photos", [None])[0] == f2["id"] and p2 in stack.get("photos", []), stack)

r = core.edit("viveza", "original", [p3], PORT)
check("original : fichier lui-même ouvert", r["files"][0]["id"] == p3 and r["files"][0]["path"] == lc.photo_path(p3), r)

r = core.hdr([p1, p2], "adjusted", PORT)
check("HDR : résultat importé et empilé", r.get("imported") and os.path.exists(r["path"]), r)
if r.get("imported"):
    stack = (lc.run("photo.inspect", {"id": r["imported"]}) or {}).get("stack") or {}
    check("HDR : pile avec les photos sources", set([p1, p2]) <= set(stack.get("photos", [])), stack)

check("détection : Silver Efex", core.plugin_from_params('{"Info":{"Engine":{"PluginName":"Nik 9 Silver Efex"}}}') == "silver")
check("détection : Color Efex (ancien format)", core.plugin_from_params("<ColorEfexPro4_filter>...") == "color")
check("détection : Sharpener Output", core.plugin_from_params('{"PluginName":"Nik 9 Sharpener Output"}') == "sharpener")

os.makedirs(core.PARAMS_DIR, exist_ok=True)
with open(os.path.join(core.PARAMS_DIR, "silver.params"), "w") as f:
    f.write('{"PluginName":"Nik 9 Silver Efex"}')
with open(os.path.join(core.PARAMS_DIR, "silver.json"), "w") as f:
    json.dump({"source": "test", "copied": "2026-10-17 22:00:00"}, f)
r = core.apply_params([p3], None, False, "adjusted", PORT)
out = r["applied"][0]["path"] if r["applied"] else ""
check("appliquer : résultat -sep.tif empilé", out.endswith("-sep.tif") and os.path.exists(out) and not r["errors"], r)

time.sleep(8)  # laisser les surveillances recharger
log = open(os.path.join(T, "fakenik.log"), encoding="utf-8", errors="replace").read()
print("--- appels reçus par le faux Nik :\n" + log)
check("faux Nik : --paste --input --params --output", "--paste | --input |" in log and "| --params |" in log and "| --output |" in log)
check("faux Nik : --host-lightroom <config>", "--host-lightroom | " in log)
check("rechargements journalisés", "rechargé" in open(core.LOG_FILE, encoding="utf-8").read())
print("RÉSULTAT :", "tout est bon" if ok else "des échecs")
lc.close()
sys.exit(0 if ok else 1)
