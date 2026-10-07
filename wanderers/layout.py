#!/usr/bin/env python3
"""wanderers W-Corne layout — single source of truth.

Generates, from the tables below:
  w-corne-wanderers.vil      Vial saved layout (File → Load saved layout)
  xkb/symbols/wanderers      xkb option `wanderers:magic`: the 20 spare
                             scancodes the Magic layers send, 4 levels each
  xkb/rules/evdev            user rules file mapping the option
  compose-missing.txt        Compose sequences the macros need that the fleet
                             ~/.XCompose lacks (empty when none)

Run:  python3 layout.py            (from this directory)
See README.md for the design and the workflow.
"""
import json
import os
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
FLEET_XCOMPOSE = pathlib.Path("/etc/nixos/home/xcompose/XCompose")

# ---------------------------------------------------------------------------
# Board facts (from probe/wcorne-vial-def.json and probe/vialq2.py)
# ---------------------------------------------------------------------------
UID_BYTES = bytes.fromhex("f74728af31f62f36")        # Vial keyboard uid, raw
UID = struct.unpack("<Q", UID_BYTES)[0]
ROWS, COLS = 4, 12
LAYER_COUNT, MACRO_COUNT = 8, 16
VIAL_PROTOCOL, VIA_PROTOCOL = 6, 9

# Physical key order used by every layer table below:
#   row0 L(6) R(6), row1 L(6) R(6), row2 L(6) R(6), thumbs L(3) R(3)  = 42
#
# Matrix wiring, from probe/wcorne-vial-def.json (verified against the Vial
# keymap view 2026-10-07):
#   left half   rows 0-2, matrix cols 0-5          (col 0 = pinky, col 5 = inner)
#   right half  rows 0-2, matrix cols 7-11         (col 7 = inner, col 11 = ring)
#               + the OUTER pinky column on (3,9) (3,10) (3,11) for rows 0/1/2
#   thumbs      (3,3) (3,4) (3,5) | (3,6) (3,7) (3,8)
#   optional inner keys (not on this 42-key board): (3,0) (3,1) left, (0,6) (1,6) right
#   (2,6) and (3,2) do not exist in the definition at all.
def _row(r):
    return [(r, c) for c in range(6)] + [(r, c) for c in range(7, 12)] + [(3, 9 + r)]

MATRIX_ORDER = _row(0) + _row(1) + _row(2) + [(3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8)]
EXTRA_KEYS = [(3, 0), (3, 1), (0, 6), (1, 6)]   # inner keys: left (3,0) top (3,1) bottom; right (0,6) top (1,6) bottom
ABSENT = [(2, 6), (3, 2)]                        # not in the definition at all

# Inner keys on Base (beto, Vial 2026-10-07): F12 / LCtrl inside the left half,
# PrtSc / RCtrl inside the right half. Transparent on every other layer.
EXTRA_BASE = {(3, 0): "KC_F12", (3, 1): "KC_LCTRL", (0, 6): "KC_PSCREEN", (1, 6): "KC_RCTRL"}

# QMK settings (Vial QSIDs): 7 = Tapping Term (ms); 8 = Tap-Hold flags, bit 0 set
# as saved from the GUI with Permissive Hold enabled.
SETTINGS = {"7": 200, "8": 1}

L_BASE, L_LOWER, L_RAISE, L_ADJUST, L_MAGIC1, L_MAGIC2, L_MOUSE = range(7)

T, X = "KC_TRNS", "KC_NO"

def RSA(kc_hex):
    """RALT+RSFT+kc as a raw QMK keycode (Vial has no RSA(kc) template)."""
    return 0x1600 | kc_hex

