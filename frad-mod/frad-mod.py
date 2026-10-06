#!/usr/bin/env python3
"""
frad-mod  (single file): inventory editor + login / friends / matchmaking.

Run:  python frad-mod.py
Optional: pip install pillow  (for avatars)
"""

import base64, io
import json
import os
import queue
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None


# Paths that work both from source and when frozen with PyInstaller.
# RES_DIR: bundled read-only assets (logo.ico, tab PNGs).
# APP_DIR: writable files that must survive restarts (frad_social.json, server.txt).
if getattr(sys, "frozen", False):
    RES_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    RES_DIR = APP_DIR = os.path.dirname(os.path.abspath(__file__))


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
        self.geometry("920x520")
        self.resizable(False, False)

        # Set custom window icon (resolve path relative to this script)
        try:
            _ico = os.path.join(RES_DIR, "logo.ico")
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
        self.social = Social(self, self, self._show_toast)
        self._inv_frame = tk.Frame(self.social.content, bg=BG, bd=0, highlightthickness=0)
        self.social.inventory = self._inv_frame
        self.social.get_inventory = self._save_get_inventory
        self.social.set_inventory = self._save_set_inventory
        self._build_ui()
        self.social.show_start()

        self.after(100, self._auto_load)

    def _sync_servers_file(self, inv_path):
        """Make server.txt live in the same csgo_gc folder as inventory.txt."""
        global SERVERS_FILE
        try:
            if not inv_path:
                return
            target = os.path.join(os.path.dirname(os.path.abspath(inv_path)), "server.txt")
            old = SERVERS_FILE
            if os.path.normcase(old) != os.path.normcase(target):
                # carry over an existing server.txt from next to the script
                if os.path.isfile(old) and not os.path.exists(target):
                    import shutil
                    shutil.copy2(old, target)
                SERVERS_FILE = target
        except Exception:
            pass

    def _inv_file(self):
        path = self.inv_path.get().strip() or find_inventory_txt()
        self._sync_servers_file(path)
        return path

    def _save_get_inventory(self):
        path = self._inv_file()
        if not path or not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _save_set_inventory(self, text):
        path = self._inv_file()
        if not path:
            return False, "inventory.txt not found"
        if is_csgo_running():
            return False, "close CS:GO first"
        try:
            if os.path.isfile(path):
                import shutil
                shutil.copy2(path, path + ".bak")
        except Exception:
            pass
        ok, err = safe_write_inventory(path, text)
        if ok:
            self.inv_path.set(path)
            self._load_equipped_from_file(path)
        return ok, err

    def _auto_load(self):
        found = find_inventory_txt()
        if not found:
            self.status_var.set("No inventory.txt found.")
            self._refresh_equipped()
            return

        self.inv_path.set(found)
        self._sync_servers_file(found)
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

    def _round_wrap(self, parent, pady=(0, 12)):
        wrap = RoundFrame(parent, bg=BORDER, outer=BG, radius=4)
        wrap.pack(fill="x", pady=pady)
        return wrap

    def _round_button(self, parent, **kwargs):
        # fixed-width rounded button: don't auto-measure (that collapsed it to a thin bar)
        wrap = RoundFrame(parent, bg=BORDER, outer=BG, radius=4)
        wrap._cv.configure(width=170)
        btn = self._animated_button(wrap, style="Add.TButton", **kwargs)
        btn.pack(fill="both", expand=True, padx=1, pady=1)
        wrap.pack(side="left")
        return btn

    def _combo(self, parent, var, values, on_select=None):
        wrap = self._round_wrap(parent)
        cb = ttk.Combobox(wrap, textvariable=var, values=values, state="readonly")
        cb.pack(fill="x", padx=1, pady=1)
        if on_select:
            cb.bind("<<ComboboxSelected>>", on_select)
        return cb

    def _entry(self, parent, var):
        wrap = self._round_wrap(parent)
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
        def on_main_map(e=None):
            if e is not None and e.widget is not self:
                return
            try:
                toast.deiconify()
                self._toast_reposition(toast)
            except Exception:
                pass

        def on_main_unmap(e=None):
            if e is not None and e.widget is not self:
                return
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

        def on_main_focus(_e=None):
            try:
                if toast.winfo_exists() and self.wm_state() == "normal":
                    toast.lift()
            except Exception:
                pass

        ids = {
            "<FocusIn>":   self.bind("<FocusIn>",   on_main_focus,     add="+"),
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
        toast.lift()
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
        toast.lift()
        self._bind_toast_visibility(toast)

        # If main window is already minimized, hide immediately
        if self.wm_state() in ("iconic", "withdrawn"):
            toast.withdraw()

        self._toast_win = toast
        self.after(duration_ms, dismiss)

    def _build_ui(self):
        try:
            # Tab button images: put the PNGs in the same folder as this script
            _base = RES_DIR

            def _load_tab_img(fname):
                return tk.PhotoImage(file=os.path.join(_base, fname))

            self._tab_img_gloves   = _load_tab_img("gloves.png")
            self._tab_img_knife    = _load_tab_img("knife.png")
            self._tab_img_agent    = _load_tab_img("agent.png")
            self._tab_img_equipped = _load_tab_img("equiped.png")
            _use_images = True
        except Exception:
            _use_images = False

        tab_bar = tk.Frame(self._inv_frame, bg=TAB_BG, bd=0, highlightthickness=0)
        tab_bar.pack(fill="x", side="top")

        content_area = tk.Frame(self._inv_frame, bg=BG, bd=0, highlightthickness=0)
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

        bottom = tk.Frame(self._inv_frame, bg=BG, bd=0, highlightthickness=0)
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
        wrap = self._round_wrap(left)
        self.glove_finish_cb = ttk.Combobox(wrap, textvariable=self.glove_finish,
                                             state="readonly")
        self.glove_finish_cb.pack(fill="x", padx=1, pady=1)

        self._label(right, "FLOAT")
        self._entry(right, self.glove_wear)

        self._label(right, "PATTERN SEED")
        self._entry(right, self.glove_pattern)

        btn_row = tk.Frame(right, bg=BG, bd=0, highlightthickness=0)
        btn_row.pack(fill="x", pady=(8, 0))
        self._round_button(
            btn_row,
            text="+ Add to Equipped",
            command=self._add_glove_to_equipped,
        )

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
        self._round_button(
            btn_row,
            text="+ Add to Equipped",
            command=self._add_knife_to_equipped,
        )

    def _build_agent_tab(self, parent):
        pad = tk.Frame(parent, bg=BG, bd=0, highlightthickness=0)
        pad.pack(fill="both", expand=True, padx=20, pady=18)

        left = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right = tk.Frame(pad, bg=BG, bd=0, highlightthickness=0)
        right.pack(side="left", fill="both", expand=True)

        self._label(left, "FILTER BY TEAM")
        team_wrap = self._round_wrap(left)
        self.agent_team_cb = ttk.Combobox(team_wrap, textvariable=self.agent_team,
                                           values=["All", "CT", "T"], state="readonly")
        self.agent_team_cb.pack(fill="x", padx=1, pady=1)
        self.agent_team_cb.bind("<<ComboboxSelected>>", self._on_agent_team)

        self._label(left, "AGENT")
        agent_wrap = self._round_wrap(left)
        self.agent_name_cb = ttk.Combobox(agent_wrap, textvariable=self.agent_name,
                                           state="readonly")
        self.agent_name_cb.pack(fill="x", padx=1, pady=1)
        self._refresh_agent_list()

        btn_row = tk.Frame(left, bg=BG, bd=0, highlightthickness=0)
        btn_row.pack(fill="x", pady=(4, 0))
        self._round_button(
            btn_row,
            text="+ Add to Equipped",
            command=self._add_agent_to_equipped,
        )

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
# SOCIAL  (was frad_social.py) - login, main menu, P2P friends, matchmaking
# ─────────────────────────────────────────────────────────

BG, PANEL, CARD = "#0a0a0a", "#111111", "#1c1c1c"
S_TEXT, S_MUTED = "#e6e6e6", "#9a9a9a"
S_GREEN, GREEN_DK, RED = "#8bc34a", "#5a7a3a", "#e53935"
F, FB, FH, FS = ("Segoe UI", 10), ("Segoe UI", 10, "bold"), ("Segoe UI", 13, "bold"), ("Segoe UI", 8)

DEFAULT_PORT = 27650
CFG = os.path.join(APP_DIR, "frad_social.json")


# ───────────── Steam profile lookup ─────────────

def _get(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "frad-mod"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def resolve_profile(text):
    """SteamID64, /profiles/ URL, /id/ URL or vanity name -> dict(steamid, name, avatar)."""
    t = text.strip().rstrip("/")
    if re.fullmatch(r"\d{17}", t):
        url = f"https://steamcommunity.com/profiles/{t}/?xml=1"
    else:
        m = re.search(r"steamcommunity\.com/profiles/(\d{17})", t)
        if m:
            url = f"https://steamcommunity.com/profiles/{m.group(1)}/?xml=1"
        else:
            m = re.search(r"steamcommunity\.com/id/([^/?#]+)", t)
            vanity = m.group(1) if m else t
            if not re.fullmatch(r"[A-Za-z0-9_\-]{2,32}", vanity):
                raise ValueError("Not a valid SteamID64, URL or vanity name")
            url = f"https://steamcommunity.com/id/{vanity}/?xml=1"
    xml = _get(url).decode("utf-8", "ignore")
    sid = re.search(r"<steamID64>(\d{17})</steamID64>", xml)
    if not sid:
        raise ValueError("Profile not found")
    name = re.search(r"<steamID><!\[CDATA\[(.*?)\]\]></steamID>", xml, re.S)
    av = re.search(r"<avatarFull><!\[CDATA\[(.*?)\]\]></avatarFull>", xml, re.S)
    return {"steamid": sid.group(1),
            "name": name.group(1) if name else sid.group(1),
            "avatar": av.group(1) if av else ""}


# ───────────── storage ─────────────

class Store:
    def __init__(self):
        self.d = {"me": None, "port": DEFAULT_PORT,
                  "friends": {}, "out": {}, "in": {}}
        try:
            with open(CFG, "r", encoding="utf-8") as f:
                self.d.update(json.load(f))
        except Exception:
            pass
        self.lock = threading.Lock()

    def save(self):
        with self.lock:
            try:
                with open(CFG, "w", encoding="utf-8") as f:
                    json.dump(self.d, f, indent=2)
            except Exception:
                pass


# ───────────── Network: free public MQTT broker, fully automatic ─────────────
# No server, no ports. Each user listens on a topic named after their SteamID.
# types: request, accept, decline, cancel, remove, hello (presence)

BROKERS = [("broker.hivemq.com", 1883), ("broker.emqx.io", 1883), ("test.mosquitto.org", 1883)]
NS = "frad-mod-v1"


def _rl(n):
    out = bytearray()
    while True:
        b = n % 128
        n //= 128
        out.append(b | (128 if n else 0))
        if not n:
            return bytes(out)


def _rd(sock, n):
    buf = b""
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c:
            raise ConnectionError("closed")
        buf += c
    return buf


class MQTT:
    """Tiny MQTT 3.1.1 client (QoS 0) so no extra packages are needed."""

    def __init__(self, on_message):
        self.on_message = on_message
        self.sock = None
        self.lock = threading.Lock()

    def connect(self, host, port, client_id, topic):
        s = socket.create_connection((host, port), timeout=8)
        cid = client_id.encode()
        vh = b"\x00\x04MQTT\x04\x02\x00\x1e"
        pl = len(cid).to_bytes(2, "big") + cid
        s.sendall(b"\x10" + _rl(len(vh) + len(pl)) + vh + pl)
        h = _rd(s, 4)
        if h[0] != 0x20 or h[3] != 0:
            raise ConnectionError("refused")
        body = b"\x00\x01"
        for tp in (topic, topic + "/req/+"):
            t = tp.encode()
            body += len(t).to_bytes(2, "big") + t + b"\x00"
        s.sendall(b"\x82" + _rl(len(body)) + body)
        s.settimeout(40)
        self.sock = s

    def publish(self, topic, payload, retain=False):
        t = topic.encode()
        body = len(t).to_bytes(2, "big") + t + payload
        with self.lock:
            self.sock.sendall(bytes([0x31 if retain else 0x30]) + _rl(len(body)) + body)

    def ping(self):
        with self.lock:
            self.sock.sendall(b"\xc0\x00")

    def read_loop(self):
        s = self.sock
        while True:
            first = _rd(s, 1)[0]
            mult, ln = 1, 0
            while True:
                b = _rd(s, 1)[0]
                ln += (b & 127) * mult
                mult *= 128
                if not b & 128:
                    break
            data = _rd(s, ln) if ln else b""
            if first >> 4 == 3:
                tl = int.from_bytes(data[:2], "big")
                off = 2 + tl + (2 if (first >> 1) & 3 else 0)
                self.on_message(data[2:2 + tl].decode("utf-8", "ignore"), data[off:])

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass


class P2P:
    def __init__(self, store, events):
        self.s = store
        self.ev = events
        self.online = {}
        self.running = False
        self.mq = None
        self.connected = False
        self.party_hook = None
        self.last_rm = {}

    def me_info(self):
        me = self.s.d["me"]
        return {"steamid": me["steamid"], "name": me["name"], "avatar": me["avatar"]}

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        threading.Thread(target=self._beat, daemon=True).start()

    def _run(self):
        i = 0
        while self.running:
            host, port = BROKERS[i % len(BROKERS)]
            i += 1
            mq = MQTT(self._on_raw)
            try:
                me = self.s.d["me"]["steamid"]
                mq.connect(host, port, f"frad{me}{int(time.time()) % 100000}", f"{NS}/{me}")
                self.mq = mq
                self.connected = True
                self._hello_all()
                mq.read_loop()
            except Exception:
                pass
            self.connected = False
            self.mq = None
            mq.close()
            time.sleep(3)

    def _beat(self):
        n = 0
        while self.running:
            time.sleep(15)
            try:
                if self.mq:
                    self.mq.ping()
                    n += 1
                    if n % 2 == 0:
                        self._hello_all()
            except Exception:
                pass
            self.ev.put(("refresh",))

    def _hello_all(self):
        for sid, rec in list(self.s.d["friends"].items()):
            self.send(rec, "hello")
        # requests are not stored by the broker, so keep re-sending pending ones
        for sid, rec in list(self.s.d["out"].items()):
            self.send(rec, "request")

    def _on_raw(self, topic, payload):
        try:
            self._on_msg(json.loads(payload.decode("utf-8")))
        except Exception:
            pass

    def _on_msg(self, msg):
        t = msg.get("type")
        frm = msg.get("from") or {}
        sid = str(frm.get("steamid", ""))
        if not re.fullmatch(r"\d{17}", sid) or sid == self.s.d["me"]["steamid"]:
            return
        d = self.s.d
        rec = {"steamid": sid, "name": str(frm.get("name", sid))[:40],
               "avatar": str(frm.get("avatar", ""))[:300]}
        if t and t.startswith("party_"):
            if sid in d["friends"] and self.party_hook:
                self.party_hook(t, rec, msg)
            return
        if t == "hello":
            if sid not in d["friends"]:
                # they still list me as a friend but I don't have them: tell them to drop me
                if sid not in d["out"] and sid not in d["in"]:
                    if time.time() - self.last_rm.get(sid, 0) > 20:
                        self.last_rm[sid] = time.time()
                        self.send(rec, "remove")
                return
            was = self.is_online(sid)
            self.online[sid] = time.time()
            if not was:
                self.send(rec, "hello")
            self.ev.put(("refresh",))
            return
        if t == "request":
            if sid in d["out"]:
                d["out"].pop(sid)
                d["friends"][sid] = rec
                self.send(rec, "accept")
            elif sid not in d["friends"]:
                d["in"][sid] = rec
        elif t == "accept":
            if d["out"].pop(sid, None) is None:
                return
            d["friends"][sid] = rec
            self.send(rec, "hello")
        elif t == "decline":
            if d["out"].pop(sid, None) is None:
                return
        elif t == "cancel":
            if d["in"].pop(sid, None) is None:
                return
        elif t == "remove":
            if d["friends"].pop(sid, None) is None:
                return
            self.online.pop(sid, None)
        self.s.save()
        self.ev.put(("refresh",))

    def send(self, rec, mtype, wait_reply=False, extra=None):
        for _ in range(10):                      # wait up to ~5s for connection
            if self.mq:
                break
            time.sleep(0.5)
        try:
            body = {"type": mtype, "from": self.me_info()}
            if extra:
                body.update(extra)
            payload = json.dumps(body).encode()
            me = self.s.d["me"]["steamid"]
            self.mq.publish(f"{NS}/{rec['steamid']}", payload)
            # requests are also stored (retained) on the broker so an offline player gets them later
            if mtype == "request":
                self.mq.publish(f"{NS}/{rec['steamid']}/req/{me}", payload, retain=True)
            elif mtype in ("accept", "decline"):
                self.mq.publish(f"{NS}/{me}/req/{rec['steamid']}", b"", retain=True)
            elif mtype == "cancel":
                self.mq.publish(f"{NS}/{rec['steamid']}/req/{me}", b"", retain=True)
            return True
        except Exception:
            return False

    def is_online(self, sid):
        return time.time() - self.online.get(sid, 0) < 50


# ───────────── avatars ─────────────

class Avatars:
    def __init__(self, root):
        self.root = root
        self.cache = {}

    def get(self, url, size, label="?"):
        key = (url, size)
        if key in self.cache:
            return self.cache[key]
        self.cache[key] = None
        return None

    def load_async(self, url, size, callback):
        if not url or Image is None:
            return
        key = (url, size)
        hit = self.cache.get(key)
        if hit is not None:
            callback(hit)                  # cached: no download, no flicker
            return

        def work():
            try:
                im = Image.open(io.BytesIO(_get(url))).convert("RGB").resize((size, size))
                self.cache[key] = im
                self.root.after(0, lambda: callback(im))
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()


AV_BORDER = "#9bd066"


def _avatar_photo(im, size, bg, b=2, border=AV_BORDER):
    """Rounded-square avatar with a light-green rounded border (antialiased)."""
    from PIL import ImageDraw
    k, S = 4, size + 2 * b
    r = max(4, round(size * 0.12))
    canvas = Image.new("RGB", (S * k, S * k), bg)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((0, 0, S * k - 1, S * k - 1), radius=(r + b) * k, fill=border)
    inner = Image.new("RGB", (size * k, size * k), CARD)
    if im is not None:
        inner = im.convert("RGB").resize((size * k, size * k), Image.LANCZOS)
    mask = Image.new("L", (size * k, size * k), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size * k - 1, size * k - 1), radius=r * k, fill=255)
    canvas.paste(inner, (b * k, b * k), mask)
    return ImageTk.PhotoImage(canvas.resize((S, S), Image.LANCZOS))


AV_OFFLINE = "#6b6b6b"


def avatar_widget(parent, avatars, url, size, name, bg, offline=False):
    """Rounded square with light-green border, letter fallback, image loads async."""
    S = size + 4
    if Image is None:
        box = tk.Frame(parent, bg=S_GREEN, width=S, height=S)
        box.pack_propagate(False)
        tk.Label(box, text=(name or "?")[:1].upper(), bg=CARD, fg=S_TEXT,
                 font=("Segoe UI", max(10, size // 3), "bold")).pack(fill="both", expand=True, padx=2, pady=2)
        return box
    cv = tk.Canvas(parent, width=S, height=S, bg=bg, highlightthickness=0, bd=0)
    bc = AV_OFFLINE if offline else AV_BORDER
    cv._ph = _avatar_photo(None, size, bg, border=bc)
    cv.create_image(0, 0, anchor="nw", image=cv._ph, tags="img")
    cv.create_text(S // 2, S // 2, text=(name or "?")[:1].upper(), fill=S_TEXT, tags="ltr",
                   font=("Segoe UI", max(10, size // 3), "bold"))

    def setimg(im):
        try:
            cv._ph = _avatar_photo(im, size, bg, border=bc)
            cv.itemconfigure("img", image=cv._ph)
            cv.delete("ltr")
        except tk.TclError:
            pass
    avatars.load_async(url, size, setimg)
    return cv


# ───────────── Party + server query ─────────────

SERVERS_FILE = os.path.join(APP_DIR, "server.txt")
SERVERS_TEMPLATE = ("# Put your CS:GO server IPs here, one per line.\n"
                    "# Examples:\n# 123.45.67.89:27015\n# 123.45.67.89   (port 27015 is the default)\n"
                    "# Make a category with // and a name; servers under it belong to it:\n"
                    "# //DM\n# 123.45.67.89:27015\n# //5v5\n# 123.45.67.90:27015\n")


def _parse_servers():
    """[(category or None, host, port)] in file order. A '//Name' line starts a category."""
    out, cat = [], None
    with open(SERVERS_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("//"):
                cat = line[2:].strip() or None
                continue
            host, sep, port = line.rpartition(":")
            if sep and port.isdigit():
                out.append((cat, host, int(port)))
            else:
                out.append((cat, line, 27015))
    return out


def read_categories():
    """Category names from server.txt, in file order (no file or none declared -> [])."""
    try:
        seen = []
        with open(SERVERS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("//"):
                    name = line[2:].strip()
                    if name and name.lower() not in [c.lower() for c in seen]:
                        seen.append(name)
        return seen
    except Exception:
        return []


def read_servers(category=None):
    """List of (host, port) from server.txt (only the given category if set).
    Creates a template and returns None if the file is missing."""
    if not os.path.exists(SERVERS_FILE):
        try:
            with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                f.write(SERVERS_TEMPLATE)
        except Exception:
            pass
        return None
    want = category.lower() if category else None
    return [(h, p) for c, h, p in _parse_servers()
            if want is None or (c or "").lower() == want]


def a2s_info(host, port, timeout=2.0):
    """Ask a Source server how many players it has. Returns dict or None."""
    req = b"\xff\xff\xff\xffTSource Engine Query\x00"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(req, (host, port))
        data, _ = sock.recvfrom(4096)
        if len(data) > 4 and data[4] == 0x41:               # challenge
            sock.sendto(req + data[5:9], (host, port))
            data, _ = sock.recvfrom(4096)
        if len(data) < 6 or data[4] != 0x49:
            return None
        i = 6

        def cstr():
            nonlocal i
            j = data.index(b"\x00", i)
            v = data[i:j].decode("utf-8", "ignore")
            i = j + 1
            return v
        name, mp, _folder, _game = cstr(), cstr(), cstr(), cstr()
        i += 2                                                # app id
        return {"name": name, "map": mp, "players": data[i], "max": data[i + 1]}
    except Exception:
        return None
    finally:
        sock.close()


class PartyCtl:
    MAX = 5

    def __init__(self, get_net, events):
        self.get_net = get_net
        self.ev = events
        self.cat = None            # selected server category (None = all)
        self.reset()

    def reset(self):
        self.leader = None
        self.people = {}
        self.inv_in = {}
        self.inv_out = set()
        self.q = {"busy": False, "status": "", "result": None}

    def _me(self):
        return self.get_net().me_info()

    def ensure(self):
        me = self._me()
        if self.leader is None or me["steamid"] not in self.people:
            self.leader = me["steamid"]
            self.people = {me["steamid"]: me}

    def is_leader(self):
        self.ensure()
        return self.leader == self._me()["steamid"]

    def members(self):
        self.ensure()
        order = [self.people[self.leader]] if self.leader in self.people else []
        return order + [p for k, p in self.people.items() if k != self.leader]

    def _others(self):
        me = self._me()["steamid"]
        return [p for k, p in self.people.items() if k != me]

    def _refresh(self):
        self.ev.put(("refresh",))

    def _send(self, rec, t, extra=None):
        threading.Thread(target=self.get_net().send, args=(rec, t, False, extra),
                         daemon=True).start()

    # --- actions from the UI
    def invite(self, rec):
        if self.is_leader() and len(self.people) < self.MAX:
            self.inv_out.add(rec["steamid"])
            self._send(rec, "party_invite")
            self._refresh()

    def accept(self, sid):
        rec = self.inv_in.pop(sid, None)
        if not rec:
            return
        if len(self.people) > 1:
            self.leave()
        me = self._me()
        self.leader = sid
        self.people = {sid: rec, me["steamid"]: me}
        self._send(rec, "party_join")
        self._refresh()

    def decline(self, sid):
        rec = self.inv_in.pop(sid, None)
        if rec:
            self._send(rec, "party_decline")      # so the inviter can invite again
        self._refresh()

    def cancel_invite(self, rec):
        self.inv_out.discard(rec["steamid"])
        self._send(rec, "party_cancel")           # remove it from their invite list
        self._refresh()

    def leave(self):
        self.ensure()
        if self.is_leader():
            for p in self._others():
                self._send(p, "party_disband")
        else:
            lead = self.people.get(self.leader)
            if lead:
                self._send(lead, "party_leave")
        self.leader = None
        self.people = {}
        self.q = {"busy": False, "status": "", "result": None}
        self.ensure()
        self._refresh()

    def _broadcast_state(self):
        extra = {"leader": self.leader, "people": list(self.people.values())}
        for p in self._others():
            self._send(p, "party_state", extra)

    # --- messages from friends
    def handle(self, t, rec, msg):
        sid = rec["steamid"]
        self.ensure()
        if t == "party_invite":
            is_new = sid not in self.inv_in
            self.inv_in[sid] = rec
            if is_new:
                self.ev.put(("toast", f"{rec.get('name') or 'A friend'} invited you to a party"))
        elif t == "party_decline":
            self.inv_out.discard(sid)
        elif t == "party_cancel":
            self.inv_in.pop(sid, None)
        elif t == "party_join":
            if self.is_leader() and sid in self.inv_out and len(self.people) < self.MAX:
                self.inv_out.discard(sid)
                self.people[sid] = rec
                self._broadcast_state()
            else:
                self._send(rec, "party_disband")
        elif t == "party_leave":
            if self.is_leader() and sid in self.people:
                self.people.pop(sid)
                self._broadcast_state()
        elif t == "party_disband":
            if sid == self.leader and not self.is_leader():
                self.leader = None
                self.people = {}
                self.q = {"busy": False, "status": "", "result": None}
        elif t == "party_state":
            if msg.get("leader") == sid:
                ppl = {}
                for p in (msg.get("people") or [])[: self.MAX]:
                    ps = str(p.get("steamid", ""))
                    if re.fullmatch(r"\d{17}", ps):
                        ppl[ps] = {"steamid": ps, "name": str(p.get("name", ps))[:40],
                                   "avatar": str(p.get("avatar", ""))[:300]}
                if self._me()["steamid"] in ppl and sid in ppl:
                    self.leader, self.people = sid, ppl
        elif t == "party_server":
            if sid == self.leader and not self.is_leader():
                try:
                    self.q["result"] = {"ip": str(msg.get("ip", ""))[:100],
                                        "players": int(msg.get("players", 0)),
                                        "max": int(msg.get("max", 0)),
                                        "map": str(msg.get("map", ""))[:40]}
                    self.q["status"] = ""
                except Exception:
                    pass
        self._refresh()

    # --- queue
    def start_queue(self):
        if not self.is_leader() or self.q["busy"]:
            return
        self.q.update(busy=True, status="Searching\u2026", result=None)
        self._refresh()
        threading.Thread(target=self._queue_work, args=(len(self.people), self.cat), daemon=True).start()

    def _done(self, status, result=None):
        self.q.update(busy=False, status=status, result=result)
        self._refresh()

    def _queue_work(self, need, cat=None):
        try:
            servers = read_servers(cat)
            if servers is None:
                return self._done("Made server.txt - put your server IP in it, then press Queue.")
            if not servers:
                if cat:
                    return self._done(f"No servers in category {cat}.")
                return self._done("server.txt is empty. Put one IP per line.")
            self.q["status"] = f"Checking {len(servers)} server(s)\u2026"
            self._refresh()
            from concurrent.futures import ThreadPoolExecutor

            def probe(sv):
                return sv, a2s_info(sv[0], sv[1])

            with ThreadPoolExecutor(max_workers=min(16, len(servers))) as ex:
                results = list(ex.map(probe, servers))
            dead = sum(1 for _, info in results if info is None)
            best = None                      # fullest server that still fits the party
            for (host, port), info in results:
                if info is None or info["max"] - info["players"] < need:
                    continue
                if best is None or info["players"] > best[1]["players"]:
                    best = ((host, port), info)
            if best is not None:
                (host, port), info = best
                res = {"ip": f"{host}:{port}", "players": info["players"],
                       "max": info["max"], "map": info["map"]}
                for p in self._others():
                    self._send(p, "party_server", res)
                return self._done("", res)
            msg = f"No room on any {cat} server right now. Try again." if cat else "No room on any server right now. Try again."
            if dead:
                msg += f" ({dead} not responding)"
            self._done(msg)
        except Exception as e:
            self._done(f"Error: {e}")


# ───────────── UI helpers ─────────────

def round_poly(cv, w, h, r, color, tag="rr"):
    """Draw a rounded rectangle on canvas cv (antialiased when Pillow is available)."""
    cv.delete(tag)
    w, h = int(w), int(h)
    if w < 2 or h < 2:
        return
    r = max(0, min(r, w // 2, h // 2))
    if Image is not None:
        try:
            from PIL import ImageDraw
            k = 4
            im = Image.new("RGB", (w * k, h * k), cv.cget("bg"))
            ImageDraw.Draw(im).rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=r * k, fill=color)
            ph = ImageTk.PhotoImage(im.resize((w, h), Image.LANCZOS))
            cv._rr_img = ph
            cv.create_image(0, 0, anchor="nw", image=ph, tags=tag)
            cv.tag_lower(tag)
            return
        except Exception:
            pass
    p = [r, 0, w - r, 0, w, 0, w, r, w, h - r, w, h, w - r, h, r, h, 0, h, 0, h - r, 0, r, 0, 0]
    cv.create_polygon(p, smooth=True, fill=color, outline=color, tags=tag)
    cv.tag_lower(tag)


class RoundFrame(tk.Frame):
    """Frame with rounded corners (drawn on a canvas). Use like a normal Frame."""

    def __init__(self, parent, bg=CARD, outer=BG, radius=4):
        self._cv = tk.Canvas(parent, bg=outer, highlightthickness=0, bd=0, height=40)
        super().__init__(self._cv, bg=bg)
        self._fill, self._r = bg, radius
        self._pad = max(2, int(radius * 0.34))      # keeps the square inner frame inside the curves
        self._win = self._cv.create_window(self._pad, self._pad, window=self, anchor="nw")
        self._cv.bind("<Configure>", self._on_cv)
        self.bind("<Configure>", self._on_in)
        self._cv.after(50, self._sync)

    def _sync(self):
        try:
            if getattr(self, "_fit_w", False):
                w = self.winfo_reqwidth() + 2 * self._pad
                if int(self._cv.cget("width")) != w:
                    self._cv.configure(width=w)
            h = self.winfo_reqheight() + 2 * self._pad
            if h > 2 * self._pad + 1 and int(self._cv.cget("height")) != h:
                self._cv.configure(height=h)
                round_poly(self._cv, self._cv.winfo_width(), h, self._r, self._fill)
        except tk.TclError:
            pass

    def _on_cv(self, e):
        self._cv.itemconfigure(self._win, width=max(1, e.width - 2 * self._pad))
        round_poly(self._cv, e.width, self._cv.winfo_height(), self._r, self._fill)

    def _on_in(self, e):
        if e.height < 4:
            return
        h = e.height + 2 * self._pad
        if int(self._cv.cget("height")) != h:
            self._cv.configure(height=h)
        round_poly(self._cv, self._cv.winfo_width(), h, self._r, self._fill)

    def pack(self, **kw):
        self._cv.pack(**kw)

    def pack_forget(self):
        self._cv.pack_forget()

    def destroy(self):
        cv = self._cv
        super().destroy()
        cv.destroy()


class RoundBtn(RoundFrame):
    """Rounded flat button; configure()/cget() go to the real button."""

    def __init__(self, parent, text, cmd, bg=CARD, outer=BG, radius=3, fg=S_TEXT,
                 active="#4a4a4a", **kw):
        super().__init__(parent, bg=bg, outer=outer, radius=radius)
        self.b = tk.Button(self, text=text, command=cmd, bg=bg, fg=fg, activebackground=active,
                           activeforeground=fg, bd=0, relief="flat", cursor="hand2",
                           font=F, padx=12, pady=5, **kw)
        self.b.pack()
        self._fit_w = True
        self._cv.configure(width=110)

    def configure(self, **kw):
        r = self.b.configure(**kw)
        self._cv.after(30, self._sync)
        return r

    config = configure

    def cget(self, key):
        return self.b.cget(key)


def flat_btn(parent, text, cmd, bg=CARD, fg=S_TEXT, **kw):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, activebackground="#4a4a4a",
                     activeforeground=S_TEXT, bd=0, relief="flat", cursor="hand2",
                     font=F, padx=12, pady=5, **kw)


# ───────────── Login screen ─────────────

class LoginScreen(tk.Frame):
    def __init__(self, parent, app, on_done):
        super().__init__(parent, bg=BG)
        self.app, self.on_done = app, on_done
        box = tk.Frame(self, bg=BG)
        box.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(box, text="frad-mod", bg=BG, fg=S_TEXT, font=("Segoe UI", 20, "bold")).pack()
        tk.Label(box, text="Log in with your Steam profile", bg=BG, fg=S_MUTED, font=F).pack(pady=(2, 14))
        self.var = tk.StringVar()
        e = tk.Entry(box, textvariable=self.var, width=40, bg=BG, fg=S_TEXT, insertbackground=S_TEXT,
                     relief="flat", font=F, highlightthickness=1, highlightbackground="#444",
                     highlightcolor=S_GREEN)
        e.pack(ipady=7, pady=(0, 6))
        e.bind("<Return>", lambda _: self.go())
        e.focus_set()
        tk.Label(box, text="SteamID64, profile URL, or /id/ vanity name",
                 bg=BG, fg=S_MUTED, font=FS).pack(anchor="w")
        self.btn = flat_btn(box, "Log in", self.go, bg=GREEN_DK)
        self.btn.pack(pady=12, fill="x")
        self.msg = tk.Label(box, text="", bg=BG, fg=RED, font=FS, wraplength=320)
        self.msg.pack()

    def go(self):
        txt = self.var.get().strip()
        if not txt:
            return
        self.btn.configure(state="disabled", text="Looking up…")
        self.msg.configure(text="", fg=RED)

        def work():
            try:
                me = resolve_profile(txt)
                self.after(0, lambda: self.done(me))
            except Exception as ex:
                self.after(0, lambda e=ex: self.fail(str(e)))
        threading.Thread(target=work, daemon=True).start()

    def note(self, text, ok=True):
        if text:
            self.msg.configure(text=text, fg=S_GREEN if ok else RED)

    def fail(self, m):
        self.btn.configure(state="normal", text="Log in")
        self.msg.configure(text=m or "Lookup failed (check internet)", fg=RED)

    def done(self, me):
        self.app.store.d["me"] = me
        self.app.store.save()
        self.on_done()


# ───────────── Backup screen (login-page theme) ─────────────

class BackupScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        box = tk.Frame(self, bg=BG)
        box.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(box, text="Backup", bg=BG, fg=S_TEXT, font=("Segoe UI", 20, "bold")).pack()
        tk.Label(box, text="Export or import your save data", bg=BG, fg=S_MUTED, font=F).pack(pady=(2, 14))
        row = tk.Frame(box, bg=BG)
        row.pack()
        flat_btn(row, "Export data", lambda: self._io(self.app.export_save), bg="#2a2a2a").pack(side="left", padx=4)
        flat_btn(row, "Import data", lambda: self._io(self.app.import_save), bg="#2a2a2a").pack(side="left", padx=4)
        self.msg = tk.Label(box, text="", bg=BG, fg=RED, font=FS, wraplength=320)
        self.msg.pack(pady=(14, 0))

    def _io(self, fn):
        text, ok = fn()
        if text:
            self.app.toast(text)
            if self.winfo_exists():
                self.msg.configure(text=text, fg=S_GREEN if ok else RED)


# ───────────── Friends screen ─────────────

class FriendsScreen(tk.Frame):
    def __init__(self, parent, app, go_menu):
        super().__init__(parent, bg=BG)
        self.app = app
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0, 0), window=self.body, anchor="nw")

        def fit_region(_e=None):
            # scroll area is never smaller than the view, so short content can't be dragged down
            ch, bh = canvas.winfo_height(), self.body.winfo_reqheight()
            canvas.configure(scrollregion=(0, 0, canvas.winfo_width(), max(bh, ch)))
            if bh <= ch:
                canvas.yview_moveto(0)

        def on_canvas(e):
            canvas.itemconfigure(win, width=e.width)
            fit_region()

        self.body.bind("<Configure>", fit_region)
        canvas.bind("<Configure>", on_canvas)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(14, 10))
        sb.pack(side="right", fill="y", pady=10)

        def wheel(e):
            if not self.winfo_ismapped():
                return
            if self.body.winfo_reqheight() <= canvas.winfo_height():
                canvas.yview_moveto(0)          # nothing to scroll
                return
            canvas.yview_scroll(int(-e.delta / 120), "units")

        canvas.bind_all("<MouseWheel>", wheel)

        self._build_static()
        self.refresh()

    # header: add friend form
    def _build_static(self):
        b = self.body
        tk.Label(b, text="Add a friend", bg=BG, fg=S_TEXT, font=FH).pack(anchor="w", pady=(6, 8))
        row = tk.Frame(b, bg=BG)
        row.pack(fill="x", padx=(0, 20))
        self.id_var = tk.StringVar()
        ent = dict(bg=BG, fg=S_TEXT, insertbackground=S_TEXT, relief="flat", font=F,
                   highlightthickness=1, highlightbackground="#444", highlightcolor=S_GREEN)
        self.send_btn = RoundBtn(row, "Send request", self.add_friend, bg=AV_BORDER, fg=BG,
                                 active="#aad676", disabledforeground="#5a7a3a")
        self.send_btn.pack(side="right", padx=(6, 0))
        field = RoundFrame(row, bg=CARD)
        field.pack(side="left", fill="x", expand=True)
        tk.Entry(field, textvariable=self.id_var, bg=CARD, fg=S_TEXT, insertbackground=S_TEXT,
                 relief="flat", font=F, bd=0, highlightthickness=0
                 ).pack(fill="x", expand=True, ipady=7, padx=10)
        tk.Label(b, text="Accepts 17-digit SteamID64, steamcommunity.com/profiles/\u2026 URLs, or /id/ vanity names.",
                 bg=BG, fg=S_MUTED, font=FS).pack(anchor="w", pady=(4, 0))
        self.err = tk.Label(b, text="", bg=BG, fg=RED, font=FS)
        self.err.pack(anchor="w")
        self.lists = tk.Frame(b, bg=BG)
        self.lists.pack(fill="x", padx=(0, 20))

    def add_friend(self):
        txt = self.id_var.get().strip()
        if not txt:
            return
        self.err.configure(text="")
        self.send_btn.configure(state="disabled", text="Sending…")

        def work():
            try:
                p = resolve_profile(txt)
                d = self.app.store.d
                if p["steamid"] == d["me"]["steamid"]:
                    raise ValueError("That's you.")
                if p["steamid"] in d["friends"]:
                    raise ValueError("Already friends.")
                rec = dict(p)
                ok = self.app.net.send(rec, "request")
                if not ok:
                    raise ValueError("Couldn't connect. Check your internet.")
                d["out"][p["steamid"]] = rec
                self.app.store.save()
                self.after(0, lambda: self.sent_ok())
            except Exception as ex:
                self.after(0, lambda e=ex: self.sent_fail(str(e)))
        threading.Thread(target=work, daemon=True).start()

    def sent_ok(self):
        self.send_btn.configure(state="normal", text="Send request")
        self.id_var.set("")
        self.refresh()

    def sent_fail(self, m):
        self.send_btn.configure(state="normal", text="Send request")
        self.err.configure(text=m)

    # lists
    def _section(self, title, count, label):
        r = tk.Frame(self.lists, bg=BG)
        r.pack(fill="x", pady=(22, 8))
        tk.Label(r, text=title, bg=BG, fg=S_TEXT, font=FH).pack(side="left")
        tk.Label(r, text=label.format(count), bg=BG, fg=S_MUTED, font=FS).pack(side="right")

    def _row(self, rec, sub, sub_fg, buttons):
        row = RoundFrame(self.lists)
        row.pack(fill="x", pady=3)
        avatar_widget(row, self.app.avatars, rec.get("avatar", ""), 36, rec["name"], CARD,
                      offline=(sub != "Online")).pack(side="left", padx=10, pady=10)
        col = tk.Frame(row, bg=CARD)
        col.pack(side="left")
        tk.Label(col, text=rec["name"], bg=CARD, fg=S_TEXT, font=F).pack(anchor="w")
        tk.Label(col, text=sub, bg=CARD, fg=sub_fg, font=FS).pack(anchor="w")
        for text, cmd in reversed(buttons):
            RoundBtn(row, text, cmd, bg="#2a2a2a", outer=CARD).pack(side="right", padx=(0, 8))

    def refresh(self):
        self._sig = self.app._sig("friends")
        d, net = self.app.store.d, self.app.net
        for w in self.lists.winfo_children():
            w.destroy()

        if d["in"]:
            self._section("Friend requests", len(d["in"]), "{} incoming")
            for sid, rec in list(d["in"].items()):
                self._row(rec, "wants to be your friend", S_GREEN,
                          [("Accept", lambda r=rec: self.accept(r)),
                           ("Decline", lambda r=rec: self.decline(r))])

        self._section("Sent requests", len(d["out"]), "{} pending")
        for sid, rec in list(d["out"].items()):
            self._row(rec, "Request pending…", S_MUTED, [("Cancel", lambda r=rec: self.cancel(r))])

        self._section("Friends", len(d["friends"]), "{} friend" + ("" if len(d["friends"]) == 1 else "s"))
        for sid, rec in list(d["friends"].items()):
            on = net.is_online(sid)
            self._row(rec, "Online" if on else "Offline", S_GREEN if on else S_MUTED,
                      [("Steam", lambda r=rec: self.open_steam(r)),
                       ("Remove", lambda r=rec: self.remove(r))])

    def _bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def accept(self, rec):
        d = self.app.store.d
        d["in"].pop(rec["steamid"], None)
        d["friends"][rec["steamid"]] = rec
        self.app.store.save()
        self._bg(lambda: self.app.net.send(rec, "accept"))
        self.app.refresh_all()

    def decline(self, rec):
        self.app.store.d["in"].pop(rec["steamid"], None)
        self.app.store.save()
        self._bg(lambda: self.app.net.send(rec, "decline"))
        self.app.refresh_all()

    def cancel(self, rec):
        self.app.store.d["out"].pop(rec["steamid"], None)
        self.app.store.save()
        self._bg(lambda: self.app.net.send(rec, "cancel"))
        self.app.refresh_all()

    def remove(self, rec):
        self.app.store.d["friends"].pop(rec["steamid"], None)
        self.app.net.online.pop(rec["steamid"], None)
        self.app.store.save()
        self._bg(lambda: self.app.net.send(rec, "remove"))
        self.app.refresh_all()

    def open_steam(self, rec):
        import webbrowser
        webbrowser.open(f"https://steamcommunity.com/profiles/{rec['steamid']}")


# ───────────── Matchmaking screen ─────────────

class MatchScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        cols = tk.Frame(self, bg=BG)
        cols.pack(fill="both", expand=True, padx=26, pady=18)
        self.left = tk.Frame(cols, bg=BG, width=330)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)
        self.right = tk.Frame(cols, bg=BG)
        self.right.pack(side="left", fill="both", expand=True, padx=(24, 0))
        self.refresh()

    def _hdr(self, parent, text, right="", top=0):
        r = tk.Frame(parent, bg=BG)
        r.pack(fill="x", pady=(top, 8))
        tk.Label(r, text=text, bg=BG, fg="#bdbdbd", font=("Segoe UI", 9, "bold")).pack(side="left")
        if right:
            tk.Label(r, text=right, bg=BG, fg=S_MUTED, font=("Segoe UI", 8)).pack(side="right")
        return r

    def _row(self, rec, tags=(), btns=()):
        row = RoundFrame(self.left)
        row.pack(fill="x", pady=(0, 2))
        avatar_widget(row, self.app.avatars, rec.get("avatar", ""), 36, rec["name"], CARD,
                      offline=any(t == "Offline" for t, _ in tags)).pack(side="left", padx=10, pady=10)
        tk.Label(row, text=rec["name"], bg=CARD, fg=S_TEXT, font=F).pack(side="left")
        for text, fg in tags:
            tk.Label(row, text="  " + text, bg=CARD, fg=fg, font=FS).pack(side="left")
        for w in reversed(btns):
            w(row).pack(side="right", padx=(0, 8))

    def _set_cat(self, name):
        self.app.party.cat = name
        self.refresh()

    def refresh(self):
        P = self.app.party
        P.ensure()
        self._sig = self.app._sig("matchmaking")
        d = self.app.store.d
        me = d["me"]["steamid"]
        for w in self.left.winfo_children():
            w.destroy()
        for w in self.right.winfo_children():
            w.destroy()
        people = P.members()
        leader = P.is_leader()

        # left: party
        self._hdr(self.left, "YOUR PARTY", f"{len(people)}/{P.MAX} PLAYERS")
        for rec in people:
            tags = []
            if rec["steamid"] == P.leader:
                tags.append(("LEADER", AV_BORDER))
            self._row(rec, tags)
        if len(people) > 1:
            flat_btn(self.left, "Leave party", P.leave, bg="#1c1c1c").pack(anchor="w", pady=(6, 0))

        # incoming invites
        if P.inv_in:
            self._hdr(self.left, "PARTY INVITES", top=18)
            for sid, rec in list(P.inv_in.items()):
                self._row(rec, [("invited you", S_GREEN)],
                          [lambda p, s=sid: flat_btn(p, "Accept", lambda: P.accept(s), bg="#2a2a2a"),
                           lambda p, s=sid: flat_btn(p, "Decline", lambda: P.decline(s), bg="#2a2a2a")])

        # invite friends
        self._hdr(self.left, "INVITE FRIENDS", top=18)
        in_party = set(P.people)
        friends = [r for k, r in d["friends"].items() if k not in in_party]
        if not leader:
            tk.Label(self.left, text="Only the party leader can invite.", bg=BG, fg=S_MUTED,
                     font=FS).pack(anchor="w")
        elif len(people) >= P.MAX:
            tk.Label(self.left, text="Party is full.", bg=BG, fg=S_MUTED, font=FS).pack(anchor="w")
        elif not friends:
            tk.Label(self.left, text="No friends to invite. Add some in the Friends tab.",
                     bg=BG, fg=S_MUTED, font=FS).pack(anchor="w")
        else:
            for rec in friends:
                sid = rec["steamid"]
                if not self.app.net.is_online(sid):
                    self._row(rec, [("Offline", S_MUTED)])
                elif sid in P.inv_out:
                    self._row(rec, [], [lambda p: tk.Label(p, text="Invited", bg=CARD, fg=S_GREEN, font=FS),
                                        lambda p, r=rec: RoundBtn(p, "Cancel", lambda: P.cancel_invite(r),
                                                                  bg="#2a2a2a", outer=CARD)])
                else:
                    self._row(rec, [], [lambda p, r=rec: RoundBtn(p, "+ Invite", lambda: P.invite(r),
                                                                  bg="#2a2a2a", outer=CARD)])

        # right: queue
        self._hdr(self.right, "FIND A SERVER")
        busy = P.q["busy"]
        if not leader:
            label, state = "Waiting for leader", "disabled"
        elif busy:
            label, state = "Searching\u2026", "disabled"
        else:
            label, state = "Queue", "normal"
        cats = read_categories()
        if not cats:
            P.cat = None
        elif not P.cat or P.cat.lower() not in [c.lower() for c in cats]:
            P.cat = cats[0]
        status = P.q["status"] or (f"PARTY OF {len(people)}" + (f"  \u00b7  {P.cat.upper()}" if P.cat else ""))
        y_chip, y_btn, y_txt, card_h = (26, 96, 158, 190) if cats else (0, 62, 124, 150)
        card = tk.Canvas(self.right, bg=BG, height=card_h, highlightthickness=0, bd=0)
        card.pack(fill="x")
        chip_id = None
        if cats:
            can_pick = leader and not busy
            mb = tk.Menubutton(card, text=f"{P.cat}   \u25be", bg="#2a2a2a", fg=S_TEXT,
                               activebackground="#3a3a3a", activeforeground=S_TEXT, bd=0, relief="flat",
                               cursor="hand2" if can_pick else "arrow", font=("Segoe UI", 9),
                               padx=10, pady=6, width=44, indicatoron=False,
                               state="normal" if can_pick else "disabled", disabledforeground=S_MUTED)
            menu = tk.Menu(mb, tearoff=0, bg="#2a2a2a", fg=S_TEXT, activebackground=GREEN_DK,
                           activeforeground=S_TEXT, bd=0, relief="flat", font=("Segoe UI", 9))
            for name in cats:
                menu.add_command(label=name, command=lambda n=name: self._set_cat(n))
            mb.configure(menu=menu)
            chips = mb
            chip_id = card.create_window(0, y_chip, window=chips)
        qwrap = RoundFrame(card, bg=AV_BORDER, outer=CARD, radius=3)
        qwrap._fit_w = True
        qwrap._cv.configure(width=330)
        qbtn = tk.Button(qwrap, text=label, state=state, command=P.start_queue, bg=AV_BORDER, fg=BG,
                         activebackground="#aad676", activeforeground=BG, disabledforeground="#5a7a3a",
                         bd=0, relief="flat", cursor="hand2", font=("Segoe UI", 15, "bold"),
                         width=22, pady=10)
        qbtn.pack()
        win_id = card.create_window(0, y_btn, window=qwrap._cv)
        txt_id = card.create_text(0, y_txt, text=status, fill=S_MUTED, font=("Segoe UI", 8), width=360)
        def fit(e, c=card):
            w = max(e.width, 2)
            round_poly(c, w, e.height, 4, CARD)
            if chip_id is not None:
                c.coords(chip_id, w // 2, y_chip)
            c.coords(win_id, w // 2, y_btn)
            c.coords(txt_id, w // 2, y_txt)
        card.bind("<Configure>", fit)

        res = P.q["result"]
        if res:
            box = RoundFrame(self.right)
            box.pack(fill="x", pady=(10, 0))
            tk.Label(box, text="SERVER FOUND", bg=CARD, fg=S_GREEN,
                     font=("Segoe UI", 9, "bold")).pack(pady=(16, 4))
            tk.Label(box, text=res["ip"], bg=CARD, fg=S_TEXT, font=("Consolas", 18, "bold")).pack()
            sub = f"{res['players']}/{res['max']} players"
            if res.get("map"):
                sub += f"  \u00b7  {res['map']}"
            tk.Label(box, text=sub, bg=CARD, fg=S_MUTED, font=FS).pack(pady=(2, 8))
            btn = flat_btn(box, "Copy IP", lambda: None, bg="#2a2a2a")

            def copy(ip=res["ip"], b=btn):
                self.clipboard_clear()
                self.clipboard_append("connect " + ip)
                b.configure(text="Copied!")
            btn.configure(command=copy)
            btn.pack(pady=(0, 16))


# ───────────── glue ─────────────

SIDE_BG, SIDE_SEL = "#161616", "#2a2a2a"


class Social:
    """Login + left side tabs (Inventory / Friends)."""

    def __init__(self, app, container, toast):
        self.app = app
        self.container = container
        self.toast = toast
        self.inventory = None            # set by the app after it builds its frame
        self.get_inventory = None        # () -> inventory.txt text or None
        self.set_inventory = None        # (text) -> (ok, error)
        self.store = Store()
        self.events = queue.Queue()
        self.net = P2P(self.store, self.events)
        self.party = PartyCtl(lambda: self.net, self.events)
        self.net.party_hook = self.party.handle
        self.avatars = Avatars(app)
        self.screens = {}
        self.nav = {}
        self.active = None

        self.shell = tk.Frame(container, bg=BG)
        self.side = tk.Frame(self.shell, bg=SIDE_BG, width=190)
        self.side.pack(side="left", fill="y")
        self.side.pack_propagate(False)
        self.content = tk.Frame(self.shell, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.app.after(300, self._poll)

    # events
    def _poll(self):
        refresh = False
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "refresh":
                    refresh = True
                elif ev[0] in ("error", "toast"):
                    self.toast(ev[1])
        except queue.Empty:
            pass
        if refresh:
            self.refresh_all()
        self.app.after(500, self._poll)

    def _sig(self, key):
        d, net = self.store.d, self.net
        sig = [tuple(sorted((k, r.get("name"), r.get("avatar")) for k, r in d[x].items()))
               for x in ("in", "out", "friends")]
        sig.append(tuple(sorted(k for k in d["friends"] if net.is_online(k))))
        if key == "matchmaking":
            P = self.party
            sig += [P.leader, tuple(P.people), tuple(sorted(P.inv_in)), tuple(sorted(P.inv_out)),
                    P.q["busy"], P.q["status"], repr(P.q["result"]), P.cat]
        return tuple(sig)

    def refresh_all(self):
        for key in ("friends", "matchmaking"):
            f = self.screens.get(key)
            if f is not None and f.winfo_exists() and self.active == key:
                if self._sig(key) != getattr(f, "_sig", None):   # only redraw when something changed
                    f.refresh()
        self._update_badge()

    def _update_badge(self):
        b = self.nav.get("friends")
        if b is not None:
            n = len(self.store.d["in"])
            b.configure(text="  Friends" + (f"   ({n})" if n else ""))

    # flow
    def show_start(self):
        if self.store.d.get("me"):
            self._enter()
        else:
            self.show_login()

    def show_login(self):
        self.shell.place_forget()
        self._drop("login")
        self.screens["login"] = LoginScreen(self.container, self, self._after_login)
        self.screens["login"].place(relx=0, rely=0, relwidth=1, relheight=1)

    def _do_export(self):
        text, _ok = self.export_save()
        if text:
            self.toast(text)

    def _do_import(self):
        text, _ok = self.import_save()
        if text:
            self.toast(text)

    # save data export / import (friends + profile + inventory)
    def export_save(self):
        from tkinter import filedialog
        inv = None
        try:
            inv = self.get_inventory() if self.get_inventory else None
        except Exception:
            inv = None
        path = filedialog.asksaveasfilename(
            title="Export save data", defaultextension=".json", initialfile="frad-save.json",
            filetypes=[("frad-mod save", "*.json")])
        if not path:
            return "", True
        servers = None
        try:
            if os.path.isfile(SERVERS_FILE):
                with open(SERVERS_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    servers = f.read()
        except Exception:
            servers = None
        bundle = {"frad_save": 1, "exported": int(time.time()),
                  "social": self.store.d, "inventory": inv, "servers": servers}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, indent=2)
        except Exception as e:
            return f"Export failed: {e}", False
        extra = "" if inv else " (no inventory.txt found, so inventory was not included)"
        return f"Saved friends, inventory + servers to {os.path.basename(path)}{extra}", bool(inv)

    @staticmethod
    def _clean_rec(r):
        if not isinstance(r, dict) or not re.fullmatch(r"\d{17}", str(r.get("steamid", ""))):
            return None
        return {"steamid": str(r["steamid"]), "name": str(r.get("name", r["steamid"]))[:40],
                "avatar": str(r.get("avatar", ""))[:300]}

    def import_save(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Import save data", filetypes=[("frad-mod save", "*.json"), ("All files", "*.*")])
        if not path:
            return "", True
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            soc = data["social"]
            assert data.get("frad_save") == 1 and isinstance(soc, dict)
        except Exception:
            return "That isn't a valid frad-mod save file.", False
        d = self.store.d
        me = self._clean_rec(soc.get("me")) or d.get("me")
        d["me"] = me
        for key in ("friends", "out", "in"):
            src = soc.get(key) if isinstance(soc.get(key), dict) else {}
            d[key] = {}
            for rec in src.values():
                c = self._clean_rec(rec)
                if c and (not me or c["steamid"] != me["steamid"]):
                    d[key][c["steamid"]] = c
        self.party.reset()
        self.store.save()
        msg, ok = f"Imported {len(d['friends'])} friend(s)", True
        inv = data.get("inventory")
        if isinstance(inv, str) and inv and self.set_inventory:
            wrote, err = self.set_inventory(inv)
            if wrote:
                msg += " and inventory."
            else:
                msg += f". Inventory NOT restored: {err}"
                ok = False
        elif not inv:
            msg += " (save had no inventory)."
        srv = data.get("servers")
        if isinstance(srv, str) and srv.strip():
            try:
                if os.path.isfile(SERVERS_FILE):
                    import shutil
                    shutil.copy2(SERVERS_FILE, SERVERS_FILE + ".bak")
                with open(SERVERS_FILE, "w", encoding="utf-8") as f:
                    f.write(srv)
                msg += " Servers restored."
            except Exception as e:
                msg += f" Servers NOT restored: {e}"
                ok = False
        if me:
            # restart networking + rebuild screens for the imported account
            self.net.running = False
            if self.net.mq:
                self.net.mq.close()
            self.net = P2P(self.store, self.events)
            self.net.party_hook = self.party.handle
            self._drop("friends", "matchmaking", "login")
            self._enter()
            return msg, ok
        return msg + " Log in to continue.", ok

    def _after_login(self):
        self._drop("login")
        self._enter()

    def _drop(self, *names):
        for n in names:
            w = self.screens.pop(n, None)
            if w is not None:
                w.destroy()

    def _enter(self):
        self.net.start()
        self._build_side()
        self.shell.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.show_inventory()

    def _build_side(self):
        for w in self.side.winfo_children():
            w.destroy()
        me = self.store.d["me"]
        head = tk.Frame(self.side, bg=SIDE_BG)
        head.pack(fill="x", padx=12, pady=(16, 14))
        avatar_widget(head, self.avatars, me["avatar"], 40, me["name"], SIDE_BG).pack(side="left")
        tk.Label(head, text=me["name"], bg=SIDE_BG, fg=S_TEXT, font=FB, anchor="w",
                 wraplength=110, justify="left").pack(side="left", padx=8)

        self.nav = {}
        for key, label, cmd in (("matchmaking", "  Matchmaking", self.show_matchmaking),
                                ("inventory", "  Inventory", self.show_inventory),
                                ("friends", "  Friends", self.show_friends)):
            b = tk.Button(self.side, text=label, command=cmd, bg=SIDE_BG, fg=S_MUTED,
                          activebackground=SIDE_SEL, activeforeground=S_TEXT, bd=0,
                          relief="flat", cursor="hand2", font=FB, anchor="w", padx=14, pady=10)
            b.pack(fill="x")
            self.nav[key] = b

        bar = tk.Frame(self.side, bg=SIDE_BG)
        bar.pack(side="bottom", fill="x", padx=6, pady=8)
        for text, cmd in (("Log out", self.logout), ("Backup", self.show_backup)):
            tk.Button(bar, text=text, command=cmd, bg=SIDE_BG, fg=S_MUTED,
                      activebackground=SIDE_SEL, activeforeground=S_TEXT, bd=0, relief="flat",
                      cursor="hand2", font=("Segoe UI", 9), padx=8, pady=6
                      ).pack(side="left")
        self._update_badge()

    def _show(self, key, frame):
        for w in (self.inventory, self.screens.get("friends"), self.screens.get("matchmaking"),
                  self.screens.get("backup")):
            if w is not None:
                w.place_forget()
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        for k, b in self.nav.items():
            b.configure(bg=SIDE_SEL if k == key else SIDE_BG, fg=S_TEXT if k == key else S_MUTED)
        self.active = key

    def show_friends(self):
        if "friends" not in self.screens:
            self.screens["friends"] = FriendsScreen(self.content, self, None)
        self.screens["friends"].refresh()
        self._show("friends", self.screens["friends"])

    def show_matchmaking(self):
        if "matchmaking" not in self.screens:
            self.screens["matchmaking"] = MatchScreen(self.content, self)
        self._show("matchmaking", self.screens["matchmaking"])
        self.screens["matchmaking"].refresh()

    def show_backup(self):
        if "backup" not in self.screens:
            self.screens["backup"] = BackupScreen(self.content, self)
        self._show("backup", self.screens["backup"])

    def show_inventory(self):
        self._show("inventory", self.inventory)

    def logout(self):
        self.net.running = False
        if self.net.mq:
            self.net.mq.close()
        self.net = P2P(self.store, self.events)
        self.net.party_hook = self.party.handle
        self.party.reset()
        self.store.d["me"] = None
        self.store.save()
        self._drop("friends", "matchmaking")
        self.show_login()


# ─────────────────────────────────────────────────────────
# ENTRY
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CSGOEditor()
    app.mainloop()
