# Nik Collection pour LightCraft

**Retrouvez dans LightCraft l'intégration de la Nik Collection de DxO que vous aviez dans Lightroom** : Silver Efex,
Color Efex, Analog Efex, Viveza, HDR Efex, Dfine et Sharpener, ouverts depuis vos photos, et les retouches qui
reviennent toutes seules dans votre bibliothèque, empilées avec l'original.

> **Projet indépendant.** Il n'est ni affilié ni approuvé par DxO Labs (éditeur de la Nik Collection) ni par
> ArtCraft / storytold (éditeurs de LightCraft). « Nik Collection », « Silver Efex », etc. sont des marques de DxO.
> Ce projet ne contient aucun code de DxO et ne modifie ni la Nik Collection ni LightCraft : il les fait communiquer.
> Il vous faut une **Nik Collection officielle** (version d'essai ou licence achetée sur [dxo.com](https://www.dxo.com/fr/nik-collection/)).

> **Statut : expérimental (version 1.0.0).** Tout le côté LightCraft est testé automatiquement. Les commandes
> envoyées aux applis Nik reproduisent celles du module Lightroom de DxO, mais certaines n'ont pas encore été validées
> sur les vraies applis : voir [Ce qui est vérifié, ce qui ne l'est pas encore](#ce-qui-est-vérifié-ce-qui-ne-lest-pas-encore).
> Faites vos premiers essais sur des copies de photos.

---

## Sommaire

**Pour tout le monde**
1. [De quoi s'agit-il ?](#1-de-quoi-sagit-il-)
2. [Ce que vous pourrez faire](#2-ce-que-vous-pourrez-faire)
3. [Ce qu'il vous faut](#3-ce-quil-vous-faut)
4. [Installation pas à pas](#4-installation-pas-à-pas)
5. [Utilisation](#5-utilisation)
6. [Où sont mes fichiers ?](#6-où-sont-mes-fichiers-)
7. [Questions fréquentes et dépannage](#7-questions-fréquentes-et-dépannage)
8. [Désinstaller](#8-désinstaller)
9. [Sécurité et vie privée](#9-sécurité-et-vie-privée)

**Pour les développeurs**

10. [Architecture](#10-architecture)
11. [Le protocole LightCraft utilisé](#11-le-protocole-lightcraft-utilisé)
12. [Le protocole des applis Nik](#12-le-protocole-des-applis-nik)
13. [Déroulé détaillé de chaque fonction](#13-déroulé-détaillé-de-chaque-fonction)
14. [Le serveur MCP](#14-le-serveur-mcp)
15. [Fichiers, réglages et journal](#15-fichiers-réglages-et-journal)
16. [Tests](#16-tests)
17. [Ce qui est vérifié, ce qui ne l'est pas encore](#ce-qui-est-vérifié-ce-qui-ne-lest-pas-encore)
18. [Limites connues et pistes](#18-limites-connues-et-pistes)
19. [Contribuer](#19-contribuer)
20. [Licence](#20-licence)

---

# Partie 1 — Pour tout le monde

## 1. De quoi s'agit-il ?

- **LightCraft** est un logiciel **libre et gratuit** de gestion et de développement de photos, sur le modèle
  d'Adobe Lightroom. Il est publié par ArtCraft sur [GitHub](https://github.com/storytold/lightcraft).
- La **Nik Collection** de DxO est une suite de filtres photo réputés : Silver Efex pour le noir et blanc, Color Efex
  pour les effets couleur, HDR Efex pour la fusion d'expositions, etc.
- Dans **Lightroom**, la Nik Collection s'installe comme un module : clic droit sur une photo ▸ *Modifier dans* ▸
  *Silver Efex*, vous retouchez, vous enregistrez, et la photo retouchée apparaît dans Lightroom à côté de l'originale.
- **LightCraft ne sait pas faire ça tout seul** : il n'a pas (encore) de système de modules comme Lightroom.

**Ce projet fait le pont.** Il s'installe à côté de LightCraft, sans le modifier, et lui apprend à travailler avec
la Nik Collection comme Lightroom le faisait. Comme il ne touche pas à LightCraft, il continue de marcher quand
LightCraft se met à jour.

## 2. Ce que vous pourrez faire

| Dans Lightroom | Avec Nik Collection pour LightCraft |
|---|---|
| Photo ▸ Modifier dans ▸ Silver Efex (ou une autre appli Nik) | **Photo ▸ Edit In ▸ Edit in Other Editor** (raccourci **Ctrl+Alt+E**), puis le choix de l'appli Nik dans une petite fenêtre |
| « Modifier une copie avec les ajustements Lightroom » | Mode **copie avec les réglages LightCraft** (le plus courant) |
| « Modifier une copie » | Mode **copie de l'original** |
| « Modifier l'original » | Mode **original** |
| La photo retouchée apparaît, empilée avec l'originale | Pareil : elle est empilée au-dessus de l'originale et se met à jour quand vous enregistrez dans Nik |
| Exporter vers Nik HDR Efex | **Fusion HDR Efex** depuis la palette, avec plusieurs photos sélectionnées |
| Copier et appliquer les paramètres | **Copier les paramètres** d'une photo déjà retouchée dans Nik, puis les **appliquer** à toute une sélection, en une fois |
| Rouvrir une retouche Nik pour la modifier | **Reprendre la retouche Nik** : la photo se rouvre dans la bonne appli, avec ses réglages |

En bonus, si vous utilisez **Claude Code**, l'assistant peut piloter tout cela pour vous, par exemple : *« passe les
photos sélectionnées dans Silver Efex avec les paramètres que j'ai copiés »*. Voir [le serveur MCP](#14-le-serveur-mcp).

## 3. Ce qu'il vous faut

| Quoi | Où le trouver | Remarque |
|---|---|---|
| **Windows 10 ou 11, 64 bits** | — | macOS et Linux ne sont pas pris en charge pour l'instant. |
| **LightCraft** (version 0.8 ou plus récente) | [github.com/storytold/lightcraft/releases](https://github.com/storytold/lightcraft/releases), fichier `…-windows-x64.msi` | Installé à l'emplacement proposé (`C:\Program Files\LightCraft`). |
| **Nik Collection de DxO** (conçu pour la version 9 ; 6 à 8 probablement compatibles, non testées) | [dxo.com](https://www.dxo.com/fr/nik-collection/) | Essai gratuit de 30 jours ou licence. Installée à l'emplacement proposé. |
| **Python 3.10 ou plus récent** | [python.org/downloads](https://www.python.org/downloads/) | Gratuit. Voir l'encadré ci-dessous. |

> **Installer Python correctement** : lancez l'installateur de python.org et, sur le premier écran, **cochez
> « Add python.exe to PATH »** avant de cliquer sur *Install Now*. L'option « tcl/tk and IDLE » (cochée par défaut)
> doit rester cochée : c'est elle qui permet d'afficher les fenêtres.

## 4. Installation pas à pas

1. **Téléchargez ce projet** : en haut de cette page, bouton vert **Code** ▸ **Download ZIP**.
2. **Décompressez-le dans un dossier qui ne bougera plus**, par exemple `C:\Outils\lightcraft-nik`.
   Évitez le dossier *Téléchargements* (on le vide un jour ou l'autre) et les dossiers synchronisés par OneDrive.
3. **Ouvrez PowerShell dans ce dossier** : dans l'explorateur, ouvrez le dossier, cliquez dans la barre d'adresse,
   tapez `powershell` puis Entrée.
4. **Lancez l'installation** en copiant cette ligne puis Entrée :
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```
   Le script vérifie que Python, LightCraft et la Nik Collection sont là, puis :
   - fabrique le petit programme `NikPourLightCraft.exe` (à partir de son code source, fourni) ;
   - demande à LightCraft d'ouvrir son **canal de contrôle** à chaque démarrage (c'est par là que les deux logiciels
     se parlent) ;
   - ajoute **« Nik Collection pour LightCraft »** dans le menu Démarrer ;
   - si Claude Code est installé, lui ajoute le serveur MCP.
5. **Fermez LightCraft s'il était ouvert, puis rouvrez-le.** C'est indispensable la première fois.
6. **Vérifiez** : ouvrez *Nik Collection pour LightCraft* depuis le menu Démarrer. En haut de la fenêtre, vous devez
   lire « LightCraft connecté — N photo(s) sélectionnée(s) ». Au même moment, le projet règle LightCraft pour qu'il
   lui confie les photos : *Settings ▸ External Editing ▸ Other editor* pointe désormais vers
   `NikPourLightCraft.exe`, en **TIFF 16 bits ProPhoto** (comme Lightroom avec Nik).

> Si vous aviez déjà choisi un autre éditeur dans *Other editor*, le projet **ne le remplace pas**. Videz ce champ dans
> LightCraft pour qu'il se règle, ou tapez-y vous-même le chemin de `NikPourLightCraft.exe`.

## 5. Utilisation

### 5.1 Modifier une photo dans une appli Nik (le cas le plus courant)

1. Dans LightCraft, sélectionnez une ou plusieurs photos.
2. Menu **Photo ▸ Edit In ▸ Edit in Other Editor**, ou **Ctrl+Alt+E**, ou clic droit ▸ *Edit In*.
3. LightCraft prépare une copie de chaque photo **avec tous vos réglages** (exposition, recadrage, masques…), en TIFF
   16 bits, et la range **au-dessus de l'originale, dans une pile**.
4. Une petite fenêtre demande **quelle appli Nik** utiliser. Cliquez par exemple sur *Silver Efex*. La dernière appli
   choisie est présélectionnée : la touche Entrée suffit la fois suivante.
5. Retouchez dans Nik, puis cliquez sur **Enregistrer** dans Nik.
6. Revenez dans LightCraft : la copie se met à jour toute seule.

### 5.2 Les trois façons de modifier, et laquelle choisir

Ces trois choix sont dans la **palette** (menu Démarrer ▸ *Nik Collection pour LightCraft*), cadre *Modifier dans* :

| Mode | Ce qui part dans Nik | Quand le choisir |
|---|---|---|
| **Copie avec les réglages LightCraft** | Une copie TIFF 16 bits de la photo telle que vous la voyez dans LightCraft | Presque toujours : vous avez développé la photo dans LightCraft et vous voulez y ajouter un effet Nik. |
| **Copie de l'original** | Une copie du fichier d'origine, **sans** vos réglages LightCraft | Vous voulez que Nik parte de la photo brute, sans toucher à l'originale. |
| **Original** | Le fichier d'origine lui-même | Vous savez ce que vous faites : Nik va **écraser** le fichier. Possible seulement pour les TIFF et JPEG. |

> **Et les fichiers RAW (NEF, CR3, ARW, DNG…) ?** Nik ne sait pas les ouvrir. Comme Lightroom, le projet en fait
> toujours une copie TIFF avec vos réglages, quel que soit le mode choisi.

### 5.3 La palette

Lancez-la depuis le menu Démarrer. Elle agit sur **les photos sélectionnées dans LightCraft**. Elle peut rester au
premier plan (case *Toujours au premier plan*), comme la palette Nik dans Photoshop.

- **Modifier** : ouvre la sélection dans l'appli et le mode choisis.
- **Fusion HDR Efex…** : sélectionnez vos photos en bracketing (par exemple −2, 0, +2 IL), cliquez, réglez la fusion
  dans HDR Efex et enregistrez. L'image HDR est ajoutée à LightCraft, **empilée avec les photos de départ**.
  Si le mode *Original* est coché, HDR Efex reçoit les fichiers d'origine ; sinon, des copies avec vos réglages.
- **Copier les paramètres de la photo active** : sélectionnez une photo **déjà retouchée dans Nik** (un TIFF enregistré
  par Nik). Le projet lit les réglages Nik qu'elle contient et les garde en mémoire.
- **Appliquer les paramètres à la sélection** : applique ces réglages à toutes les photos sélectionnées, d'un coup.
  Chaque résultat est ajouté et empilé sur sa photo. Cochez **Afficher Nik pour ajuster chaque photo** pour pouvoir
  corriger photo par photo.
- **Reprendre la retouche Nik** : sélectionnez un TIFF déjà retouché ; il se rouvre dans l'appli Nik qui l'a produit,
  avec ses réglages, pour que vous puissiez les modifier.

En bas, un message vert confirme chaque opération ; un message rouge explique ce qui n'a pas marché.

## 6. Où sont mes fichiers ?

Rien n'est caché : tout est écrit **dans le dossier de la photo d'origine**, à côté d'elle.

| Opération | Fichier créé | Exemple |
|---|---|---|
| Copie avec les réglages LightCraft (et tout RAW) | `<nom>-Edit.tif` | `mariage-0412-Edit.tif` |
| Copie de l'original | `<nom>-copy.<extension>` | `mariage-0412-copy.jpg` |
| Original | aucun : le fichier d'origine est modifié | — |
| Appliquer les paramètres | `<nom><suffixe>.tif` : `-sep` Silver Efex, `-cep` Color Efex, `-aep` Analog Efex, `-vvz` Viveza, `-df` Dfine, `-sh` Sharpener Output, `-psh` Presharpener, `-hdr` HDR Efex (les suffixes du module Lightroom de DxO) | `mariage-0412-sep.tif` |
| Fusion HDR Efex | le fichier enregistré par HDR Efex, dans le dossier de la première photo | — |

Un nom déjà pris reçoit `-1`, `-2`… : rien n'est jamais écrasé, sauf en mode *Original*.

## 7. Questions fréquentes et dépannage

**La palette affiche « LightCraft non joignable ».**
LightCraft n'est pas ouvert, ou il a été ouvert avant l'installation. Fermez-le complètement et rouvrez-le. Si ça
persiste, fermez votre session Windows et rouvrez-la (la variable `LIGHTCRAFT_CONTROL_PORT` n'est vue que par les
programmes lancés après l'installation).

**Ctrl+Alt+E ouvre autre chose que le choix Nik.**
Un autre éditeur est réglé dans *Settings ▸ External Editing ▸ Other editor*. Videz le champ, puis ouvrez une fois la
palette : elle le règle. Ou tapez-y le chemin complet de `NikPourLightCraft.exe`.

**« Aucune appli de la Nik Collection n'a été trouvée ».**
La Nik Collection doit être installée dans `C:\Program Files\DxO\…` (emplacement par défaut).

**J'ai enregistré dans Nik mais la photo n'a pas changé dans LightCraft.**
Cliquez dans la fenêtre de LightCraft : il relit les fichiers modifiés quand il reprend la main. Sinon, clic droit
sur la photo ▸ *Reload from Disk*. Vérifiez aussi que vous avez bien cliqué sur *Enregistrer* et pas *Enregistrer sous*
dans Nik.

**« Copier les paramètres » répond que la photo ne contient pas de paramètres Nik.**
Seuls les **TIFF enregistrés par une appli Nik** contiennent ses réglages. Un JPEG, ou un TIFF enregistré par un autre
logiciel, n'en a pas.

**LightCraft refuse d'ajouter un fichier (« could not be added »).**
LightCraft refuse les fichiers dont le contenu est identique à une photo déjà présente (doublon). Ça arrive si Nik
enregistre l'image sans l'avoir modifiée.

**Où voir ce qui s'est passé ?**
Dans le journal `%LOCALAPPDATA%\LightCraftNik\lcnik.log` (collez ce chemin dans la barre d'adresse de l'explorateur).
Joignez-le si vous signalez un problème.

## 8. Désinstaller

Dans PowerShell, dans le dossier du projet :

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Cela retire le raccourci, le réglage du canal de contrôle, le serveur MCP, le lanceur compilé et les paramètres
copiés (ajoutez `-KeepData` pour garder ces derniers). **Vos photos, LightCraft et la Nik Collection ne sont pas
touchés.** Pensez à vider *Settings ▸ External Editing ▸ Other editor* dans LightCraft, puis supprimez le dossier du
projet.

## 9. Sécurité et vie privée

- **Rien ne sort de votre ordinateur** : pas de compte, pas de statistiques, aucune connexion à Internet.
- Les deux logiciels se parlent par le **canal de contrôle** de LightCraft, ouvert sur `127.0.0.1` (votre propre PC,
  inaccessible depuis le réseau). Ce canal **n'a pas de mot de passe** : n'importe quel programme lancé sur votre PC
  peut piloter LightCraft tant qu'il est ouvert. C'est une limite de LightCraft, documentée par ses auteurs. Si cela
  vous gêne, désinstallez le projet quand vous ne vous en servez pas.
- Le projet ne lance que les applis Nik installées dans `C:\Program Files\DxO\` et l'outil `lightcraft-cli.exe` de
  LightCraft.

---

# Partie 2 — Pour les développeurs

## 10. Architecture

LightCraft 0.8 n'a pas d'équivalent du SDK Lightroom : c'est la ligne 19 de son
[`docs/gaps.md`](https://github.com/storytold/lightcraft/blob/main/docs/gaps.md) (« Plug-in ecosystem »). En revanche,
**tout** y est une commande, accessible par un canal de contrôle JSON. L'intégration est donc **externe** : elle ne
patche pas LightCraft, ce qui la rend indépendante de ses mises à jour (fréquentes : plusieurs versions par semaine).

```
                         ┌──────────────────────────── LightCraft (non modifié) ────────────────────────────┐
  Photo ▸ Edit In ▸      │ photo.editInExternal : rend <nom>-Edit.tif (TIFF 16 bits ProPhoto), l'empile,   │
  Edit in Other Editor ──┤ lance « Other editor » <fichiers…>, recharge la copie quand la fenêtre reprend   │
                         │ le focus                                                                         │
                         │                     canal de contrôle JSON-lines, 127.0.0.1:7980                 │
                         └──────────────▲──────────────────────────────┬────────────────────────────────────┘
                                        │ library.state, photo.inspect,│ « Other editor » =
                                        │ develop.get, library.import, │ NikPourLightCraft.exe <fichiers>
                                        │ stack.group, photo.reload…   ▼
 ┌─────────────────┐  stdio   ┌─────────┴────────┐   import   ┌───────────────────────┐   ┌──────────────────────┐
 │ Claude Code     ├─────────►│ lcnik_mcp.py     ├───────────►│ lcnik_core.py         │◄──┤ NikPourLightCraft.pyw│
 │ (client MCP)    │ JSON-RPC │ serveur MCP      │            │ moteur                │   │ sélecteur + palette  │
 └─────────────────┘          └──────────────────┘            └──┬──────────┬─────────┘   └──────────▲───────────┘
                                                                 │          │                        │ pythonw -I
                                          lightcraft-cli render  │          │ Nik 9 *.exe,           │
                                          (TIFF 16 bits ProPhoto)│          │ nondestructive_util    │
                                                                 ▼          ▼                 ┌──────┴───────────┐
                                                          fichiers TIFF   applis Nik          │NikPourLightCraft │
                                                                                              │.exe (lanceur C#) │
                                                                                              └──────────────────┘
```

| Fichier | Rôle |
|---|---|
| `lcnik_core.py` | Moteur, **sans dépendance** (bibliothèque standard Python). Détection des applis Nik, client du canal de contrôle, rendus, les cinq fonctions, la surveillance des fichiers (`python lcnik_core.py watch <json>`). `python lcnik_core.py` seul affiche l'état en JSON. |
| `lcnik_mcp.py` | Serveur MCP écrit à la main (JSON-RPC 2.0 sur stdio, révision `2025-06-18`). |
| `NikPourLightCraft.pyw` | Interface tkinter : le **sélecteur** (appelé avec des fichiers) et la **palette** (sans argument). |
| `launcher/NikPourLightCraft.cs` | Lanceur Windows en C# 5. LightCraft n'accepte qu'**un programme** comme « Other editor » (`Command::new(path).arg(file)`, voir `apps/lightcraft/src/editors.rs`) ; celui-ci démarre `pythonw -I NikPourLightCraft.pyw <fichiers>`. Le chemin de `pythonw.exe` est lu dans `launcher.cfg`. Compilé par `csc.exe` de .NET Framework 4, présent sur tout Windows : pas de SDK à installer. |
| `install.ps1` / `uninstall.ps1` | Installation et retrait. |
| `tests/` | Tests de bout en bout (faux Nik + LightCraft isolé). |

Choix de conception :

- **Python sans dépendance** : rien à `pip install`, le même moteur sert à l'interface et au serveur MCP.
- **Rendus par `lightcraft-cli render`**, pas par `app.export` sur le canal : le canal répond sur le fil de l'interface
  avec un délai de 60 s, trop court pour plusieurs TIFF pleine taille. `render` reçoit le JSON complet de
  `develop.get` par `--settings`, que LightCraft applique par `develop.merge`.
- **La surveillance tourne dans un processus détaché** (`pythonw … watch`), pour survivre à la fermeture de la palette
  ou du serveur MCP.

## 11. Le protocole LightCraft utilisé

Le canal ([`docs/control-protocol.md`](https://github.com/storytold/lightcraft/blob/main/docs/control-protocol.md))
s'ouvre avec `lightcraft --control PORT` ou la variable `LIGHTCRAFT_CONTROL_PORT`, que `install.ps1` définit (7980,
au niveau de l'utilisateur). Une requête par ligne, `{"id", "method", "params"}` ; une réponse par ligne,
`{"id", "ok", "result" | "error"}`. Une ligne invalide fait fermer la connexion. Les commandes passent par
`engine.execute {command, params}`.

| Commande | Utilisée pour | Détail |
|---|---|---|
| `library.state` | sélection et photo active | → `selection: {ids, active}` |
| `photo.inspect {id}` | chemin du fichier | → `source: {type: "file", path}` (`type: "demo"` pour les photos de démonstration, sans fichier) ; `stack: {photos, …}` |
| `develop.get {id}` | réglages pour le rendu | JSON complet, transmis à `lightcraft-cli render --settings` |
| `photo.editInExternal {ids, app, format, colorSpace, bitDepth}` | mode « copie avec les réglages » | Commande d'**interface** (`crates/ui-egui/src/menus.rs`, `edit_in`) : appelle `photo.editExternal`, lance `app` avec chaque copie, mémorise les copies dans `external_edits` et les recharge au retour du focus. `app` remplace l'éditeur des réglages pour cet appel. |
| `photo.duplicate {ids}` | mode « copie de l'original » | Copie octet pour octet `<nom>-copy.<ext>`, ajoutée avec réglages et métadonnées. Une copie faite à la main serait refusée par `library.import` comme **doublon de contenu**. |
| `develop.reset {ids}` | idem | La copie repart sans réglages, comme dans Lightroom |
| `library.import {paths, mode: "add"}` | ajout des résultats (HDR, Copier/Appliquer, RAW) | → `imported: [id]` ; `duplicates` si le contenu existe déjà |
| `stack.group {ids, top, collapsed}` | empilement | Résultat en haut, pile dépliée, comme `photo.editExternal` |
| `photo.reload {ids}` | après un enregistrement dans Nik | Relit les fichiers modifiés sur le disque |
| `ui.set {settings: {externalEditor, externalFile}}` | réglage de l'« Other editor » | `ui.set` fusionne un état partiel (`deep_merge`) ; `ui.set {}` renvoie l'état, dont `settings`. Champs de `AppSettings` en camelCase (`crates/ui-egui/src/state.rs`). |

## 12. Le protocole des applis Nik

DxO ne documente pas ces commandes. Elles ont été **déduites des chaînes lisibles** du module Lightroom livré avec
la Nik Collection 9 (`bin\lrplugins\Nik9PluginParam.lrplugin` et `Nik9HDR.lrplugin`, en bytecode Lua 5.1) et de l'aide
de `nondestructive_util.exe`. Ce module **n'est ni copié ni redistribué** ici.

| Usage | Commande | Source | Confiance |
|---|---|---|---|
| Ouvrir un fichier | `"Nik 9 <Appli>.exe" <fichier>` | Mécanisme « Modifier dans » de Lightroom | élevée |
| HDR | `"Nik 9 HDR Efex.exe" --host-lightroom <config.xml>` | `HDRRunApp.lua` : constante `" --host-lightroom "`, espaces des deux côtés | moyenne |
| Lire les paramètres d'un TIFF | `nondestructive_util.exe <tiff d'entrée> <fichier de sortie>` | `--help` de l'outil | élevée (syntaxe), moyenne (format de sortie) |
| Appliquer des paramètres | `"<Appli>.exe" --paste --input <in> --params <p> --output <out> [--showUI]` | `PluginParamNew.lua` : constantes dans cet ordre | moyenne |

Fichier de configuration HDR (structure lue dans `HDRRunApp.lua`) :

```xml
<configuration>
 <group name="general">
  <key name="input-images" type="string_array">
   <string value="C:\…\img1.tif"/>
   <string value="C:\…\img2.tif"/>
  </key>
  <key name="output-path" type="string" value="C:\dossier\de\la\première\photo"/>
  <key name="run-results-file" type="string" value="C:\…\results.txt"/>
 </group>
</configuration>
```

Le fichier de résultats contient des lignes `clé=valeur` (motif `(%w+)=(.*)` dans le module). Les clés `reimport`,
`stack`, `filename` et `result` y sont lues.

Identification de l'appli dans un fichier de paramètres (`plugin_from_params`) : clés `PluginName` / `pluginName` /
`Info.Engine`, ou balise de l'ancien format `<SilverEfexPro2_filter>`. Les suffixes de sortie (`-sep`, `-cep`, `-aep`,
`-vvz`, `-hdr`, `-df`, `-sh`, `-psh`) sont ceux de `PluginParamInit.lua`.

## 13. Déroulé détaillé de chaque fonction

**`edit(app, mode, ids)`**
- `adjusted` : `photo.editInExternal {ids, app: <exe Nik>, format: "tiff", colorSpace: "proPhoto", bitDepth: 16}`.
  LightCraft rend `<nom>-Edit.tif`, empile la copie et lance l'appli. Une surveillance est lancée en plus de son
  rechargement au retour du focus.
- `copy` : `photo.duplicate`, `develop.reset`, `stack.group`, lancement de Nik sur `<nom>-copy.<ext>`, surveillance.
- `original` : lancement de Nik sur le fichier d'origine, surveillance.
- Un RAW, ou un format que Nik n'ouvre pas, passe toujours par `render_tiff` → `<nom>-Edit.tif`, importé et empilé.

**`hdr(ids, mode)`** — rendu de chaque photo en TIFF dans un dossier temporaire (ou fichiers d'origine en mode
`original`), écriture du XML, `HDR Efex --host-lightroom <xml>`, attente de la fin du processus. Si l'appli a passé
la main à une instance déjà ouverte, le fichier de résultats est attendu jusqu'à 3 h. Lecture des résultats ; à
défaut de `filename`, le TIFF ou JPEG le plus récent apparu dans le dossier de sortie. Import, puis empilement avec
les sources (sauf `reimport=false` / `stack=false`).

**`copy_params(id)`** — `nondestructive_util.exe <tiff> <tmp>`, identification de l'appli, copie dans
`%LOCALAPPDATA%\LightCraftNik\params\<appli>.params`, avec `<appli>.json` (source, date). Un seul jeu par appli,
comme le module Lightroom.

**`apply_params(ids, plugin, show_ui, mode)`** — pour chaque photo, entrée : rendu TIFF (`adjusted`), copie
(`copy`) ou original ; sortie `<nom><suffixe>.tif` (nom libre suivant). `--paste --input --params --output
[--showUI]`, attente, import et empilement. Les erreurs sont collectées photo par photo sans arrêter le lot.

**`reedit(id)`** — identification de l'appli par `nondestructive_util`, lancement sur le fichier, surveillance.

**Surveillance (`watch`)** — interrogation toutes les 2 s de la date de modification des fichiers. À chaque
changement : 1 s de délai (fin d'écriture), puis `photo.reload`. Arrêt quand l'image de l'exécutable Nik n'apparaît
plus dans `tasklist` trois fois de suite (au moins 10 s après le départ), ou au bout de 3 h.

## 14. Le serveur MCP

Inscription (faite par `install.ps1` si Claude Code est présent) :

```powershell
claude mcp add -s user lightcraft-nik -- python -I C:\chemin\vers\lightcraft-nik\lcnik_mcp.py
```

Pour un autre client MCP (Claude Desktop, Cursor…) :

```json
{ "mcpServers": { "lightcraft-nik": { "command": "python", "args": ["-I", "C:\\chemin\\vers\\lightcraft-nik\\lcnik_mcp.py"] } } }
```

| Outil | Arguments | Effet |
|---|---|---|
| `nik_status` | — | Applis Nik trouvées, connexion à LightCraft et sélection, paramètres copiés ; règle l'« Other editor » s'il est vide |
| `nik_edit` | `app`, `mode?`, `ids?` | Modifier dans (§ 13) |
| `nik_hdr` | `ids?`, `mode?` | Fusion HDR ; **bloque** jusqu'à la fermeture de HDR Efex |
| `nik_copy_params` | `id?` | Copier les paramètres |
| `nik_apply_params` | `ids?`, `plugin?`, `mode?`, `show_ui?` | Appliquer en lot |
| `nik_reedit` | `id?` | Reprendre une retouche |

Sans `ids`, les outils prennent la sélection de LightCraft. Les erreurs attendues (LightCraft fermé, rien de
sélectionné, appli absente) reviennent en résultat `isError: true`, lisible par le modèle. Un argument inconnu est
refusé avec la liste des arguments acceptés. Le serveur tolère un BOM UTF-8 en entrée (PowerShell en ajoute un dans
les tubes).

Le serveur MCP de LightCraft lui-même (`lightcraft-cli mcp --connect 127.0.0.1:7980`) est complémentaire : il donne
accès à toutes les commandes de LightCraft (développement, export…).

## 15. Fichiers, réglages et journal

| Emplacement | Contenu |
|---|---|
| `%LOCALAPPDATA%\LightCraftNik\config.json` | `last_app`, `last_mode`, `topmost`, `port` (optionnel, remplace 7980) |
| `%LOCALAPPDATA%\LightCraftNik\params\` | Paramètres copiés : `<appli>.params` + `<appli>.json` |
| `%LOCALAPPDATA%\LightCraftNik\lcnik.log` | Journal (lancements, rechargements, erreurs) |
| `launcher.cfg` (dossier du projet) | Chemin de `pythonw.exe`, écrit par `install.ps1` |
| Variable `LIGHTCRAFT_CONTROL_PORT` (utilisateur) | Port du canal de contrôle (lue par LightCraft et par le moteur) |

Ordre de priorité du port : argument `port` des fonctions > `LIGHTCRAFT_CONTROL_PORT` > `config.json` > 7980.

## 16. Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -NoMcp      # le test du menu a besoin du lanceur compilé
powershell -ExecutionPolicy Bypass -File .\tests\run-tests.ps1 [-Keep]
```

`run-tests.ps1` :
1. compile `tests/FakeNik.cs`, un **faux Nik** qui journalise ses arguments et imite les effets des vraies applis :
   il touche le fichier reçu, copie `--input` vers `--output`, et pour HDR lit le XML, écrit un TIFF et le fichier
   de résultats ;
2. génère trois JPEG de test (dégradés, `System.Drawing`) ;
3. démarre un **LightCraft isolé** : `LIGHTCRAFT_CONFIG_DIR` et `--library` dans un dossier temporaire, port 7981. Votre
   bibliothèque et vos réglages ne sont pas touchés ;
4. lance `test_e2e.py` (19 vérifications : réglage de l'éditeur, les trois modes, empilements, copie sans réglages,
   HDR, détection d'appli, Copier/Appliquer, arguments reçus par le faux Nik, rechargements) et `test_menu.py` (le vrai
   chemin du menu : `photo.editInExternal` sans `app` → `NikPourLightCraft.exe` → sélecteur) ;
5. arrête LightCraft et efface le dossier (sauf `-Keep`). Code de sortie non nul en cas d'échec.

La fenêtre du LightCraft de test doit rester visible pendant les tests : LightCraft ne traite les requêtes qu'entre
deux images, et une fenêtre qui ne se redessine plus pendant 5 s fait refuser les requêtes.

## Ce qui est vérifié, ce qui ne l'est pas encore

| | État |
|---|---|
| Dialogue avec LightCraft, rendus, imports, piles, rechargements, réglage de l'éditeur, menu *Edit In* → sélecteur | ✅ testé automatiquement (LightCraft 0.8.0, Windows 11) |
| Arguments envoyés aux applis Nik | ✅ testés contre le faux Nik (forme des commandes) |
| Ouverture d'une photo dans une vraie appli Nik, enregistrement en place, rechargement | ⏳ à valider |
| HDR Efex : `output-path` attend-il un dossier ou un fichier ? quelles clés exactes dans le fichier de résultats ? | ⏳ à valider (repli : nouveau fichier dans le dossier) |
| Copier/Appliquer : `--params` accepte-t-il tel quel le fichier de `nondestructive_util` ? Le module de DxO semble le retravailler (décodage base64, ajout de `<ImageSize>`) pour certains formats | ⏳ à valider : point le plus incertain |
| Nik Collection 6 à 8 | ⏳ non testé (noms d'exécutables détectés par motif `Nik * <Appli>.exe`) |

Vos retours sur ces points sont les bienvenus : ouvrez une *issue* avec le journal `lcnik.log`.

## 18. Limites connues et pistes

- **Un seul « Other editor »** dans LightCraft : le sélecteur sert d'intermédiaire. Un vrai sous-menu *Edit In ▸ Silver
  Efex…* demanderait une évolution de LightCraft : une liste d'éditeurs dans `AppSettings`, à proposer en amont.
- **Windows seulement** : chemins DxO, `tasklist`, lanceur C#. macOS (`open -a`) et Linux sont envisageables.
- **Le canal de contrôle n'a pas d'authentification** (choix de LightCraft) ; le projet ne l'ouvre qu'en local.
- **HDR et Copier/Appliquer** dépendent de commandes Nik non documentées (§ 12).
- Pistes : préréglages d'export par appli Nik, traitement en lot avec file d'attente, interface traduite si LightCraft
  passe en français.

## 19. Contribuer

Les *issues* et *pull requests* sont bienvenues. Merci de :
- garder le moteur **sans dépendance externe** ;
- faire passer `tests\run-tests.ps1` ;
- **ne jamais ajouter de code, de fichier ou de binaire de DxO** au dépôt : documentez le comportement observé, pas le
  code d'autrui.

## 20. Licence

[MIT](LICENSE). LightCraft, la Nik Collection et leurs marques appartiennent à leurs propriétaires respectifs.