# ---------------------------------------------------------------------------
# Glyph table: Magic1 / Magic2 keys that the HOST maps (xkb option).
# position -> (vial keycode, xkb keycode, L1, L2(Shift), L3(AltGr), L4(AltGr+Shift))
# Positions are Dvorak letters as typed on a Wanderers host.
# F13 is deliberately absent: the desktops bind it to `pbt practice`.
# ---------------------------------------------------------------------------
XKB_KEYS = {
    "p": ("KC_F14",          "FK14",   "π", "Π", "∝", "‰"),
    "y": ("KC_F15",          "FK15",   "θ", "Θ", "∼", "≅"),
    "f": ("KC_F16",          "FK16",   "φ", "Φ", "∫", "∮"),
    "g": ("KC_F17",          "FK17",   "γ", "Γ", "⊤", "⊥"),
    "c": ("KC_F18",          "FK18",   "χ", "Χ", "⊂", "⊃"),
    "r": ("KC_F19",          "FK19",   "ρ", "Ρ", "ℝ", "ℤ"),
    "l": ("KC_F20",          "FK20",   "λ", "Λ", "←", "↔"),
    "a": ("KC_F21",          "FK21",   "α", "Α", "∀", "∧"),
    "e": ("KC_F22",          "FK22",   "ε", "Ε", "∃", "∨"),
    "d": ("KC_F23",          "FK23",   "δ", "Δ", "∂", "∇"),
    "h": ("KC_F24",          "FK24",   "η", "Η", "⋯", "⋮"),
    "t": ("KC_RO",           "AB11",   "τ", "Τ", "⇒", "⇔"),
    "n": ("KC_KANA",         "HKTG",   "ν", "Ν", "ℕ", "ℚ"),
    "s": ("KC_JYEN",         "AE13",   "σ", "Σ", "∑", "∏"),
    "b": ("KC_HENK",         "HENK",   "β", "Β", "∪", "∩"),
    "m": ("KC_MHEN",         "MUHE",   "μ", "Μ", "𝔼", "ℙ"),
    ",": ("KC_LANG1",        "HNGL",   "“", "«", "⟨", "⟦"),
    ".": ("KC_LANG2",        "HJCV",   "”", "»", "⟩", "⟧"),
    ";": ("KC_NONUS_BSLASH", "LSGT",   "¿", "¡", "≠", "≡"),
    "-": ("KC_KP_EQUAL",     "KPEQ",   "–", "—", "÷", "∓"),
}
GREEK_POSITIONS = set("pyfgcrladehtnsbm")                 # alphabetic type (Caps Lock aware)

# Compose macros (Menu + decimal codepoint + Space). Index = Vial macro number.
MACROS = ["—", "…", "·", "→", "≤", "≥", "±", "∞", "•", "°", "×", "≈", "√", "∈", "∅", "κ"]
assert len(MACROS) == MACRO_COUNT
M = {g: "M%d" % i for i, g in enumerate(MACROS)}

def macro_actions(glyph):
    digits = str(ord(glyph))
    taps = ["KC_APPLICATION"] + ["KC_%s" % d for d in digits] + ["KC_SPACE"]
    return [["tap"] + taps]

# ---------------------------------------------------------------------------
# Layers (42 entries each, MATRIX_ORDER). Comments show what gets TYPED.
# ---------------------------------------------------------------------------
BASE = [
    "KC_GESC", "KC_Q", "KC_W", "KC_E", "KC_R", "KC_T",      "KC_Y", "KC_U", "KC_I", "KC_O", "KC_P", "KC_BSPC",
    "KC_TAB",  "KC_A", "KC_S", "KC_D", "KC_F", "KC_G",      "KC_H", "KC_J", "KC_K", "KC_L", "KC_SCLN", "KC_QUOT",
    "KC_LSFT", "KC_Z", "KC_X", "KC_C", "KC_V", "KC_B",      "KC_N", "KC_M", "KC_COMM", "KC_DOT", "KC_SLSH", "KC_RSFT",
    "KC_LGUI", "MO(%d)" % L_LOWER, "LCTL_T(KC_SPC)",        "LALT_T(KC_ENT)", "MO(%d)" % L_RAISE, "KC_RALT",
]

