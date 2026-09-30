#!/usr/bin/env python3
"""
CS:GO GC Inventory Editor v15
"""

import tkinter as tk
from tkinter import ttk
import os
import re
import subprocess
import tempfile
import time

# ─────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────

GLOVES = {
    # def_index and finish paint_kit IDs verified against:
    # Steam Guide "All gloves Weapon index Codes Vault" (id=3057480218)
    # + CSGO-skin-ID-dumper/item_index.txt (adamb70/CSGO-skin-ID-dumper)
    "Bloodhound Gloves":    {"def_index": "5027", "finishes": {
        "Charred":          "10006",
        "Snakebite":        "10007",
        "Bronzed":          "10008",
        "Guerrilla":        "10039",
    }},
    "Broken Fang Gloves":   {"def_index": "4725", "finishes": {
        "Jade":             "10085",
        "Yellow-Banded":    "10086",
        "Needle Point":     "10087",
        "Unhinged":         "10088",
    }},
    "Driver Gloves":        {"def_index": "5031", "finishes": {
        "Lunar Weave":      "10013",
        "Convoy":           "10015",
        "Crimson Weave":    "10016",
        "Diamondback":      "10040",
        "King Snake":       "10041",
        "Imperial Plaid":   "10042",
        "Overtake":         "10043",
        "Racing Green":     "10044",
        "Rezan the Red":    "10069",
        "Snow Leopard":     "10070",
        "Queen Jaguar":     "10071",
        "Black Tie":        "10072",
    }},
    "Hand Wraps":           {"def_index": "5032", "finishes": {
        "Leather":          "10009",
        "Spruce DDPAT":     "10010",
        "Badlands":         "10036",
        "Cobalt Skulls":    "10053",
        "Overprint":        "10054",
        "Duct Tape":        "10055",
        "Arboreal":         "10056",
        "Desert Shamagh":   "10081",
        "Giraffe":          "10082",
        "Constrictor":      "10083",
        "CAUTION!":         "10084",
    }},
    "Hydra Gloves":         {"def_index": "5035", "finishes": {
        "Emerald":          "10057",
        "Mangrove":         "10058",
        "Rattler":          "10059",
        "Case Hardened":    "10060",
    }},
    "Moto Gloves":          {"def_index": "5033", "finishes": {
        "Eclipse":          "10024",
        "Spearmint":        "10026",
        "Boom!":            "10027",
        "Cool Mint":        "10028",
        "Turtle":           "10050",
        "Transport":        "10051",
        "Polygon":          "10052",
        "Finish Line":      "10077",
        "Smoke Out":        "10078",
        "Blood Pressure":   "10079",
        "3rd Commando Co.": "10080",
        "POW!":             "10049",
    }},
    "Specialist Gloves":    {"def_index": "5034", "finishes": {
        "Forest DDPAT":     "10030",
        "Crimson Kimono":   "10033",
        "Emerald Web":      "10034",
        "Foundation":       "10035",
        "Crimson Web":      "10061",
        "Buckshot":         "10062",
        "Fade":             "10063",
        "Mogul":            "10064",
        "Marble Fade":      "10065",
        "Lt. Commander":    "10066",
        "Tiger Strike":     "10067",
        "Field Agent":      "10068",
    }},
    "Sport Gloves":         {"def_index": "5030", "finishes": {
        "Superconductor":   "10018",
        "Arid":             "10019",
        "Pandora's Box":    "10037",
        "Hedge Maze":       "10038",
        "Amphibious":       "10045",
        "Bronze Morph":     "10046",
        "Omega":            "10047",
        "Vice":             "10048",
        "Slingshot":        "10073",
        "Big Game":         "10074",
        "Scarlet Shamagh":  "10075",
        "Nocts":            "10076",
    }},
}

KNIVES = {
    "Bayonet":          {"def_index": "500"},
    "Flip Knife":       {"def_index": "505"},
    "Gut Knife":        {"def_index": "506"},
    "Karambit":         {"def_index": "507"},
    "M9 Bayonet":       {"def_index": "508"},
    "Huntsman Knife":   {"def_index": "509"},
    "Bowie Knife":      {"def_index": "514"},
    "Falchion Knife":   {"def_index": "512"},
    "Butterfly Knife":  {"def_index": "515"},
    "Shadow Daggers":   {"def_index": "516"},
    "Navaja Knife":     {"def_index": "523"},
    "Skeleton Knife":   {"def_index": "525"},
}

KNIFE_FINISHES = {
    "Vanilla (no skin)":        None,
    "Forest DDPAT":             ("5",   "0"),
    "Crimson Web":              ("12",  "0"),
    "Fade":                     ("38",  "0"),
    "Night":                    ("40",  "0"),
    "Blue Steel":               ("42",  "0"),
    "Stained":                  ("43",  "0"),
    "Case Hardened":            ("44",  "0"),
    "Slaughter":                ("59",  "0"),
    "Safari Mesh":              ("72",  "0"),
    "Boreal Forest":            ("77",  "0"),
    "Ultraviolet":              ("98",  "0"),
    "Urban Masked":             ("143", "0"),
    "Scorched":                 ("175", "0"),
    "Rust Coat":                ("414", "0"),
    "Tiger Tooth":              ("409", "0"),
    "Damascus Steel":           ("410", "0"),
    "Marble Fade":              ("413", "0"),
    "Doppler (Ruby)":           ("415", "0"),
    "Doppler (Sapphire)":       ("416", "0"),
    "Doppler (Black Pearl)":    ("417", "0"),
    "Doppler (Phase 1)":        ("418", "0"),
    "Doppler (Phase 2)":        ("419", "0"),
    "Doppler (Phase 3)":        ("420", "0"),
    "Doppler (Phase 4)":        ("421", "0"),
    "Gamma Doppler (Emerald)":  ("568", "0"),
    "Gamma Doppler (Phase 1)":  ("569", "0"),
    "Gamma Doppler (Phase 2)":  ("570", "0"),
    "Gamma Doppler (Phase 3)":  ("571", "0"),
    "Gamma Doppler (Phase 4)":  ("572", "0"),
    "Lore": {
        "500": ("558", "0"),
        "505": ("559", "0"),
        "506": ("560", "0"),
        "507": ("561", "0"),
        "508": ("562", "0"),
        "515": ("1105", "0"),
    },
    "Black Laminate": {
        "500": ("563", "0"),
        "505": ("564", "0"),
        "506": ("565", "0"),
        "507": ("566", "0"),
        "508": ("567", "0"),
        "515": ("1110", "0"),
    },
    "Autotronic": {
        "500": ("573", "0"),
        "505": ("574", "0"),
        "506": ("575", "0"),
        "507": ("576", "0"),
        "508": ("577", "0"),
        "515": ("1115", "0"),
    },
    "Bright Water": {
        "500": ("579", "0"),
        "505": ("579", "0"),
        "506": ("579", "0"),
        "507": ("579", "0"),
        "508": ("580", "0"),
    },
    "Freehand": {
        "500": ("581", "0"),
        "505": ("581", "0"),
        "506": ("581", "0"),
        "507": ("582", "0"),
        "508": ("582", "0"),
    },
}

