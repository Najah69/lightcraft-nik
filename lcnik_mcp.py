"""Serveur MCP « lightcraft-nik » : la Nik Collection de DxO dans LightCraft, pour Claude Code (stdio, JSON-RPC 2.0)."""

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lcnik_core as core  # noqa: E402

PROTOCOL = "2025-06-18"
IDS = {"type": "array", "items": {"type": "integer"},
       "description": "Photos LightCraft (par défaut : la sélection de l'application ouverte)"}
MODE = {"type": "string", "enum": list(core.MODES),
        "description": "adjusted = copie TIFF 16 bits ProPhoto avec les réglages LightCraft (défaut) ; copy = copie du "
                       "fichier original sans les réglages ; original = le fichier lui-même (TIFF/JPEG seulement ; un raw "
                       "passe toujours en copie TIFF)"}
APP = {"type": "string", "description": "Appli Nik : silver, color, analog, viveza, hdr, dfine, sharpener, presharpener"}

TOOLS = [
    {"name": "nik_status", "title": "État Nik + LightCraft",
     "description": "Applis Nik installées, connexion au LightCraft ouvert (sélection), paramètres copiés. Règle aussi "
                    "l'« autre éditeur » de LightCraft sur le sélecteur Nik.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
     "run": lambda a: core.status()},
    {"name": "nik_edit", "title": "Modifier dans une appli Nik",
     "description": "Comme Photo ▸ Modifier dans ▸ Nik de Lightroom : ouvre les photos dans l'appli Nik ; la copie est "
                    "empilée sur l'original et rechargée dans LightCraft quand Nik l'enregistre. L'utilisateur retouche "
                    "et enregistre lui-même dans Nik.",
     "inputSchema": {"type": "object", "properties": {"app": APP, "mode": MODE, "ids": IDS}, "required": ["app"],
                     "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
     "run": lambda a: core.edit(a["app"], a.get("mode", "adjusted"), a.get("ids"))},
    {"name": "nik_hdr", "title": "Fusion HDR Efex",
     "description": "Comme Exporter vers Nik HDR Efex : envoie les photos (bracketing) à HDR Efex, attend la fin et "
                    "ajoute le résultat empilé avec elles. Bloque jusqu'à la fermeture de HDR Efex.",
     "inputSchema": {"type": "object", "properties": {"ids": IDS, "mode": {"type": "string", "enum": ["adjusted", "original"],
                     "description": "adjusted = rendus avec les réglages LightCraft (défaut) ; original = fichiers d'origine"}},
                     "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
     "run": lambda a: core.hdr(a.get("ids"), a.get("mode", "adjusted"))},
    {"name": "nik_copy_params", "title": "Copier les paramètres Nik",
     "description": "Lit les réglages Nik enregistrés dans un TIFF retouché par Nik (photo active ou `id`) et les garde "
                    "pour nik_apply_params, comme Copier et appliquer les paramètres de Lightroom.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}}, "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
     "run": lambda a: core.copy_params(a.get("id"))},
    {"name": "nik_apply_params", "title": "Appliquer les paramètres Nik",
     "description": "Applique les paramètres copiés (les derniers, ou ceux de `plugin`) aux photos, sans interface sauf "
                    "show_ui ; chaque résultat <nom><suffixe>.tif est empilé sur sa photo.",
     "inputSchema": {"type": "object", "properties": {"ids": IDS, "plugin": APP, "mode": MODE,
                     "show_ui": {"type": "boolean", "description": "Ouvrir Nik pour ajuster chaque photo"}},
                     "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
     "run": lambda a: core.apply_params(a.get("ids"), a.get("plugin"), bool(a.get("show_ui")), a.get("mode", "adjusted"))},
    {"name": "nik_reedit", "title": "Reprendre une retouche Nik",
     "description": "Rouvre un TIFF déjà retouché dans l'appli Nik qui l'a produit, avec ses réglages (non destructif).",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}}, "additionalProperties": False},
     "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
     "run": lambda a: core.reedit(a.get("id"))},
]
BY_NAME = {t["name"]: t for t in TOOLS}
INSTRUCTIONS = (
    "Nik Collection (Silver Efex, Color Efex, Analog Efex, Viveza, HDR Efex, Dfine, Sharpener) branchée sur l'application "
    "LightCraft ouverte, comme dans Lightroom. LightCraft doit tourner avec son canal de contrôle (port 7980). Les "
    "retouches dans Nik sont faites par l'utilisateur ; ces outils ouvrent, fusionnent, copient/appliquent et réimportent."
)


def reply(msg_id, result=None, error=None):
    out = {"jsonrpc": "2.0", "id": msg_id}
    if error:
        out["error"] = error
    else:
        out["result"] = result
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def call(params):
    tool = BY_NAME.get(params.get("name"))
    if not tool:
        return None
    args = params.get("arguments") or {}
    allowed = set(tool["inputSchema"]["properties"])
    unknown = set(args) - allowed
    if unknown:
        return {"content": [{"type": "text", "text": "argument inconnu : %s (acceptés : %s)" % (", ".join(sorted(unknown)), ", ".join(sorted(allowed)) or "aucun")}],
                "isError": True}
    try:
        result = tool["run"](args)
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=1)}],
                "structuredContent": result if isinstance(result, dict) else {"result": result}, "isError": False}
    except core.NikError as e:
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}
    except Exception as e:
        core.log("erreur MCP : %s" % traceback.format_exc())
        return {"content": [{"type": "text", "text": "erreur interne : %r" % e}], "isError": True}


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    for line in sys.stdin:
        line = line.strip().lstrip("﻿")
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            reply(None, error={"code": -32700, "message": "parse error"})
            continue
        method, msg_id = msg.get("method"), msg.get("id")
        if msg_id is None:
            continue  # notifications (initialized, cancelled)
        if method == "initialize":
            asked = (msg.get("params") or {}).get("protocolVersion")
            reply(msg_id, {"protocolVersion": asked if asked in (PROTOCOL, "2025-03-26", "2024-11-05") else PROTOCOL,
                           "capabilities": {"tools": {"listChanged": False}},
                           "serverInfo": {"name": "lightcraft-nik", "version": "1.0.0"},
                           "instructions": INSTRUCTIONS})
        elif method == "ping":
            reply(msg_id, {})
        elif method == "tools/list":
            reply(msg_id, {"tools": [{k: v for k, v in t.items() if k != "run"} for t in TOOLS]})
        elif method == "tools/call":
            r = call(msg.get("params") or {})
            if r is None:
                reply(msg_id, error={"code": -32602, "message": "outil inconnu"})
            else:
                reply(msg_id, r)
        else:
            reply(msg_id, error={"code": -32601, "message": "méthode inconnue : %s" % method})


if __name__ == "__main__":
    main()