LOWER = [
    # `      1       2       3       4       5          6        7          8           9          0        Del
    "KC_GRV", "KC_1", "KC_2", "KC_3", "KC_4", "KC_5",    "KC_6", "KC_7", "KC_8", "KC_9", "KC_0", "KC_DEL",
    # ___    ^dead(a) `dead(o) ´dead(e) ¨dead(u) ˘dead(i)   Play   PrtSc     Menu     ~dead(n)  F13    —
    T, "RALT(KC_6)", "RALT(KC_GRV)", "RALT(KC_Q)", RSA(0x14), RSA(0x26),
        "KC_MPLY", "KC_PSCREEN", "LSFT(KC_F10)", RSA(0x35), "KC_F13", M["—"],
    # CapsW  Copy     Paste    Cut     Undo     Redo       Mute      Home      PgUp       PgDn       End     LSft
    "QK_CAPS_WORD_TOGGLE", "KC_COPY", "KC_PSTE", "KC_CUT", "KC_UNDO", "KC_AGIN",
        "KC_MUTE", "KC_HOME", "KC_PGUP", "KC_PGDN", "KC_END", "KC_LSFT",
    T, T, T,                                               "KC_VOLD", "MO(%d)" % L_ADJUST, "KC_VOLU",
]

RAISE = [
    # Esc   !        @       #        $       %          ^        &        *        (        )        Ctrl-Bspc
    "KC_ESC", "KC_EXLM", "KC_AT", "KC_HASH", "KC_DLR", "KC_PERC",
        "KC_CIRC", "KC_AMPR", "KC_ASTR", "KC_LPRN", "KC_RPRN", "LCTL(KC_BSPC)",
    # ___   F1 F2 F3 F4 F5                                 F6      /        =        [        ]        \
    T, "KC_F1", "KC_F2", "KC_F3", "KC_F4", "KC_F5",        "KC_F6", "KC_LBRC", "KC_RBRC", "KC_MINS", "KC_EQL", "KC_BSLS",
    # ___   F7 F8 F9 F10 F11                               F12     ←        ↑        ↓        →        Ins
    T, "KC_F7", "KC_F8", "KC_F9", "KC_F10", "KC_F11",      "KC_F12", "KC_LEFT", "KC_UP", "KC_DOWN", "KC_RGHT", "KC_INSERT",
    "OSL(%d)" % L_MAGIC1, "MO(%d)" % L_ADJUST, "OSL(%d)" % L_MAGIC2,    T, T, T,
]

ADJUST = [
    # Boot    Sleep     Bri-      Bri+      Pause      NumLk         ScrLk           EEClr             7  8  9  /
    "QK_BOOT", "KC_SLEP", "KC_BRID", "KC_BRIU", "KC_PAUSE", "KC_NUMLOCK",
        "KC_SCROLLLOCK", "QK_CLEAR_EEPROM", "KC_KP_7", "KC_KP_8", "KC_KP_9", "KC_KP_SLASH",
    # CapsLk  Prev     Play      Next      Stop      Mute          Ins         Menu              4  5  6  *
    "KC_CAPSLOCK", "KC_MPRV", "KC_MPLY", "KC_MNXT", "KC_MSTP", "KC_MUTE",
        "KC_INSERT", "KC_APPLICATION", "KC_KP_4", "KC_KP_5", "KC_KP_6", "KC_KP_ASTERISK",
    # ___     Vol-     Vol+      TG(Ms)    TG(Mag1)  TG(Mag2)      ___  ___  1  2  3  -
    T, "KC_VOLD", "KC_VOLU", "TG(%d)" % L_MOUSE, "TG(%d)" % L_MAGIC1, "TG(%d)" % L_MAGIC2,
        X, X, "KC_KP_1", "KC_KP_2", "KC_KP_3", "KC_KP_MINUS",
    T, T, T,                                               "KC_KP_0", T, "KC_KP_DOT",
]

def xk(pos):            # Magic1: plain scancode -> xkb levels 1/2
    return XKB_KEYS[pos][0]

def xk2(pos):           # Magic2: AltGr+scancode -> xkb levels 3/4
    return "RALT(%s)" % XKB_KEYS[pos][0]