AGENTS = {
    "'Blueberries' Buckshot | NSWC SEAL":               {"def_index": "4619", "team": "CT"},
    "'Two Times' McCoy | TACP Cavalry":                 {"def_index": "4680", "team": "CT"},
    "Cmdr. Mae 'Dead Cold' Jamison | SWAT":             {"def_index": "4711", "team": "CT"},
    "1st Lieutenant Farlow | SWAT":                     {"def_index": "4712", "team": "CT"},
    "John 'Van Healen' Kask | SWAT":                    {"def_index": "4713", "team": "CT"},
    "Bio-Haz Specialist | SWAT":                        {"def_index": "4714", "team": "CT"},
    "Sergeant Bombson | SWAT":                          {"def_index": "4715", "team": "CT"},
    "Chem-Haz Specialist | SWAT":                       {"def_index": "4716", "team": "CT"},
    "Sous-Lieutenant Medic | Gendarmerie Nationale":    {"def_index": "4749", "team": "CT"},
    "Chem-Haz Capitaine | Gendarmerie Nationale":       {"def_index": "4750", "team": "CT"},
    "Chef d'Escadron Rouchard | Gendarmerie Nationale": {"def_index": "4751", "team": "CT"},
    "Aspirant | Gendarmerie Nationale":                 {"def_index": "4752", "team": "CT"},
    "Officer Jacques Beltram | Gendarmerie Nationale":  {"def_index": "4753", "team": "CT"},
    "Lieutenant 'Tree Hugger' Farlow | SWAT":           {"def_index": "4756", "team": "CT"},
    "Cmdr. Davida 'Goggles' Fernandez | SEAL Frogman":  {"def_index": "4757", "team": "CT"},
    "Cmdr. Frank 'Wet Sox' Baroud | SEAL Frogman":      {"def_index": "4771", "team": "CT"},
    "Lieutenant Rex Krikey | SEAL Frogman":             {"def_index": "4772", "team": "CT"},
    "Operator | FBI SWAT":                              {"def_index": "5305", "team": "CT"},
    "Markus Delrow | FBI HRT":                          {"def_index": "5306", "team": "CT"},
    "Michael Syfers | FBI Sniper":                      {"def_index": "5307", "team": "CT"},
    "Special Agent Ava | FBI":                          {"def_index": "5308", "team": "CT"},
    "3rd Commando Company | KSK":                       {"def_index": "5400", "team": "CT"},
    "Seal Team 6 Soldier | NSWC SEAL":                  {"def_index": "5401", "team": "CT"},
    "Buckshot | NSWC SEAL":                             {"def_index": "5402", "team": "CT"},
    "'Two Times' McCoy | USAF TACP":                    {"def_index": "5403", "team": "CT"},
    "Lt. Commander Ricksaw | NSWC SEAL":                {"def_index": "5404", "team": "CT"},
    "Primeiro Tenente | Brazilian 1st Battalion":       {"def_index": "5405", "team": "CT"},
    "B Squadron Officer | SAS":                         {"def_index": "5601", "team": "CT"},
    "D Squadron Officer | NZSAS":                       {"def_index": "5602", "team": "CT"},
    "Rezan the Redshirt | Sabre":                       {"def_index": "4718", "team": "T"},
    "Sir Bloody Miami Darryl | The Professionals":      {"def_index": "4726", "team": "T"},
    "Safecracker Voltzmann | The Professionals":        {"def_index": "4727", "team": "T"},
    "Little Kev | The Professionals":                   {"def_index": "4728", "team": "T"},
    "Getaway Sally | The Professionals":                {"def_index": "4730", "team": "T"},
    "Number K | The Professionals":                     {"def_index": "4732", "team": "T"},
    "Sir Bloody Silent Darryl | The Professionals":     {"def_index": "4733", "team": "T"},
    "Sir Bloody Skullhead Darryl | The Professionals":  {"def_index": "4734", "team": "T"},
    "Sir Bloody Darryl Royale | The Professionals":     {"def_index": "4735", "team": "T"},
    "Sir Bloody Loudmouth Darryl | The Professionals":  {"def_index": "4736", "team": "T"},
    "Elite Trapper Solman | Guerrilla Warfare":         {"def_index": "4773", "team": "T"},
    "Crasswater The Forgotten | Guerrilla Warfare":     {"def_index": "4774", "team": "T"},
    "Arno The Overgrown | Guerrilla Warfare":           {"def_index": "4775", "team": "T"},
    "Col. Mangos Dabisi | Guerrilla Warfare":           {"def_index": "4776", "team": "T"},
    "Vypa Sista of the Revolution | Guerrilla Warfare": {"def_index": "4777", "team": "T"},
    "Trapper Aggressor | Guerrilla Warfare":            {"def_index": "4778", "team": "T"},
    "'Medium Rare' Crasswater | Guerrilla Warfare":     {"def_index": "4780", "team": "T"},
    "Trapper | Guerrilla Warfare":                      {"def_index": "4781", "team": "T"},
    "Ground Rebel | Elite Crew":                        {"def_index": "5105", "team": "T"},
    "Osiris | Elite Crew":                              {"def_index": "5106", "team": "T"},
    "Prof. Shahmat | Elite Crew":                       {"def_index": "5107", "team": "T"},
    "The Elite Mr. Muhlik | Elite Crew":                {"def_index": "5108", "team": "T"},
    "Jungle Rebel | Elite Crew":                        {"def_index": "5109", "team": "T"},
    "Soldier | Phoenix":                                {"def_index": "5205", "team": "T"},
    "Enforcer | Phoenix":                               {"def_index": "5206", "team": "T"},
    "Slingshot | Phoenix":                              {"def_index": "5207", "team": "T"},
    "Street Soldier | Phoenix":                         {"def_index": "5208", "team": "T"},
    "Dragomir | Sabre":                                 {"def_index": "5500", "team": "T"},
    "Maximus | Sabre":                                  {"def_index": "5501", "team": "T"},
    "Rezan The Ready | Sabre":                          {"def_index": "5502", "team": "T"},
    "Blackwolf | Sabre":                                {"def_index": "5503", "team": "T"},
    "'The Doctor' Romanov | Sabre":                     {"def_index": "5504", "team": "T"},
    "Dragomir | Sabre Footsoldier":                     {"def_index": "5505", "team": "T"},
    "Bloody Darryl The Strapped | The Professionals":   {"def_index": "4613", "team": "T"},
}

# ─────────────────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────────────────

BG      = "#0a0a0a"
PANEL   = "#111111"
BORDER  = "#3a3a3a"
TEXT    = "#ffffff"
MUTED   = "#888888"
ACCENT  = "#ffffff"
SEL_BG  = "#252525"
TAB_BG  = "#161616"
TAB_SEL = "#0a0a0a"
GREEN   = "#4caf50"
RED     = "#e53935"
GOLD    = "#ffc107"

FONT    = ("Consolas", 10)
FONT_SM = ("Consolas", 9)
FONT_LG = ("Consolas", 13, "bold")
FONT_H  = ("Consolas", 11, "bold")

# ─────────────────────────────────────────────────────────
# INVENTORY PARSER / WRITER
# ─────────────────────────────────────────────────────────

