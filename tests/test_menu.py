"""Le vrai chemin du menu : Photo ▸ Edit In ▸ Edit in Other Editor → NikPourLightCraft.exe → sélecteur Nik."""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lcnik_core as core  # noqa: E402


def pyw_cmdlines():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"],
                         capture_output=True, text=True, errors="replace").stdout
    return dict(l.split("\t", 1) for l in out.splitlines() if "\t" in l)


lc = core.LightCraft(7981)
q = lc.run("catalog.query", {"limit": 500})
photos = q.get("photos", q) if isinstance(q, dict) else q
# photo-2 : test_e2e n'a encore mis au catalogue aucun rendu identique de celle-ci (LightCraft refuse les doublons,
# et le faux Nik recopie ses entrées telles quelles)
pid = next(p["id"] for p in photos if p.get("fileName") == "photo-2.jpg")
before = pyw_cmdlines()
lc.run("library.select", {"ids": [pid], "active": pid})
r = lc.run("photo.editInExternal")  # sans `app` : l'« autre éditeur » réglé, donc notre lanceur
print("copie rendue par LightCraft :", r["path"])
new = {}
for _ in range(10):  # LightCraft lance l'éditeur entre deux images : surveiller jusqu'à 10 s
    time.sleep(1)
    new = {k: v for k, v in pyw_cmdlines().items() if k not in before and "NikPourLightCraft" in v}
    if new:
        break
print("sélecteur lancé :", bool(new))
if not new:
    ui = lc.request("ui.inspect") or {}
    print("  diagnostic : toast =", ui.get("toast"), "| editor =", (lc.request("ui.set", {}) or {}).get("settings", {}).get("externalEditor"))
for k, v in new.items():
    print("  ligne de commande :", v.split("NikPourLightCraft.pyw\"")[-1].strip())
    subprocess.run(["taskkill", "/PID", k, "/F"], capture_output=True)
lc.close()
sys.exit(0 if new else 1)