MAGIC1 = [
    # Exit        …        “«        ”»        πΠ        θΘ          φΦ       γΓ       χΧ       ρΡ       λΛ       ·
    "TG(%d)" % L_MAGIC1, M["…"], xk(","), xk("."), xk("p"), xk("y"),
        xk("f"), xk("g"), xk("c"), xk("r"), xk("l"), M["·"],
    # →           αΑ       ≤         εΕ        ≥         ±           δΔ       ηΗ       τΤ       νΝ       σΣ       –—
    M["→"], xk("a"), M["≤"], xk("e"), M["≥"], M["±"],
        xk("d"), xk("h"), xk("t"), xk("n"), xk("s"), xk("-"),
    # ∞           ¿¡       •         °         κ         ×           βΒ       μΜ       ≈        √        ∈        ∅
    M["∞"], xk(";"), M["•"], M["°"], M["κ"], M["×"],
        xk("b"), xk("m"), M["≈"], M["√"], M["∈"], M["∅"],
    T, T, T,                                               T, T, T,
]

MAGIC2 = [
    # Exit        .        ⟨⟦        ⟩⟧        ∝‰        ∼≅          ∫∮       ⊤⊥       ⊂⊃       ℝℤ       ←↔       .
    "TG(%d)" % L_MAGIC2, X, xk2(","), xk2("."), xk2("p"), xk2("y"),
        xk2("f"), xk2("g"), xk2("c"), xk2("r"), xk2("l"), X,
    # .           ∀∧       .         ∃∨        .         .           ∂∇       ⋯⋮       ⇒⇔       ℕℚ       ∑∏       ÷∓
    X, xk2("a"), X, xk2("e"), X, X,
        xk2("d"), xk2("h"), xk2("t"), xk2("n"), xk2("s"), xk2("-"),
    # .           ≠≡       .         .         .         .           ∪∩       𝔼ℙ       .        .        .        .
    X, xk2(";"), X, X, X, X,
        xk2("b"), xk2("m"), X, X, X, X,
    T, T, T,                                               T, T, T,
]

MOUSE = [
    "TG(%d)" % L_MOUSE, X, X, X, X, X,                     X, X, X, X, X, X,
    X, "KC_ACL0", "KC_ACL1", "KC_ACL2", X, X,              X, "KC_WH_L", "KC_WH_U", "KC_WH_D", "KC_WH_R", X,
    "KC_LSFT", X, X, X, X, X,                              X, "KC_MS_L", "KC_MS_U", "KC_MS_D", "KC_MS_R", X,
    "KC_BTN3", "KC_BTN2", "KC_BTN1",                       "KC_BTN1", "KC_BTN2", "KC_BTN3",
]

LAYERS = [BASE, LOWER, RAISE, ADJUST, MAGIC1, MAGIC2, MOUSE]
LAYER_NAMES = ["Base", "Lower", "Raise", "Adjust", "Magic1", "Magic2", "Mouse"]

# Raise: Shift + symbol row -> digit (reverse of normal). QMK ko_make_basic options.
MOD_MASK_SHIFT = 0x22
KO_OPTIONS = 0x80 | 0x07        # enabled | trigger_down | required_mod_down | negative_mod_up
KEY_OVERRIDES = [
    {"trigger": t, "replacement": r, "layers": 1 << L_RAISE, "trigger_mods": MOD_MASK_SHIFT,
     "negative_mod_mask": 0, "suppressed_mods": MOD_MASK_SHIFT, "options": KO_OPTIONS}
    for t, r in zip(
        ["KC_EXLM", "KC_AT", "KC_HASH", "KC_DLR", "KC_PERC", "KC_CIRC", "KC_AMPR", "KC_ASTR", "KC_LPRN", "KC_RPRN"],
        ["KC_1", "KC_2", "KC_3", "KC_4", "KC_5", "KC_6", "KC_7", "KC_8", "KC_9", "KC_0"])
]

# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------
# Vial's own spelling of the keycodes we use, so a layout saved from the GUI
# diffs cleanly against the generated file (`python3 layout.py --diff FILE`).
CANON = {
    "KC_SCLN": "KC_SCOLON", "KC_LSFT": "KC_LSHIFT", "KC_RSFT": "KC_RSHIFT", "KC_COMM": "KC_COMMA",
    "KC_SLSH": "KC_SLASH", "KC_SPC": "KC_SPACE", "KC_ENT": "KC_ENTER", "KC_BSPC": "KC_BSPACE",
    "KC_QUOT": "KC_QUOTE", "KC_GRV": "KC_GRAVE", "KC_PGDN": "KC_PGDOWN", "KC_DEL": "KC_DELETE",
    "KC_ESC": "KC_ESCAPE", "KC_LBRC": "KC_LBRACKET", "KC_RBRC": "KC_RBRACKET", "KC_MINS": "KC_MINUS",
    "KC_EQL": "KC_EQUAL", "KC_RGHT": "KC_RIGHT", "KC_BSLS": "KC_BSLASH", "KC_INS": "KC_INSERT",
    "KC_EXLM": "LSFT(KC_1)", "KC_AT": "LSFT(KC_2)", "KC_HASH": "LSFT(KC_3)", "KC_DLR": "LSFT(KC_4)",
    "KC_PERC": "LSFT(KC_5)", "KC_CIRC": "LSFT(KC_6)", "KC_AMPR": "LSFT(KC_7)", "KC_ASTR": "LSFT(KC_8)",
    "KC_LPRN": "LSFT(KC_9)", "KC_RPRN": "LSFT(KC_0)",
}

def canon(kc):
    if isinstance(kc, int):
        return kc if kc == -1 else "0x%04X" % kc
    if kc in CANON:
        return CANON[kc]
    if "(" in kc and kc.endswith(")"):
        outer, inner = kc[:-1].split("(", 1)
        return "%s(%s)" % (outer, canon(inner))
    return kc

EMPTY_TD = ["KC_NO", "KC_NO", "KC_NO", "KC_NO", 200]
EMPTY_COMBO = ["KC_NO"] * 5
EMPTY_KO = {"trigger": "KC_NO", "replacement": "KC_NO", "layers": 65535, "trigger_mods": 0,
            "negative_mod_mask": 0, "suppressed_mods": 0, "options": 7}
SLOTS = 32

def build_vil():
    layout = []
    for li, layer in enumerate(LAYERS + [[T] * 42] * (LAYER_COUNT - len(LAYERS))):
        assert len(layer) == 42, len(layer)
        grid = [[-1] * COLS for _ in range(ROWS)]
        for (r, c), kc in zip(MATRIX_ORDER, layer):
            grid[r][c] = canon(kc)
        for rc in EXTRA_KEYS:
            grid[rc[0]][rc[1]] = EXTRA_BASE[rc] if li == L_BASE else T
        layout.append(grid)
    overrides = [dict(ko, trigger=canon(ko["trigger"]), replacement=canon(ko["replacement"]))
                 for ko in KEY_OVERRIDES]
    return {
        "version": 1,
        "uid": UID,
        "layout": layout,
        "encoder_layout": [[] for _ in range(LAYER_COUNT)],
        "layout_options": -1,
        "macro": [macro_actions(g) for g in MACROS],
        "vial_protocol": VIAL_PROTOCOL,
        "via_protocol": VIA_PROTOCOL,
        "tap_dance": [list(EMPTY_TD) for _ in range(SLOTS)],
        "combo": [list(EMPTY_COMBO) for _ in range(SLOTS)],
        "key_override": overrides + [dict(EMPTY_KO) for _ in range(SLOTS - len(overrides))],
        "alt_repeat_key": [],
        "settings": dict(SETTINGS),
    }

POS_NAMES = ("GEsc ' , . p y f g c r l Bspc Tab a o e u i d h t n s - LSft ; q j k x b m w v z RSft "
             "L1 L2 L3 R1 R2 R3").split()
POS = {rc: n for rc, n in zip(MATRIX_ORDER, POS_NAMES)}
POS.update({(3, 0): "Lin1", (3, 1): "Lin2", (0, 6): "Rin1", (1, 6): "Rin2"})