def find_inventory_txt():
    candidates = [
        os.path.join(os.path.expanduser("~"), "csgo_gc", "inventory.txt"),
        "inventory.txt",
    ]

    try:
        import winreg
        steam_roots = []
        for hive, key_path, value_name in [
            (winreg.HKEY_CURRENT_USER,  r"Software\Valve\Steam",             "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam",             "InstallPath"),
        ]:
            try:
                with winreg.OpenKey(hive, key_path) as k:
                    p, _ = winreg.QueryValueEx(k, value_name)
                    if p:
                        steam_roots.append(p)
            except OSError:
                continue

        for root in steam_roots:
            candidates.append(os.path.join(root, "steamapps", "common",
                                           "csgo legacy", "csgo_gc", "inventory.txt"))
            candidates.append(os.path.join(root, "steamapps", "common",
                                           "Counter-Strike Global Offensive",
                                           "csgo_gc", "inventory.txt"))
            lib_vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
            if os.path.isfile(lib_vdf):
                try:
                    with open(lib_vdf, "r", encoding="utf-8", errors="ignore") as f:
                        txt = f.read()
                    for mp in re.findall(r'"path"\s+"([^"]+)"', txt):
                        mp = mp.replace("\\\\", "\\")
                        candidates.append(os.path.join(mp, "steamapps", "common",
                                                       "csgo legacy", "csgo_gc", "inventory.txt"))
                        candidates.append(os.path.join(mp, "steamapps", "common",
                                                       "Counter-Strike Global Offensive",
                                                       "csgo_gc", "inventory.txt"))
                except Exception:
                    pass
    except ImportError:
        pass

    import string
    steam_subdirs = [
        "SteamLibrary/steamapps/common/csgo legacy/csgo_gc/inventory.txt",
        "SteamLibrary/steamapps/common/Counter-Strike Global Offensive/csgo_gc/inventory.txt",
        "Steam/steamapps/common/csgo legacy/csgo_gc/inventory.txt",
        "Steam/steamapps/common/Counter-Strike Global Offensive/csgo_gc/inventory.txt",
        "Program Files (x86)/Steam/steamapps/common/csgo legacy/csgo_gc/inventory.txt",
        "Program Files (x86)/Steam/steamapps/common/Counter-Strike Global Offensive/csgo_gc/inventory.txt",
        "Program Files/Steam/steamapps/common/csgo legacy/csgo_gc/inventory.txt",
        "Program Files/Steam/steamapps/common/Counter-Strike Global Offensive/csgo_gc/inventory.txt",
    ]
    for drive in string.ascii_uppercase:
        for sub in steam_subdirs:
            candidates.append(os.path.join(f"{drive}:\\", sub.replace("/", os.sep)))

    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        if os.path.isfile(c):
            return c
    return None


def is_csgo_running():
    if os.name != "nt":
        return False
    try:
        flags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            flags = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq csgo.exe", "/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=flags,
        )
        return "csgo.exe" in (result.stdout or "").lower()
    except Exception:
        return False


def safe_write_inventory(path, content, retries=10, delay=0.5):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    last_err = None
    for _ in range(retries):
        tmp_fd = None
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                prefix=".inventory_", suffix=".tmp", dir=directory)
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                tmp_fd = None
                f.write(content)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass

            os.replace(tmp_path, path)
            return True, None

        except PermissionError as e:
            last_err = e
        except Exception as e:
            last_err = e
            if tmp_fd is not None:
                try: os.close(tmp_fd)
                except Exception: pass
            if tmp_path and os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except Exception: pass
            return False, str(e)
        finally:
            if tmp_fd is not None:
                try: os.close(tmp_fd)
                except Exception: pass
            if tmp_path and os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except Exception: pass

        time.sleep(delay)

    return False, str(last_err) if last_err else "unknown error"


def build_glove_entry(slot, inventory_num, def_index, finish_catalog, pattern="0", wear="0.06"):
    return (
        f'"{slot}"\n'
        f'{{\n'
        f'\t"inventory"\t\t"{inventory_num}"\n'
        f'\t"def_index"\t\t"{def_index}"\n'
        f'\t"level"\t\t"1"\n'
        f'\t"quality"\t\t"5"\n'
        f'\t"flags"\t\t"0"\n'
        f'\t"origin"\t\t"8"\n'
        f'\t"in_use"\t\t"0"\n'
        f'\t"rarity"\t\t"1"\n'
        f'\t"attributes"\n'
        f'\t{{\n'
        f'\t\t"6"\t\t"{finish_catalog}.000000"\n'
        f'\t\t"7"\t\t"{pattern}.000000"\n'
        f'\t\t"8"\t\t"{wear}"\n'
        f'\t}}\n'
        f'}}\n'
    )


def build_knife_entry(slot, inventory_num, def_index, finish_catalog=None, pattern="0", wear="0.01"):
    attrs = ""
    if finish_catalog:
        attrs = (
            f'\t"attributes"\n'
            f'\t{{\n'
            f'\t\t"6"\t\t"{finish_catalog}.000000"\n'
            f'\t\t"7"\t\t"{pattern}.000000"\n'
            f'\t\t"8"\t\t"{wear}"\n'
            f'\t}}\n'
        )
    return (
        f'"{slot}"\n'
        f'{{\n'
        f'\t"inventory"\t\t"{inventory_num}"\n'
        f'\t"def_index"\t\t"{def_index}"\n'
        f'\t"level"\t\t"1"\n'
        f'\t"quality"\t\t"3"\n'
        f'\t"flags"\t\t"0"\n'
        f'\t"origin"\t\t"8"\n'
        f'\t"in_use"\t\t"0"\n'
        f'\t"rarity"\t\t"6"\n'
        f'{attrs}'
        f'}}\n'
    )


def build_agent_entry(slot, inventory_num, def_index):
    return (
        f'"{slot}"\n'
        f'{{\n'
        f'\t"inventory"\t\t"{inventory_num}"\n'
        f'\t"def_index"\t\t"{def_index}"\n'
        f'\t"level"\t\t"1"\n'
        f'\t"quality"\t\t"5"\n'
        f'\t"flags"\t\t"0"\n'
        f'\t"origin"\t\t"8"\n'
        f'\t"in_use"\t\t"0"\n'
        f'\t"rarity"\t\t"1"\n'
        f'}}\n'
    )


def _parse_sections(inv_text):
    sections = {}
    i = 0
    n = len(inv_text)
    while i < n:
        m = re.search(r'(?:^|\n)[ \t]*"([^"]+)"[ \t]*\n[ \t]*\{', inv_text[i:])
        if not m:
            break
        name = m.group(1)
        abs_open = i + m.end()
        depth = 1
        j = abs_open
        while j < n and depth > 0:
            if inv_text[j] == '{':
                depth += 1
            elif inv_text[j] == '}':
                depth -= 1
            j += 1
        close_pos = j - 1
        sections[name] = (abs_open, close_pos)
        i = j
    return sections


def remove_item_blocks(section_text, target_indexes):
    if not target_indexes:
        return section_text
    lines = section_text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        if re.match(r'^[ \t]*"[^"]+"[ \t]*$', lines[i]):
            block = [lines[i]]
            i += 1
            depth = 0
            while i < len(lines):
                block.append(lines[i])
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
                if depth == 0:
                    break
            block_text = '\n'.join(block)
            m = re.search(r'"def_index"\s+"([^"]+)"', block_text)
            if m and m.group(1) in target_indexes:
                continue
            out.extend(block)
        else:
            out.append(lines[i])
            i += 1
    return '\n'.join(out)