def diff_vil(path):
    """Print what a layout saved from Vial changes relative to the tables here."""
    gen, saved = build_vil(), json.load(open(path))
    n = 0
    for li in range(LAYER_COUNT):
        for r in range(ROWS):
            for c in range(COLS):
                a = gen["layout"][li][r][c]
                b = saved["layout"][li][r][c] if li < len(saved["layout"]) else None
                if a != b:
                    n += 1
                    print("%-7s %-5s (%d,%d): %s -> %s" % (LAYER_NAMES[li] if li < len(LAYER_NAMES) else "L%d" % li,
                                                          POS.get((r, c), "?"), r, c, a, b))
    for k in ("macro", "tap_dance", "combo", "key_override", "alt_repeat_key", "encoder_layout"):
        for i, (a, b) in enumerate(zip(gen[k], saved.get(k, []))):
            if a != b:
                n += 1; print("%s #%d: %s -> %s" % (k, i, a, b))
        if len(saved.get(k, [])) != len(gen[k]):
            n += 1; print("%s: count %d -> %d" % (k, len(gen[k]), len(saved.get(k, []))))
    for q in sorted(set(gen["settings"]) | set(saved.get("settings", {})), key=int):
        a, b = gen["settings"].get(q), saved.get("settings", {}).get(q)
        if a is not None and a != b:
            n += 1; print("setting qsid %s: %s -> %s" % (q, a, b))
    print("differences:", n)
    return n

def keysym(ch):
    return "U%04X" % ord(ch)

def build_xkb_symbols():
    lines = [
        "// wanderers:magic — generated by ~/code/crkbd/wanderers/layout.py. Do not edit.",
        "// The W-Corne Magic layers send these otherwise-unused scancodes; the host",
        "// turns them into glyphs. Applied as an OPTION so it lands after inet(evdev),",
        "// which would otherwise override F14..F24 with XF86 keysyms.",
        "partial alphanumeric_keys",
        'xkb_symbols "magic" {',
    ]
    for pos, (vial, xkbname, l1, l2, l3, l4) in XKB_KEYS.items():
        typ = "FOUR_LEVEL_ALPHABETIC" if pos in GREEK_POSITIONS else "FOUR_LEVEL"
        syms = ", ".join("%-6s" % keysym(ch) for ch in (l1, l2, l3, l4))
        lines.append('    key <%s> { type[Group1] = "%s", [ %s ] }; // %s: %s %s %s %s'
                     % (xkbname, typ, syms, pos, l1, l2, l3, l4))
    lines.append("};")
    return "\n".join(lines) + "\n"

XKB_RULES = """! include %S/evdev

! option          = symbols
  wanderers:magic = +wanderers(magic)
"""

def compose_missing():
    if not FLEET_XCOMPOSE.exists():
        return ["(fleet XCompose not found at %s)" % FLEET_XCOMPOSE]
    have = set()
    for line in FLEET_XCOMPOSE.read_text().splitlines():
        if line.startswith("<Multi_key>") and "# U+" in line:
            have.add(int(line.split("# U+")[1].split()[0], 16))
    out = []
    for g in MACROS:
        if ord(g) not in have:
            seq = " ".join("<%s>" % d for d in str(ord(g)))
            out.append('<Multi_key> %s <space>\t: "%s"   # U+%04X' % (seq, g, ord(g)))
    return out

def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--diff":
        sys.exit(1 if diff_vil(sys.argv[2]) else 0)
    vil = build_vil()
    (HERE / "w-corne-wanderers.vil").write_text(json.dumps(vil, ensure_ascii=False, indent=1) + "\n")
    (HERE / "xkb" / "symbols").mkdir(parents=True, exist_ok=True)
    (HERE / "xkb" / "rules").mkdir(parents=True, exist_ok=True)
    (HERE / "xkb" / "symbols" / "wanderers").write_text(build_xkb_symbols())
    (HERE / "xkb" / "rules" / "evdev").write_text(XKB_RULES)
    missing = compose_missing()
    (HERE / "compose-missing.txt").write_text("\n".join(missing) + ("\n" if missing else ""))
    print("vil layers:", len(vil["layout"]), "macros:", len(vil["macro"]), "key overrides:", len(vil["key_override"]))
    print("xkb keys:", len(XKB_KEYS), "compose sequences missing from fleet:", len(missing))
    for m in missing:
        print("  ", m)

if __name__ == "__main__":
    main()