def parse_equipped_from_inventory(inv_text):
    _glove_by_idx = {}
    for gname, gdata in GLOVES.items():
        di = gdata["def_index"]
        if di not in _glove_by_idx:
            _glove_by_idx[di] = {"_name": gname, "finishes": {}}
        for fname, fcat in gdata["finishes"].items():
            _glove_by_idx[di]["finishes"][fcat] = fname

    _knife_by_idx = {v["def_index"]: k for k, v in KNIVES.items()}

    _finish_cat_to_name = {}
    for fname, finfo in KNIFE_FINISHES.items():
        if finfo is None:
            continue
        if isinstance(finfo, dict):
            for sub in finfo.values():
                _finish_cat_to_name[sub[0]] = fname
        else:
            _finish_cat_to_name[finfo[0]] = fname

    _agent_by_idx = {v["def_index"]: k for k, v in AGENTS.items()}

    sections = _parse_sections(inv_text)
    items_key = next((k for k in sections if k.lower() == "items"), None)
    if items_key is None:
        return []

    body_start, close_pos = sections[items_key]
    section_body = inv_text[body_start:close_pos]

    lines = section_body.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        if re.match(r'^[ \t]*"[^"]+"[ \t]*$', lines[i]):
            block = [lines[i]]
            i += 1
            depth = 0
            while i < len(lines):
                block.append(lines[i])
                depth += lines[i].count("{") - lines[i].count("}")
                i += 1
                if depth == 0:
                    break
            blocks.append("\n".join(block))
        else:
            i += 1

    results = []
    for block in blocks:
        di_m = re.search(r'"def_index"\s+"([^"]+)"', block)
        if not di_m:
            continue
        di = di_m.group(1)

        attr6_m  = re.search(r'(?m)^[ \t]*"6"[ \t]+"([^"]+)"', block)
        attr7_m  = re.search(r'(?m)^[ \t]*"7"[ \t]+"([^"]+)"', block)
        attr8_m  = re.search(r'(?m)^[ \t]*"8"[ \t]+"([^"]+)"', block)
        fin_cat  = attr6_m.group(1).split(".")[0] if attr6_m else None
        pat_val  = attr7_m.group(1).split(".")[0] if attr7_m else "0"
        wear_val = attr8_m.group(1) if attr8_m else "0.01"

        if di in _glove_by_idx:
            gentry  = _glove_by_idx[di]
            gname   = gentry["_name"]
            if fin_cat and fin_cat in gentry["finishes"]:
                fname = gentry["finishes"][fin_cat]
                fcat  = fin_cat
            else:
                fname, fcat = next(iter(
                    (v, k) for k, v in gentry["finishes"].items()
                ))
            results.append({
                "type":       "glove",
                "name":       gname,
                "finish":     fname,
                "wear":       wear_val,
                "pattern":    pat_val,
                "def_index":  di,
                "finish_cat": fcat,
                "from_file":  True,
            })
            continue

        if di in _knife_by_idx:
            kname       = _knife_by_idx[di]
            finish_name = "Vanilla (no skin)"
            if fin_cat and fin_cat in _finish_cat_to_name:
                finish_name = _finish_cat_to_name[fin_cat]
            results.append({
                "type":       "knife",
                "name":       kname,
                "finish":     finish_name,
                "wear":       wear_val if fin_cat else "—",
                "pattern":    pat_val  if fin_cat else "—",
                "def_index":  di,
                "finish_cat": fin_cat,
                "pat_val":    pat_val,
                "wear_val":   wear_val,
                "from_file":  True,
            })
            continue

        if di in _agent_by_idx:
            aname = _agent_by_idx[di]
            team  = AGENTS[aname]["team"]
            results.append({
                "type":      "agent",
                "name":      aname,
                "finish":    f"[{team}]",
                "wear":      "—",
                "pattern":   "—",
                "def_index": di,
                "from_file": True,
            })
            continue

    return results


def inject_items(inv_text, new_entries, indexes_to_replace):
    sections = _parse_sections(inv_text)
    items_key = next((k for k in sections if k.lower() == "items"), None)
    if items_key is None:
        return '"items"\n{\n' + new_entries + '}\n'
    body_start, close_pos = sections[items_key]
    section_body = inv_text[body_start:close_pos]
    cleaned_body = remove_item_blocks(section_body, indexes_to_replace)
    if not cleaned_body.endswith('\n'):
        cleaned_body += '\n'
    new_body = cleaned_body + new_entries
    return inv_text[:body_start] + new_body + inv_text[close_pos:]


# ─────────────────────────────────────────────────────────
# BORDER HELPER
# ─────────────────────────────────────────────────────────

def bordered(parent, **pack_kw):
    outer = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
    outer.pack(**pack_kw)
    inner = tk.Frame(outer, bg=PANEL, bd=0, highlightthickness=0)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return inner


# ─────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────

class CSGOEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("frad-mod")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("920x600")
        self.minsize(820, 520)

        # Set custom window icon (resolve path relative to this script)
        try:
            _ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            self.iconbitmap(default=_ico)
            self.wm_iconbitmap(_ico)
        except Exception:
            pass

        self.tk_setPalette(background=BG, foreground=TEXT,
                           activeBackground=SEL_BG, activeForeground=TEXT,
                           highlightBackground=BG, highlightColor=BG)

        self.inv_path   = tk.StringVar()
        self.status_var = tk.StringVar(value="No file loaded.")

        self.glove_name    = tk.StringVar()
        self.glove_finish  = tk.StringVar()
        self.glove_wear    = tk.StringVar(value="0.060")
        self.glove_pattern = tk.StringVar(value="0")

        self.knife_name    = tk.StringVar()
        self.knife_finish  = tk.StringVar()
        self.knife_wear    = tk.StringVar(value="0.010")
        self.knife_pattern = tk.StringVar(value="0")

        self.agent_name = tk.StringVar()
        self.agent_team = tk.StringVar(value="All")

        self.equipped_items = []

        self._animation_jobs = {}
        self._animation_colors = {}
        self._tab_is_hot = False

        self._toast_win = None

        self._style()
        self._build_ui()

        self.after(100, self._auto_load)

    def _auto_load(self):
        found = find_inventory_txt()
        if not found:
            self.status_var.set("No inventory.txt found.")
            self._refresh_equipped()
            return

        self.inv_path.set(found)
        self.update_idletasks()
        self._load_equipped_from_file(found)

        if getattr(self, "_show_tab_func", None) and getattr(self, "_equipped_tab_ref", None):
            self._show_tab_func(self._equipped_tab_ref)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        self._ttk_style = s

        s.configure(".",
                    background=BG, foreground=TEXT, font=FONT,
                    borderwidth=0, relief="flat", troughcolor=BG,
                    fieldbackground=PANEL, selectbackground=SEL_BG,
                    selectforeground=TEXT, highlightthickness=0,
                    highlightcolor=BG, highlightbackground=BG,
                    lightcolor=BG, darkcolor=BG, bordercolor=BG)

        for style in ("TFrame", "TLabel", "Muted.TLabel", "Head.TLabel",
                      "Title.TLabel", "Section.TLabel"):
            s.configure(style, background=BG, foreground=TEXT, font=FONT,
                        borderwidth=0, relief="flat",
                        highlightthickness=0, highlightcolor=BG,
                        highlightbackground=BG,
                        lightcolor=BG, darkcolor=BG, bordercolor=BG)

        s.configure("Muted.TLabel",   foreground=MUTED,   font=FONT_SM)
        s.configure("Head.TLabel",    foreground=MUTED,   font=FONT_SM)
        s.configure("Title.TLabel",   foreground=ACCENT,  font=FONT_LG)
        s.configure("Section.TLabel", foreground=TEXT,    font=FONT_H)

        s.configure("TNotebook",
                    background=BG, borderwidth=0, relief="flat",
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BG, darkcolor=BG,
                    bordercolor=BG, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=TAB_BG, foreground=MUTED, font=FONT_H,
                    padding=[22, 8], borderwidth=0, relief="flat",
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=TAB_BG,
                    darkcolor=TAB_BG, bordercolor=BG)
        s.map("TNotebook.Tab",
              background=[("selected", TAB_SEL), ("active", "#1e1e1e")],
              foreground=[("selected", TEXT),    ("active", TEXT)],
              padding=[("selected", [22, 8]), ("active", [22, 8]),
                       ("!selected", [22, 8])],
              lightcolor=[("selected", TAB_SEL), ("active", "#1e1e1e")],
              darkcolor= [("selected", TAB_SEL), ("active", "#1e1e1e")])

        s.layout("TCombobox", [
            ("Combobox.field", {
                "sticky": "nswe",
                "children": [
                    ("Combobox.padding", {
                        "sticky": "nswe",
                        "children": [
                            ("Combobox.textarea", {"sticky": "nswe"})
                        ]
                    })
                ]
            })
        ])
        DROPDOWN_BG = "#3a3a3a"
        DROPDOWN_HOVER = "#4a4a4a"
        s.configure("TCombobox",
                    fieldbackground=DROPDOWN_BG, background=DROPDOWN_BG,
                    foreground="#ffffff", selectforeground="#ffffff",
                    selectbackground=DROPDOWN_HOVER, arrowcolor="#ffffff",
                    borderwidth=1, relief="flat",
                    padding=(6, 4), highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("TCombobox",
              fieldbackground=[("readonly", DROPDOWN_BG),
                               ("disabled", DROPDOWN_BG),
                               ("active", DROPDOWN_HOVER)],
              foreground=[("readonly", "#ffffff"),
                          ("disabled", "#ffffff"),
                          ("active", "#ffffff")],
              selectbackground=[("readonly", DROPDOWN_HOVER)],
              selectforeground=[("readonly", "#ffffff")],
              arrowcolor=[("readonly", "#ffffff"), ("active", "#ffffff")],
              lightcolor=[("focus", BORDER), ("!focus", BORDER)],
              darkcolor= [("focus", BORDER), ("!focus", BORDER)],
              bordercolor=[("focus", BORDER), ("!focus", BORDER)])

        s.configure("TEntry",
                    fieldbackground="#3a3a3a", foreground="#ffffff", insertcolor="#ffffff",
                    selectforeground="#ffffff", selectbackground="#505050",
                    borderwidth=1, relief="flat", padding=(6, 4),
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("TEntry",
              lightcolor= [("focus", BORDER), ("!focus", BORDER)],
              darkcolor=  [("focus", BORDER), ("!focus", BORDER)],
              bordercolor=[("focus", BORDER), ("!focus", BORDER)])

        s.configure("Vertical.TScrollbar",
                    background="#555555",
                    troughcolor="#151515",
                    bordercolor="#151515",
                    arrowcolor="#cccccc",
                    borderwidth=0,
                    relief="flat",
                    width=10)
        s.map("Vertical.TScrollbar",
              background=[("active", "#666666"), ("pressed", "#777777")])

        s.configure("TButton",
                    background=PANEL, foreground=MUTED,
                    borderwidth=1, relief="flat", padding=(10, 5),
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("TButton",
              background=[("active", SEL_BG)],
              foreground=[("active", TEXT)],
              lightcolor= [("active", BORDER)],
              darkcolor=  [("active", BORDER)],
              bordercolor=[("active", BORDER)])

        s.configure("Apply.TButton",
                    background="#181818", foreground=ACCENT, font=FONT_H,
                    borderwidth=1, relief="flat", padding=(14, 8),
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("Apply.TButton",
              background=[("active", "#181818"), ("pressed", "#181818")],
              foreground=[("active", ACCENT), ("pressed", ACCENT)],
              lightcolor=[("active", BORDER), ("pressed", BORDER)],
              darkcolor=[("active", BORDER), ("pressed", BORDER)],
              bordercolor=[("active", BORDER), ("pressed", BORDER)])

        s.configure("Add.TButton",
                    background="#181818", foreground=GREEN, font=FONT_H,
                    borderwidth=1, relief="flat", padding=(10, 6),
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("Add.TButton",
              background=[("active", "#181818"), ("pressed", "#181818")],
              foreground=[("active", GREEN), ("pressed", GREEN)],
              lightcolor=[("active", BORDER), ("pressed", BORDER)],
              darkcolor=[("active", BORDER), ("pressed", BORDER)],
              bordercolor=[("active", BORDER), ("pressed", BORDER)])

        s.configure("Remove.TButton",
                    background=PANEL, foreground=RED, font=FONT_SM,
                    borderwidth=1, relief="flat", padding=(6, 4),
                    highlightthickness=0, highlightcolor=BG,
                    highlightbackground=BG, lightcolor=BORDER,
                    darkcolor=BORDER, bordercolor=BORDER)
        s.map("Remove.TButton",
              background=[("active", SEL_BG)],
              lightcolor= [("active", BORDER)],
              darkcolor=  [("active", BORDER)],
              bordercolor=[("active", BORDER)])

        self.option_add("*TCombobox*Listbox.background",       "#3a3a3a")
        self.option_add("*TCombobox*Listbox.foreground",       "#ffffff")
        self.option_add("*TCombobox*Listbox.selectBackground", "#4a4a4a")
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font",             FONT)
        self.option_add("*TCombobox*Listbox.relief",           "flat")
        self.option_add("*TCombobox*Listbox.borderWidth",      "0")
        self.option_add("*TCombobox*Listbox.highlightThickness", "0")

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=MUTED,
                 font=FONT_SM, bd=0, highlightthickness=0).pack(anchor="w", pady=(0, 3))

    def _combo(self, parent, var, values, on_select=None):
        wrap = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
        wrap.pack(fill="x", pady=(0, 12))
        cb = ttk.Combobox(wrap, textvariable=var, values=values, state="readonly")
        cb.pack(fill="x", padx=1, pady=1)
        if on_select:
            cb.bind("<<ComboboxSelected>>", on_select)
        return cb

    def _entry(self, parent, var):
        wrap = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
        wrap.pack(fill="x", pady=(0, 12))
        e = ttk.Entry(wrap, textvariable=var)
        e.pack(fill="x", padx=1, pady=1)
        return e

    def _blend_colors(self, start, end, amount):
        start_rgb = tuple(int(start[i:i + 2], 16) for i in (1, 3, 5))
        end_rgb = tuple(int(end[i:i + 2], 16) for i in (1, 3, 5))
        rgb = tuple(round(a + (b - a) * amount) for a, b in zip(start_rgb, end_rgb))
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def _animate_style_background(self, style_name, target):
        key = f"{style_name}:background"
        previous_job = self._animation_jobs.get(key)
        if previous_job is not None:
            self.after_cancel(previous_job)

        start = self._animation_colors.get(style_name, PANEL)
        steps = 10

        def advance(step=0):
            amount = min(step / steps, 1.0)
            color = self._blend_colors(start, target, amount)
            self._animation_colors[style_name] = color

            if style_name == "TNotebook.Tab":
                self._ttk_style.map(
                    style_name,
                    background=[("selected", TAB_SEL), ("active", color)],
                )
            else:
                self._ttk_style.map(
                    style_name,
                    background=[("active", color), ("pressed", color)],
                )

            if step < steps:
                self._animation_jobs[key] = self.after(
                    16, lambda: advance(step + 1))
            else:
                self._animation_jobs.pop(key, None)

        advance()

    def _animated_button(self, parent, style="TButton", **kwargs):
        button = ttk.Button(parent, style=style, **kwargs)
        button.bind(
            "<Enter>",
            lambda _event, name=style:
                self._animate_style_background(name, SEL_BG),
            add="+",
        )
        button.bind(
            "<Leave>",
            lambda _event, name=style:
                self._animate_style_background(name, "#3a3a3a"),
            add="+",
        )
        return button

    def _toast_reposition(self, toast):
        """Reposition toast relative to main window. Call after geometry is known."""
        try:
            toast.update_idletasks()
            tw = toast.winfo_width()
            th = toast.winfo_height()
            x = self.winfo_rootx() + self.winfo_width()  - tw - 24
            y = self.winfo_rooty() + self.winfo_height() - th - 60
            toast.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _bind_toast_visibility(self, toast):
        """Show/hide toast in sync with the main window's minimized state."""
        def on_main_map(_e=None):
            try:
                toast.deiconify()
                self._toast_reposition(toast)
            except Exception:
                pass

        def on_main_unmap(_e=None):
            try:
                toast.withdraw()
            except Exception:
                pass

        def on_main_configure(e=None):
            # Follow the main window when it is dragged or resized
            if e is not None and e.widget is not self:
                return
            try:
                if toast.winfo_exists() and self.wm_state() == "normal":
                    self._toast_reposition(toast)
            except Exception:
                pass

        ids = {
            "<Map>":       self.bind("<Map>",       on_main_map,       add="+"),
            "<Unmap>":     self.bind("<Unmap>",     on_main_unmap,     add="+"),
            "<Configure>": self.bind("<Configure>", on_main_configure, add="+"),
        }

        # Clean up bindings when the toast is gone
        def _cleanup():
            for seq, fid in ids.items():
                try:
                    self.unbind(seq, fid)
                except Exception:
                    pass

        toast._fradmod_cleanup = _cleanup

    def _show_toast(self, message, duration_ms=4000):
        if self._toast_win is not None:
            try:
                # Clean up old visibility bindings
                cleanup = getattr(self._toast_win, "_fradmod_cleanup", None)
                if cleanup:
                    cleanup()
                self._toast_win.destroy()
            except Exception:
                pass
            self._toast_win = None

        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg="#2a2a2a")
        toast.attributes("-topmost", True)
        try:
            toast.attributes("-alpha", 0.97)
        except Exception:
            pass

        tk.Label(
            toast, text=message, bg="#2a2a2a", fg="#ffffff",
            font=FONT_SM, justify="left",
            padx=18, pady=14,
        ).pack()

        self._toast_reposition(toast)
        self._bind_toast_visibility(toast)

        # If main window is already minimized, hide immediately
        if self.wm_state() in ("iconic", "withdrawn"):
            toast.withdraw()

        self._toast_win = toast

        def dismiss(_e=None):
            try:
                cleanup = getattr(toast, "_fradmod_cleanup", None)
                if cleanup:
                    cleanup()
                toast.destroy()
            except Exception:
                pass
            if self._toast_win is toast:
                self._toast_win = None

        toast.bind("<Button-1>", dismiss)
        for w in (toast,) + tuple(toast.winfo_children()):
            w.bind("<Button-1>", dismiss)

        self.after(duration_ms, dismiss)

    def _show_confirm_toast(self, message, on_yes, duration_ms=8000):
        if self._toast_win is not None:
            try:
                cleanup = getattr(self._toast_win, "_fradmod_cleanup", None)
                if cleanup:
                    cleanup()
                self._toast_win.destroy()
            except Exception:
                pass
            self._toast_win = None

        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.configure(bg="#2a2a2a")
        toast.attributes("-topmost", True)
        try:
            toast.attributes("-alpha", 0.97)
        except Exception:
            pass

        def dismiss(_e=None):
            try:
                cleanup = getattr(toast, "_fradmod_cleanup", None)
                if cleanup:
                    cleanup()
                toast.destroy()
            except Exception:
                pass
            if self._toast_win is toast:
                self._toast_win = None

        def confirm():
            dismiss()
            on_yes()

        tk.Label(
            toast, text=message, bg="#2a2a2a", fg="#ffffff",
            font=FONT_SM, justify="left",
            padx=18, pady=12,
        ).pack()

        btn_row = tk.Frame(toast, bg="#2a2a2a")
        btn_row.pack(padx=18, pady=(0, 12), fill="x")

        yes_btn = tk.Button(
            btn_row, text="Yes", command=confirm,
            bg="#333333", fg=GREEN, activebackground="#3a3a3a",
            activeforeground=GREEN, relief="flat", font=FONT_SM,
            padx=14, pady=4, bd=0, highlightthickness=0, cursor="hand2",
        )
        yes_btn.pack(side="left", padx=(0, 6))

        no_btn = tk.Button(
            btn_row, text="No", command=dismiss,
            bg="#333333", fg=MUTED, activebackground="#3a3a3a",
            activeforeground="#ffffff", relief="flat", font=FONT_SM,
            padx=14, pady=4, bd=0, highlightthickness=0, cursor="hand2",
        )
        no_btn.pack(side="left")

        self._toast_reposition(toast)
        self._bind_toast_visibility(toast)

        # If main window is already minimized, hide immediately
        if self.wm_state() in ("iconic", "withdrawn"):
            toast.withdraw()

        self._toast_win = toast
        self.after(duration_ms, dismiss)

    def _build_ui(self):
        try:
            # Tab button images: put the PNGs in the same folder as this script
            _base = os.path.dirname(os.path.abspath(__file__))

            def _load_tab_img(fname):
                return tk.PhotoImage(file=os.path.join(_base, fname))

            self._tab_img_gloves   = _load_tab_img("gloves.png")
            self._tab_img_knife    = _load_tab_img("knife.png")
            self._tab_img_agent    = _load_tab_img("agent.png")
            self._tab_img_equipped = _load_tab_img("equiped.png")
            _use_images = True
        except Exception:
            _use_images = False

        tab_bar = tk.Frame(self, bg=TAB_BG, bd=0, highlightthickness=0)
        tab_bar.pack(fill="x", side="top")

        content_area = tk.Frame(self, bg=BG, bd=0, highlightthickness=0)
        content_area.pack(fill="both", expand=True)

        glove_tab    = tk.Frame(content_area, bg=BG, bd=0, highlightthickness=0)
        knife_tab    = tk.Frame(content_area, bg=BG, bd=0, highlightthickness=0)
        agent_tab    = tk.Frame(content_area, bg=BG, bd=0, highlightthickness=0)
        equipped_tab = tk.Frame(content_area, bg=BG, bd=0, highlightthickness=0)

        self._build_glove_tab(glove_tab)
        self._build_knife_tab(knife_tab)
        self._build_agent_tab(agent_tab)
        self._build_equipped_tab(equipped_tab)

        _all_tabs = [glove_tab, knife_tab, agent_tab, equipped_tab]
        self._active_tab_frame = glove_tab
        self._equipped_tab_ref = equipped_tab

        SEL_HIGHLIGHT  = "#2a2a2a"
        IDLE_HIGHLIGHT = TAB_BG

        self._tab_buttons = []

        def _show_tab(frame):
            for f in _all_tabs:
                f.place_forget()
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._active_tab_frame = frame
            _refresh_btn_states()

        def _refresh_btn_states():
            tab_map = {glove_tab: 0, knife_tab: 1, agent_tab: 2, equipped_tab: 3}
            active_idx = tab_map.get(self._active_tab_frame, 0)
            for i, btn in enumerate(self._tab_buttons):
                btn.configure(
                    bg=SEL_HIGHLIGHT if i == active_idx else IDLE_HIGHLIGHT,
                    activebackground=SEL_HIGHLIGHT,
                )

        self._show_tab_func = _show_tab

        _tab_defs = [
            (self._tab_img_gloves   if _use_images else None, "  Gloves  ",   glove_tab),
            (self._tab_img_knife    if _use_images else None, "  Knife  ",    knife_tab),
            (self._tab_img_agent    if _use_images else None, "  Agent  ",    agent_tab),
            (self._tab_img_equipped if _use_images else None, "  Equipped  ", equipped_tab),
        ]

        for img, label_text, frame in _tab_defs:
            if _use_images and img is not None:
                btn = tk.Button(
                    tab_bar,
                    image=img,
                    compound="center",
                    bg=IDLE_HIGHLIGHT,
                    activebackground=SEL_HIGHLIGHT,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda f=frame: _show_tab(f),
                )
            else:
                btn = tk.Button(
                    tab_bar,
                    text=label_text,
                    bg=IDLE_HIGHLIGHT,
                    fg=MUTED,
                    activebackground=SEL_HIGHLIGHT,
                    activeforeground=TEXT,
                    font=FONT_H,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda f=frame: _show_tab(f),
                )
            btn.pack(side="left", padx=(0, 1), pady=(4, 0))
            self._tab_buttons.append(btn)

        glove_tab.place(relx=0, rely=0, relwidth=1, relheight=1)
        _refresh_btn_states()

        bottom = tk.Frame(self, bg=BG, bd=0, highlightthickness=0)
        bottom.pack(fill="x", padx=20, pady=(10, 14))
        self._animated_button(
            bottom,
            style="Apply.TButton",
            text="Export",
            command=self._apply,
        ).pack(side="right")

    def _build_glove_tab(self, parent):
        pad = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        pad.pack(fill="both", expand=True, padx=20, pady=18)

        left = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        right.pack(side="left", fill="both", expand=True)

        self._label(left, "TYPE")
        self._combo(left, self.glove_name, sorted(GLOVES.keys()),
                    on_select=self._on_glove_type)

        self._label(left, "FINISH")
        wrap = tk.Frame(left, bg=BORDER, bd=0, highlightthickness=0)
        wrap.pack(fill="x", pady=(0, 12))
        self.glove_finish_cb = ttk.Combobox(wrap, textvariable=self.glove_finish,
                                             state="readonly")
        self.glove_finish_cb.pack(fill="x", padx=1, pady=1)

        self._label(right, "FLOAT")
        self._entry(right, self.glove_wear)

        self._label(right, "PATTERN SEED")
        self._entry(right, self.glove_pattern)

        btn_row = tk.Frame(right, bg=BG, bd=0, highlightthickness=0)
        btn_row.pack(fill="x", pady=(8, 0))
        self._animated_button(
            btn_row,
            style="Add.TButton",
            text="+ Add to Equipped",
            command=self._add_glove_to_equipped,
        ).pack(side="left")

    def _build_knife_tab(self, parent):
        pad = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        pad.pack(fill="both", expand=True, padx=20, pady=18)

        left = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        right.pack(side="left", fill="both", expand=True)

        self._label(left, "TYPE")
        self._combo(left, self.knife_name, sorted(KNIVES.keys()))

        self._label(left, "FINISH")
        self._combo(left, self.knife_finish, list(KNIFE_FINISHES.keys()))

        self._label(right, "FLOAT")
        self._entry(right, self.knife_wear)

        self._label(right, "PATTERN SEED")
        self._entry(right, self.knife_pattern)

        btn_row = tk.Frame(right, bg=BG, bd=0, highlightthickness=0)
        btn_row.pack(fill="x", pady=(8, 0))
        self._animated_button(
            btn_row,
            style="Add.TButton",
            text="+ Add to Equipped",
            command=self._add_knife_to_equipped,
        ).pack(side="left")

    def _build_agent_tab(self, parent):
        pad = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        pad.pack(fill="both", expand=True, padx=20, pady=18)

        left = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        right.pack(side="left", fill="both", expand=True)

        self._label(left, "FILTER BY TEAM")
        team_wrap = tk.Frame(left, bg=BORDER, bd=0, highlightthickness=0)
        team_wrap.pack(fill="x", pady=(0, 12))
        self.agent_team_cb = ttk.Combobox(team_wrap, textvariable=self.agent_team,
                                           values=["All", "CT", "T"], state="readonly")
        self.agent_team_cb.pack(fill="x", padx=1, pady=1)
        self.agent_team_cb.bind("<<ComboboxSelected>>", self._on_agent_team)

        self._label(left, "AGENT")
        agent_wrap = tk.Frame(left, bg=BORDER, bd=0, highlightthickness=0)
        agent_wrap.pack(fill="x", pady=(0, 12))
        self.agent_name_cb = ttk.Combobox(agent_wrap, textvariable=self.agent_name,
                                           state="readonly")
        self.agent_name_cb.pack(fill="x", padx=1, pady=1)
        self._refresh_agent_list()

        btn_row = tk.Frame(left, bg=BG, bd=0, highlightthickness=0)
        btn_row.pack(fill="x", pady=(4, 0))
        self._animated_button(
            btn_row,
            style="Add.TButton",
            text="+ Add to Equipped",
            command=self._add_agent_to_equipped,
        ).pack(side="left")

    def _build_equipped_tab(self, parent):
        pad = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        pad.pack(fill="both", expand=True, padx=20, pady=14)

        list_outer = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        list_outer.pack(fill="both", expand=True)
        list_inner = tk.Frame(list_outer, bg=BG, bd=0, highlightthickness=0)
        list_inner.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            list_inner,
            orient="vertical",
            command=lambda *args: canvas.yview,
            style="Vertical.TScrollbar",
        )
        canvas = tk.Canvas(
            list_inner,
            bg=BG,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self._equipped_canvas  = canvas
        self._equipped_scrollbar = scrollbar
        self._equipped_frame   = tk.Frame(canvas, bg=BG, bd=0, highlightthickness=0)
        self._equipped_win_id  = canvas.create_window((0, 0), window=self._equipped_frame,
                                                       anchor="nw")

        self._equipped_frame.bind("<Configure>", self._on_equipped_configure)
        canvas.bind("<Configure>", self._on_canvas_resize)

        self._equipped_count_var = tk.StringVar(value="0 items queued")
        tk.Label(pad, textvariable=self._equipped_count_var, bg=BG, fg=MUTED,
                 font=FONT_SM, bd=0, highlightthickness=0).pack(anchor="w", pady=(8, 0))

    def _on_equipped_configure(self, _=None):
        self._equipped_canvas.configure(
            scrollregion=self._equipped_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self._equipped_canvas.itemconfig(self._equipped_win_id, width=event.width)

    def _refresh_equipped(self):
        for w in self._equipped_frame.winfo_children():
            w.destroy()

        if not self.equipped_items:
            tk.Label(self._equipped_frame,
                     text="No items added yet.\nUse the Gloves / Knife / Agent tabs to add items.",
                     bg=BG, fg=MUTED, font=FONT_SM,
                     bd=0, highlightthickness=0,
                     justify="left").pack(anchor="nw", padx=10, pady=20)
            self._equipped_count_var.set("0 items queued")
            return

        for idx, item in enumerate(self.equipped_items):
            row = tk.Frame(self._equipped_frame, bg=BG if idx % 2 == 0 else PANEL,
                           bd=0, highlightthickness=0)
            row.pack(fill="x", padx=6, pady=1)

            itype   = item.get("type", "")
            iname   = item.get("name", "")
            ifinish = item.get("finish", "—")
            iwear   = item.get("wear",   "—")
            ipat    = item.get("pattern", "—")

            type_color = {"glove": "#7986cb", "knife": GOLD, "agent": "#4db6ac"}.get(itype, MUTED)
            from_file  = item.get("from_file", False)
            tag_label  = f"{itype.upper()}" + (" *" if not from_file else "")

            tk.Label(row, text=tag_label, bg=row["bg"], fg=type_color,
                     font=FONT_SM, width=10, anchor="w",
                     bd=0, highlightthickness=0).pack(side="left")
            tk.Label(row, text=iname[:36], bg=row["bg"], fg=TEXT,
                     font=FONT_SM, width=34, anchor="w",
                     bd=0, highlightthickness=0).pack(side="left")
            tk.Label(row, text=ifinish[:28], bg=row["bg"], fg=MUTED,
                     font=FONT_SM, width=26, anchor="w",
                     bd=0, highlightthickness=0).pack(side="left")
            tk.Label(row, text=iwear, bg=row["bg"], fg=MUTED,
                     font=FONT_SM, width=8, anchor="w",
                     bd=0, highlightthickness=0).pack(side="left")
            tk.Label(row, text=ipat, bg=row["bg"], fg=MUTED,
                     font=FONT_SM, width=8, anchor="w",
                     bd=0, highlightthickness=0).pack(side="left")

            rm_btn = self._animated_button(
                row,
                style="Remove.TButton",
                text="✕",
                command=lambda i=idx: self._remove_equipped(i),
            )
            rm_btn.pack(side="right", padx=(0, 4))

        n = len(self.equipped_items)
        self._equipped_count_var.set(
            f"{n} item{'s' if n != 1 else ''} queued"
        )

    def _validate_float_pattern(self, wear, pat):
        """Return True if wear is a number 0-1 and pat is a whole number; else toast."""
        try:
            wear_ok = 0.0 <= float(wear) <= 1.0
        except ValueError:
            wear_ok = False
        if not wear_ok:
            self._show_toast("Float must be a number from 0 to 1.\nPlease fix it and try again.")
            return False
        if not (pat.isascii() and pat.isdigit()):
            self._show_toast("Pattern must be a whole number (e.g. 0, 123).\nPlease fix it and try again.")
            return False
        return True

    def _add_glove_to_equipped(self):
        gname   = self.glove_name.get()
        gfinish = self.glove_finish.get()
        if not gname or not gfinish:
            self._show_toast("Select a glove type and finish first.")
            return
        gdata      = GLOVES[gname]
        finish_cat = gdata["finishes"].get(gfinish)
        if not finish_cat:
            self._show_toast(f"Unknown finish: {gfinish}")
            return
        wear = self.glove_wear.get().strip()    or "0.06"
        pat  = self.glove_pattern.get().strip() or "0"
        if not self._validate_float_pattern(wear, pat):
            return
        self.equipped_items.append({
            "type":       "glove",
            "name":       gname,
            "finish":     gfinish,
            "wear":       wear,
            "pattern":    pat,
            "def_index":  gdata["def_index"],
            "finish_cat": finish_cat,
        })
        self._refresh_equipped()
        self.status_var.set(f"Added: {gname} — {gfinish}")
        self._show_toast(f"Added: {gname}\n{gfinish}  |  float {wear}  |  seed {pat}")

    def _add_knife_to_equipped(self):
        kname   = self.knife_name.get()
        kfinish = self.knife_finish.get()
        if not kname:
            self._show_toast("Select a knife type first.")
            return
        kdata       = KNIVES[kname]
        finish_info = KNIFE_FINISHES.get(kfinish) if kfinish else None
        if isinstance(finish_info, dict):
            finish_info = finish_info.get(kdata["def_index"])
            if finish_info is None:
                self._show_toast(f"{kfinish} isn't available for {kname}.")
                return
        wear = self.knife_wear.get().strip()    or "0.01"
        pat  = self.knife_pattern.get().strip() or "0"
        fin_cat = finish_info[0] if finish_info else None
        if fin_cat and not self._validate_float_pattern(wear, pat):
            return
        self.equipped_items.append({
            "type":       "knife",
            "name":       kname,
            "finish":     kfinish if kfinish else "Vanilla",
            "wear":       wear if fin_cat else "—",
            "pattern":    pat if fin_cat else "—",
            "def_index":  kdata["def_index"],
            "finish_cat": fin_cat,
            "pat_val":    pat,
            "wear_val":   wear,
        })
        self._refresh_equipped()
        label = f"{kname} — {kfinish}" if kfinish else f"{kname} (Vanilla)"
        self.status_var.set(f"Added: {label}")
        wear_disp = wear if fin_cat else "—"
        pat_disp  = pat  if fin_cat else "—"
        self._show_toast(f"Added: {kname}\n{kfinish if kfinish else 'Vanilla'}  |  float {wear_disp}  |  seed {pat_disp}")

    def _add_agent_to_equipped(self):
        aname = self.agent_name.get()
        if not aname or aname not in AGENTS:
            self._show_toast("Select an agent first.")
            return
        adata = AGENTS[aname]
        self.equipped_items.append({
            "type":      "agent",
            "name":      aname,
            "finish":    f"[{adata['team']}]",
            "wear":      "—",
            "pattern":   "—",
            "def_index": adata["def_index"],
        })
        self._refresh_equipped()
        self.status_var.set(f"Added Agent: {aname}")
        self._show_toast(f"Added: {aname}\n[{adata['team']}]")

    def _remove_equipped(self, idx):
        if 0 <= idx < len(self.equipped_items):
            removed = self.equipped_items.pop(idx)
            self._refresh_equipped()
            self.status_var.set(f"Removed: {removed.get('name','item')}")

    def _on_agent_team(self, _=None):
        self._refresh_agent_list()

    def _refresh_agent_list(self):
        team = self.agent_team.get()
        if team == "All":
            names = sorted(AGENTS.keys())
        else:
            names = sorted(k for k, v in AGENTS.items() if v["team"] == team)
        self.agent_name_cb["values"] = names
        if names:
            self.agent_name.set(names[0])
        else:
            self.agent_name.set("")

    def _on_glove_type(self, _=None):
        name = self.glove_name.get()
        if name in GLOVES:
            finishes = list(GLOVES[name]["finishes"].keys())
            self.glove_finish_cb["values"] = finishes
            if finishes:
                self.glove_finish.set(finishes[0])

    def _load_equipped_from_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            return
        parsed = parse_equipped_from_inventory(text)
        self.equipped_items = parsed
        self._refresh_equipped()
        if parsed:
            self.status_var.set(f"Loaded {len(parsed)} item(s) from inventory.txt")
        else:
            self.status_var.set(f"Loaded {path} — no recognizable items found.")

    def _apply(self):
        path = self.inv_path.get().strip()
        if not path or not os.path.isfile(path):
            self._show_toast("inventory.txt not found.")
            return

        if not self.equipped_items:
            self._show_toast("Add items on the Gloves / Knife / Agent tabs first,\n"
                             "then check the Equipped tab before applying.")
            return

        if is_csgo_running():
            self._show_toast("Close CS:GO before exporting.")
            self.status_var.set("Export blocked — close CS:GO and try again.")
            return

        entries = ""
        slot = 9000
        for item in self.equipped_items:
            itype = item["type"]
            if itype == "glove":
                entries += build_glove_entry(
                    slot, slot,
                    item["def_index"],
                    item["finish_cat"],
                    item["pattern"],
                    item["wear"],
                )
                slot += 1
            elif itype == "knife":
                entries += build_knife_entry(
                    slot, slot,
                    item["def_index"],
                    item.get("finish_cat"),
                    item.get("pat_val", "0"),
                    item.get("wear_val", "0.01"),
                )
                slot += 1
            elif itype == "agent":
                entries += build_agent_entry(slot, slot, item["def_index"])
                slot += 1

        new_text = '"items"\n{\n' + entries + '}\n'

        success, err = safe_write_inventory(path, new_text)
        if not success:
            self._show_toast(
                f"Write failed: {err}\n\n"
                "Check the file isn't read-only\n"
                "and that the folder is writable."
            )
            self.status_var.set(f"Write failed: {err}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                written = f.read()
        except Exception as e:
            self._show_toast(f"Write succeeded but couldn't verify:\n{e}")
            self.status_var.set("Write succeeded (verification failed).")
            return

        if written != new_text:
            self._show_toast(
                "inventory.txt was written but doesn't match.\n"
                "Another process may have interfered."
            )
            self.status_var.set("Write did not persist — another process interfered.")
            return

        n = len(self.equipped_items)
        self.status_var.set(f"Exported {n} item(s) to inventory.txt.")
        self._show_toast(
            f"Exported {n} item{'s' if n != 1 else ''} to inventory.txt.\n\n"
            "Launch CS:GO to see the new loadout."
        )


# ─────────────────────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CSGOEditor()
    app.mainloop()